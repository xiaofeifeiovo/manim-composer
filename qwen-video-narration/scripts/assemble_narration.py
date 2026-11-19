#!/usr/bin/env python3
"""Mux an audio-first master track, or dub an existing video from verified cue times."""
import argparse
import json
import math
from pathlib import Path
import subprocess


def probe(path):
    return json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)], text=True))


def stamp(seconds):
    ms = round(seconds * 1000)
    return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'


def prepare_timeline(rows, video_seconds, base):
    if not rows:
        raise ValueError('Timeline is empty.')
    checked = []
    for row in rows:
        if 'actual_start' not in row:
            raise ValueError('Each cue requires a verified actual_start; planned start is not substituted.')
        start = float(row['actual_start'])
        audio = Path(row['audio'])
        audio = audio if audio.is_absolute() else base / audio
        speech = float(probe(audio)['format']['duration'])
        if not math.isfinite(start) or start < 0 or not math.isfinite(speech) or speech <= 0:
            raise ValueError('Invalid cue time or audio duration.')
        checked.append({**row, 'actual_start': start, 'speech': speech, 'audio': str(audio.resolve())})
    for i, row in enumerate(checked):
        boundary = checked[i+1]['actual_start'] if i+1 < len(checked) else video_seconds
        if row['actual_start'] + row['speech'] > boundary + 1 / 48000:
            raise ValueError(f"Cue {row.get('id', i)} overlaps the next cue or video end; resynchronize before export.")
    return checked


def prepare_audio_master(document, video_seconds, base, render_path):
    if document.get('timing_basis') != 'audio':
        raise ValueError('Unknown timeline object; expected timing_basis=audio.')
    fps = float(document['fps'])
    total = float(document['total_duration'])
    if not math.isfinite(fps) or fps <= 0 or not math.isfinite(total) or total <= 0:
        raise ValueError('Invalid audio timeline duration or frame rate.')
    tolerance = 1 / fps + 1e-6
    if abs(video_seconds - total) > tolerance:
        raise ValueError('Animation duration differs from the frozen audio clock; fix the animation.')
    if render_path is None:
        raise ValueError('Audio-first export requires --render-timeline to verify rendered sentence starts.')
    rendered = json.loads(render_path.read_text(encoding='utf-8'))
    cues = document['cues']
    if not isinstance(rendered, list) or [r.get('id') for r in rendered] != [r.get('id') for r in cues]:
        raise ValueError('Rendered sentence IDs/order do not match the audio timeline.')
    for cue, actual in zip(cues, rendered):
        start = float(cue['start'])
        observed = float(actual['actual_start'])
        if not math.isfinite(observed) or abs(observed - start) > tolerance:
            raise ValueError('Rendered sentence start differs from the frozen audio clock: ' + cue['id'])
    # Convert only for the existing boundary checker; frozen start is never replaced
    # with the render observation. A shorter video must still contain all speech.
    rows = prepare_timeline([{**r, 'actual_start': r['start']} for r in cues],
                            min(video_seconds, total), base)
    for row in rows:
        if abs(row['actual_start'] + row['speech'] - float(row['end'])) > 1 / 48000 + 1e-6:
            raise ValueError('Stored speech end no longer matches its audio: ' + row['id'])
    master = Path(document['master_audio'])
    master = master if master.is_absolute() else base / master
    measured = float(probe(master)['format']['duration'])
    if abs(measured - total) > 1 / 48000 + 1e-6:
        raise ValueError('Master audio duration no longer matches the frozen timeline.')
    return rows, master.resolve()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--timeline', type=Path, required=True)
    p.add_argument('--video', type=Path, required=True)
    p.add_argument('--work-dir', type=Path, required=True)
    p.add_argument('--output-prefix', type=Path, required=True)
    p.add_argument('--overwrite', action='store_true')
    p.add_argument('--render-timeline', type=Path, help='Global rendered sentence actual_start values; required for audio-first export.')
    args = p.parse_args()
    info = probe(args.video)
    streams = [s for s in info['streams'] if s['codec_type'] == 'video']
    if not streams:
        raise ValueError('No video stream found.')
    # Prefer visual duration: a longer old audio track must not conceal overflow.
    seconds = float(streams[0].get('duration', info['format']['duration']))
    document = json.loads(args.timeline.read_text(encoding='utf-8'))
    master = None
    if isinstance(document, dict):
        rows, master = prepare_audio_master(document, seconds, args.timeline.resolve().parent, args.render_timeline)
    else:
        rows = prepare_timeline(document, seconds, args.timeline.resolve().parent)
    outputs = [Path(str(args.output_prefix) + ext) for ext in ('.mp4', '.mp3', '.srt')]
    if any(p.resolve() == args.video.resolve() for p in outputs):
        raise ValueError('Input and output video paths must differ.')
    if not args.overwrite and any(p.exists() for p in outputs):
        raise ValueError('An output exists; choose a new prefix or use an authorized --overwrite.')
    args.work_dir.mkdir(parents=True, exist_ok=True)
    args.output_prefix.parent.mkdir(parents=True, exist_ok=True)
    if master is not None:
        track = master
    else:
        track = args.work_dir / 'narration.wav'
        cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y']
        for row in rows:
            cmd += ['-i', row['audio']]
        filters = [f"[{i}:a]aresample=48000,aformat=channel_layouts=mono,adelay={round(r['actual_start']*48000)}S:all=1[a{i}]"
                   for i, r in enumerate(rows)]
        filters += [''.join(f'[a{i}]' for i in range(len(rows)))
                    + f'amix=inputs={len(rows)}:normalize=0:duration=longest,apad,atrim=duration={seconds}[out]']
        cmd += ['-filter_complex', ';'.join(filters), '-map', '[out]', '-c:a', 'pcm_s16le', str(track)]
        subprocess.run(cmd, check=True)
    flag = '-y' if args.overwrite else '-n'
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', flag,
                    '-i', str(args.video), '-i', str(track), '-map', '0:v:0', '-map', '1:a:0',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-movie_timescale', '1000', '-movflags', '+faststart', str(outputs[0])], check=True)
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', flag, '-i', str(track),
                    '-c:a', 'libmp3lame', '-q:a', '2', str(outputs[1])], check=True)
    subtitles = '\n'.join(f"{i+1}\n{stamp(r['actual_start'])} --> {stamp(r['actual_start']+r['speech'])}\n"
                           f"{r.get('subtitle', r.get('text', ''))}\n" for i, r in enumerate(rows))
    outputs[2].write_text(subtitles, encoding='utf-8')
    print(json.dumps({'video': str(outputs[0].resolve()), 'duration': seconds, 'cues': len(rows)}, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(str(exc)) from None
