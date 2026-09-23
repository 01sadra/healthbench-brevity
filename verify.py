"""Recompute every number in ARTICLE-NUMBERS.md straight from the .eval logs.

Nothing here talks to an API. It reads the stored logs only, so it is free,
offline, and deterministic. Run it and diff its output against the article.

    .venv/bin/python verify.py                # all themes, all arms
    .venv/bin/python verify.py --theme emergency

Every reported figure is derived from three primitives and nothing else:

  score   sample.scores[<axis>].value   -- NaN where the theme carries no
                                           criteria on that axis; NaN samples
                                           are dropped pairwise, never zeroed
  length  len(sample.output.completion) -- measured from the stored text, NOT
                                           from usage.output_tokens, which is
                                           empty for cached generations
  ask     "?" in completion             -- the ask-rate proxy

Judge failures: a criterion the judge never returned a verdict for (e.g. a
rejected OpenAI batch) was scored "not met" by the original scorer. Those
items are set to NaN here -- dropped pairwise, like any unmeasured axis.
134 criteria in the global_health sharp_routing_noprior log are affected.
Pass --as-published to reproduce the original, uncorrected numbers.

Pairing is by sample.id, which is the HealthBench record index and is
identical across arms because every arm runs the same dataset in file order.
"""

import argparse
import json
import math
import os
import re
from collections import Counter, defaultdict
from statistics import mean

from inspect_ai.log import list_eval_logs, read_eval_log

AXES = [
    "substance",
    "accuracy",
    "completeness",
    "context_awareness",
    "communication_quality",
    "instruction_following",
]

# Only these logs back the published numbers. Every other file in logs/ is a
# smoke test, a gpt-4o-mini pass, or a run that died on the billing limit.
# Listed by basename so the map is auditable by eye.
CANONICAL = {
    ("hedging", "none"):                  "2026-08-21T14-40-24-00-00_hedging-none_XLiCQQQHu5zrwzguRMHSh5.eval",
    ("hedging", "terse"):                 "2026-08-21T15-16-49-00-00_hedging-terse_CnnTHD5UgdGW55WRaCBrFL.eval",
    ("hedging", "sharp"):                 "2026-08-21T15-46-50-00-00_hedging-sharp_SEMzygLMfjR3kBmusGzTHj.eval",
    ("hedging", "sharp_routing"):         "2026-08-21T23-13-50-00-00_hedging-sharp-routing_ZQuQ8jDjvaSXC2Las6oY2u.eval",
    ("hedging", "sharp_routing_noprior"): "2026-08-22T12-17-23-00-00_hedging-sharp-routing-noprior_5ax4EcjF3RQZFqp2aKRhTy.eval",
    ("emergency", "none"):                "2026-08-27T11-53-13-00-00_emergency-none_3mijoiQuXQdovSXgKQBKDH.eval",
    ("emergency", "terse"):               "2026-08-27T11-53-18-00-00_emergency-terse_PJ5GGxBQFp8LYoZdzAXxb6.eval",
    ("emergency", "sharp_routing_noprior"): "2026-08-27T12-15-38-00-00_emergency-sharp-routing-noprior_hguZ2wRV7rZe5vyfijQhof.eval",
    ("global_health", "none"):            "2026-08-27T14-34-33-00-00_global-health-none_2EKfjNKHramyLbZ92ktYHp.eval",
    ("global_health", "terse"):           "2026-08-27T15-32-23-00-00_global-health-terse_R57tnLqZzkU92xyy2ZC8H8.eval",
    ("global_health", "sharp_routing_noprior"): "2026-08-28T13-18-11-00-00_global-health-sharp-routing-noprior_oR9sKxEPpLEQbsDTvd2D8c.eval",
}


AS_PUBLISHED = False


def _verdict(text):
    """criteria_met from a judge reply, or None if there is no usable one."""
    m = re.search(r"\{.*\}", text or "", re.S)
    try:
        v = json.loads(m.group(0)).get("criteria_met") if m else None
    except (json.JSONDecodeError, AttributeError):
        return None
    return v if isinstance(v, bool) else None


def judge_failures(sample):
    """Per scorer: criteria that never got a verdict from the judge.

    Each criterion is retried until it gets a verdict, so criteria graded =
    judge calls with a usable verdict; the rest of n_criteria failed.
    """
    spans = {e.id: e.name for e in sample.events
             if e.event == "span_begin" and getattr(e, "type", None) == "scorer"}
    graded = Counter(spans[e.span_id] for e in sample.events
                     if e.event == "model" and e.span_id in spans
                     and _verdict(e.output.completion) is not None)
    failed = {}
    for ax, score in sample.scores.items():
        n = (score.metadata or {}).get("n_criteria", 0)
        if n and graded[ax] < n:
            failed[ax] = n - graded[ax]
    return failed


