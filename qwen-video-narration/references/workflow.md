# 从视听脚本到声音，再到动画

在视频项目根目录运行以下命令。示例中的 `QWEN_SKILL_DIR` 是一个 shell 变量，由使用者设为本技能 `SKILL.md` 所在的实际目录。例如，若技能在当前项目的 `.agents/skills/` 下，先运行 `QWEN_SKILL_DIR=".agents/skills/qwen-video-narration"`。通过其他方式安装时，换成对应目录。直接调用进程的客户端可把脚本路径作为一个参数交给 Python。

使用 Python 3.10+。处理音视频时需要 ffmpeg 和 ffprobe，只有 `synthesize` 会请求配音服务。所有试听、缓存、时间轴、检查文件与未交付的音轨放入项目 `tmp/`。

## 1. 完整视听脚本

新建讲解视频时先创建 `scenes.md` 和 `video_script.json`。使用 `manim-composer` 的完整视听脚本模板；每个场景含稳定 `id`、来源和一句一条的 `sentences`。每句必须先写准旁白及画面，不能只写“讲解要点”就开始配音或动画。

```json
{
  "title": "一个加权求和算例",
  "scenes": [{
    "id": "s01",
    "source": "原文：加权求和小节",
    "sentences": [{
      "id": "s01_001",
      "narration": "先把三个值向量，分别乘以零点二、零点三和零点五。",
      "subtitle": "先把三个值向量，分别乘以 0.2、0.3 和 0.5。",
      "screen_text": ["标题：按权重缩放", "值向量：(1,0)、(0,2)、(2,2)"],
      "screen_notes": [{"text": "数值为教学示意", "placement": "图右下角小字", "lifetime": "本场景结束"}],
      "animation": "本句开始显示值向量及权重，依次缩放并保留缩放结果。",
      "pause_after": 0.2
    }]
  }]
}
```

只有 `narration` 进入 TTS。`subtitle` 是同一句的屏幕表达；`screen_text`、`screen_notes`、`animation` 不参加合成。注释小字可以跨句保留，不在每个算例末尾重新朗读。改变小字或图形动作不会改变音频缓存键。

旧的旁白列表仍可用于固定视频配音：`[{"id":"s01_001","text":"一句旁白。","subtitle":"一句旁白。","pause_after":0.2}]`。新建动画优先使用上面的完整视听脚本。

## 2. 逐句合成声音

`config.json` 示例：

```json
{
  "model": "qwen-audio-3.0-tts-plus",
  "voice": "longanlufeng",
  "input": {"rate": 1.1, "instruction": "用自然、沉稳的成年男性中低音清晰讲解。", "language_hints": ["zh"]},
  "fps": 30,
  "tail_seconds": 0.2
}
```

每句单独合成并测量。`pause_after` 覆盖本句的全局 `tail_seconds`；未设置时默认 0.2 秒。模型音频本身可能包含句尾停顿，应结合衔接效果调整，不机械追加长暂停。观察、推导或转场需要的时间在脚本中明确写出。兼容字段 `min_duration` 默认 0，仅留给已有固定时间窗等需求，不能依据尚未实现的动画给每句强加统一最小时长。

可配置 `endpoint`；本工具使用已核实的 Qwen-Audio-TTS HTTP 端点，不用于不同端点的 Qwen3-TTS。生成参数位于 `input`，`text`、`voice`、`format`、`sample_rate` 由脚本设定，请求 24 kHz WAV；最终标准化为 48 kHz 单声道，不做本地变调或变速。密钥只通过环境配置。

```sh
python3 "$QWEN_SKILL_DIR/scripts/qwen_tts.py" plan --script video_script.json --config tmp/config.json
python3 "$QWEN_SKILL_DIR/scripts/qwen_tts.py" synthesize --script video_script.json --config tmp/config.json --work-dir tmp/voice --ids s01_001
python3 "$QWEN_SKILL_DIR/scripts/qwen_tts.py" synthesize --script video_script.json --config tmp/config.json --work-dir tmp/voice
```

