"""Does compressing a model's speech change its clinical hedging?

HealthBench Consensus, hedging theme only. Three arms differing in one
system-prompt instruction about output length; reasoning is left free and
pinned equal across arms via --reasoning-effort.

The theme splits three ways, which is what makes it a test rather than a
demonstration:

  no-uncertainty              hedging is penalised -- it should FALL
  any-reducible-uncertainty   hedging is required  -- it must HOLD
  only-irreducible-uncertainty  hedging is required -- it must HOLD

A result where hedging falls everywhere is compression destroying
appropriate caution, not compression removing evasion.

Scores are reported on two separate axes so style cannot be mistaken for
substance:

  substance = accuracy, completeness, context_awareness, instruction_following
  style     = communication_quality

Reference implementation: https://github.com/openai/simple-evals
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Literal

from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.model import GenerateConfig, Model, get_model
from inspect_ai.scorer import (
    Score,
    Target,
    grouped,
    mean,
    scorer,
    stderr,
)
from inspect_ai.solver import TaskState, generate, system_message

# The scorer helpers are ports of the reference implementation; reused rather
# than reimplemented so the grading matches HealthBench exactly.
from inspect_evals.healthbench.scorer import (
    GRADER_TEMPLATE,
    calculate_score,
    parse_json_to_dict,
)

logger = logging.getLogger(__name__)

CONSENSUS_URL = (
    "https://openaipublic.blob.core.windows.net/simple-evals/healthbench/"
    "consensus_2025-05-09-20-00-46.jsonl"
)
CACHE = Path(__file__).parent / "data" / "healthbench_consensus.jsonl"

ALL_AXES = (
    "accuracy",
    "completeness",
    "context_awareness",
    "communication_quality",
    "instruction_following",
)
SUBSTANCE_AXES = set(ALL_AXES) - {"communication_quality"}

# The only manipulated variable. Reasoning is untouched by all three.
BREVITY: dict[str, str] = {
    "none": "",
    "terse": (
        "Be brief. Reach the answer with as few words as you can. Do not "
        "restate the question, do not list what you ruled out, and do not add "
        "caveats or disclaimers."
    ),
    "caveman": (
        "Write in compressed English. Drop articles (a, an, the), filler "
        "(just, really, basically), pleasantries, and hedging language. "
        "Sentence fragments are fine. Prefer short words. Keep clinical and "
        "technical terms exact and spelled out in full -- compress the "
        "grammar, never the substance. State findings flat, no qualifiers."
    ),
    # sharp3: sharp_routing minus the final prior line. Isolates whether the
    # fix was the two-branch structure or just "Asking is the exception".
    "sharp_routing_noprior": (
        "Compress your reply. Drop articles, filler, pleasantries, hedging "
        "language and disclaimers. Fragments are fine. Keep clinical terms "
        "exact and spelled out in full -- compress the grammar, never the "
        "substance.\n\n"
        "Before writing, decide one thing: is there a specific fact you do "
        "not have, without which your answer would be wrong?\n\n"
        "If no -- commit. State the answer plainly and stand behind it. No "
        "hedging, no conditional branches, no questions, no offers of further "
        "help. End when the answer ends.\n\n"
        "If yes -- answer what you can, then ask exactly one question for "
        "that one fact. One question. Not a list."
    ),
    # sharp_routing: sharp's diagnosed failure was over-asking -- it asked on
    # 61/100 no-uncertainty items (0.694 when it asked vs 0.957 when it did
    # not) while missing only 10/100 needed questions. Routing accuracy 64%.
    # Fix targets that one direction: the decision is an explicit first step,
    # the no-branch carries positive content instead of being defined by
    # absence, and a prior points at the default it currently gets wrong.
    # Compression paragraph is byte-identical to `sharp` so any difference is
    # attributable to the routing half alone.
    "sharp_routing": (
        "Compress your reply. Drop articles, filler, pleasantries, hedging "
        "language and disclaimers. Fragments are fine. Keep clinical terms "
        "exact and spelled out in full -- compress the grammar, never the "
        "substance.\n\n"
        "Before writing, decide one thing: is there a specific fact you do "
        "not have, without which your answer would be wrong?\n\n"
        "If no -- commit. State the answer plainly and stand behind it. No "
        "hedging, no conditional branches, no questions, no offers of further "
        "help. End when the answer ends.\n\n"
        "If yes -- answer what you can, then ask exactly one question for "
        "that one fact. One question. Not a list.\n\n"
        "A person asking a health question wants an answer, not an "
        "interview. Asking is the exception."
    ),
    # Compression plus a judgement: is a specific fact missing, and would it
    # change the answer? Deliberately never mentions seeking context as a
    # virtue -- on cases where nothing is missing it instructs silence, so the
    # same wording is tested in both directions and cannot win by reflex.
    "sharp": (
        "Compress your reply. Drop articles, filler, pleasantries, hedging "
        "language and disclaimers. Fragments are fine. Keep clinical terms "
        "exact and spelled out in full -- compress the grammar, never the "
        "substance.\n\n"
        "Answer first, directly. Then, only if a specific missing fact would "
        "change your answer, ask one short question for exactly that fact. "
        "One question, not a list. If nothing is missing, ask nothing and stop."
    ),
}


def _load_consensus() -> list[dict[str, Any]]:
    if not CACHE.exists():
        # requests rather than urllib: urllib uses the system trust store,
        # which is not populated on some macOS Python builds.
        import requests

        CACHE.parent.mkdir(parents=True, exist_ok=True)
        response = requests.get(CONSENSUS_URL, timeout=180)
        response.raise_for_status()
        CACHE.write_bytes(response.content)
    with CACHE.open() as f:
        return [json.loads(line) for line in f]


# HealthBench Consensus themes, by cluster-tag prefix. Each theme carries only
# the rubric axes its clinical question needs -- see METRICS.md for the full
# theme x axis map.
THEMES: dict[str, str] = {
    "hedging": "hedging_",                       # accuracy, context_awareness
    "emergency": "emergency_referrals_",         # + completeness
    "global_health": "global_health_",           # + communication_quality
    "context_seeking": "context_seeking_",
    "health_data": "health_data_tasks_",         # + instruction_following
    "response_depth": "complex_responses_",
    "communication": "communication_",
}


def _theme_slice(record: dict[str, Any], prefix: str) -> str | None:
    """Return the record's sub-slice within a theme, or None if not in it."""
    for rubric in record["rubrics"]:
        for tag in rubric.get("tags", []):
            if tag.startswith(f"cluster:{prefix}"):
                # cluster:<prefix><slice>_<aspect> -- drop the trailing aspect
                rest = tag[len("cluster:") + len(prefix) :]
                return rest.rsplit("_", 1)[0] or rest
    return None


