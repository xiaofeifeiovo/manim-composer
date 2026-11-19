# Scene Examples

Example scene ideas from 3b1b-style videos. These are conceptual sketches, not production scripts. Their durations are editorial estimates. Expand narration notes into exact sentence-level narration, screen text, silent notes and animation actions using [the current template](../templates/scenes-template.md); obtain actual audio timestamps before implementing timed animation.

---

## Example 1: Explaining the Dot Product

### Scene 1: The Question
**Duration**: ~30 seconds
**Purpose**: Hook the viewer with the mystery

**Visual Elements**
- Two vectors a and b drawn as arrows
- The dot product formula: a · b = |a||b|cos(θ)
- Question mark animation

**Content**
Open on two vectors. Show the formula. Pose the question: "Why does multiplying components and adding them give you something related to the angle between vectors?"

**Narration Notes**
Tone: curious, slightly puzzled. Emphasize that the formula seems arbitrary.

**Technical Notes**
- Use Arrow for vectors
- MathTex for formula
- Indicate() on the cos(θ) term

---

### Scene 2: Geometric Interpretation
**Duration**: ~90 seconds
**Purpose**: Show projection interpretation

**Visual Elements**
- Vector a (horizontal, blue)
- Vector b (angled, green)
- Projection of b onto a (dashed line)
- Right angle marker
- Length labels

**Content**
Show that a · b equals |a| times the projection of b onto a. Animate the projection dropping down. Show this equals |a||b|cos(θ) geometrically.

**Narration Notes**
"The dot product measures how much one vector goes in the direction of another."

**Technical Notes**
- DashedLine for projection
- RightAngle mobject
- animate.rotate() for showing different angles

---

### Scene 3: Numeric Connection
**Duration**: ~60 seconds
**Purpose**: Connect geometry to algebra

**Visual Elements**
- Coordinate grid
- Vector a = [a₁, a₂]
- Vector b = [b₁, b₂]
- Components highlighted

**Content**
Show vectors on grid with components labeled. Demonstrate why a₁b₁ + a₂b₂ equals the geometric interpretation. Use specific numbers.

**Narration Notes**
Walk through calculation slowly. "Let's see why the algebra matches the geometry."

**Technical Notes**
- NumberPlane or Axes
- Brace for component labels
- TransformMatchingTex for equation steps

---

## Example 2: Introduction to Fourier Series

### Scene 1: The Hook
**Duration**: ~45 seconds
**Purpose**: Show the surprising result

**Visual Elements**
- A square wave (sharp corners)
- Sum of smooth sine waves
- Morphing animation between them

**Content**
"You can build a square wave—something with sharp corners—from perfectly smooth sine waves." Show the result first, then promise to explain how.

**Narration Notes**
Tone: wonder, slight disbelief. This should feel surprising.

**Technical Notes**
- ParametricFunction for waves
- Transform animation for the morph
- Consider showing 1, 3, 5 terms building up

---

### Scene 2: Building Blocks
**Duration**: ~120 seconds
**Purpose**: Introduce sine waves as basis

**Visual Elements**
- Single sine wave
- Frequency visualization (faster oscillation)
- Amplitude visualization (taller/shorter)
- Phase visualization (shifting left/right)

**Content**
Introduce the three parameters: frequency, amplitude, phase. Show each one separately, then combine.

**Narration Notes**
Go slow. "A sine wave has three knobs we can adjust..."

**Technical Notes**
- ValueTracker for animating parameters
- Updaters to make wave respond to trackers
- Labels for each parameter

---

### Scene 3: Superposition
**Duration**: ~90 seconds
**Purpose**: Show waves can be added

**Visual Elements**
- Two sine waves (different colors)
- Their sum (third color)
- Point-by-point addition visualization

**Content**
Show that adding waves means adding their heights at each point. Demonstrate with two specific frequencies combining.

**Narration Notes**
"Adding waves is simple—at each point, just add the heights."

**Technical Notes**
- VGroup of three function graphs
- Vertical lines showing addition at specific x values
- Animate the addition happening

---

## Example 3: Matrix as Linear Transformation

