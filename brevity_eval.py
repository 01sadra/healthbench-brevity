"""Does instructing a model to talk less change its accuracy?

Two clinical short-answer tasks. Both are free-text generation graded by exact
match against a small fixed label vocabulary — so the answer carries no
arithmetic and needs no scratchpad. Reasoning length is genuinely optional,
which is what makes the brevity instruction the thing under test rather than a
proxy for "removed the working space it needed".

`brevity` is the only difference between arms.

Datasets:
  pubmedqa - biomedical research questions over open-access PubMed abstracts,
             answered yes/no/maybe (Jin et al. 2019). 1000 expert-labelled
             items, MIT licence. "maybe" is the hedge class, so an instruction
             not to hedge acts directly on the failure mode under test.
  mednli   - clinical NLI over MIMIC-III derived notes (Romanov & Shivade 2018).
             1422 test items, balanced 3-way. Real clinical text.
             NOTE: derives from MIMIC-III, which normally requires PhysioNet
             credentialed access under a DUA. Aggregate numbers are one thing;
             quoting examples publicly is redistribution of clinical data.
  symptoms - synthetic patient symptom descriptions -> diagnosis, 22 classes
             (Gretel, Apache-2.0). Clean licence, but likely easier: check for
             a ceiling effect before trusting a null result.
"""

import re
import string
from typing import Any, Literal

from datasets import concatenate_datasets, load_dataset
from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.scorer import CORRECT, INCORRECT, Score, Target, accuracy, scorer, stderr
from inspect_ai.solver import TaskState, generate, system_message

MEDNLI_LABELS = ["entailment", "contradiction", "neutral"]
PUBMEDQA_LABELS = ["yes", "no", "maybe"]

PUBMEDQA_PROMPT = """You are given the abstract of a biomedical research paper and a question about its findings.

Answer the question with yes, no, or maybe, based on the abstract. Use "maybe" only when the abstract genuinely does not settle the question.

End your reply with a final line of exactly this form:

Answer: <yes|no|maybe>"""

MEDNLI_PROMPT = """You are given a premise from a clinical note and a hypothesis about the same patient.

Decide whether the hypothesis is an entailment, a contradiction, or neutral with respect to the premise.

End your reply with a final line of exactly this form:

Answer: <entailment|contradiction|neutral>"""

SYMPTOMS_PROMPT_TEMPLATE = """A patient describes their symptoms. Name the single most likely diagnosis.

Choose exactly one of the following, and use its exact wording:
{labels}

End your reply with a final line of exactly this form:

Answer: <diagnosis>"""

# The only manipulated variable, ordered by how hard they squeeze the visible
# output. Reasoning is NOT constrained by any of these -- thinking runs free and
# is pinned equal across arms by --reasoning-effort. What varies is only how
# much of it the model is allowed to say.
BREVITY: dict[str, str] = {
    "none": "",
    "terse": (
        "\n\nBe brief. Reach the answer with as few words as you can. Do not "
        "restate the case, do not list the possibilities you ruled out, and do "
        "not add caveats, hedges, or disclaimers."
    ),
    "caveman": (
        "\n\nWrite your reply in compressed English. Drop articles (a, an, the), "
        "filler (just, really, basically), pleasantries, and hedging. Sentence "
        "fragments are fine. Prefer short words. Keep technical and clinical "
        "terms exact and spelled out in full -- compress the grammar, never the "
        "substance. State findings flat, with no qualifiers."
    ),
    "cap": (
        "\n\nUse at most 15 words in total before the final answer line. Think as "
        "long as you need, but say almost none of it."
    ),
}


def _normalise(text: str) -> str:
    text = text.lower().strip()
    text = text.translate(str.maketrans("", "", string.punctuation))
    return " ".join(text.split())


def _extract(completion: str, vocabulary: list[str]) -> str | None:
    """Pull the committed answer out of the reply.

    Prefers the explicit `Answer:` line. Falls back to the last vocabulary term
    mentioned anywhere, so that a model ignoring the output format is scored on
    what it actually said rather than counted as a parse failure -- parse
    failures would otherwise be confounded with the brevity manipulation.
    """
    match = re.findall(r"answer\s*[:=]\s*\**\s*([^\n*]+)", completion, re.IGNORECASE)
    if match:
        candidate = _normalise(match[-1])
        for label in vocabulary:
            if _normalise(label) == candidate:
                return label
        for label in vocabulary:
            if _normalise(label) in candidate:
                return label

    positions = [
        (completion.lower().rfind(label.lower()), label)
        for label in vocabulary
        if label.lower() in completion.lower()
    ]
    return max(positions)[1] if positions else None


@scorer(metrics=[accuracy(), stderr()])
def label_match(vocabulary: list[str]) -> Any:
    async def score(state: TaskState, target: Target) -> Score:
        answer = _extract(state.output.completion, vocabulary)
        correct = answer is not None and _normalise(answer) == _normalise(target.text)
        return Score(
            value=CORRECT if correct else INCORRECT,
            answer=answer,
            explanation=None if answer else "no label found in output",
        )

    return score


def _pubmedqa() -> tuple[list[Sample], str, list[str]]:
    data = load_dataset("qiaojin/PubMedQA", "pqa_labeled", split="train")
    samples = [
        Sample(
            input="Abstract:\n{}\n\nQuestion: {}".format(
                "\n".join(r["context"]["contexts"]).strip(), r["question"].strip()
            ),
            target=r["final_decision"].strip(),
        )
        for r in data
    ]
    return samples, PUBMEDQA_PROMPT, PUBMEDQA_LABELS


def _mednli() -> tuple[list[Sample], str, list[str]]:
    data = load_dataset("araag2/MedNLI", "processed", split="test")
    samples = [
        Sample(
            input=f"Premise: {r['Premise'].strip()}\n\nHypothesis: {r['Hypothesis'].strip()}",
            target=r["Label"].strip(),
        )
        for r in data
    ]
    return samples, MEDNLI_PROMPT, MEDNLI_LABELS


def _symptoms() -> tuple[list[Sample], str, list[str]]:
    data = load_dataset("gretelai/symptom_to_diagnosis")
    # Both splits: the task is zero-shot, so the train split is unused
    # elsewhere and quadruples statistical power (212 -> 1065).
    combined = concatenate_datasets([data["train"], data["test"]])
    labels = sorted({r["output_text"].strip() for r in combined})
    samples = [
        Sample(input=r["input_text"].strip(), target=r["output_text"].strip())
        for r in combined
    ]
    prompt = SYMPTOMS_PROMPT_TEMPLATE.format(
        labels="\n".join(f"- {label}" for label in labels)
    )
    return samples, prompt, labels


@task
def brevity_eval(
    dataset: Literal["pubmedqa", "mednli", "symptoms"] = "pubmedqa",
    brevity: Literal["none", "terse", "caveman", "cap"] = "none",
) -> Task:
    builders = {"pubmedqa": _pubmedqa, "mednli": _mednli, "symptoms": _symptoms}
    samples, prompt, labels = builders[dataset]()
    return Task(
        dataset=MemoryDataset(samples),
        solver=[system_message(prompt + BREVITY[brevity]), generate()],
        scorer=label_match(labels),
        name=f"brevity_{dataset}_{brevity}",
    )
