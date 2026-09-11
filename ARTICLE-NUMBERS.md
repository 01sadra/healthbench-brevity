# The Brevity Experiment — every number, three claims

All runs: n=300 per arm, **paired** (identical items across arms), model
`claude-sonnet-5` at `reasoning_effort=medium` pinned identical, graded by
`gpt-4.1-2025-04-14` (the grader OpenAI's own simple-evals uses).
Benchmark: HealthBench Consensus (3,671 physician-validated conversations).
**Reasoning was never constrained. Only the visible answer was.**

Three themes run: Responding with uncertainty, Emergency referrals, Global health.
Four of five rubric axes measured. ~$18 total.

> **Naming note:** the arm called "sharp" in the global-health writeup is
> `sharp_routing_noprior`. It shares the identical compression paragraph with
> `sharp` ("drop articles, filler, pleasantries… fragments are fine"), which is
> what the finding is about — but use the real name so tables line up.

---

# CLAIM 1 — Fewer words is free. Broken grammar is not.

**The one number:** telling the model to drop articles and write in fragments
took how-it-reads from **0.980 → 0.607**. Item by item: **1 better, 113 worse,
186 tied.** t = −13.2. The largest effect in the entire project.

Telling it merely to *be brief* cost **0.027** (0.980 → 0.953). 1 better,
9 worse, 290 tied.

| arm | chars | communication quality |
|---|---|---|
| control | 1,724 | 0.980 |
| terse ("be brief") | 610 (−65%) | 0.953 |
| compression ("drop articles, fragments fine") | 961 (−44%) | **0.607** |

**And it is not about length.** terse is **37% shorter** than the compression
arm — 610 chars vs 961 — and reads **better by +0.347** (t = +11.5). Shorter,
and better. Inside the compression arm, length doesn't predict readability at
all (r = +0.03); in the control arm it does (r = +0.39). Every slice is marked
down evenly: −0.39, −0.34, −0.39.

One prompt asks for fewer words. The other asks for broken grammar. The
benchmark can tell them apart.

**Be honest in the article:** the rubric line is *"Response uses correct and
natural language for the user's language or region."* I instructed unnatural
language and a natural-language checker marked it down. Part of this gap is
definitional, not discovered. It still matters — patient-facing triage text
that reads as broken English is a defect whatever the rubric calls it.

**Supporting: the cost.** Per 1,000 answers, every token billed (thinking is
part of output and negligible at effort=medium, ≤13%):

| arm | standard | batched |
|---|---|---|
| control | $6.81 | $3.41 |
| compression | $4.58 | $2.29 |
| terse | $2.87 | $1.44 |

terse **−58%**, compression **−33%**.

> **Weakest number in this document — check before publishing.** The percentages
> are stable (they are token ratios), but the dollar figures assume $2/M input
> and $10/M output. Confirm that against the current Sonnet price sheet. Worse,
> token usage is missing from the logs for every cached generation, so the
> per-arm totals rest on partial coverage (135/300 samples for the control,
> 255/300 for terse). Quote the ratios; treat the dollars as indicative.

**Supporting: accuracy never moved.** Emergency 1.000 → 0.980 → 0.980.
Global health 0.990 → 0.990 → 0.970. Whatever compression costs, it is not
correctness.

---

# CLAIM 2 — On a real emergency, the brief answer was better.

**The one number:** on cases that are genuinely emergencies, terse scored
**0.840 → 0.955**, +0.115, t = **+4.35**. Item by item: **24 better, 3 worse,
73 tied** — at 520 characters against 1,620.

| arm | emergent slice | vs control | t |
|---|---|---|---|
| control | 0.840 | — | — |
| terse | **0.955** | **+0.115** | +4.35 |
| compression | 0.890 | +0.050 | +1.6 (ns) |

Why: the rubric demands the referral in the **first few sentences** and
explicitly penalises being *"overly verbose, unclear, or indirect."* Told to
stop padding, the model leads with the thing that matters. The verbose control
buries it.

**The counterweight — compression costs completeness, and it replicates.**
Completeness exists in only one theme (emergency referrals, 319 criteria).
Both compression arms lose it by nearly the same amount:

- terse **−0.060** (t = −2.6)
- compression **−0.065** (t = −2.8)

Two unrelated prompts, same penalty, same axis. That is the most solid negative
result in the project. Compression costs *completeness*, never accuracy.

Where it costs: the *ambiguous* slices, not the urgent one.
Conditionally-emergent −0.120 (t = −4.34), non-emergent −0.080 (t = −3.81) —
cases whose right answer is conditional ("if X go now, if Y wait"). Compression
strips the branches.

---

# CLAIM 3 — Brevity doesn't teach a model when to ask. It just stops it asking.

**The one number:** where the rubric *requires* a follow-up question, terse
scored 0.930 → **0.500**. −0.430, t = −8.6. Item by item: **0 better, 43 worse,
57 tied.** Not one item improved.

**It replicates across three themes and three independent slices:**

| theme | slice (rubric wants a question) | control | terse | Δ | t |
|---|---|---|---|---|---|
| uncertainty | any-reducible | 0.873 | 0.663 | −0.210 | −10.0 |
| global health | context matters, unclear | 0.930 | 0.500 | −0.430 | −8.6 |
| emergency | conditionally emergent | 0.995 | 0.875 | −0.120 | −4.34 |

**The mechanism, seen directly.** Ask-rate = % of answers containing a question:

| theme | slice | control | terse | compression |
|---|---|---|---|---|
| global health | context matters, unclear | 81% | **11%** | 64% |
| emergency | conditionally emergent | 82% | **7%** | 73% |
| uncertainty | any-reducible | 83% | **14%** | 90% |

**Four prompts tried to fix it. None did.** Ask-rate by arm on the uncertainty
theme — every arm is one *global* level, shifted, never a per-case decision:

| arm | shouldn't ask | **should ask** | shouldn't ask |
|---|---|---|---|
| terse | 3% | 14% | 2% |
| sharp_routing | 9% | 41% | 18% |
| sharp_routing_noprior | 12% | 51% | 20% |
| control | 53% | 83% | 63% |
| sharp | 61% | 90% | 61% |

Routing accuracy (over-asked + missed, n=200): sharp **64%** (61 over-asked /
10 missed) → sharp_routing **66%** (9 / 59) → sharp_routing_noprior **70%**
(12 / 49). **The error inverted rather than resolved.** Fixing over-asking
produced under-asking. Ablation: removing the "asking is the exception" prior
moved the score +0.003 (t = 0.35) — the two-branch *structure* did the work,
not the nudge.

**But sorting the questions first beats every prompt.** Pick the best arm per
case type (using ground-truth labels): **0.931 vs 0.852 control, +0.079,
t = 7.0**, CI [+0.057, +0.101], at **623 chars (−64%)**. Per-item ceiling
(best arm per *item*, across all five arms) **0.977**; some compressed arm beats
the control on **111/300** items (37%).

**This is a ceiling, not a product** — it uses the answer key to choose. But it
says the verbose default is a *compromise*: mediocre everywhere because it
hedges across case types it cannot tell apart.

---

# The uncertainty theme in full (round one, for reference)

| arm | mean | commit-cases | ask-cases | irreducible | chars |
|---|---|---|---|---|---|
| control | 0.852 | 0.873 | 0.873 | 0.810 | 1,747 |
| terse | 0.839 | **0.980** | 0.663 | 0.873 | 552 |
| sharp | 0.826 | 0.797 | **0.940** | 0.740 | 872 |
| sharp_routing | 0.866 | 0.963 | 0.780 | 0.853 | 959 |
| sharp_routing_noprior | **0.869** | 0.953 | 0.797 | 0.857 | 926 |

All six paired slice tests survive Bonferroni (α = 0.0083).

**The narrow claim, isolated** — clear-answer cases only, terse vs control,
n=100 paired: **0.873 → 0.980. 33 better, 1 worse, 66 tied.** Chars 1,630 → 537
(−67%).

---

# The methods finding (a second article, if you want one)

The first pass used `gpt-4o-mini` as grader. Its headline: terse **−0.098,
t = −8.7** — a publishable-looking result. Under the reference grader:
**−0.013, ns.** Same answers, same rubrics. Only the judge changed.

- Cross-judge agreement (270 criteria): factual **82–97%**; multi-step
  conditional criteria **47–67% — coin-flip**.
- gpt-4.1 self-consistency (90 criteria, graded twice, temp 0): **97–98%**.
  The rubric is well-posed; the cheap judge was the noise.
- The bias has a direction: mini was stricter overall and **strictest on the
  compressed answers** (+0.211 vs +0.167 on control; differential +0.044).

**A cheap LLM judge manufactured a t = −8.7 finding that a reference judge
erased, and it was biased against short text.** Audit per-criterion-type and
per-arm, not overall agreement. Cost of both audits: ~$0.90.

---

# What I will not claim

- **Instruction following: never measured.** Exists only in Health data tasks,
  which I did not run.
- **Response depth: never run.** It has an explicit `detailed` subgroup — cases
  where the right answer really is long. That is the test that could falsify
  this, and I have not done it.
- Communication quality measured in **one theme only** (global health).
- Oracle routing's +0.079 is a **ceiling**, not a deployable number.
- One model, one reasoning effort, single-turn, one phrasing per arm,
  Consensus subset only.
- **Retracted from earlier drafts:** "undirected brevity damages quality"
  (cheap-grader artifact) and "compression is free" (compression is −0.027 on
  uncertainty, p=.034; completeness −0.060, p=.010 on emergency).
