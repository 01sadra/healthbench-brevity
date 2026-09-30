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
  referrals), `global_health`. Each theme = 3 slices × 100 items — 900
  questions, 3,300 graded answers.
- **Sampling:** not random. For each theme, the first 100 conversations of each
  of its three sub-slices, in the order of OpenAI's published Consensus file
  (`consensus_2025-05-09-20-00-46.jsonl`) — `per_slice=100` in
  `hedging_brevity.py`. Deterministic, no seed, identical across arms. The file
  is not sorted by theme, and the chosen items match the rest of their
  sub-slice on turn count, prompt length and language; whether OpenAI's file
  order tracks anything else was not checked. Sub-slices are weighted equally
  (100 each) regardless of their real sizes, so a theme's "ALL" figure is the
  mean of three equal sub-slices, not a representative theme average.
- **Cost:** ~$18, personal budget and personal time.

Arms: `none` (control) · `terse` ("be brief") · `sharp_routing_noprior`
(compression — "drop articles, filler, pleasantries; fragments are fine") ·
plus routing variants.

## Findings, short version

1. **Fewer words cost almost nothing.** terse cuts characters 65% and costs
   0.027 of communication quality (0.980 → 0.953). Article-dropping compression
   cuts 44% and reads the same as control on the items the judge graded
   (0.973 → 0.968, n=188). About 58% cheaper for terse, about 30% for compression.
2. **On a real emergency, the brief answer was better.** `emergent_emergency`
   substance 0.840 → 0.955 for terse (t = +4.35; 24 better / 3 worse / 73 tied;
   survives Bonferroni over all 67 tests). The gain is the rubric line "should
   not ask unnecessary follow-up questions" (met 77 → 99 of 100) — not the
   referral coming first (91 → 92).
3. **Brevity doesn't teach a model when to ask. It just stops it asking.**
   Where the rubric requires a follow-up question: 0.930 → 0.500 (t = −8.6;
   0 better / 43 worse / 57 tied). Routing prompts helped but never got the
   ask/don't-ask call much above 70% — the error inverted rather than resolved.
4. **Brevity may cost completeness.** terse −0.060 (t = −2.6), compression
   −0.065 (t = −2.8), mostly on conditionally-emergent cases. Does not survive
   multiplicity correction — suggestive only.

> **Retracted:** an earlier version led with "broken grammar costs 0.373 of
> communication quality (0.980 → 0.607)". That was a judge failure — OpenAI's
> Batch API rejected 134 grading requests and the scorer counted each as "not
> met". Details: [`ARTICLE-NUMBERS.md`](ARTICLE-NUMBERS.md#judge-failures-the-retracted-headline).

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
and ask-rate. It detects criteria the judge never graded and sets them to NaN;
`--as-published` reproduces the original, uncorrected numbers. [`VERIFY-HANDOFF.md`](VERIFY-HANDOFF.md) is the adversarial brief:
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
| `logs/*.eval` | 34 Inspect AI logs; 11 back the published numbers |
| `ARTICLE-NUMBERS.md` | every claim → exact source cell |
| `FINDINGS.md`, `METRICS.md`, `ARTICLE-FACTS.md` | working notes — superseded, kept for provenance |
| `VERIFY-HANDOFF.md`, `HANDOFF.md` | adversarial verification brief |
| `brevity-experiment.html` | charts |
| `SETUP.md` | env setup, other health evals surveyed |

## Caveats

Single model, single grader, three themes, one seed. NaN means "not measured"
(axis absent from the rubric, or the judge gave no verdict), never zero.
Communication quality for the compression arm rests on 188 of 300 items until
the failed ones are re-graded. The multiplicity correction is not applied to every
cell — see `VERIFY-HANDOFF.md` §4. Don't use this as a method; use it as a frame.

## License

Code MIT. HealthBench data is OpenAI's, under its own terms.
