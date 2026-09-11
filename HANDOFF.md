# Brevity experiment — handoff context

Everything an incoming agent needs. Written 2026-08-26.

---

## 1. The question

Does instructing an LLM to **talk less** preserve answer quality while cutting
cost and improving readability?

Origin: the author moved to London speaking self-taught English. Limited
fluency forced a discipline — think fully, then ask one short, sharp question.
Separately, the "caveman" skill (tells LLMs to compress output, keep code
quality) became popular, suggesting models are verbose beyond need. The author
builds AI triage for Huma in UK healthcare, so the question is operational, not
academic.

Deliverable: a **Substack article**, not a paper.

---

## 2. Setup

**Model under test:** `claude-sonnet-5`, `reasoning_effort=medium`, pinned
identical across arms. Reasoning is *not* constrained — only visible output is.

**Benchmark:** HealthBench (OpenAI). ~5,000 simulated patient–clinician
conversations, rubric-graded by LLM-as-judge, rubrics written by 262
physicians. We use **HealthBench Consensus** (3,671), the physician-validated
subset.

7 themes (Consensus counts): Expertise-tailored communication 746, Responding
with uncertainty 711, Global health 634, Emergency referrals 453, Context
seeking 408, Health data tasks 395, Response depth 324.

5 axes: accuracy, completeness, context_awareness, communication_quality,
instruction_following. **Critically, each theme carries only some axes:**

| theme | n | accuracy | completeness | context | comm | instr |
|---|---|---|---|---|---|---|
| Expertise-tailored comm | 746 | 746 | · | · | 746 | · |
| Responding w/ uncertainty | 711 | 1422 | · | 711 | · | · |
| Global health | 634 | 220 | · | 414 | 634 | · |
| Emergency referrals | 453 | 134 | **319** | 453 | · | · |
| Context seeking | 408 | 408 | · | 408 | · | · |
| Health data tasks | 395 | 215 | · | · | · | 575 |
| Response depth | 324 | 324 | · | · | 324 | · |

`completeness` exists **only** in Emergency referrals. `instruction_following`
only in Health data tasks.

**Grader:** `gpt-4.1-2025-04-14` — the grader OpenAI's own `simple-evals` uses.
All primary numbers use it. (An earlier `gpt-4o-mini` pass is retained only as
a judge-validity study; see §6.)

**Harness:** Inspect AI. Task file `hedging_brevity.py`. Design is **paired** —
identical items across arms, stratified 100 per sub-slice, 300/arm.

---

## 3. Arms (verbatim prompts)

`none` — nothing added (control).

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

