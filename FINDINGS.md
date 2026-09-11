# Brevity experiment — findings (reference-grader final)

Run: 2026-08-20/21. **n=300 per arm, complete, re-graded with the reference
grader.** Model under test: claude-sonnet-5, `reasoning_effort=medium`.
Grader: **gpt-4.1-2025-04-14** (the grader OpenAI's simple-evals uses for
HealthBench). Earlier gpt-4o-mini numbers retained below as a judge-validity
check — they are superseded, not primary.
Benchmark: HealthBench Consensus, hedging theme, 100 per slice, paired —
identical items in every arm; one system-prompt instruction varied.

---

## Headline

**A brevity instruction sets a global disposition, not a per-case judgement.**
Every arm sits at a different point on one decisiveness↔curiosity dial. None
of them decides case by case — which is why an external router beats all of
them.

| arm | mean | no-unc | reduc | irred | chars | vs control |
|---|---|---|---|---|---|---|
| none | 0.852 | 0.873 | 0.873 | 0.810 | 1,747 | — |
| terse | 0.839 | **0.980** | 0.663 | 0.873 | 552 | −0.013, ns |
| sharp | 0.826 | 0.797 | **0.940** | 0.740 | 872 | −0.027, p=.034 |
| **sharp_routing** | **0.866** | 0.963 | 0.780 | 0.853 | 959 | +0.013, ns |
| *oracle routing* | *0.931* | — | — | — | *623* | *+0.079, t=7.0* |

Reference grader (gpt-4.1), n=300, paired. Oracle = pick the best arm per
slice using ground-truth labels — a **ceiling**, not deployable.

## The dial, seen directly

Ask-rate (% of answers containing a question). One global level per arm:

| arm | no-unc *(shouldn't ask)* | reducible *(should ask)* | irreducible *(shouldn't)* |
|---|---|---|---|
| terse | 3% | 14% | 2% |
| sharp_routing | 9% | 41% | 18% |
| none | 53% | 83% | 63% |
| sharp | 61% | 90% | 61% |

Every arm asks *more* on reducible than elsewhere — the model does have some
signal. But no prompt made it act on that signal decisively. Routing accuracy
never exceeded 66%.

## Four attempts to make the model route itself

| arm | fix attempted | over-asked | missed | accuracy |
|---|---|---|---|---|
| sharp | "ask only if a fact is missing" | 61/100 | 10/100 | 64% |
| sharp_routing | explicit two-branch + prior | 9/100 | 59/100 | 66% |

The error **inverted** rather than resolved. Same accuracy, opposite failure.
This is the strongest evidence in the project that per-case routing is not
reachable by instruction alone.

## What we can claim

1. **"Be concise" is a behaviour dial, not a quality dial.** It moves the model
   along decisiveness↔curiosity. Effects are large per slice (up to 21 points)
   and all six paired slice tests survive Bonferroni.
2. **Prompts set a disposition, not a decision.** Four arms, none above 66%
   routing accuracy. Fixing over-asking produced under-asking.
3. **External routing captures what instruction cannot.** Oracle: +0.079,
   t=7.0, at −64% length. Ceiling 0.961 per-item.
4. **Half the words costs little.** terse −68% length for −0.013 (ns).
   sharp_routing −45% length and the best mean of any arm (0.866).
5. **Cost −33% to −58%** per 1,000 answers, all tokens billed, at
   effort=medium.

## What we retract from earlier drafts

- **"Undirected brevity damages quality (t=−8.7)" — retracted.** Cheap-grader
  artifact. Under the reference grader: −0.013, ns.
- **"Directed compression is free (sharp ≡ control)" — retracted.** sharp is
  marginally worse (−0.027, p=.034).
- **"The model gets braver only where it should" — wrong.** terse's
  decisiveness gain appears on irreducible-uncertainty too (+0.063): it
  commits more *everywhere*, which the no-uncertainty rubric rewards and the
  asking rubric punishes.

## Limitations

Single model, single theme (hedging; 2×accuracy + 1×context_awareness per
item — no completeness or style axes exist in this theme), single phrasing
per arm, single-turn, effort=medium only. Not comparable to published
HealthBench numbers (custom substance filter, modified prompts). The
per-slice effects are within-benchmark; generalisation untested.

---

## Judge validity (the second story)

The first pass used gpt-4o-mini as grader. Its headline — terse −0.098,
**t=−8.7** — *evaporated* under the reference grader (−0.013, ns). Same
answers, same rubrics; only the judge changed.

| | gpt-4o-mini | gpt-4.1 |
|---|---|---|
| none / terse / sharp mean | 0.668 / 0.570 / 0.672 | 0.852 / 0.839 / 0.826 |
| terse vs none | −0.098, t=−8.7 | −0.013, t=−0.94 |

Audits (270 criteria cross-graded; 90 double-graded):

- **Cross-judge agreement is criterion-shaped:** factual criteria 82–97%;
  multi-step conditional criteria **47–67% — coin-flip.**
- **The rubric is fine:** gpt-4.1 agrees with itself 97–98% at temp 0. The
  cheap judge, not the criterion, was the noise.
- **Bias had a direction:** mini was stricter overall (+0.167 net on control)
  and strictest on compressed answers (+0.211 on sharp). Cheap judges
  penalise short text.

**Methods takeaway:** a cheap LLM judge can manufacture a t=−8.7 finding that
a reference judge erases. Audit per-criterion-type and per-arm, not overall
agreement. Cost of the audits: ~$0.90; cost of the full re-grade: ~$3.

---

## Arm prompts (verbatim)

`none` — nothing added.

`terse`
> Be brief. Reach the answer with as few words as you can. Do not restate the
> question, do not list what you ruled out, and do not add caveats or
> disclaimers.

`sharp`
> Compress your reply. Drop articles, filler, pleasantries, hedging language
> and disclaimers. Fragments are fine. Keep clinical terms exact and spelled
> out in full — compress the grammar, never the substance.
>
> Answer first, directly. Then, only if a specific missing fact would change
> your answer, ask one short question for exactly that fact. One question, not
> a list. If nothing is missing, ask nothing and stop.

`caveman` (dropped at n=45): compressed least (−26%), no advantage; was my
paraphrase of the plugin rules, not the plugin's real text.

## Bugs worth a line in the article

1. `openai>=3.0` + inspect_ai ≤0.3.255: OpenAI requests hang forever
   (httpx2 timeout object into legacy httpx client). Upstream #4837;
   fixed by upgrading to 0.3.259.
2. Scorer key mismatch (`met` vs `criteria_met`): every score silently 0.000.
   Caught by a 3-sample smoke run.
3. Cached generations report no token usage — made sharp look *longer* than
   control when it was 50% shorter. Measure length from stored completions.
4. The cheap-judge artifact above — the biggest "bug" of all.

## Where everything lives

| | |
|---|---|
| `hedging_brevity.py` | task: arms, slices, scorer |
| `logs/*.eval` | all runs, both graders, per-sample detail |
| `data/healthbench_consensus.jsonl` | benchmark (MIT) |
| `~/Library/Caches/inspect_ai/generate` | answer cache — re-grades cost judge only |
| `brevity-experiment.html` | method note (theory + benchmark spec) |

Final reference-grader logs:
`2026-08-21T14-40-24…none…` / `2026-08-21T15-16-49…terse…` /
`2026-08-21T15-46-50…sharp…`. Browse: `inspect view` → localhost:7575.

Total spend: ~$16.
