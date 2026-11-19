# 接口与调音经验

## 官方资料

使用时核实，模型兼容性、能力和价格可能变化：

- [Qwen-Audio-TTS / CosyVoice HTTP API](https://help.aliyun.com/zh/model-studio/cosyvoice-tts-http-api)
- [非实时语音合成与指令控制](https://help.aliyun.com/zh/model-studio/non-realtime-tts-user-guide)
- [Qwen-Audio-TTS 音色列表](https://help.aliyun.com/zh/model-studio/qwen-audio-tts-voice-list)
- [模型价格与计费规则](https://help.aliyun.com/zh/model-studio/model-pricing)

## 不同模型系列

2026-09-10 项目核实的情况：

| 项目 | Qwen-Audio-TTS | Qwen3-TTS |
|---|---|---|
| 使用过的模型 | `qwen-audio-3.0-tts-plus` | `qwen3-tts-instruct-flash` |
| HTTP 路径 | `/api/v1/services/audio/tts/SpeechSynthesizer` | `/api/v1/services/aigc/multimodal-generation/generation` |
| 指令字段 | `input.instruction`，单数 | `input.instructions`，复数，需匹配模型能力 |
| 已用声音 | `longanlufeng` | `Cherry`、`Eldric Sage` |

`longanlufeng` 当时属于 Plus，不能直接切到 Flash 并假定兼容。这个有日期的记录不能替代今后的官方查询。

北京端点当时支持 `https://dashscope.aliyuncs.com/api/v1/services/audio/tts/SpeechSynthesizer`，官方同时推荐业务空间专属域名。既有端点仍受官方支持且可用时，不因缺少 Workspace ID 阻塞工作。

## 可选预设

延续本用户在此项目中的偏好时，可用 Plus、`longanlufeng`、`rate: 1.1`，配合：

> 用低沉、厚实、带胸腔共鸣的男低音讲解。整体音高明显偏低，语气沉稳克制，保持标准普通话和清晰吐字。语速略快、连贯自然，句末自然收束。避免气声、沙哑、拖长尾音和夸张的语调。

这是候选预设，不是所有视频的默认声音，不保证固定基频。用户在新任务中的明确偏好优先。

## 数值音调的实测限制

当时 HTTP 文档列出了 `pitch`（默认 `1.0`，范围 `[0.5, 2.0]`）。但在相同模型、音色、文本、指令及 `rate: 1.1` 下，分别传入 `pitch: 0.92` 和 `pitch: 0.85`，29 段原始 WAV 全部逐字节相同。

只能判断该次调用组合中的数值调音没有可观察效果，不能推广为所有 Qwen 模型都不支持音调，也不能确定内部原因。最终改用男低音自然语言指令，返回了不同音频。后期本地变调曾让用户感觉不自然，后续版本没有再用它。

实验时保持文本和其他条件一致，比较原始字节；编码不同时比较统一采样率的解码 PCM。不同后再试听。API 内部实现未公开时，不声称一定是模型原生调音或完全没有服务端后处理。

## 计费教训

当时规则为汉字计两个字符，其他字符计一个。项目 1,566 个普通文本字符对应接口返回 2,807 个计费字符，按普通字数估价曾偏低。

报价以当前地域单价、计数规则和接口用量为准；`usage.characters` 是用量，不是账单。免费额度影响扣费，额外 ASR 与重试费用需单独考虑。
