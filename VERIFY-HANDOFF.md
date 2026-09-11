# Verification handoff

You are being asked to **attack** the numbers in `ARTICLE-NUMBERS.md`. They are
going into a public Substack article about health-AI evaluation. Assume they are
wrong until you have recomputed them yourself. I wrote them; I am not a
trustworthy source about them.

Everything you need is on disk. **No API key and no spend is required for the
core check** — the model answers and the judge verdicts are already stored in
`logs/*.eval`.

---

## 1. What the experiment claims to be

One thesis: *let the model reason as much as it wants, constrain only the
visible output — does answer quality survive?*

- **Benchmark:** HealthBench Consensus (OpenAI), 3,671 physician-validated
  conversations. Local copy: `data/healthbench_consensus.jsonl` (37 MB).
- **Model under test:** `anthropic/claude-sonnet-5`, `reasoning_effort=medium`,
  identical in every arm. **Reasoning was never constrained.**
- **Grader:** `openai/gpt-4.1-2025-04-14` — the grader OpenAI's own
  `simple-evals` uses. (An earlier pass used `gpt-4o-mini`; see §7.)
- **Design:** paired. Every arm sees the identical 300 items in file order, so
  every comparison is within-item.
- **Manipulation:** one system message, nothing else. Arm texts are verbatim in
  `hedging_brevity.py` in the `BREVITY` dict — read them, they are the entire
  independent variable.
- **Themes run:** `hedging` (Responding with uncertainty), `emergency`
  (Emergency referrals), `global_health`. Each theme is 3 slices × 100 items.

Scoring: `hedging_brevity.py` builds **six** scorers per run — one per rubric
axis, plus a `substance` scorer (all axes except `communication_quality`). A
theme's rubrics only carry *some* axes, so an axis with no criteria returns
`NaN` for that sample. **NaN means "not measured here", never zero.** If you see
a pipeline treat NaN as 0, that is a bug and it would change everything.

---

## 2. Run this first

```bash
cd "/Users/sadra/Extended Memory/Projects/health BM Caveman" && .venv/bin/python verify.py
```

I wrote `verify.py` for you today. It reads the stored logs only — offline,
free, deterministic — and recomputes every per-slice mean, paired delta, paired
t, win/loss/tie count, character count, and ask-rate from three primitives:

| quantity | derived from | note |
|---|---|---|
| score | `sample.scores[axis].value` | NaN dropped pairwise, never zeroed |
| length | `len(sample.output.completion)` | **from the stored text, not from `usage.output_tokens`** |
| ask | `"?" in completion` | crude proxy — see blind spot B4 |

Pairing is on `sample.id` (the HealthBench record index), identical across arms.

**Do not trust `verify.py` either.** I wrote it after I wrote the claims, which
is exactly the direction of bias you should worry about. Read it, then write
your own from the raw logs and see whether you land in the same place.

---

## 3. The canonical log map — and the decoys

`logs/` holds 34 `.eval` files. **Only 11 back the published numbers.** The map
is hard-coded in `verify.py` as `CANONICAL`. Check it against `logs/` yourself,
because the traps are real:

- **`2026-08-26T15-11-15…_emergency-none…`** is a complete, successful 300/300
  run that is **not** the canonical one. It is a superseded first attempt; the
  rest of that batch died on an OpenAI `billing_hard_limit_reached`. The
  canonical emergency runs are all from **08-27**.
- **Every `hedging` log with `judge_model=openai/gpt-4o-mini`** is the discarded
  first grading pass (§7). Nine files. They produce a *different and more
  exciting* answer. Do not mix them in.
- **`2026-08-27T16-08-52…_global-health-sharp-routing-noprior…`** has
  `status=error`. Its successful re-run **shares the same run ID** and appears
  as `2026-08-28T13-18-11…`. Same ID, different file. Easy to grab the wrong one.
- Several files are 3- and 15-sample smoke tests.

Sanity gate: every canonical log must be `status=success`, `300/300` samples,
and `task_args.judge_model == "openai/gpt-4.1-2025-04-14"`.

---

## 4. Claim-by-claim: what to check and where it comes from

### Claim 1 — "Fewer words is free. Broken grammar is not."

| number | source |
|---|---|
| 0.980 → 0.607 comm. quality, t = −13.2, 1/113/186 | `global_health`, `communication_quality`, ALL slices, `sharp_routing_noprior` vs `none` |
| terse 0.953 (−0.027), 1/9/290 | same, `terse` vs `none` |
| chars 1,724 / 610 / 961 | mean `len(completion)` |
| terse beats compression by +0.347, t = +11.5 | paired, `terse` vs `sharp_routing_noprior` |
| r = +0.03 vs +0.39 | Pearson (chars, comm. quality) within arm |

The load-bearing logic is the **dissociation**: terse is 37% *shorter* and
scores *higher*. If that survives, "it's just length" is dead. Attack it there.

