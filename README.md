# manim-composer

一个为数学和科学讲解视频编写分镜与旁白的 Codex 技能。它将素材整理成两份对应的脚本：供人审阅的 `scenes.md` 和供配音、字幕与动画制作使用的 `video_script.json`。每句旁白都有对应的画面、屏幕文字和动画动作。

## 安装与使用

将仓库中的 [`manim-composer/`](manim-composer/) 目录复制到 `~/.codex/skills/` 下。在 Codex 中可以这样调用：

> 用 $manim-composer 把这份讲义中关于 Simpson 求积公式的证明写成视频分镜和逐句旁白。请在画面上标出每一步用到了哪个条件。

技能入口和完整制作流程见 [SKILL.md](manim-composer/SKILL.md)。编写脚本时可以参照[分镜模板](manim-composer/templates/scenes-template.md)和[已填写的场景示例](manim-composer/references/scene-examples.md)。
