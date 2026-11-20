# manim-composer

这组技能把数学或科学讲义做成讲解视频。`manim-composer` 先把素材写成两份对应的脚本，供人审阅的 `scenes.md` 和供配音、字幕与动画使用的 `video_script.json`。每句旁白都有对应的画面、屏幕文字和动画动作。

四个目录都是独立的 [Agent Skills 标准技能包](https://agentskills.io/specification)。只写分镜时，使用 `manim-composer` 即可。需要成片时，按动画引擎和配音服务选用配套技能。

| 技能 | 什么时候用 |
| --- | --- |
| [manim-composer](manim-composer/SKILL.md) | 根据素材编写分镜、逐句旁白和动画动作。 |
| [manimce-best-practices](manimce-best-practices/SKILL.md) | 项目使用 Manim Community Edition（`from manim import ...`）时，编写和渲染动画。 |
| [manimgl-best-practices](manimgl-best-practices/SKILL.md) | 项目使用 ManimGL（`from manimlib import ...`）时，编写和渲染动画。 |
| [qwen-video-narration](qwen-video-narration/SKILL.md) | 选用千问配音时，生成逐句音频、实测时间轴和同步字幕。配音脚本从本机环境变量 `DASHSCOPE_API_KEY` 读取密钥。 |

## 安装

在制作视频的项目目录运行下方命令，然后选择需要的技能和客户端。安装器会处理不同客户端的目录差异。[skills CLI 使用说明](https://github.com/vercel-labs/skills#install-a-skill)

```sh
npx skills add xiaofeifeiovo/manim-composer
```

也可以手动复制完整的技能目录，包括其中的模板、参考资料和脚本。将它放在客户端会扫描的项目目录中，例如 Claude Code 的 `.claude/skills/`、GitHub Copilot 的 `.github/skills/`，或支持共享目录的客户端的 `.agents/skills/`。安装后的文件结构应类似 `.claude/skills/manim-composer/SKILL.md`。[Claude Code 文档](https://code.claude.com/docs/en/skills#choose-where-skills-load) · [GitHub Copilot 文档](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills) · [共享目录约定](https://agentskills.io/client-implementation/adding-skills-support#where-to-scan)

## 使用

在能发现这些技能的客户端里，直接描述任务即可。

> 用 manim-composer 把这份讲义中关于 Simpson 求积公式的证明写成视频分镜和逐句旁白。请在画面上标出每一步用到了哪个条件。

如果客户端没有技能发现功能，把仓库放进它可读取的工作区，明确告诉它“请先读取 `manim-composer/SKILL.md`，按其中的分镜模板处理这份讲义”。只支持上传文件的客户端可以把技能说明、模板和所需参考资料作为附件提供。渲染阶段需要能运行对应的 Manim 引擎；千问配音需要 Python 3.10+、FFmpeg、ffprobe 和可访问千问服务的执行环境。只写分镜没有这些依赖。

技能入口和完整制作流程见 [SKILL.md](manim-composer/SKILL.md)。编写脚本时可以参照[分镜模板](manim-composer/templates/scenes-template.md)和[已填写的场景示例](manim-composer/references/scene-examples.md)。

两个动画技能各自附有许可和署名。[ManimCE 使用 MIT 许可](manimce-best-practices/LICENSE.txt)，[ManimGL 使用 CC BY-NC-SA 4.0 许可](manimgl-best-practices/LICENSE.txt)。