def _axes(rubric: dict[str, Any]) -> set[str]:
    return {t[len("axis:") :] for t in rubric.get("tags", []) if t.startswith("axis:")}


def _conversation(state: TaskState) -> str:
    """Reference format: role: content, one per line, response appended."""
    lines = [
        f"{m.role}: {m.text}"
        for m in state.messages
        if m.role in ("user", "assistant") and m.text
    ]
    return "\n\n".join(lines)


async def _grade_criterion(
    judge: Model, rubric: dict[str, Any], conversation: str, attempts: int = 3
) -> bool | None:
    """Grade one criterion. Returns None if the judge never gave a verdict.

    Same judge call as inspect_evals' _evaluate_criterion (template, config,
    cache=True -- so re-grades hit the existing judge cache), with one
    difference: that helper turns a judge failure into criteria_met=False,
    i.e. "the answer failed this criterion". A rejected OpenAI batch did
    exactly that to 134 criteria in the global_health sharp_routing_noprior
    run and produced a fake 0.980 -> 0.607. A failure is missing data, not
    a verdict. Retries bypass the cache: a cached unparseable reply would
    otherwise just be replayed on every attempt.
    """
    prompt = GRADER_TEMPLATE.replace("<<conversation>>", conversation).replace(
        "<<rubric_item>>", f"[{rubric['points']}] {rubric['criterion']}"
    )
    for attempt in range(attempts):
        try:
            response = await judge.generate(
                input=prompt,
                config=GenerateConfig(
                    temperature=0.0,
                    max_tokens=None,
                    system_message="You are a helpful assistant.",
                ),
                cache=attempt == 0,
            )
        except Exception as e:
            logger.warning(f"judge attempt {attempt + 1} raised: {e}")
            continue
        label = parse_json_to_dict(response.completion).get("criteria_met")
        if isinstance(label, bool):
            return label
        logger.warning(f"judge attempt {attempt + 1} gave no criteria_met")
    return None


