---
name: manim-composer
description: Plan educational videos and math or science explainers, including Manim and 3Blue1Brown-style animations. Turn source material into a storyboard and a sentence-level audiovisual script with exact narration, screen text, silent notes, and animation cues.
---

# Compose an audiovisual script

Resolve template and reference paths from the directory containing this file. Write `scenes.md` and `video_script.json` in the video project. Planning needs only the source material and this skill's resources.

## Teaching priority

The primary goal is for the viewer to understand the content and explain how its parts connect. Allow a video to become longer and its treatment more mathematically complete when prerequisites, definitions, intermediate reasoning or synthesis are needed. Do not remove essential explanation to meet an estimated duration, keep chapters uniform, reduce scene count or simplify production. Introduce added complexity in understandable stages; extra material and longer holds are not improvements by themselves. Treat an approximate duration as a planning target, report material changes, and respect an explicitly stated hard limit by resolving scope rather than silently exceeding it or compressing speech.

## Workflow

### 1. Read the source and establish the narrative

Read the user's supplied text and figures first. Track which source section supports each scene; verify technical uncertainties against appropriate primary sources. Identify the audience's existing understanding, the central question, and what they should be able to explain, predict or judge afterward. Preserve the document's meaning while adapting its prose for speech.

When establishing or revising the narrative, read [narrative patterns](references/narrative-patterns.md). Choose a route suited to a concept, a mechanism or a proof, and use a recurring concrete example when it can carry the main relationships. Each scene should resolve a question that advances the learning goal; introduce new ideas through the need they address. A conclusion may appear early, and a short explanation need not invent suspense or a failed attempt.

Use existing choices for audience, length, depth and voice. Ask only about missing choices that materially affect the script. Do not pad scenes with repeated caveats or long silent holds to reach a requested duration.

For a multi-topic explanation, organize scenes into meaningful modules. At each module's opening, name the subject, explain why it is needed, give a plain-language definition and locate its inputs, outputs and role in the larger task. Show a compact roadmap and the current module. At its close, rebuild the mechanism from the results just established, answer its opening question and explain why the next module follows. These openings and summaries belong in actual narration and visuals, not only planning metadata. A single short explanation can form one module; do not give every small scene a repetitive introduction and recap.

Establish a unified notation and representation contract before drafting derivations. Near the beginning, explain the foundational objects, how they are represented, and the index/shape conventions the viewer will need. Define later specialist symbols before first use; do not front-load a glossary of unexplained future machinery. Record symbol meanings, types/dimensions, index roles, scope and definition cues in the script. For a sequence task, explicitly connect the ordered token sequence, an individual token/vector, the stacked vector matrix and the output sequence before operating on them. Keep conventions stable; explain any change of notation, orientation or representation.

### 2. Write the complete audiovisual script

Before calling TTS or writing animation code, produce `scenes.md` and a matching `video_script.json`. Read [the script and timing contract](references/audio-first-script.md), use [the script template](templates/scenes-template.md), and read [visual techniques](references/visual-techniques.md) when designing the scenes.

For each scene, decide what the viewer should notice before choosing an animation. Record its source, question, teaching purpose, observation task, key operation and incoming/outgoing visual state using the shared contract. Explain relevant conditions and what stays unchanged. Narration supplies the reason for a step and the meaning of its result; visuals expose the objects, operations and comparisons that support it.

For every scene that consumes an earlier result, specify the producing scene, the exact carried object and its identity, and how the new operation uses it. Preserve, move, copy or explicitly restore that result on screen. A recurring example, matching colors or a generic transition sentence alone does not establish the connection. Retain numerical values, indices and shapes, or explain the change. Read the handoffs as one continuous reasoning chain before synthesizing narration; see the worked handoff in [visual techniques](references/visual-techniques.md).

Each sentence or short sentence group should advance one main thinking action, such as establishing an object, predicting, observing or explaining. A visual process may continue across several sentences; stable sentence IDs do not require a new shot or object for every sentence. Each sentence specifies:

- **Exact narration**: one complete spoken sentence, not talking points or a paragraph to split later.
- **Subtitle**: the displayed equivalent of that sentence; formulas may use mathematical notation.
- **Screen text**: exact headings, labels and formulas, with positions or associations.
- **Silent screen notes**: short qualifications or explanatory details, with placement and lifetime.
- **Animation**: what appears, changes, moves or is highlighted while that sentence is spoken, and what remains afterward.
- **Intentional pause**, if needed for a derivation, observation or transition.

The machine-readable script is the source of truth; keep the readable version consistent. Initial duration estimates are editorial estimates, never animation timing data. A request only for planning ends with this script; an authorized full-video task continues through the following stages without a routine approval gate.

