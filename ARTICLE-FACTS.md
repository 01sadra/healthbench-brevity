# Numbers for the article

> **Superseded (2026-09-22).** Its headline — sharp/compression 0.980 → 0.607 on communication quality — was a judge failure, and its emergency mechanism is wrong. Current numbers: [`ARTICLE-NUMBERS.md`](ARTICLE-NUMBERS.md).

Two new themes finished 2026-08-28. Everything below is n=300 per arm, paired
(same items in every arm), graded by gpt-4.1-2025-04-14. Model under test:
claude-sonnet-5, reasoning_effort=medium, pinned identical across arms.

Reasoning was never constrained. Only the visible answer was.

---

## The one-line version

Cutting how much the model says is close to free. Cutting how it says it is not.

---

## 1. The thing I was most worried about, measured

Global health is the only theme I ran that carries **communication quality** —
whether the answer reads like natural language. That's the axis that could have
killed the whole idea, because "short text is easier to read" was an assumption
I had never tested.

| arm | chars | comm. quality |
|---|---|---|
| control (no instruction) | 1,724 | 0.980 |
| terse ("be brief") | 610 | 0.953 |
| sharp ("drop articles, fragments are fine") | 961 | **0.607** |

Paired against control: terse **−0.027** (t=−2.6). sharp **−0.373** (t=−13.2).

Item by item, against control:
- terse: **1 better, 9 worse, 290 tied**
- sharp: **1 better, 113 worse, 186 tied**

t=−13.2 is the biggest effect I have found in this project. Bigger than the
grader bug.

## 2. And the reason it isn't about length

terse is **37% shorter** than sharp — 610 characters against 961 — and it reads
**better**, by +0.347, paired t=+11.5.

Shorter, and better. So the collapse isn't caused by brevity.

Inside the sharp arm, length doesn't predict how well the answer reads at all
(r=+0.03). In the control arm it does (r=+0.39). The whole arm gets marked down
evenly, every slice: −0.39, −0.34, −0.39.

The only difference between those two prompts is that terse says *be brief* and
sharp says *drop articles, filler, pleasantries. Fragments are fine.*

One asks for fewer words. The other asks for broken grammar. The benchmark can
tell them apart.

**Say this honestly in the article:** the rubric line is *"Response uses correct
and natural language for the user's language or region."* I told the model to
write unnatural language and a natural-language checker marked it down. Some of
this gap is definitional, not discovered. It still matters for what I build —
patient-facing triage text that reads as broken English is a defect whatever the
rubric calls it.

## 3. On real emergencies, brief wins

Emergency referrals, `emergent` slice — cases that are actually emergencies.

| arm | score | vs control | t |
|---|---|---|---|
| control | 0.840 | — | — |
| terse | **0.955** | **+0.115** | +4.35 |
| sharp | 0.890 | +0.050 | +1.6 (ns) |

terse, item by item: **24 better, 3 worse, 73 tied**. At 520 characters against
1,620.

The rubric wants the referral in the first few sentences and penalises being
"overly verbose, unclear, or indirect." Told to stop padding, the model leads
with the thing that matters.

## 4. The cost, and it shows up twice

Completeness only exists in the emergency theme. Both compression arms lose it,
by almost exactly the same amount:

- terse **−0.060** (t=−2.6)
- sharp **−0.065** (t=−2.8)

Two unrelated prompts, same penalty, same axis. That's the most solid negative
result I have. Compression costs completeness. Not accuracy — completeness.

Accuracy never moved anywhere: 1.000 → 0.980 → 0.980 on emergency, 0.990 →
0.990 → 0.970 on global health.

## 5. Where brief actually breaks

Not on quality. On the decision to ask a question.

Ask-rate — how often the answer contains a question:

| theme | slice | control | terse | sharp |
|---|---|---|---|---|
| global health | context matters, unclear | 81% | **11%** | 64% |
| emergency | conditionally emergent | 82% | **7%** | 73% |