`sharp_routing` — same compression paragraph, then an explicit two-branch
decision ("is there a specific fact you do not have…? If no — commit… If yes —
ask exactly one question"), plus a prior: "A person asking a health question
wants an answer, not an interview. Asking is the exception."

`sharp_routing_noprior` — identical minus that final prior line.

`caveman` — dropped at n=45 (compressed least, no advantage). Was a paraphrase
of the plugin rules, not the plugin's real text.

---

## 4. RESULTS — Responding with uncertainty (n=300/arm, gpt-4.1)

Three sub-slices, 100 each: `no-uncertainty` (commit; hedging penalised),
`any-reducible-uncertainty` (hedge AND ask for the missing fact),
`only-irreducible-uncertainty` (hedge; cannot resolve).

| arm | mean | no-unc | reduc | irred | chars | paired vs control |
|---|---|---|---|---|---|---|
| none | 0.852 | 0.873 | 0.873 | 0.810 | 1,747 | — |
| terse | 0.839 | **0.980** | 0.663 | 0.873 | 552 | −0.013, t=−0.94 |
| sharp | 0.826 | 0.797 | **0.940** | 0.740 | 872 | −0.027, t=−2.12 |
| sharp_routing | 0.866 | 0.963 | 0.780 | 0.853 | 959 | +0.013, t=+1.04 |
| sharp_routing_noprior | **0.869** | 0.953 | 0.797 | 0.857 | 926 | +0.017, t=+1.30 |

**All six paired slice tests survive Bonferroni (α=0.0083):** terse
+0.107/−0.210/+0.063 (t=6.5/−10.0/2.8); sharp −0.077/+0.067/−0.070
(t=−3.6/3.6/−3.1).

**Narrow claim, isolated** (no-uncertainty only, terse vs none, n=100 paired):
0.873 → 0.980, **33 better / 1 worse / 66 tied**, chars 1,630 → 537 (−67%).

### Ask-rate (% of answers containing a question) — the behavioural metric

| arm | no-unc *(shouldn't)* | reducible *(should)* | irreducible *(shouldn't)* |
|---|---|---|---|
| terse | 3% | 14% | 2% |
| sharp_routing | 9% | 41% | 18% |
| sharp_routing_noprior | 12% | 51% | 20% |
| none | 53% | 83% | 63% |
| sharp | 61% | 90% | 61% |

**Routing accuracy** (over-ask + miss, on the two decidable slices, n=200):
sharp 64% (61 over-asked / 10 missed) → sharp_routing 66% (9 / 59) →
sharp_routing_noprior 70% (12 / 49). **The error inverted rather than
resolved.** Ablation: removing the prior line changed score by +0.003
(t=0.35) — the two-branch *structure* did the work, not the prior.

### Oracle routing (CEILING, not deployable)

Pick the best arm per slice using ground-truth labels: **0.931 vs control
0.852, +0.079, t=7.0, CI [+0.057, +0.101], at 623 chars (−64%).** Per-item
oracle ceiling 0.961. A compressed arm beats control on 98/300 items (33%).

---

## 5. RESULTS — Emergency referrals (n=300 paired, gpt-4.1) — PARTIAL

Only `none` and `terse` complete so far.

| arm | substance | accuracy | **completeness** | context | chars |
|---|---|---|---|---|---|
| none | 0.945 | 1.000 | 0.950 | 0.923 | 1,683 |
| terse | 0.917 | 0.980 | **0.890** | 0.913 | 500 (−70%) |

Paired terse vs none: **completeness −0.060, t=−2.59, p=0.010** (the only
significant axis); substance −0.028 (p=0.071); accuracy −0.020 (ns); context
−0.010 (ns).

**By slice — the counter-intuitive result:**

| slice | none | terse | diff | t |
|---|---|---|---|---|
| **emergent** (real emergency) | 0.840 | **0.955** | **+0.115** | **+4.35** |
| conditionally-emergent | 0.995 | 0.875 | −0.120 | −4.34 |
| non-emergent | 1.000 | 0.920 | −0.080 | −3.81 |

**On genuine emergencies brief is BETTER** — the rubric requires the referral
in the first few sentences and penalises being "overly verbose, unclear, or
indirect." Brief loses only on *conditional* cases where the answer needs
if/then branches, and only on completeness — never accuracy.

---

## 6. Judge-validity study (a second, publishable finding)

The first pass used `gpt-4o-mini`. Its headline: terse −0.098, **t=−8.7**.
Under `gpt-4.1`: **−0.013, ns.** Same answers, same rubrics, different judge.

- Cross-judge agreement (270 criteria): factual **82–97%**, multi-step
  conditional **47–67% (coin-flip)**.
- gpt-4.1 self-consistency (90 criteria, twice, temp 0): **97–98%** → the
  rubric is well-posed; the cheap judge was the noise.
- Bias is directional: mini stricter overall, **strictest on compressed
  answers** (net +0.211 on sharp vs +0.167 on control; differential +0.044).

**Takeaway:** a cheap judge manufactured a t=−8.7 finding a reference judge
erased, and it was biased against short text. Audit per-criterion-type and
per-arm, not overall agreement.

---

## 7. Cost (per 1,000 answers, all tokens billed, thinking ⊂ output)

| arm | input | thinking | visible | $/1k std | $/1k batch |
|---|---|---|---|---|---|
| none | 247 | 17 | 615 | $6.81 | $3.41 |
| terse | 271 | 21 | 212 | $2.87 | $1.44 |
| sharp | 340 | 50 | 340 | $4.58 | $2.29 |

sharp **−33%**, terse **−58%**. Thinking is negligible at effort=medium
(≤13% of output cost) — the +194% thinking rise is a large multiple of a small
number. sharp's drag is its own long instruction (+38% input). Holds at
effort=medium only.

---

## 8. STATE RIGHT NOW

**Running** (background, `/tmp/themes2.log`): 6 runs = {emergency,
global_health} × {none, terse, sharp_routing_noprior}. Complete:
emergency/none, emergency/terse. In progress: emergency/sharp_routing_noprior.
Pending: all 3 global_health.

Command:
```
for th in emergency global_health; do for arm in none terse sharp_routing_noprior; do
  ./.venv/bin/inspect eval hedging_brevity.py --model anthropic/claude-sonnet-5 \
    --reasoning-effort medium -T brevity=$arm -T theme=$th -T per_slice=100 \
    -T judge_model=openai/gpt-4.1-2025-04-14 --display plain
done; done
```

Global health adds the **communication_quality** axis (634 criteria) — the
untested half of the thesis ("short text is easier to read"). It may go
*against* the claim; a judge grading communication quality plausibly rewards
warmth and structure. Run it and report honestly either way.

**Spend so far ~$12–16.** OpenAI hit a `billing_hard_limit_reached` once;
console has since been topped up. Watch for it again.

---

## 9. Files

| file | contents |
|---|---|
| `hedging_brevity.py` | the task — arms, themes, per-axis scorers |
| `FINDINGS.md` | narrative findings (⚠ predates emergency results) |
| `METRICS.md` | every metric, current values, pre-declared criteria |
| `logs/*.eval` | ~30 runs, both graders, full per-sample detail |
| `data/healthbench_consensus.jsonl` | benchmark, 35 MB, MIT |
| `~/Library/Caches/inspect_ai/generate` | answer cache — **re-grades cost judge only** |
| `brevity-experiment.html` | method note (theory + benchmark spec) |

Panel: `./.venv/bin/inspect view --port 7575` → localhost:7575.

---

## 10. Methodology guardrails (learned the hard way)

1. **Reference grader (gpt-4.1) for all primary numbers.** Never gpt-4o-mini.
2. **Measure answer length from stored completions, not token usage** — cached
   generations report zero usage and once made sharp look 5% *longer* than
   control when it was 50% shorter.
3. **Paired tests**, identical items across arms.
4. **Bonferroni** when reporting the slice tests.
5. **Report ask-rate alongside score** — the score alone hid the mechanism for
   two full rounds.
6. **Label oracle results as ceilings** wherever they appear.
7. Judge batching is a task param (`judge_batch`); turn it **off** for smoke
   tests or you wait on Batch API queues.

## 11. Bugs already found and fixed (each worth a line in the article)

1. `openai>=3.0` + `inspect_ai≤0.3.255`: all OpenAI requests hang forever
   (httpx2 timeout object into legacy httpx client). Upstream #4837. Fixed by
   upgrading to 0.3.259.
2. Scorer key mismatch: `_evaluate_criterion` returns `met`, `calculate_score`
   reads `criteria_met` → every score silently 0.000. Caught by a 3-sample run.
3. Cached generations report no token usage (see guardrail 2).
4. The cheap-judge artifact (§6) — the biggest of all.

---

## 12. Open work, ranked

1. **Finish the 6 runs** — especially global_health for communication_quality.
2. **Router experiment** (~$5): cheap first-pass classifier ("is a key fact
   missing?") → route to terse/sharp. Turns the 0.931 oracle ceiling into a
   real, deployable number. **Highest-value remaining item.**
3. **Length-matched control** (~$3): terse compressed to sharp's ~870 chars.
   Length and instruction-content are currently confounded.
4. **Second model** (~$4): Haiku 4.5 or GPT. One model → "Sonnet does this."
5. **Second phrasing per arm** (~$9): rules out "it's the wording."
6. **Response depth theme** (~$7): has an explicit `detailed` subgroup — cases
   where the right answer *is* long. Direct falsification test.
7. **The real caveman plugin text as an arm** — needs the plugin's verbatim
   rules, which were never supplied.

## 13. Claims that are SAFE vs NOT

**Safe:**
- On clear-cut medical questions, compressed answers score equal or better at
  ~⅔ fewer words (33 better / 1 worse / 66 tied, n=100).
- Brevity instructions set a *global disposition*, not a per-case decision —
  four arms, routing accuracy never above 70%.
- On genuine emergencies, brief scored higher (+0.115, t=4.35).
- Cost −33% to −58%.
- Cheap LLM judges can manufacture significant findings (t=−8.7 → ns).

**Not safe / retracted:**
- ~~"Undirected brevity damages quality"~~ — cheap-grader artifact.
- ~~"Compression is free"~~ — sharp is −0.027 (p=.034); completeness drops
  −0.060 (p=.010) on emergency.
- Oracle routing's +0.079 as a *product* number — it uses ground-truth labels.
- Anything about communication_quality or instruction_following — **never
  measured**.
- Generalisation beyond: one model, effort=medium, single-turn, one phrasing
  per arm, HealthBench Consensus only.
