#!/usr/bin/env python3
"""Cached Qwen-Audio-TTS synthesis. Python stdlib + ffmpeg/ffprobe."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request

ENDPOINT = 'https://dashscope.aliyuncs.com/api/v1/services/audio/tts/SpeechSynthesizer'
INPUT_KEYS = {'rate', 'pitch', 'instruction', 'language_hints', 'volume', 'seed', 'enable_ssml'}


def write_json(path, value):
    part = path.with_suffix(path.suffix + '.part')
    part.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    part.replace(path)


def duration(path):
    return float(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'csv=p=0', str(path)], text=True).strip())


def narration_rows(document):
    """Extract only spoken content from the audiovisual script; retain legacy lists."""
    if isinstance(document, list):
        return document
    if not isinstance(document, dict) or not isinstance(document.get('scenes'), list):
        raise ValueError('Use a narration list or an audiovisual script with scenes.')
    rows, scene_ids = [], set()
    for scene in document['scenes']:
        if (not isinstance(scene, dict) or not isinstance(scene.get('sentences'), list)
                or not scene['sentences']):
            raise ValueError('Each scene requires a nonempty sentences list.')
        scene_id = scene.get('id')
        if not isinstance(scene_id, str) or not scene_id.strip() or scene_id in scene_ids:
            raise ValueError('Each scene requires a unique nonempty string id.')
        scene_ids.add(scene_id)
        for sentence in scene['sentences']:
            if not isinstance(sentence, dict):
                raise ValueError('Each sentence must be an object.')
            spoken = sentence.get('narration')
            row = dict(id=sentence.get('id'), text=spoken,
                       subtitle=sentence.get('subtitle', spoken), scene_id=scene.get('id'))
            if 'pause_after' in sentence:
                row['pause_after'] = sentence['pause_after']
            rows.append(row)
    return rows


def load_inputs(script_path, config_path):
    rows = narration_rows(json.loads(script_path.read_text(encoding='utf-8')))
    cfg = json.loads(config_path.read_text(encoding='utf-8'))
    if set(cfg) - {'model', 'voice', 'input', 'endpoint', 'fps', 'tail_seconds'}:
        raise ValueError('Unknown config fields; keep credentials in environment variables.')
    if not str(cfg.get('model', '')).startswith('qwen-audio-') or not cfg.get('voice'):
        raise ValueError('Provide a verified Qwen-Audio-TTS model and compatible voice.')
    extra = cfg.get('input', {})
    if not isinstance(extra, dict) or set(extra) - INPUT_KEYS:
        raise ValueError('Unsupported input fields. See --help and references/workflow.md.')
    for field in ('rate', 'pitch'):
        if field in extra and not .5 <= float(extra[field]) <= 2:
            raise ValueError(field + ' must be between 0.5 and 2.')
    endpoint = cfg.get('endpoint', ENDPOINT)
    u = urllib.parse.urlsplit(endpoint)
    host_ok = u.hostname == 'dashscope.aliyuncs.com' or re.fullmatch(
        r'[a-zA-Z0-9-]+\.cn-beijing\.maas\.aliyuncs\.com', u.hostname or '')
    if (u.scheme != 'https' or not host_ok or u.username or u.password
            or u.port not in (None, 443) or u.query or u.fragment
            or u.path != '/api/v1/services/audio/tts/SpeechSynthesizer'):
        raise ValueError('Use the verified official Beijing Qwen-Audio-TTS HTTPS endpoint.')
    fps, tail = float(cfg.get('fps', 30)), float(cfg.get('tail_seconds', .2))
    if not math.isfinite(fps) or fps <= 0 or not math.isfinite(tail) or tail < 0:
        raise ValueError('Invalid frame rate or tail duration.')
    ids = set()
    if not isinstance(rows, list) or not rows:
        raise ValueError('Narration must be a nonempty list.')
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Each narration cue must be an object.')
        sid, spoken = row.get('id'), row.get('text')
        if not isinstance(sid, str) or not sid or sid in ids:
            raise ValueError('Each cue needs a unique nonempty string id.')
        if not isinstance(spoken, str) or not spoken.strip():
            raise ValueError('Each cue needs nonempty text.')
        minimum = float(row.get('min_duration', 0))
        if not math.isfinite(minimum) or minimum < 0:
            raise ValueError('min_duration must be nonnegative and finite.')
        pause = float(row.get('pause_after', tail))
        if not math.isfinite(pause) or pause < 0:
            raise ValueError('pause_after must be nonnegative and finite.')
        if not isinstance(row.get('subtitle', spoken), str):
            raise ValueError('subtitle must be text.')
        ids.add(sid)
    cfg.update(endpoint=endpoint, fps=fps, tail_seconds=tail)
    return rows, cfg


def request_for(row, cfg):
    return {'model': cfg['model'], 'input': {
        **cfg.get('input', {}), 'text': row['text'], 'voice': cfg['voice'],
        'format': 'wav', 'sample_rate': 24000}}


def synthesize(row, cfg, work, retry_incomplete=False):
    payload = request_for(row, cfg)
    request_info = {'endpoint': cfg['endpoint'], 'payload': payload}
    digest = hashlib.sha256(json.dumps(request_info, ensure_ascii=False,
                                      sort_keys=True).encode()).hexdigest()
    cache = work / 'cache' / digest
    cache.mkdir(parents=True, exist_ok=True)
    raw, normalized, meta_path = cache / 'raw.wav', cache / 'normalized-v1.wav', cache / 'metadata.json'
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    if not raw.exists():
        attempts = meta.get('attempts', 0)
        if attempts and (not retry_incomplete or attempts >= 2):
            raise RuntimeError('Incomplete request: inspect its state before a single --retry-incomplete retry.')
        key = os.environ.get('DASHSCOPE_API_KEY')
        if not key:
            raise RuntimeError('DASHSCOPE_API_KEY is missing; configure it locally without sharing it in chat.')
        meta = {'request': request_info, 'attempts': attempts + 1, 'state': 'request_started'}
        write_json(meta_path, meta)
        req = urllib.request.Request(cfg['endpoint'], data=json.dumps(payload).encode(), headers={
            'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.load(response)
            audio_url = result.get('output', {}).get('audio', {}).get('url')
            meta.update(state='response_received', usage=result.get('usage', {}))
            write_json(meta_path, meta)
            if not audio_url:
                raise RuntimeError('Response has no audio URL.')
            # A signed URL is consumed in memory only; never logged or saved.
            parsed = urllib.parse.urlsplit(audio_url)
            if parsed.scheme not in ('http', 'https'):
                raise RuntimeError('Unsupported result URL scheme.')
            if parsed.scheme == 'http':
                audio_url = urllib.parse.urlunsplit(parsed._replace(scheme='https'))
            with urllib.request.urlopen(audio_url, timeout=120) as response:
                audio_data = response.read()
            part = cache / 'raw.wav.part'
            part.write_bytes(audio_data)
            duration(part)
            part.replace(raw)
            meta.update(state='complete', audio_sha256=hashlib.sha256(audio_data).hexdigest())
            write_json(meta_path, meta)
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f'HTTP {exc.code}; request details and signed URLs suppressed.') from None
        except Exception as exc:
            raise RuntimeError(f'Synthesis/download incomplete ({type(exc).__name__}); inspect cache state.') from None
    if not normalized.exists():
        part = cache / 'normalized-v1.part.wav'
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(raw),
                        '-af', 'loudnorm=I=-18:TP=-1.5:LRA=9', '-ar', '48000', '-ac', '1', str(part)], check=True)
        part.replace(normalized)
    speech = duration(normalized)
    pause = float(row.get('pause_after', cfg['tail_seconds']))
    length = math.ceil(max(float(row.get('min_duration', 0)), speech + pause)
                       * cfg['fps']) / cfg['fps']
    return dict(id=row['id'], text=row['text'], subtitle=row.get('subtitle', row['text']),
                audio=str(normalized.resolve()), speech=speech, duration=length,
                pause_after=pause, request_sha256=digest, usage=meta.get('usage', {}),
                **({'scene_id': row['scene_id']} if row.get('scene_id') else {}))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['plan', 'synthesize'])
    p.add_argument('--script', type=Path, required=True)
    p.add_argument('--config', type=Path, required=True)
    p.add_argument('--work-dir', type=Path)
    p.add_argument('--ids', help='Comma-separated cue ids for a small audition.')
    p.add_argument('--retry-incomplete', action='store_true', help='One bounded retry after inspecting an incomplete request.')
    args = p.parse_args()
    rows, cfg = load_inputs(args.script, args.config)
    if args.ids:
        chosen = set(args.ids.split(','))
        if chosen - {r['id'] for r in rows}:
            raise ValueError('Unknown cue ids.')
        rows = [r for r in rows if r['id'] in chosen]
    if args.action == 'plan':
        print(json.dumps({'cues': len(rows), 'text_characters_not_billing_units': sum(len(r['text']) for r in rows),
                          'model': cfg['model'], 'voice': cfg['voice'], 'network_requests': 0}, ensure_ascii=False))
        return
    if not args.work_dir:
        p.error('synthesize requires --work-dir inside the project tmp directory')
    work = args.work_dir.resolve()
    work.mkdir(parents=True, exist_ok=True)
    cues, elapsed = [], 0.0
    for row in rows:
        cue = synthesize(row, cfg, work, args.retry_incomplete)
        cue['start'] = elapsed
        cue['end'] = elapsed + cue['speech']
        cue['window_end'] = elapsed + cue['duration']
        elapsed = cue['window_end']
        cues.append(cue)
        print(f"Ready: {cue['id']} ({cue['speech']:.2f}s)", flush=True)
    write_json(work / 'cues.json', cues)
    write_json(work / 'settings.json', {**cfg, 'post_pitch_change': False, 'post_speed_change': False})
    print(f'Prepared {len(cues)} cues, {elapsed:.2f}s before any closing hold.')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, ValueError, OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(str(exc)) from None
