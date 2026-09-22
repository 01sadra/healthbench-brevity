# Metrics log — what we measure and why

> **Superseded (2026-09-22).** Round-one hedging metrics; values still reproduce. Current numbers: [`ARTICLE-NUMBERS.md`](ARTICLE-NUMBERS.md).

One page. Every metric in the project, what it answers, current value, and
what would count as a change. Reference grader = gpt-4.1-2025-04-14,
n=300/arm, paired (identical items across arms).

---

## 0. The thesis

> Let the model reason freely. Constrain only what it is allowed to say.
> Does answer quality survive?

Operationalised: one system-prompt sentence varies between arms. Reasoning
effort pinned identical (`medium`). Everything else held constant.

**Status: answered, and the answer reframed the question.** Quality survives
(terse −0.013, ns). But the average hides two large opposite effects. The real
finding is not about quality — it is about *behaviour*.

---

## 1. Primary metric

**`substance` score** — fraction of physician-written rubric points earned,
0–1. Axes present in this theme: `accuracy` (2 criteria/item),
`context_awareness` (1 criterion/item). No completeness or style axes exist
in the hedging theme, so the "substance-only" filter is a no-op here.

| arm | mean | paired diff vs control | t | 95% CI |
|---|---|---|---|---|
| none (control) | 0.852 | — | — | — |
| terse | 0.839 | −0.013 | −0.94 | [−0.041, +0.015] |
| sharp | 0.826 | −0.027 | −2.12 | [−0.051, −0.002] |

**Reading:** neither compressed arm meaningfully differs. This metric alone
would conclude "nothing happened." It is the *least* informative number in
the project and must not be the headline.

---

## 2. The slice metrics — where the finding lives

Three slices, 100 items each. Each rubric wants something different, so a
single behaviour cannot win all three.

| slice | rubric wants | none | terse | sharp |
|---|---|---|---|---|
| `no-uncertainty` | commit; hedging **penalised** | 0.873 | **0.980** | 0.797 |
| `any-reducible-uncertainty` | hedge **and ask** | 0.873 | 0.663 | **0.940** |
| `only-irreducible-uncertainty` | hedge; cannot resolve | 0.810 | **0.873** | 0.740 |

Paired diffs vs control. Six tests, Bonferroni α=0.0083 — **all six survive.**

| slice | terse | t | sharp | t |
|---|---|---|---|---|
| no-uncertainty | +0.107 | +6.5 | −0.077 | −3.6 |
| reducible | −0.210 | −10.0 | +0.067 | +3.6 |
| irreducible | +0.063 | +2.8 | −0.070 | −3.1 |

**Reading:** brevity is a **decisiveness ↔ curiosity dial**, not a quality
dial. terse = decisive, incurious. sharp = curious, indecisive. Direct paired
sharp−terse: −0.013, t=−0.80 — neither dominates.

---

## 3. Behavioural metric — the routing decision

**Ask-rate** = % of answers containing a question to the user. This is the
model's routing decision, observed directly rather than inferred from score.

| slice | should | none | terse | sharp |
|---|---|---|---|---|
| no-uncertainty | don't ask | 53% | 3% | **61%** |
| reducible | **ask** | 83% | 14% | **90%** |
| irreducible | don't ask | 63% | 2% | 61% |

**Routing accuracy** (two decidable slices, n=200): sharp ≈ **64%**.
- Asked when it shouldn't: **61/100** ← the entire failure
- Failed to ask when it should: 10/100

**Cost of the error, measured:** on `no-uncertainty`, sharp scores
**0.957 when it doesn't ask** and **0.694 when it does**. A self-inflicted
26-point penalty on 61% of those cases.

**This is the metric `sharp2` is designed to move.**

---

## 4. Compression metric

**Answer length in characters**, measured from stored completions — *not*
from token usage (cached generations report no usage; that artifact once made
sharp look 5% longer than control when it was 50% shorter).

| arm | chars | vs control |
|---|---|---|
| none | 1,747 | — |
| terse | 552 | −68% |
| sharp | 872 | −50% |

**Known confound:** length is not matched across arms, so "shortness causes
the dial" and "these words cause the dial" are not yet separable. A
length-matched control is outstanding work.

---

## 5. Cost metric

Per 1,000 answers, every token billed, thinking included in output
(verified: `reasoning_tokens` ⊂ `output_tokens`).

| arm | input tok | thinking | visible | $/1k std | $/1k batch |
|---|---|---|---|---|---|
| none | 247 | 17 | 615 | $6.81 | $3.41 |
| terse | 271 | 21 | 212 | $2.87 | $1.44 |
| sharp | 340 | 50 | 340 | $4.58 | $2.29 |

sharp: **−33%** cost. terse: **−58%**. Thinking is negligible at
`effort=medium` (≤13% of output cost) — the +194% thinking increase is a large
multiple of a small number. sharp's drag is its own long instruction:
**+38% input tokens on every request.**

**Scope:** holds at `effort=medium` only. At higher effort the thinking share
grows and this arithmetic must be redone.

---

## 6. Routing metric (oracle — upper bound, not deployable)

Pick the best arm per slice using the benchmark's own labels.