Also attack the construct: the rubric line is *"Response uses correct and
natural language."* I instructed unnatural language and a natural-language
checker marked it down. **How much of the 0.373 gap is tautology?** Pull 20
`sharp_routing_noprior` completions and read them. If they are competent English
that merely omits articles, the article is overclaiming. If they read as broken,
it stands. This is a judgement call I could not make objectively about my own
result — it is the single most useful thing you can do.

### Claim 2 — "On a real emergency, the brief answer was better."

| number | source |
|---|---|
| 0.840 → 0.955, +0.115, t = +4.35, 24/3/73 | `emergency`, `substance`, slice `emergent_emergency`, `terse` vs `none` |
| 520 vs 1,620 chars | same slice |
| completeness −0.060 (t=−2.6) / −0.065 (t=−2.8) | `emergency`, `completeness`, ALL, both compression arms |
| conditionally-emergent −0.120 (t=−4.34); non-emergent −0.080 (t=−3.81) | `substance`, by slice |

This is the counter-intuitive claim, so it carries the most reputational risk.
Two specific things to hit:

1. **Multiplicity.** I ran 3 themes × 3 slices × up to 5 axes × 2–4 arms. That
   is well over a hundred paired tests. `t = +4.35` on one cell is not obviously
   surviving a correction across that surface. The article only claims Bonferroni
   for the six hedging slice tests (α = 0.0083) — **it does not correct the
   emergency finding.** Count the actual comparison family and tell me whether
   +0.115 survives it. If it does not, Claim 2 should be demoted to a hypothesis.
2. **Is the mechanism real?** The article says the rubric rewards leading with
   the referral and penalises being *"overly verbose, unclear, or indirect."*
   Grep the `emergent_emergency` rubrics in `data/healthbench_consensus.jsonl`
   and confirm that language exists and carries meaningful weight. If it does
   not, the explanation is a story I told after the fact.

### Claim 3 — "Brevity doesn't teach a model when to ask. It just stops it asking."

| number | source |
|---|---|
| 0.930 → 0.500, t = −8.6, **0/43/57** | `global_health`, `substance`, slice `context-matters-but-unclear_aligned`, `terse` vs `none` |
| replication rows | `hedging`/`any-reducible-uncertainty` (−0.210, t=−10.0); `emergency`/`conditionally-emergent` (−0.120, t=−4.34) |
| ask-rate tables | `"?" in completion`, by arm × slice |
| routing accuracy 64.5% / 66.0% / 69.5% | `routing_and_oracle()` in `verify.py` |
| oracle 0.931 vs 0.852, +0.079, t = 7.0, 623 chars | same |

Routing accuracy has a **definitional choice you should challenge**: it scores
only the 200 hedging items where ask/don't-ask is unambiguous
(`any-reducible` = must ask, `no-uncertainty` = must not) and **excludes
`only-irreducible-uncertainty`**, where asking is defensible either way. That
exclusion is a judgement call that flatters the framing. Recompute including it
and see if "never above 70%" holds.

Oracle routing is labelled a ceiling in the article. Verify it is honestly
labelled everywhere it appears — it picks the arm using the ground-truth slice
label, so it is not a policy anyone could deploy.

---

## 5. Two numbers I already found wrong today

Fixed in `ARTICLE-NUMBERS.md` before handing this to you — flagged so you can
check the pattern didn't repeat elsewhere:

- **Per-item ceiling** was `0.961` and **"beats control on 98/300"**. Both were
  computed in round one over only three arms (`none`, `terse`, `sharp`), then
  left standing next to five-arm framing. Correct five-arm values: **0.977** and
  **111/300 (37%)**.
- **The cost table** ($6.81 / $4.58 / $2.87 per 1,000 answers) was computed with
  **$2/M input, $10/M output**. Verify that against the actual Sonnet price
  sheet — I did not. The ratios (−58%, −33%) are stable regardless; the dollars
  may not be.

The lesson for you: **numbers computed in an early round and never recomputed
after arms were added are the highest-risk category in this project.** Round-one
hedging numbers are the ones to re-derive from scratch.

---

## 6. My blind spots, ranked by how much damage they could do

**B1 — The analysis code was never saved.** This is the big one. Every published
slice mean, paired t, ask-rate and routing figure was originally computed in
throwaway shell heredocs during the session. They are gone. `verify.py` is a
*reconstruction* written today, after the fact, by the same author. It agrees
with the article — but agreement between an author and their own reconstruction
is weak evidence. An independent implementation is the only real check.

**B2 — Researcher degrees of freedom, unregistered.** I chose the themes, the
slices to headline, which axis to headline per claim, and which arms to compare,
*after* seeing results. `METRICS.md` pre-declared criteria for the
`sharp_routing` arm only. Nothing else was pre-registered. Claim 2 in particular
(one slice, one axis, one arm) is exactly the shape a garden of forking paths
produces. Treat every claim as exploratory unless you can show otherwise.

