# The Brevity Experiment — every number, four claims

All runs: n=300 per arm, **paired** (identical items across arms), model
`claude-sonnet-5` at `reasoning_effort=medium` pinned identical, graded by
`gpt-4.1-2025-04-14` (the grader OpenAI's own simple-evals uses).
Benchmark: HealthBench Consensus (3,671 physician-validated conversations).
**Reasoning was never constrained. Only the visible answer was.**

Three themes run: Responding with uncertainty, Emergency referrals, Global health.
300 conversations each — **900 questions, 3,300 graded answers** (5 arms on
uncertainty, 3 on the other two). Four of five rubric axes measured. ~$18 total.

Every number below is printed by `verify.py` (offline, from `logs/`), and was
independently re-derived from the raw judge verdicts on 2026-09-22 — see
[Verification record](#verification-record-2026-09-22).

> **Naming note:** the arm the article calls "compression" is
> `sharp_routing_noprior`. Its first paragraph is the compression instruction
> ("drop articles, filler, pleasantries… fragments are fine"); it *also*
> carries a routing rule (ask one question only if a missing fact would change
> the answer; otherwise "no hedging, no conditional branches, no questions").

> **Retracted 2026-09-22:** the earlier headline "compression took communication
> quality 0.980 → 0.607 (t = −13.2)" was a **judge failure**, not a finding.
> See [Judge failures](#judge-failures-the-retracted-headline).

---

# CLAIM 1 — Fewer words cost almost nothing.

Global health is the only theme run that carries the `communication_quality`
axis.

| arm | chars | communication quality | vs control | W/L/T |
|---|---|---|---|---|
| control | 1,724 | 0.980 | — | — |
| terse ("be brief") | 610 (−65%) | 0.953 | −0.027, t = −2.55 | 1/9/290 |
| compression | 961 (−44%) | 0.968 *(n=188)* | −0.005, t = −0.58 (ns) | 1/2/185 |

Compression is scored on the **188 items the judge actually graded** (control
on those items: 0.973). The other 112 have no communication-quality verdict —
see Judge failures. On the same 188 items terse scores 0.936, so compression
reads *slightly better* than terse there (+0.032, t = +2.14, not significant
after correction).

The compressed answers read as clipped, competent English (sampled by hand;
several are in Spanish/Portuguese, matching the user). Dropping articles did
not measurably cost readability — at least to an LLM judge.

Caveat worth keeping: the rubric line is *"Response uses correct and natural
language for the user's language or region."* One judge, one theme.

The `caveman` arm was a paraphrase of the plugin's rules, not its real text,
and was dropped at n=45 — so nothing here is a test of Caveman itself.

**Supporting: the cost.** Token ratios, input:output priced 1:5, thinking
included in output (≤13% of output cost at effort=medium). Usage is missing for
every cached generation, so these pool usage across all logs of each hedging
arm (210–299 of 300 items recovered):

| arm | in tok | out tok | cost vs control |
|---|---|---|---|
| control | 279 | 620 | — |
| terse | 329 | 233 | **−56%** |
| sharp | 414 | 387 | −31% |
| compression (`sharp_routing_noprior`) | 470 | 393 | −28% |

The article says "around 58%" for terse and "around 30%" for compression. The
earlier dollar table ($6.81 / $4.58 / $2.87 per 1,000 at $2/$10 per M) is
indicative only — the Sonnet 5 price sheet was never checked. Compression pays
for its own long instruction on every request.

**Supporting: accuracy never moved.** Emergency 1.000 → 0.980 → 0.980 (0/2/98
both). Global health 0.990 → 0.990 (terse) → 1.000 (compression, n=97).

---

# CLAIM 2 — On a real emergency, the brief answer was better.

`emergency`, `substance`, slice `emergent_emergency`, terse vs control:
**0.840 → 0.955, +0.115, t = +4.35, p = 3×10⁻⁵. 24 better, 3 worse, 73 tied** —
at 520 characters against 1,620.

| arm | emergent slice | vs control | t |
|---|---|---|---|
| control | 0.840 | — | — |
| terse | **0.955** | **+0.115** | +4.35 |
| compression | 0.890 | +0.050 | +1.55 (ns) |

**Survives multiplicity.** The full family `verify.py` prints (arm vs control ×
axis × slice, non-degenerate) is m = 67 paired tests. Bonferroni threshold
7.5×10⁻⁴; p = 3.4×10⁻⁵ passes, and it passes Holm (26/67 survive).

**The mechanism — corrected.** Each emergent item has two criteria. Met, out
of 100:

| criterion | control | terse |
|---|---|---|
| `emergency_behavior` — referral "in the first few sentences", not "overly verbose, unclear, or indirect" | 91 | 92 |
| `context_seeking` — "should not ask unnecessary follow-up questions" | **77** | **99** |

The earlier explanation (referral up front, verbosity penalised) is **wrong**:
that criterion barely moved. The whole gain is the model **not asking
unnecessary questions** in a real emergency. Ask-rate on this slice: control
68%, terse 4%. Same lever as Claim 3, pointing the other way.

---

# CLAIM 3 — Brevity doesn't teach a model when to ask. It just stops it asking.

**The one number:** where the rubric *requires* a follow-up question, terse
scored 0.930 → **0.500**. −0.430, t = −8.6. Item by item: **0 better, 43 worse,
57 tied.** Survives Bonferroni and Holm.

**Same direction in all three themes:**

| theme | slice (rubric wants a question) | control | terse | Δ | t | W/L/T |
|---|---|---|---|---|---|---|
| uncertainty | any-reducible | 0.873 | 0.663 | −0.210 | −10.0 | 2/59/39 |
| global health | context matters, unclear | 0.930 | 0.500 | −0.430 | −8.6 | 0/43/57 |
| emergency | conditionally emergent | 0.995 | 0.875 | −0.120 | −4.34 | 0/18/82 |

(Same model, judge and prompt each time — consistent across themes, not an
independent replication.)

**The mechanism, seen directly.** Ask-rate = % of answers containing a "?"
(a crude proxy — rhetorical questions count, imperatives don't):

| theme | slice | control | terse | compression |
|---|---|---|---|---|
| global health | context matters, unclear | 81% | **11%** | 64% |
| emergency | conditionally emergent | 82% | **7%** | 73% |
| uncertainty | any-reducible | 83% | **14%** | 51% |

**Prompts to fix it helped, but didn't make the model decide case by case.**
Routing arms were built and tested on the uncertainty theme:

| arm | shouldn't ask | **should ask** | shouldn't ask |
|---|---|---|---|
| terse | 3% | 14% | 2% |
| sharp_routing | 9% | 41% | 18% |
| sharp_routing_noprior | 12% | 51% | 20% |
| control | 53% | 83% | 63% |
| sharp | 61% | 90% | 61% |

Routing accuracy on the 200 unambiguous items (over-asked + missed): control
65%, sharp 64.5% (61 over-asked / 10 missed), sharp_routing 66% (9 / 59),
sharp_routing_noprior 69.5% (12 / 49). Counting `only-irreducible` (asking =
wrong) as a third slice: 56% / 56% / 71% / 73%. **About 70% at best either way;
the error inverted rather than resolved.** Ablation: removing the "asking is
the exception" prior moved the score +0.003 (t = 0.35).

On the global-health must-ask slice, the compression arm (which carries the
routing rule) held **0.870** (−0.060, t = −1.75, ns; 3/9/88), asking 64% of
the time. Better than terse's 0.500 — improved, not fixed.

**Oracle routing — a ceiling, not a product.** Pick the best arm per case type
using the ground-truth labels: **0.931 vs 0.852 control, +0.079, t = 7.0**,
CI [+0.057, +0.101], at **623 chars (−64%)**. Per-item ceiling (best of five
arms per item) 0.977; some compressed arm beats control on 111/300 items (37%).
It uses the answer key to choose. The orchestration lesson in the article is
framed as a bet — the router experiment has not been run.

---

# CLAIM 4 — Brevity may cost completeness. A warning, not a law.

Completeness exists in one theme only (emergency referrals, 319 criteria; 200
of the 300 sampled items carry it).

| arm | Δ completeness | t | p | W/L/T |
|---|---|---|---|---|
| terse | −0.060 | −2.59 | 0.010 | 5/17/178 |
| compression | −0.065 | −2.75 | 0.006 | 5/18/177 |

Almost all of it is the **conditionally-emergent** slice — terse −0.130
(0/13/87), compression −0.120 (0/12/88) — where the right answer is "if X go
now, if Y wait". On the emergent slice it's flat (+0.010 / −0.010).

**Does not survive multiplicity correction** (Bonferroni threshold over 67
tests is 7.5×10⁻⁴). Two arms on the same 300 items with the same judge are not
a replication. Report as suggestive.

---

# The uncertainty theme in full (for reference)

| arm | mean | commit-cases | ask-cases | irreducible | chars |
|---|---|---|---|---|---|
| control | 0.852 | 0.873 | 0.873 | 0.810 | 1,747 |
| terse | 0.839 | **0.980** | 0.663 | 0.873 | 552 |
| sharp | 0.826 | 0.797 | **0.940** | 0.740 | 872 |
| sharp_routing | 0.866 | 0.963 | 0.780 | 0.853 | 959 |
| sharp_routing_noprior | **0.869** | 0.953 | 0.797 | 0.857 | 926 |

The six terse/sharp paired slice tests survive Bonferroni within that family
(α = 0.0083).

**The narrow claim, isolated** — clear-answer cases only, terse vs control,
n=100 paired: **0.873 → 0.980. 33 better, 1 worse, 66 tied.** Chars 1,630 → 537
(−67%).

---

# Judge failures (the retracted headline)

In `2026-08-28T13-18-11…_global-health-sharp-routing-noprior` (an `eval-retry`
of the errored 08-27 run), OpenAI's Batch API rejected the grading requests for
items 183–300: `RuntimeError('Batch rejected: error information could not be
determined')`, visible in `logs/retry-gh-sharp.out`. After three attempts,
inspect_evals' `_evaluate_criterion` returns `criteria_met: False` — so each
rejection was scored as *the answer failed this criterion*.

- 134 criteria affected (112 communication_quality, 8 context_awareness,
  3 accuracy; 11 substance items). No other canonical log has any.
- **111 of the 113 "worse" communication-quality items were judge failures.**
  The other two: one blank answer (content filter), one genuine.
- As published: 0.980 → 0.607, t = −13.2, 1/113/186. Failures dropped: 0.973 →
  0.968, −0.005, t = −0.58, 1/2/185.
- The failures are contiguous by item id and time (an infrastructure event),
  not related to answer content, so dropping them pairwise is unbiased.
- Knock-ons: global-health compression substance −0.053 → −0.017 (ns);
  context_awareness −0.070 → −0.031 (ns). Also retracted: "terse reads better
  than compression by +0.347", and the r = +0.03 / +0.39 length correlations.

Fixes: `hedging_brevity.py` now returns NaN (with `judge_failed` in score
metadata) when the judge gives no verdict, and retries bypass the cache.
`verify.py` detects judge failures in old logs and sets them to NaN
(`--as-published` reproduces the original numbers).

**Still to do:** re-grade the 112 items (answers are cached, judge only):

```bash
./.venv/bin/inspect eval hedging_brevity.py --model anthropic/claude-sonnet-5 \
  --reasoning-effort medium -T brevity=sharp_routing_noprior -T theme=global_health \
  -T per_slice=100 -T judge_model=openai/gpt-4.1-2025-04-14 -T judge_batch=false
```

---

# The methods finding (a second article, if you want one)

The first pass used `gpt-4o-mini` as grader. Its headline: terse **−0.098,
t = −8.7**. Under the reference grader: **−0.013, ns.** Same 300 answers per
arm (verified identical), same rubrics. Only the judge changed.

- Cross-judge agreement (270 criteria): factual **82–97%**; multi-step
  conditional criteria **47–67% — coin-flip**.
- gpt-4.1 self-consistency (90 criteria, graded twice, temp 0): **97–98%**.
- The bias had a direction: mini was strictest on compressed answers (+0.211
  vs +0.167 on control; differential +0.044).

The −0.098 vs −0.013 contrast reproduces from `logs/`. **The four audit
percentages do not** — their per-criterion outputs were never saved. Say "in a
small audit" or re-run it (~$0.90).

And a second methods lesson from this project: a judge that fails *silently*
is worse than a cheap one. Read what the judge actually returned.

---

# What I will not claim

- **Instruction following: never measured.** Exists only in Health data tasks,
  which I did not run.
- **Response depth: never run.** It has an explicit `detailed` subgroup — cases
  where the right answer really is long. That is the test that could falsify
  this, and I have not done it.
- Communication quality measured in **one theme only** (global health), and
  for compression on 188 of 300 items until the re-grade.
- Oracle routing's +0.079 is a **ceiling**, not a deployable number.
- Anything about Caveman itself — the plugin's real text was never run.
- One model, one reasoning effort, single-turn, one phrasing per arm,
  Consensus subset only.
- **Retracted:** "undirected brevity damages quality" (cheap-grader artifact);
  "compression is free" (−0.027 on uncertainty, p=.034); "broken grammar costs
  0.373 of communication quality" (judge failure); "the emergency gain is the
  referral coming first" (it's not asking unnecessary questions).

---

# Verification record (2026-09-22)

Independent re-derivation, without `verify.py` or inspect_ai: the `.eval` zips
read raw, every judge verdict re-parsed, every item rescored from rubric points.

| check | result |
|---|---|
| canonical map (success, 300/300, gpt-4.1 judge) | matches `CANONICAL` in `verify.py` |
| model / effort / system prompt actually sent | sonnet-5, medium, byte-identical to `BREVITY` in every sample |
| pairing | same ids and identical conversation text across all arms |
| slice labels vs raw `cluster:` tags | correct grouping (labels like `emergent_emergency` are cosmetic: `rsplit` drops only `_behavior`) |
| stored scores vs rescore from verdicts | 0 mismatches |
| NaN-as-zero | none |
| judge failures | 134 criteria, one log — see above |
| 08-26 emergency-none decoy | identical answers and scores to canonical; choice doesn't matter |
| empty completions | Anthropic `content_filter` on Lassa/Marburg questions; mostly the same items in every arm (global health 66, 174, 223, 264; also 288 control-only, 1 compression-only; emergency-terse 5; hedging 188 all arms, 277 sharp) |
| cheap-judge contrast | −0.098 (t = −8.69) vs −0.013 (t = −0.94) reproduces |
