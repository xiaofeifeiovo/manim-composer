# manim-composer

一个为数学和科学讲解视频编写分镜与旁白的 Codex 技能。它将素材整理成两份对应的脚本：供人审阅的 `scenes.md` 和供配音、字幕与动画制作使用的 `video_script.json`。每句旁白都有对应的画面、屏幕文字和动画动作。

## 安装与使用

将需要的技能目录复制到 `~/.codex/skills/` 下，每个目录与 `manim-composer/` 并列。只写分镜时，安装 `manim-composer` 即可。制作成片时，按项目使用的动画引擎和配音服务选择配套技能。

| 技能 | 什么时候用 |
| --- | --- |
| [manim-composer](manim-composer/SKILL.md) | 根据素材编写分镜、逐句旁白和动画动作。 |
| [manimce-best-practices](manimce-best-practices/SKILL.md) | 项目使用 Manim Community Edition（`from manim import ...`）时，编写和渲染动画。 |
| [manimgl-best-practices](manimgl-best-practices/SKILL.md) | 项目使用 ManimGL（`from manimlib import ...`）时，编写和渲染动画。 |
| [qwen-video-narration](qwen-video-narration/SKILL.md) | 选用千问配音时，生成逐句音频、实测时间轴和同步字幕。配音脚本从本机环境变量 `DASHSCOPE_API_KEY` 读取密钥。 |

在 Codex 中可以这样调用：

> 用 $manim-composer 把这份讲义中关于 Simpson 求积公式的证明写成视频分镜和逐句旁白。请在画面上标出每一步用到了哪个条件。

技能入口和完整制作流程见 [SKILL.md](manim-composer/SKILL.md)。编写脚本时可以参照[分镜模板](manim-composer/templates/scenes-template.md)和[已填写的场景示例](manim-composer/references/scene-examples.md)。

两个动画技能各自附有许可和署名。[ManimCE 使用 MIT 许可](manimce-best-practices/LICENSE.txt)，[ManimGL 使用 CC BY-NC-SA 4.0 许可](manimgl-best-practices/LICENSE.txt)。
