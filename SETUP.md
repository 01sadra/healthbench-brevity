# Health Benchmarks — Inspect AI

## Setup

Installed in `.venv`:
- `inspect-ai` 0.3.255
- `inspect_evals` 0.16.1.dev (git main, UK AISI)
- `anthropic` SDK

Activate:

```bash
source .venv/bin/activate
```

## API keys

Set before running:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

HealthBench grading uses a judge model (default `openai/gpt-4o-mini`). Either set
`OPENAI_API_KEY` or override the judge with `-T judge_model=anthropic/claude-sonnet-5`.

Hugging Face datasets (MedQA, PubMedQA) may need `HF_TOKEN` and dataset access.

## Health evals available

| Task | Notes |
|---|---|
| `inspect_evals/healthbench` | OpenAI HealthBench. Subsets: `full`, `hard`, `consensus`, `meta_eval`. Rubric-graded by judge model. |
| `inspect_evals/medqa` | USMLE-style multiple choice. |
| `inspect_evals/pubmedqa` | Biomedical yes/no/maybe from abstracts. |
| `inspect_evals/lab_bench_*` | Biology protocol/sequence/figure QA: `litqa`, `protocolqa`, `seqqa`, `dbqa`, `figqa`, `tableqa`, `suppqa`, `cloning_scenarios`. |
| `inspect_evals/hle` | Humanity's Last Exam (has bio/medicine slice). |
| `inspect_evals/gpqa_diamond` | Graduate-level science incl. biology. |
| `inspect_evals/mmlu_pro` | Has health/biology subjects. |

## Run

Smoke test (10 samples):

```bash
inspect eval inspect_evals/medqa --model anthropic/claude-sonnet-5 --limit 10
```

HealthBench hard subset, Claude judge:

```bash
inspect eval inspect_evals/healthbench -T subset=hard -T judge_model=anthropic/claude-sonnet-5 --model anthropic/claude-sonnet-5 --limit 50
```

Multiple models in one run:

```bash
inspect eval inspect_evals/pubmedqa --model anthropic/claude-sonnet-5,anthropic/claude-opus-5
```

View results:

```bash
inspect view
```

Logs land in `./logs/`.
