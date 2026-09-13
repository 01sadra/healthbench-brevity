# Does telling an LLM to shut up cost you anything? — HealthBench brevity experiment

Data, code and raw judge logs behind the post on
[theycallmesam.com](https://theycallmesam.com).

One thesis: **let the model reason as much as it wants, constrain only the
visible answer — does answer quality survive, in a medical context?**

## Design

- **Benchmark:** [HealthBench](https://openai.com/index/healthbench/) Consensus
  (OpenAI) — 3,671 physician-validated conversations, rubric-graded.
- **Model under test:** `anthropic/claude-sonnet-5`, `reasoning_effort=medium`,
  identical in every arm. Reasoning was never constrained.
- **Grader:** `openai/gpt-4.1-2025-04-14` — the grader OpenAI's own `simple-evals`
  uses for HealthBench. (An earlier pass used `gpt-4o-mini`; superseded, logs kept.)
- **Design:** paired. Every arm sees the identical 300 items in file order, so
  every comparison is within-item. n=300 per arm.
- **Manipulation:** one system message, nothing else. Every arm's prompt,
  verbatim: [`PROMPTS.md`](PROMPTS.md).
- **Themes:** `hedging` (responding with uncertainty), `emergency` (emergency
  referrals), `global_health`. Each theme = 3 slices × 100 items.
- **Cost:** ~$18, personal budget and personal time.

Arms: `none` (control) · `terse` ("be brief") · `sharp_routing_noprior`
(compression — "drop articles, filler, pleasantries; fragments are fine") ·
plus routing variants.

## Findings, short version

1. **Fewer words is free. Broken grammar is not.** terse cuts characters 65% and
   costs 0.027 of communication quality. Article-dropping compression costs
   0.373 (0.980 → 0.607) while being *longer* than terse. Caveman-style
   compression does not transfer to medical text.
2. **On a real emergency, the brief answer was better.** `emergent_emergency`
   substance 0.840 → 0.955 for terse (t = +4.35; 24 better / 3 worse / 73 tied).
   The rubric wants the referral up front and penalises verbosity.
3. **Brevity doesn't teach a model when to ask. It just stops it asking.**
   Where the rubric requires a follow-up question: 0.930 → 0.500 (t = −8.6;
   0 better / 43 worse / 57 tied). Prompt tweaks inverted the error rather than
   fixing it — a triage product needs orchestration, not one prompt.
4. **Brevity costs completeness, and it replicates.** terse −0.060 (t = −2.6),
   compression −0.065 (t = −2.8) on the same axis. Negative result, kept.

Every number, with its source cell: [`ARTICLE-NUMBERS.md`](ARTICLE-NUMBERS.md).

## Reproduce or attack the numbers

No API key and no spend needed — model answers and judge verdicts are already in
`logs/*.eval`.

```bash
python -m venv .venv && .venv/bin/pip install inspect-ai
.venv/bin/python verify.py
```

`verify.py` reads the stored logs only — offline, deterministic — and recomputes
every per-slice mean, paired delta, paired t, win/loss/tie count, character count
and ask-rate. [`VERIFY-HANDOFF.md`](VERIFY-HANDOFF.md) is the adversarial brief:
which logs are canonical, which are decoys, and where each claim is weakest.
Read that before trusting anything here.

## Layout

| path | what |
|---|---|
| `PROMPTS.md` | every arm's system prompt, verbatim |
| `hedging_brevity.py` | the eval task — arms, slices, six per-axis scorers |
| `verify.py` | offline recompute of every published number |
| `brevity_eval.py`, `medcalc_triage.py` | earlier/adjacent probes |
| `data/healthbench_consensus.jsonl` | HealthBench Consensus, local copy (37 MB) |
| `logs/*.eval` | 35 Inspect AI logs; 11 back the published numbers |
| `ARTICLE-NUMBERS.md` | every claim → exact source cell |
| `FINDINGS.md`, `METRICS.md`, `ARTICLE-FACTS.md` | working notes |
| `VERIFY-HANDOFF.md`, `HANDOFF.md` | adversarial verification brief |
| `brevity-experiment.html` | charts |
| `SETUP.md` | env setup, other health evals surveyed |

## Caveats

Single model, single grader, three themes, one seed. NaN means "axis not measured
in this rubric", never zero. The multiplicity correction is not applied to every
cell — see `VERIFY-HANDOFF.md` §4. Don't use this as a method; use it as a frame.

## License

Code MIT. HealthBench data is OpenAI's, under its own terms.
