# AI Product Playbook

An ever-growing repository of reusable AI building blocks, patterns, and workflows used across different AI projects.

Instead of a single app, this folder is maintained as a practical component library: tested prompts, notebook experiments, API patterns, and ML templates that can be reused and adapted quickly.

## What This Repository Captures

- Reusable OpenAI API interaction patterns
- Prompt engineering techniques and evaluation workflows
- Baseline ML notebook templates for structured data problems
- Reusable Codex prompts for engineering/refactoring workflows

## Reusable Components

- `open_ai_api.ipynb`:
  reusable examples for `responses.create`, chat completions, structured outputs, moderation, and multimodal input.
- `advanced_prompt_techniques.ipynb`:
  reusable prompt patterns (zero/one/few-shot, role prompting), consistency controls, token optimization, and LLM-as-judge examples.
- `sklearn_ml.ipynb`:
  reusable ML workflow templates for classification, regression, PCA, and k-means clustering.
- `reusable_prompts.md`:
  reusable Codex prompts for repo scanning, refactor planning, and implementation workflows.

## How To Use This Playbook

- Copy/adapt notebook sections into project-specific prototypes
- Reuse prompt patterns as starting points, then tune for domain context
- Use ML notebook flows as baseline templates before production hardening
- Keep adding proven patterns as new projects are delivered

## Setup

### Prerequisites

- Python 3.10+
- Jupyter Notebook or VS Code Jupyter extension
- OpenAI API key (for LLM notebooks)

### Environment (recommended)

```bash
cd ai-product-playbook
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install notebook jupyterlab openai python-dotenv pydantic numpy pandas matplotlib seaborn scikit-learn
```

Create a local `.env` file in this folder:

```bash
OPENAI_API_KEY=your_api_key_here
```

## Run

From `ai-product-playbook/`:

```bash
jupyter notebook
```

Open notebooks in this order for a progressive path:
1. `open_ai_api.ipynb`
2. `advanced_prompt_techniques.ipynb`
3. `sklearn_ml.ipynb`

## Notes

- API-based sections require an active internet connection and valid credentials.
- Some outputs are non-deterministic due to model sampling behavior.
- This repository is intentionally iterative and should keep expanding with reusable components from future AI projects.