**B3 — No multiplicity correction outside the hedging six.** See Claim 2 above.
I never counted the full comparison family. You should.

**B4 — Ask-rate is `"?" in completion`.** A rhetorical question counts. A
question phrased as an imperative ("Tell me your age") does not. The effect
sizes are huge (81% → 11%), so the direction is safe — but any *precise* rate is
soft. Spot-check 20 completions per arm against the regex.

**B5 — Communication quality exists in one theme only.** `global_health`. Claim
1, the headline of the whole article, rests on a single theme. It has never been
replicated. Nothing on disk can fix this; it needs a new run.

**B6 — The construct-validity problem in Claim 1** (instructed unnatural
language, graded by a natural-language rubric). Flagged in the article, but I
cannot judge how much of the gap is definitional. See §4.

**B7 — Token usage in the logs is contaminated by caching.** `generate(cache=True)`
was on. Cached generations report **no** usage at all, so coverage is partial
and uneven: 135/300 samples for the hedging control, 255/300 for terse, 0/300
for `emergency-none`. **This already caused one wrong conclusion earlier** — I
briefly reported `sharp` as 5% *longer* than control when it was ~50% shorter,
because I read `usage.output_tokens` instead of the stored text. Any cost or
length number derived from `usage` in this project is suspect. Lengths in
`verify.py` come from `len(completion)` for exactly this reason.

**B8 — Single everything.** One model, one reasoning effort, one phrasing per
arm, single-turn, Consensus subset only. "It's the wording, not the compression"
is not ruled out by anything on disk.

**B9 — The falsification test was never run.** The `response_depth` theme
(`complex_responses_`) has an explicit `detailed` subgroup — cases where the
correct answer genuinely *is* long. That is the run most likely to break these
claims, and I did not do it. It is ~$7. If you have budget for one new run,
this is the one.

**B10 — Instruction following: never measured.** It only exists in
`health_data_tasks_`, which I did not run. The article says so; make sure no
sentence implies otherwise.

---

## 7. The part `verify.py` cannot check (needs API spend)

The judge-validity study behind the "second article" section:

- gpt-4o-mini headline was terse **−0.098, t = −8.7**. Under gpt-4.1: **−0.013,
  ns**. Same answers, same rubrics, only the judge changed.
- Cross-judge agreement (270 criteria): factual **82–97%**; multi-step
  conditional **47–67%** — coin-flip.
- gpt-4.1 self-consistency (90 criteria, graded twice at temp 0): **97–98%**.
- mini was biased *against short answers* (+0.211 vs +0.167; differential +0.044).

The **−0.098 vs −0.013 contrast is fully checkable offline** — both grading
passes are in `logs/` (mini pass: `2026-08-20T17-18-32` / `08-21T00-21-00`;
gpt-4.1 pass: `08-21T14-40-24` / `08-21T15-16-49`). Do check that one; it is the
most load-bearing methods claim.

The agreement and self-consistency percentages came from ad-hoc audit runs whose
per-criterion outputs I did not persist. **Those four numbers are currently
unverifiable from disk.** Either re-run the audit (~$0.90) or the article should
soften them to "in a small audit" rather than quoting figures.

---

## 8. What would actually change the conclusions

State plainly if you find any of these:

1. A NaN-as-zero bug anywhere in scoring or aggregation.
2. The slice labels don't mean what the article says (check `_theme_slice()` in
   `hedging_brevity.py` against the raw `cluster:` tags in the JSONL — the
   `rsplit("_", 1)` that strips the trailing aspect is doing real work and could
   silently merge slices).
3. Pairing is broken — `sample.id` not actually aligned across arms.
4. Claim 2's +0.115 doesn't survive an honest multiplicity correction.
5. Round-one hedging numbers don't reproduce from the gpt-4.1 logs.
6. The compression-arm completions read as fine English, making Claim 1 mostly
   tautological.

Report what fails **and what reproduces**. A clean reproduction is a result; I'd
rather publish three claims you couldn't break than four I couldn't defend.

---

## 9. Files

| file | what it is |
|---|---|
| `ARTICLE-NUMBERS.md` | the three claims — **the thing under audit** |
| `verify.py` | offline recomputation of everything checkable (written today) |
| `hedging_brevity.py` | the Inspect task: arm prompts, slicing, per-axis scorers |
| `HANDOFF.md` | fuller project context, 13 sections |
| `METRICS.md` | pre-declared criteria (`sharp_routing` only) |
| `FINDINGS.md` | **stale** — predates emergency and global_health. Ignore or delete |
| `ARTICLE-FACTS.md` | earlier round-one summary, superseded |
| `logs/*.eval` | 34 runs; 11 canonical, rest are decoys (§3) |
| `data/healthbench_consensus.jsonl` | the benchmark, for checking rubric text |

`.env` holds the API keys, `chmod 600`, gitignored. **Do not read, print, or
echo its contents** — not into a terminal, a log, or a file. If you need to run
something that spends money, say what and how much first and let Sadra approve it.