def load(basename):
    log = read_eval_log(os.path.join("logs", basename))
    assert log.status == "success", f"{basename} status={log.status}"
    rows = {}
    for s in log.samples:
        failed = judge_failures(s)
        rows[s.id] = {
            "slice": s.metadata["slice"],
            "chars": len(s.output.completion),
            "ask": "?" in s.output.completion,
            "text": s.output.completion,
            "judge_failed": failed,
            **{ax: (s.scores[ax].value
                    if ax in s.scores and (AS_PUBLISHED or ax not in failed)
                    else float("nan")) for ax in AXES},
        }
    return log, rows


def paired_t(a, b):
    """Paired t on the differences b - a. Returns (delta, t, n, win/loss/tie)."""
    d = [y - x for x, y in zip(a, b)]
    n = len(d)
    if n < 2:
        return float("nan"), float("nan"), n, (0, 0, 0)
    m = mean(d)
    var = sum((x - m) ** 2 for x in d) / (n - 1)
    se = math.sqrt(var / n)
    t = m / se if se > 0 else float("nan")
    win = sum(1 for x in d if x > 0)
    loss = sum(1 for x in d if x < 0)
    return m, t, n, (win, loss, n - win - loss)


def paired(rows_a, rows_b, axis, slice_=None):
    """Pairwise-complete vectors for one axis, optionally one slice."""
    ids = sorted(set(rows_a) & set(rows_b))
    a, b = [], []
    for i in ids:
        if slice_ and rows_a[i]["slice"] != slice_:
            continue
        x, y = rows_a[i][axis], rows_b[i][axis]
        if math.isnan(x) or math.isnan(y):
            continue
        a.append(x)
        b.append(y)
    return a, b


def report(theme, arms):
    loaded = {}
    for arm in arms:
        key = (theme, arm)
        if key not in CANONICAL:
            continue
        loaded[arm] = load(CANONICAL[key])[1]
    if "none" not in loaded:
        return
    ctrl = loaded["none"]
    slices = sorted({r["slice"] for r in ctrl.values()})

    print(f"\n{'=' * 78}\nTHEME: {theme}\n{'=' * 78}")
    print(f"slices: {slices}")
    for arm, rows in loaded.items():
        bad = Counter(ax for r in rows.values() for ax in r["judge_failed"])
        if bad:
            how = "scored as not met (--as-published)" if AS_PUBLISHED else "set to NaN"
            print(f"JUDGE FAILURES in {arm}: items per scorer {dict(bad)} -- {how}")

    print("\n-- length and ask-rate (all samples) --")
    print(f"{'arm':<24}{'n':>5}{'chars':>9}{'ask%':>7}")
    for arm, rows in loaded.items():
        print(f"{arm:<24}{len(rows):>5}{mean(r['chars'] for r in rows.values()):>9.0f}"
              f"{100 * mean(r['ask'] for r in rows.values()):>7.0f}")

    for axis in AXES:
        if all(math.isnan(r[axis]) for r in ctrl.values()):
            continue
        print(f"\n-- {axis} --")
        print(f"{'arm':<24}{'slice':<34}{'n':>4}{'mean':>8}{'delta':>8}{'t':>8}"
              f"{'  W/L/T':>12}")
        for arm, rows in loaded.items():
            for slice_ in [None] + slices:
                a, b = paired(ctrl, rows, axis, slice_)
                if not a:
                    continue
                delta, t, n, wlt = paired_t(a, b)
                label = slice_ or "ALL"
                if arm == "none":
                    print(f"{arm:<24}{label:<34}{n:>4}{mean(b):>8.3f}"
                          f"{'':>8}{'':>8}{'':>12}")
                else:
                    print(f"{arm:<24}{label:<34}{n:>4}{mean(b):>8.3f}"
                          f"{delta:>+8.3f}{t:>8.2f}"
                          f"{f'  {wlt[0]}/{wlt[1]}/{wlt[2]}':>12}")

    print("\n-- ask-rate by slice (% of answers containing '?') --")
    print(f"{'arm':<24}" + "".join(f"{s[:22]:>24}" for s in slices))
    for arm, rows in loaded.items():
        cells = []
        for slice_ in slices:
            vals = [r["ask"] for r in rows.values() if r["slice"] == slice_]
            cells.append(f"{100 * mean(vals):>23.0f}%")
        print(f"{arm:<24}" + "".join(cells))

    print("\n-- chars by slice --")
    print(f"{'arm':<24}" + "".join(f"{s[:22]:>24}" for s in slices))
    for arm, rows in loaded.items():
        cells = []
        for slice_ in slices:
            vals = [r["chars"] for r in rows.values() if r["slice"] == slice_]
            cells.append(f"{mean(vals):>24.0f}")
        print(f"{arm:<24}" + "".join(cells))




