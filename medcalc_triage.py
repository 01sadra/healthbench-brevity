"""MedCalc-Bench triage/severity subset as an Inspect task.

Free-text generation, integer answer, exact-match grading — no judge model.
The `brevity` parameter is the experimental variable: it is the ONLY difference
between arms, so any accuracy delta is attributable to the brevity instruction.

MedCalc-Bench (Khandekar et al., NeurIPS 2024 D&B). The `ncbi/*` repos are gated;
this uses an ungated mirror of v1.0.
"""

import re
from typing import Any, Literal

from datasets import load_dataset
from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.scorer import CORRECT, INCORRECT, Score, Target, accuracy, scorer, stderr
from inspect_ai.solver import TaskState, generate, system_message

REPO = "PTPReasoning/MedCalc-Bench-v1.0"

# Identical in both arms — keeps the answer parseable without dictating length.
FORMAT = (
    "You are given a patient note and asked to compute a clinical score. "
    "Work out the answer, then end your reply with a final line of exactly "
    "this form:\n\nAnswer: <integer>"
)

BREVITY: dict[str, str] = {
    "none": "",
    "terse": (
        "\n\nBe brief. Reason through the problem, but say only what you need to "
        "reach the answer. Do not restate the patient note, do not enumerate "
        "criteria you are not scoring, and do not add caveats or disclaimers."
    ),
}


def _to_sample(record: dict[str, Any]) -> Sample:
    return Sample(
        input=f"{record['Patient Note']}\n\n{record['Question']}",
        target=str(record["Ground Truth Answer"]).strip(),
        metadata={
            "calculator": record["Calculator Name"],
            "category": record["Category"],
        },
    )


@scorer(metrics=[accuracy(), stderr()])
def final_integer() -> Any:
    """Extract the trailing `Answer: <int>` and compare exactly."""

    async def score(state: TaskState, target: Target) -> Score:
        text = state.output.completion
        found = re.findall(r"answer\s*[:=]\s*\**\s*(-?\d+)", text, re.IGNORECASE)
        if not found:
            # Fall back to the last integer anywhere in the reply, so a model
            # that ignores the format instruction is not scored as a parse
            # failure. Parse failures would otherwise confound the comparison.
            found = re.findall(r"-?\d+", text)
        answer = found[-1] if found else None

        correct = answer is not None and int(answer) == int(target.text)
        return Score(
            value=CORRECT if correct else INCORRECT,
            answer=answer,
            explanation=None if found else "no integer found in output",
        )

    return score


@task
def medcalc_triage(
    brevity: Literal["none", "terse"] = "none",
    category: str = "risk,severity",
) -> Task:
    """MedCalc-Bench, integer-output subset.

    Args:
        brevity: "none" for the baseline arm, "terse" for the brevity arm.
        category: comma-separated MedCalc categories. Defaults to the
            triage-flavoured ones. Others: lab, physical, diagnosis, dosage.
    """
    wanted = {c.strip() for c in category.split(",")}
    dataset = load_dataset(REPO, split="test")
    samples = [
        _to_sample(record)
        for record in dataset
        if record["Category"] in wanted and record["Output Type"] == "integer"
    ]
    if not samples:
        raise ValueError(f"no integer-output samples for categories {sorted(wanted)}")

    return Task(
        dataset=MemoryDataset(samples),
        solver=[system_message(FORMAT + BREVITY[brevity]), generate()],
        scorer=final_integer(),
    )