| | value |
|---|---|
| routed mean | **0.931** |
| control | 0.852 |
| paired diff | **+0.079, t=7.0**, CI [+0.057, +0.101] |
| chars | 623 (**−64%** vs control) |
| per-item oracle ceiling | 0.961 |
| items where a compressed arm beats control | 98/300 (33%) |

**Reading:** verbose is a compromise — mediocre everywhere because it hedges
across case types. Two short prompts, correctly routed, beat it by 8 points at
a third of the length.

**Caveat that must appear wherever this number appears:** oracle routing uses
ground-truth slice labels. A deployed system does not know the case type in
advance. This is a ceiling, not a product number.

---

## 7. Judge validity metrics

Every score depends on a model applying rubrics. Two checks.

**Cross-judge agreement** (270 criteria, gpt-4o-mini vs gpt-4.1):

| arm | agreement | net bias (mini stricter) |
|---|---|---|
| none | 81% | +0.167 |
| terse | 74% | +0.189 |
| sharp | 77% | **+0.211** |

By criterion type: factual **82–97%**; multi-step conditional **47–67%**.

**Self-consistency** (gpt-4.1, same 90 criteria twice, temp 0, cache off):
accuracy **98%**, context_awareness **97%**. → The rubric is well-posed; the
cheap judge was the noise.

**Consequence, measured:** the cheap grader produced terse = **−0.098,
t=−8.7** (a publishable-looking finding). The reference grader produced
**−0.013, ns**. Same answers, same rubrics, different judge.

**Standing rule for this project:** all primary numbers come from gpt-4.1.
gpt-4o-mini results are retained only as a two-grader robustness check.

---

## 8. `sharp_routing` — RESULT (was `sharp2`)

**Hypothesis:** sharp's clause is a *permission* and the model reads
permissions as invitations. Explicit decision + positive no-branch + prior
should cut over-asking.

**Result: 3 of 6 criteria passed. The fix worked on its target and inverted
the error.**

| criterion | sharp | sharp_routing | target | |
|---|---|---|---|---|
| ask-rate, no-uncertainty | 61% | **9%** | <20% | PASS |
| no-uncertainty score | 0.797 | **0.963** | >0.90 | PASS |
| mean | 0.826 | **0.866** | >0.852 | PASS |
| routing accuracy | 64% | 66% | >80% | FAIL |
| reducible score | 0.940 | 0.780 | ≥0.90 | FAIL |
| chars | 872 | 959 | ≤900 | FAIL |

### Full scores, all four arms (ref grader, n=300 paired)

| arm | mean | no-unc | reduc | irred | chars | vs control |
|---|---|---|---|---|---|---|
| none | 0.852 | 0.873 | 0.873 | 0.810 | 1,747 | — |
| terse | 0.839 | 0.980 | 0.663 | 0.873 | 552 | −0.013, t=−0.94 |
| sharp | 0.826 | 0.797 | 0.940 | 0.740 | 872 | −0.027, t=−2.12 |
| **sharp_routing** | **0.866** | 0.963 | 0.780 | 0.853 | 959 | **+0.013, t=+1.04** |

Best mean of any arm, at 45% fewer characters. Still inside noise (p=0.30).

### The error inverted rather than resolved

| | over-asked (no-unc) | missed (reducible) | accuracy |
|---|---|---|---|
| sharp | **61** | 10 | 64% |
| sharp_routing | **9** | **59** | 66% |

Over-asking 61→9. Missed questions 10→59. **Accuracy barely moved.** Ask-rate
on reducible collapsed 90%→41%. The prior line ("Asking is the exception") is
the prime suspect — flagged pre-run as the line to watch.

### Standing finding: prompts set a global disposition, not a per-case decision

Ask-rate by arm, across slices — every arm shows one global level, shifted:

| arm | no-unc | reducible | irreducible |
|---|---|---|---|
| terse | 3% | 14% | 2% |
| sharp_routing | 9% | 41% | 18% |
| none | 53% | 83% | 63% |
| sharp | 61% | 90% | 61% |

No arm demonstrates case-by-case judgement. Each sits at a different point on
one dial. **This is why oracle routing gains +0.079 (t=7.0):** an external
classifier does the per-case work the model will not do internally.

---

## 9. `sharp_routing_noprior` (sharp3) — RUNNING

Identical to `sharp_routing` minus the final line "A person asking a health
question wants an answer, not an interview. Asking is the exception."

**Question:** was the fix the two-branch structure, or just the prior?

| outcome | interpretation |
|---|---|
| lands between sharp and sharp_routing | structure and prior both contribute |
| ≈ sharp_routing | prior irrelevant; structure did the work |
| ≈ sharp (over-asks again) | **prior did all the work** — structure is cosmetic |

Watch: ask-rate on reducible (sharp 90% / sharp_routing 41%) is the
discriminating number.

## Guardrails for every future run

1. **Reference grader only** for primary numbers.
2. **Measure length from completions**, never from cached token usage.
3. **Paired tests**, identical items across arms.
4. **Bonferroni** when reporting the six slice tests.
5. **Report ask-rate alongside score** — the score alone hid the mechanism
   for two full rounds of this project.
6. **Label oracle results as ceilings** wherever they appear.