`plan` 不联网。完整生成复用试听缓存。`cues.json` 每句含 `id`、`scene_id`、朗读文本、字幕、音频路径、实测 `speech`、含停顿的 `duration`、音轨 `start`、语音 `end`、`window_end`、请求摘要与用量。`start/end` 不是字数估计，`duration` 按帧率向上取整。只选部分 ID 得到的是试听子集，不能作为全片动画时间轴。

请求缓存原子保存，避免未完成请求无界重发。查明失败原因后，原有授权覆盖合理重试时，可用 `--retry-incomplete` 有界重试；不要在循环中无限使用。

## 3. 在动画前生成完整音轨与固定时间轴

```sh
python3 "$QWEN_SKILL_DIR/scripts/build_audio_timeline.py" --cues tmp/voice/cues.json --script video_script.json --output-dir tmp/audio-master --fps 30
```

工具核对完整脚本的全部句子 ID、顺序与旁白，重新读取各 WAV 的实际样本数，流式放置声音和显式停顿。拒绝试听子集、缺句、旧文本、时间漂移、截断或错误音频格式，不从字数估计时间。

输出：

- `master.wav`：按固定时间轴拼接的完整旁白，后续动画及合成以它为准。
- `master.mp3`：可试听的完整音轨。
- `sentences.srt`：每句一条字幕。
- `audio_timeline.json`：`timing_basis: "audio"`，包含 `fps`、`total_duration`、`master_audio` 和全部 `cues`；每句固定 `start`、`end`、`window_end`。

此阶段完成后再开始正式动画实现与渲染。修改旁白时重新合成受影响句子，并重建全片音轨和时间轴；修改停顿只需重建时间轴和音轨，可复用相同请求的声音缓存。小字或标签的纯画面修改无需重新合成语音。

## 4. 按声音时间制作动画

Manim 生成画面；最终合成直接复用 master 音轨。全片单场景的调度示意：

```python
frame = 1 / timeline["fps"]
render_times = []
for cue in timeline["cues"]:
    gap = cue["start"] - self.time
    if gap < -frame:
        raise RuntimeError("动画超过固定语音起点；应修改画面或返回脚本阶段")
    if gap > 0:
        self.wait(gap)
    render_times.append({"id": cue["id"], "actual_start": self.time})
    # 按此 ID 显示本句字幕、图形和仍在有效期内的静默小字。
    # 实现脚本中这句话对应的动画。
    remaining = cue["window_end"] - self.time
    if remaining < -frame:
        raise RuntimeError("动作超出本句窗口；不能顺延后续配音")
    if remaining > 0:
        self.wait(remaining)
# 保存 render_times 为 render_timeline.json，不修改 audio_timeline.json。
```

不能先渲染按字数估时的长动画，再把配音放进去。动作放不下时先简化或合并动作；确需额外停顿就回到脚本阶段修改、重建声音时间轴，然后重做相应画面。句级时间戳只保证句子边界；需要在某个术语处精确触发时，先获得真实词级对齐。

分章渲染时，以本章首句 `start` 为偏移量，先换算章内时间再调度；记录时换回全片时间。章节不得额外添加未在音轨中安排的结尾等待。拼接后检查完整视频与 master 总长相符。

## 5. 复用 master 合成成片

```sh
python3 "$QWEN_SKILL_DIR/scripts/assemble_narration.py" --timeline tmp/audio-master/audio_timeline.json --render-timeline tmp/render_timeline.json --video tmp/visuals.mp4 --work-dir tmp/export --output-prefix deliverables/narrated
```

工具核对实际画面句子起点与固定音轨，超过一帧则停止；不拿渲染时刻改写固定旁白时间。主视频总长也须与声音时间轴相符。输出 MP4、MP3、逐句 SRT，默认拒绝覆盖；已有明确替换授权时可用 `--overwrite`。合成替换原音轨，若需背景声另行混音。

固定成片换声的旧模式仍可传入带已核实 `actual_start` 的列表；它以已有视频时间窗为约束，不冒充上述新建动画流程。不得裁剪词尾来凑时间。

最后检查完整解码、句子衔接、术语、逐句字幕、小字可读性和画面含义。这里输出的是句级字幕，不宣称逐字对齐；离线工作流验证不得触发新的 API 费用。