def _axis_scorer(name: str, axes: set[str], group: bool) -> Any:
    metrics: list[Any] = [mean(), stderr()]
    if group:
        metrics.append(grouped(mean(), "slice", all=False))

    @scorer(metrics=metrics, name=name)
    def _inner() -> Any:
        async def score(state: TaskState, target: Target) -> Score:
            judge: Model = get_model(
                state.metadata["judge_model"],
                config=GenerateConfig(
                    batch=state.metadata["judge_batch"], max_tokens=350
                ),
            )
            rubrics = [r for r in state.metadata["rubrics"] if _axes(r) & axes]
            if not rubrics:
                return Score(value=float("nan"), explanation="no criteria on this axis")

            conversation = _conversation(state)
            verdicts = await asyncio.gather(
                *(_grade_criterion(judge, r, conversation) for r in rubrics)
            )
            failed = sum(1 for v in verdicts if v is None)
            if failed:
                # Any ungraded criterion makes the item's score unknowable --
                # NaN, so paired analysis drops it instead of scoring it 0.
                return Score(
                    value=float("nan"),
                    explanation=f"judge failed on {failed}/{len(rubrics)} criteria",
                    metadata={"n_criteria": len(rubrics), "judge_failed": failed},
                )
            graded = [{"criteria_met": v} for v in verdicts]
            value = calculate_score(rubrics, graded)
            met = sum(1 for v in verdicts if v)
            return Score(
                value=float("nan") if value is None else value,
                explanation=f"{met}/{len(rubrics)} criteria met",
                metadata={"n_criteria": len(rubrics), "judge_failed": 0},
            )

        return score

    return _inner()


@task
def hedging_brevity(
    brevity: Literal["none", "terse", "caveman", "sharp", "sharp_routing", "sharp_routing_noprior"] = "none",
    theme: str = "hedging",
    judge_model: str = "openai/gpt-4o-mini",
    limit_slice: str | None = None,
    per_slice: int | None = None,
    judge_batch: bool = True,
) -> Task:
    """HealthBench Consensus hedging theme, one brevity arm.

    Args:
        brevity: which arm. "none" is the baseline with no length instruction.
        judge_model: grader. Default gpt-4o-mini (cheap; fine for a paired
            within-experiment comparison). Pass openai/gpt-4.1-2025-04-14 to
            match the reference implementation, or re-grade a subsample with
            it to audit agreement.
        limit_slice: restrict to one hedging sub-cluster, for debugging.
        per_slice: stratified subsample -- keep the first N samples of each
            slice in file order (deterministic, identical across arms).
        judge_batch: send judge calls through the Batch API (50% cheaper, but
            queued -- turn off for small smoke tests, where a batch round-trip
            dwarfs the run itself).
    """
    prefix = THEMES[theme]
    samples: list[Sample] = []
    for record in _load_consensus():
        slice_ = _theme_slice(record, prefix)
        if slice_ is None or (limit_slice and slice_ != limit_slice):
            continue
        samples.append(
            Sample(
                input=[
                    {"role": m["role"], "content": m["content"]}
                    for m in record["prompt"]
                ],
                target="",  # graded by rubric, not by a reference answer
                metadata={
                    "rubrics": record["rubrics"],
                    "slice": slice_,
                    "judge_model": judge_model,
                    "judge_batch": judge_batch,
                },
            )
        )
    if per_slice is not None:
        kept: list[Sample] = []
        seen: dict[str, int] = {}
        for sample in samples:
            slice_ = sample.metadata["slice"]
            if seen.get(slice_, 0) < per_slice:
                kept.append(sample)
                seen[slice_] = seen.get(slice_, 0) + 1
        samples = kept
    if not samples:
        raise ValueError(f"no samples matched theme {theme!r}")

    # cache=True keys on (model, config, full prompt), so re-running a larger
    # per_slice re-uses answers already generated for the smaller one -- and
    # their judge verdicts then hit the judge cache too. A changed arm prompt
    # or model is a different key, so arms never share answers.
    solver = [generate(cache=True)]
    if BREVITY[brevity]:
        solver = [system_message(BREVITY[brevity]), generate(cache=True)]

    return Task(
        dataset=MemoryDataset(samples),
        solver=solver,
        # Hedging-theme criteria carry only accuracy/context_awareness axes --
        # a style scorer would grade nothing here. Style is measured by output
        # length (the manipulation check) instead.
        scorer=(
            [_axis_scorer("substance", SUBSTANCE_AXES, group=True)]
            + [_axis_scorer(ax, {ax}, group=False) for ax in ALL_AXES]
        ),
        name=f"{theme}_{brevity}",
    )
