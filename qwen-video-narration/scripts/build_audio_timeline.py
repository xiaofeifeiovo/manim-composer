#!/usr/bin/env python3
"""Freeze a complete sentence-level audio timeline before rendering animation.

Offline only. Requires Python 3.10+, ffmpeg, and normalized 48 kHz mono
16-bit PCM WAV cues. All outputs belong in the active project's tmp directory.
"""
import argparse
import json
import math
from pathlib import Path
import subprocess
import tempfile
import wave


RATE = 48000
SAMPLE_BYTES = 2
TIME_TOLERANCE = 1e-6
CHUNK_FRAMES = 65536


def number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{name} must be a finite number.')
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f'{name} must be a finite number.')
    return value


def script_sentences(document):
    scenes = document.get('scenes') if isinstance(document, dict) else None
    if not isinstance(scenes, list) or not scenes:
        raise ValueError('The audiovisual script requires a nonempty scenes list.')
    result, scene_ids, sentence_ids = [], set(), set()
    for scene in scenes:
        if not isinstance(scene, dict):
            raise ValueError('Each scene must be an object.')
        scene_id = scene.get('id')
        if not isinstance(scene_id, str) or not scene_id or scene_id in scene_ids:
            raise ValueError('Each scene needs a unique nonempty string id.')
        scene_ids.add(scene_id)
        sentences = scene.get('sentences')
        if not isinstance(sentences, list) or not sentences:
            raise ValueError(f'Scene {scene_id} requires a nonempty sentences list.')
        for sentence in sentences:
            if not isinstance(sentence, dict):
                raise ValueError('Each sentence must be an object.')
            sentence_id, spoken = sentence.get('id'), sentence.get('narration')
            if (not isinstance(sentence_id, str) or not sentence_id
                    or sentence_id in sentence_ids):
                raise ValueError('Sentence ids must be unique across the complete script.')
            if not isinstance(spoken, str) or not spoken.strip():
                raise ValueError(f'Sentence {sentence_id} requires nonempty narration.')
            sentence_ids.add(sentence_id)
            result.append((scene_id, sentence_id, spoken))
    return result


def wav_frames(path):
    with wave.open(str(path), 'rb') as source:
        if (source.getcomptype() != 'NONE' or source.getnchannels() != 1
                or source.getsampwidth() != SAMPLE_BYTES
                or source.getframerate() != RATE):
            raise ValueError(f'Cue audio must be 48 kHz mono 16-bit PCM WAV: {path.name}')
        frames = source.getnframes()
    if frames <= 0:
        raise ValueError(f'Cue audio is empty: {path.name}')
    return frames


def prepare_cues(rows, document, base, fps):
    expected = script_sentences(document)
    if not isinstance(rows, list) or len(rows) != len(expected):
        raise ValueError('Cues must cover every script sentence; audition subsets are not accepted.')
    prepared, elapsed_frames = [], 0
    for index, (row, (scene_id, sentence_id, spoken)) in enumerate(zip(rows, expected)):
        if not isinstance(row, dict):
            raise ValueError('Each cue must be an object.')
        if row.get('id') != sentence_id or row.get('text') != spoken:
            raise ValueError(f'Cue {index + 1} differs from the script sentence id, order, or narration.')
        if 'scene_id' in row and row['scene_id'] != scene_id:
            raise ValueError(f'Cue {sentence_id} has a different scene_id from the script.')
        subtitle = row.get('subtitle', spoken)
        if not isinstance(subtitle, str):
            raise ValueError(f'Cue {sentence_id} subtitle must be text.')
        audio_value = row.get('audio')
        if not isinstance(audio_value, str) or not audio_value:
            raise ValueError(f'Cue {sentence_id} requires an audio path.')
        audio = Path(audio_value)
        audio = (audio if audio.is_absolute() else base / audio).resolve()
        sample_frames = wav_frames(audio)
        speech = sample_frames / RATE
        reported_speech = number(row.get('speech'), f'{sentence_id}.speech')
        # A duration reported by ffprobe may be rounded. Allow at most one
        # audio sample, then retain the duration measured from PCM frames.
        if abs(reported_speech - speech) > 1 / RATE + 1e-12:
            raise ValueError(f'Cue {sentence_id} speech differs from its actual WAV sample count.')
        duration = number(row.get('duration'), f'{sentence_id}.duration')
        duration_frames = round(duration * fps)
        if (duration <= 0 or duration_frames <= 0
                or abs(duration - duration_frames / fps) > TIME_TOLERANCE):
            raise ValueError(f'Cue {sentence_id} duration must be a positive whole number of video frames.')
        duration = duration_frames / fps
        start = elapsed_frames / fps
        if abs(number(row.get('start'), f'{sentence_id}.start') - start) > TIME_TOLERANCE:
            raise ValueError(f'Cue {sentence_id} start differs from the preceding audio windows.')
        end = start + speech
        if 'end' in row and abs(number(row['end'], f'{sentence_id}.end') - end) > 1 / RATE + 1e-12:
            raise ValueError(f'Cue {sentence_id} end differs from its actual speech end.')
        window_end = (elapsed_frames + duration_frames) / fps
        if speech > duration + TIME_TOLERANCE:
            raise ValueError(f'Cue {sentence_id} speech exceeds its duration; revise the audio timeline first.')
        if sample_frames > round(window_end * RATE) - round(start * RATE):
            raise ValueError(f'Cue {sentence_id} does not fit its window on the audio sample grid.')
        cue = {key: value for key, value in row.items()
               if key not in {'usage', 'request_sha256'}}
        cue.update(scene_id=scene_id, audio=str(audio), subtitle=subtitle,
                   speech=speech, start=start, end=end, duration=duration,
                   window_end=window_end)
        prepared.append(cue)
        elapsed_frames += duration_frames
    return prepared, elapsed_frames / fps