### Scene 1: Grid Transformation
**Duration**: ~60 seconds
**Purpose**: Visual foundation

**Visual Elements**
- 2D coordinate grid (NumberPlane)
- Basis vectors i-hat and j-hat (colored arrows)
- Grid lines transforming

**Content**
Show a grid. Highlight i-hat (1,0) and j-hat (0,1). Apply a transformation—watch the entire grid move while tracking where basis vectors land.

**Narration Notes**
"Watch what happens to the grid when we apply this transformation. Notice how every point moves."

**Technical Notes**
- NumberPlane with visible grid lines
- apply_matrix() method
- Keep basis vectors visually distinct

---

### Scene 2: Basis Vectors Determine Everything
**Duration**: ~90 seconds
**Purpose**: Key insight

**Visual Elements**
- Transformed i-hat and j-hat
- Arbitrary vector v as combination
- v = xi + yj visualization

**Content**
Show that knowing where i-hat and j-hat land tells you where ANY vector lands. Because v = xi + yj, the transformed v = x(new i) + y(new j).

**Narration Notes**
"Here's the key insight..." Build anticipation before the reveal.

**Technical Notes**
- Vector addition animation (tip-to-tail)
- Scaling animation for coefficients
- TransformMatchingShapes for the combination

---

## Worked Example: 从双向旋转理解余弦

这个例子展示“问题与观察任务 → 旁白 → 数学操作 → 结果来源”的对应。它不规定其他视频的句数或时长；用于实际生产时按脚本契约补齐字幕、注释和实测配音时间。

- `purpose`：连接复指数分量与实数振荡。
- `question`：两个反向旋转的单位向量为什么能合成余弦？
- `prior_understanding`：单位圆上角度 t 的点横坐标为 cos(t)；e^(it) 表示对应的单位旋转向量。缺少这些基础时先建立它们。
- `observation_task`：看见竖直分量抵消，合成结果留在实轴上。
- `incoming_state`：两个坐标方向一致的小复平面；两根长度为 1 的箭头都从正实轴出发，用不同颜色标识。
- `key_operation`：转过 t 与 −t，保持长度为 1；将副本相加，再把合成结果缩小一半。
- `outgoing_state`：保留两个分量、实轴上的半长合向量以及各项同色对应的公式。

| 句子 ID | 准确旁白示例 | 画面动作、文字与保留状态 |
|---|---|---|
| cos_001 | 先让这两根长度都是一的箭头，从正实轴出发，转过大小相同、方向相反的角度。 | 同步转动，角度标 t 与 −t；保留两种颜色和坐标方向。 |
| cos_002 | 注意，在同一时刻，它们的水平分量相等，竖直分量正好相反。 | 在非特殊角度增加分量投影，突出竖直分量；原箭头保留。 |
| cos_003 | 把它们首尾相接，竖直方向的贡献就抵消了。 | 将副本放入合成区域首尾相接，终点落在实轴上；原图继续作为参照。 |
| cos_004 | 随着两根箭头继续旋转，合成结果始终沿实轴来回运动。 | 恢复跨视图同步变化，标明合成结果范围 −2 到 2。 |
| cos_005 | 再把这个结果缩小到一半，它的实轴坐标就是余弦。 | 缩放合成结果，范围更新为 −1 到 1；显示 cos(t) = [e^(it) + e^(−it)] / 2，指数项颜色对应原分量。 |

五句依次建立对象、比较分量、实施相加、观察一般运动、连接公式。不要遗漏最后的 1/2，也不要把一个时刻的示意当成对所有角度的论证；用分量关系说明竖直抵消对任意 t 成立。

## Scene Transition Patterns

### Zoom Focus
```
Full scene → Zoom into detail → Explain → Zoom out
```

### Side-by-Side Build
```
Empty left | Empty right
Add to left | Compare
Add to right | Connect them
```

### Transform Chain
```
Object A → Transform → Object B → Transform → Object C
(Maintain visual continuity throughout)
```

### Reset and Rebuild
```
Complex scene → Clear/fade most → Focus on one element → Build new complexity
```