### 3. Generate the voice before the animation

For a new narrated video or one whose animation can be regenerated, finish the script first, synthesize **one sentence per cue**, measure the resulting audio, and assemble the master narration with a fixed sentence timeline. Use `qwen-video-narration` when Qwen is the selected service. Only after all required sentence audio and timestamps exist should production animation be implemented and rendered.

Check that the audio cue IDs and narration match the full script. Every cue needs a measured speech start/end and a window end including any intentional pause. Do not infer sentence timestamps from character counts, divide a paragraph's duration evenly, or pass a short audition's timeline off as the whole film. If an existing recording must be retained, obtain real sentence boundaries by alignment instead of fabricating them.

### 4. Build the animation against the audio timeline

Choose `manimce-best-practices` for projects importing `manim`, or `manimgl-best-practices` for projects importing `manimlib`. For these skills and `qwen-video-narration`, use the client's skill catalog or read the named skill's `SKILL.md` from the supplied collection. Treat the master audio and sentence timestamps as the production clock. Plan reveals and transformations inside each sentence's measured window; subtitles and silent notes follow the same script IDs. Do not render long estimated scenes first and fit narration afterward.

Simplify incidental animation that overruns its window while preserving essential reasoning and object handoffs. If understanding needs more explanation or observation time, add or revise sentences and explicit pauses in the script, rebuild the audio timeline, then rerender affected animation. Do not silently move later speech, crop words or insert unplanned chapter holds. Audio locked to an existing finished video is a separate dubbing mode, not this creation workflow.

### 5. Review the result

Check script-to-source fidelity, complete sentences, mathematical meaning, note readability, and animation-to-speech correspondence. Verify that each scene advances its question, the requested observation is visible when discussed, results can be traced to their inputs, and the ending answers the central question. Distinguish a local example or visual demonstration from a general argument; retain conditions that determine the conclusion. Verify the measured timeline, whole-film decoding and caption alignment. Record listening and visual checks accurately.

Review teaching coherence before TTS and again in contiguous rendered sequences, including scene boundaries and complete module openings/closings. Check that the viewer can answer: what topic are we studying and why; what does each symbol represent; where did this value come from; how is it used next; and what mechanism have we now assembled? Inspect at least one complete example from input to output per main mechanism. Isolated keyframes, valid formulas and successful decoding do not establish comprehensibility. Repair missing definitions, handoffs or synthesis even when that increases the runtime; describe any review limitations accurately.

## Narration and silent notes

Keep narration on the question, calculation, mechanism and conclusion. Routine details such as “teaching values,” “illustrative tokenization,” “colors only track information,” or “not measured model weights” belong in small on-screen notes. Do not append a spoken disclaimer to every numerical example, repeat it at each topic's end, or put silent notes into the TTS text or spoken-subtitle track.

Use a short, legible note near the relevant diagram or in a stable corner. Show it when the example begins and keep it only while relevant; repeated examples can reuse the same persistent note. Small means subordinate typography with enough contrast to read at the delivery resolution, not invisible fine print.

Preserve any premise that changes the reasoning: for example, nonnegative weights summing to one are part of explaining a convex combination. State such a premise where it is needed, usually once, and carry it visually afterward. Move supplemental qualifications off the audio; do not replace an accurate statement with a misleading generalization.

## Visual storytelling and pacing

- Translate abstract terms into behaviors, constraints or observable consequences. Use real questions at reasoning transitions and answer them through the explanation.
- Make visual changes correspond to the relevant operation. Preserve object identity and useful references while retiring objects that no longer help the comparison.
- Establish one relationship before expanding to multiple objects or views. Arrange panels by the relationship being explained: parameters and responses, parts and whole, local and global, or premises and conclusions.
- Use color, labels, emphasis and camera movement to serve the observation task. Black backgrounds, characters, 3D, fixed color roles and a fixed layout are optional choices.
- Vary pace with conceptual difficulty within the measured audio timeline. Simplify or replay a hard-to-follow process; reserve pauses for actual inspection or derivation.
- A small scene may end at its result or next motivating question. A major topic module needs an explicit synthesis that reconnects its steps and answers its opening problem; avoid rote repetition and formulaic disclaimers.

## References

- [references/audio-first-script.md](references/audio-first-script.md): required script schema and audio-to-animation handoff for narrated production.
- [references/narrative-patterns.md](references/narrative-patterns.md): choose a narrative route and write narration that advances the question.
- [references/visual-techniques.md](references/visual-techniques.md): design observation tasks, meaningful operations, layouts and attention cues.
- [references/scene-examples.md](references/scene-examples.md): conceptual scene ideas and a worked narration/visual example; expand them into the complete sentence-level template before production.