# ---------------------------------------------------------------------------
# The three derived numbers that are NOT a plain slice mean. Each one is a
# definition as much as a calculation, so the definition is spelled out here
# rather than left implicit in the article.
# ---------------------------------------------------------------------------


def routing_and_oracle():
    """Reproduce routing accuracy, oracle routing, and the per-item ceiling.

    routing accuracy -- of the 200 hedging items where the right ask/don't-ask
        answer is unambiguous (any-reducible = must ask; no-uncertainty = must
        not), the share the arm got right. only-irreducible is excluded: asking
        there is defensible either way, so scoring it would beg the question.

    oracle routing -- per slice, pick whichever arm scores best on that slice,
        using the ground-truth slice label. This is a CEILING: it reads the
        answer key to choose. It is not a deployable policy.

    per-item ceiling -- max across arms, item by item. Strictly higher than
        oracle routing and even less deployable; reported only as an upper bound.
    """
    theme = "hedging"
    arms = ["none", "terse", "sharp", "sharp_routing", "sharp_routing_noprior"]
    loaded = {a: load(CANONICAL[(theme, a)])[1] for a in arms}
    ids = sorted(loaded["none"])
    slices = sorted({loaded["none"][i]["slice"] for i in ids})

    print(f"\n{'=' * 78}\nDERIVED NUMBERS (hedging)\n{'=' * 78}")

    print("\n-- routing accuracy (n=200; only-irreducible excluded) --")
    print(f"{'arm':<24}{'over-asked':>12}{'missed':>9}{'accuracy':>11}")
    for arm, rows in loaded.items():
        over = sum(1 for i in ids
                   if rows[i]["slice"] == "no-uncertainty" and rows[i]["ask"])
        missed = sum(1 for i in ids
                     if rows[i]["slice"] == "any-reducible-uncertainty" and not rows[i]["ask"])
        print(f"{arm:<24}{over:>12}{missed:>9}{(200 - over - missed) / 2:>10.1f}%")

    best = {}
    for slice_ in slices:
        scored = {a: mean(r["substance"] for i, r in loaded[a].items()
                          if r["slice"] == slice_) for a in arms}
        best[slice_] = max(scored, key=scored.get)
        print(f"\nslice {slice_:<30} best arm: {best[slice_]}")
        for a, v in sorted(scored.items(), key=lambda kv: -kv[1]):
            print(f"    {a:<26}{v:>7.3f}")

    oracle = [loaded[best[loaded['none'][i]['slice']]][i]["substance"] for i in ids]
    oracle_chars = [loaded[best[loaded['none'][i]['slice']]][i]["chars"] for i in ids]
    ctrl = [loaded["none"][i]["substance"] for i in ids]
    ctrl_chars = [loaded["none"][i]["chars"] for i in ids]
    delta, t, n, wlt = paired_t(ctrl, oracle)
    print(f"\n-- oracle routing (slice-level, ground-truth labels) --")
    print(f"oracle {mean(oracle):.3f} vs control {mean(ctrl):.3f}  "
          f"delta {delta:+.3f}  t {t:.2f}  n {n}  W/L/T {wlt[0]}/{wlt[1]}/{wlt[2]}")
    print(f"chars  {mean(oracle_chars):.0f} vs {mean(ctrl_chars):.0f}  "
          f"({100 * (mean(oracle_chars) / mean(ctrl_chars) - 1):+.0f}%)")

    ceiling = [max(loaded[a][i]["substance"] for a in arms) for i in ids]
    print(f"per-item ceiling {mean(ceiling):.3f}")
    compressed = ["terse", "sharp", "sharp_routing", "sharp_routing_noprior"]
    beats = sum(1 for i in ids
                if max(loaded[a][i]["substance"] for a in compressed)
                > loaded["none"][i]["substance"])
    print(f"items where some compressed arm beats control: {beats}/{len(ids)} "
          f"({100 * beats / len(ids):.0f}%)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--theme", default=None)
    ap.add_argument("--as-published", action="store_true",
                    help="keep judge failures scored as 'not met' (the original, wrong numbers)")
    args = ap.parse_args()
    AS_PUBLISHED = args.as_published
    themes = [args.theme] if args.theme else ["hedging", "emergency", "global_health"]
    arms = ["none", "terse", "sharp", "sharp_routing", "sharp_routing_noprior"]
    for th in themes:
        report(th, arms)
    if args.theme in (None, "hedging"):
        routing_and_oracle()