def silence(destination, frames):
    zeros = b'\0' * (CHUNK_FRAMES * SAMPLE_BYTES)
    while frames:
        count = min(frames, CHUNK_FRAMES)
        destination.writeframesraw(zeros[:count * SAMPLE_BYTES])
        frames -= count


def write_master(path, cues, total_duration):
    written = 0
    with wave.open(str(path), 'wb') as destination:
        destination.setnchannels(1)
        destination.setsampwidth(SAMPLE_BYTES)
        destination.setframerate(RATE)
        for cue in cues:
            target = round(cue['start'] * RATE)
            if target < written:
                raise ValueError(f"Cue {cue['id']} overlaps the preceding PCM audio.")
            silence(destination, target - written)
            written = target
            with wave.open(cue['audio'], 'rb') as source:
                remaining = source.getnframes()
                if abs(remaining / RATE - cue['speech']) > 1e-12:
                    raise ValueError(f"Cue {cue['id']} audio changed after validation.")
                while remaining:
                    count = min(remaining, CHUNK_FRAMES)
                    data = source.readframes(count)
                    if len(data) != count * SAMPLE_BYTES:
                        raise ValueError(f"Cue {cue['id']} WAV data is truncated.")
                    destination.writeframesraw(data)
                    remaining -= count
                    written += count
        total_samples = round(total_duration * RATE)
        if written > total_samples:
            raise ValueError('Speech exceeds the final audio window; no audio was trimmed.')
        silence(destination, total_samples - written)


def stamp(seconds):
    milliseconds = round(seconds * 1000)
    return (f'{milliseconds // 3600000:02}:{milliseconds // 60000 % 60:02}:'
            f'{milliseconds // 1000 % 60:02},{milliseconds % 1000:03}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cues', type=Path, required=True,
                        help='Complete sentence cues from qwen_tts.py, in script order.')
    parser.add_argument('--script', type=Path, required=True,
                        help='Unified audiovisual JSON script containing scenes and sentences.')
    parser.add_argument('--output-dir', type=Path, required=True,
                        help="Output directory inside the active project's tmp directory.")
    parser.add_argument('--fps', type=float, default=30,
                        help='Animation frame rate used when preparing cue durations (default: 30).')
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args()
    if not math.isfinite(args.fps) or args.fps <= 0:
        raise ValueError('fps must be positive and finite.')
    output_dir = args.output_dir.resolve()
    if 'tmp' not in output_dir.parts:
        raise ValueError('The output directory must be inside a tmp directory.')
    rows = json.loads(args.cues.read_text(encoding='utf-8'))
    document = json.loads(args.script.read_text(encoding='utf-8'))
    cues, total_duration = prepare_cues(rows, document, args.cues.resolve().parent, args.fps)
    names = ('master.wav', 'master.mp3', 'sentences.srt', 'audio_timeline.json')
    outputs = [output_dir / name for name in names]
    inputs = {args.cues.resolve(), args.script.resolve(), *(Path(c['audio']) for c in cues)}
    if any(path.resolve() in inputs for path in outputs):
        raise ValueError('An output path would replace an input file; choose a different output directory.')
    if not args.overwrite and any(path.exists() for path in outputs):
        raise ValueError('An output exists; choose a new directory or use an authorized --overwrite.')
    output_dir.mkdir(parents=True, exist_ok=True)
    # Stage every output together; failed validation or encoding leaves prior
    # deliverables intact. Temporary content remains in the project tmp tree.
    with tempfile.TemporaryDirectory(prefix='.audio-build-', dir=output_dir) as temporary:
        staging = Path(temporary)
        write_master(staging / names[0], cues, total_duration)
        subprocess.run(['ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error', '-y',
                        '-i', str(staging / names[0]), '-c:a', 'libmp3lame', '-q:a', '2',
                        str(staging / names[1])], check=True)
        subtitles = '\n'.join(
            f"{index + 1}\n{stamp(cue['start'])} --> {stamp(cue['end'])}\n{cue['subtitle']}\n"
            for index, cue in enumerate(cues))
        (staging / names[2]).write_text(subtitles, encoding='utf-8')
        timeline = dict(timing_basis='audio', fps=args.fps, total_duration=total_duration,
                        master_audio=str(outputs[0]), cues=cues)
        (staging / names[3]).write_text(json.dumps(timeline, ensure_ascii=False, indent=2),
                                       encoding='utf-8')
        for name, output in zip(names, outputs):
            (staging / name).replace(output)
    print(json.dumps({'timeline': str(outputs[3]), 'master_audio': str(outputs[0]),
                      'sentences': len(cues), 'total_duration': total_duration,
                      'network_requests': 0}, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, EOFError, wave.Error, subprocess.CalledProcessError) as exc:
        raise SystemExit(str(exc)) from None