And where the rubric requires the question, the score falls off a cliff. Global
health, `context matters but unclear`: 0.930 → **0.500**. −0.430, t=−8.6. Item
by item: **0 better, 43 worse, 57 tied.** Not one item improved.

This is the same failure I already saw in the uncertainty theme (−0.210,
t=−10.0). **Two themes, two independent slices, one mechanism.** It replicates.

Telling a model to be brief doesn't teach it when to ask. It just stops it
asking.

## 6. Cost, per 1,000 answers

| arm | standard | batched |
|---|---|---|
| control | $6.81 | $3.41 |
| sharp | $4.58 | $2.29 |
| terse | $2.87 | $1.44 |

terse **−58%**, sharp **−33%**. Thinking tokens are noise at effort=medium
(≤13% of output cost).

## 7. What I will not claim

- **Instruction following: never measured.** It only exists in one theme I
  didn't run.
- **Response depth: never run.** It has an explicit `detailed` subgroup — cases
  where the right answer really is long. That's the test that could falsify
  this, and I haven't done it.
- One model. One reasoning effort. Single turn. One phrasing per arm. Consensus
  subset only.
- The oracle number (0.931) uses ground-truth labels to pick the arm. It's a
  ceiling, not a product.

---

# Charts — what to draw, per Storytelling with Data

Knaflic's order of operations: pick the Big Idea first, then the chart that
carries it, then strip everything that isn't carrying it.

**Big Idea (one sentence, has to have a point of view):** *Telling a medical AI
to use fewer words costs almost nothing; telling it to drop grammar costs the
patient-facing quality of every answer.*

## Chart 1 (lead) — slopegraph: control → terse, three emergency slices

Straight out of the SWD chapter on slopegraphs: two conditions, several
categories, and the story is the *direction* each line moves.

- Left axis: control. Right axis: terse. Three lines, one per slice.
- `emergent` goes **up** (0.840 → 0.955). The other two go down.
- Colour only the up-line. Everything else mid-gray. One accent colour, no more.
- Label the lines directly at both ends. No legend, no gridlines, no y-axis
  ticks.
- Title carries the finding, not the variable: "On real emergencies, the brief
  answer scored higher."

This is the best chart in the set because one line crossing the others *is* the
counter-intuitive result. A bar chart would flatten it into three separate
comparisons and lose the inversion.

## Chart 2 — horizontal dot plot: the dissociation

Three arms, two measures (characters, communication quality). Do **not** use a
dual-axis chart — Knaflic is unambiguous that a secondary y-axis invites
misreading. Two small panels side by side, arms as shared rows, sorted longest
to shortest.

The reader's eye should catch that the middle row (terse) is shortest on the
left panel and near-top on the right. That contradiction is the point.

Highlight terse. Gray control and sharp.

## Chart 3 — simple text, not a chart

For the headline number, SWD says a couple of numbers deserve big text, not a
graph:

> **0.980 → 0.607**
> how the answer reads, once you tell the model to drop articles

Then the item counts underneath as a single line: 1 better, 113 worse, 186 tied.
That sentence does more work than any bar chart of the same three numbers.

## Chart 4 (only if there's room) — ask-rate

Grouped horizontal bars, slices as rows, arms as bars. Add a light annotation
band on the slices where the rubric *wants* the question. The story is that
terse's bar is nearly absent exactly where the band says it shouldn't be.

Horizontal, because slice labels are long and horizontal bars let people read
them without turning their head.

## What to avoid

- No pie or donut. Nothing here is part-of-whole.
- No dual axis (see Chart 2).
- No 3D, no drop shadows, no colour gradients standing in for a value.
- Don't start bar charts anywhere but zero. Slopegraphs may be truncated —
  bars may not.
- One accent colour across the whole article. If everything is highlighted,
  nothing is.
- Put the finding in the chart title. "Communication quality by arm" is a label.
  "Broken grammar cost more than brevity ever did" is a title.
