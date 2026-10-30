# Homebrew formula review agent evaluation

An independent assignment sandbox for Homebrew/homebrew-core. This branch retains
Homebrew's source tree; the agent reviews bounded formula snapshots and writes
advisory JSON artifacts. Read [DESIGN.md](DESIGN.md) for decisions and limitations.

## Verify the deliverables

Python 3.10+ and Git are sufficient for the offline checks:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/evaluate.py --mechanical-only
python3 scripts/measure_reviews.py
```

All 18 saved reports pass structural validation. Category agreement is 17/18;
the simple baseline scores 16/18. These are diagnostic comparisons against
AI-authored provisional expectations, not semantic accuracy or proof of usefulness.
`python3 scripts/evaluate.py` deliberately exits 1 until independent human
adjudications are recorded. See [evals/README.md](evals/README.md) for reproduction,
the retained disagreement, transcripts, and a blank human review form command.

## Existing agent configuration

The primary runtime configures **Claude Code**, an existing agent, with the supplied
AGENTS.md and SKILL.md explicitly injected into its system prompt. Built-in tools,
MCP connections, hooks/config discovery and persistent sessions are disabled.
The original direct API runner remains as an optional comparison backend; AGENTS.md
and SKILL.md retain their original API wording to preserve the replayed prompt.
Neither runtime relies on automatic skill discovery.

Install the reviewed CLI pin and configure a dedicated ANTHROPIC_API_KEY securely:

```sh
npm install --prefix work/runtime @anthropic-ai/claude-code@2.1.290
PATH="$PWD/work/runtime/node_modules/.bin:$PATH" python3 scripts/run_claude_code.py --case wslay-before --out work/live
```

Use a new output directory for every run. The model is pinned to
`claude-sonnet-4-20250514`. CLI installation and model availability could not be
verified in this environment: no Claude executable/key was present and registry
access was blocked. Review any replacement version and rerun the corpus before
activation. Command wiring is tested with a stub, not a provider request.
The permitted fallback was performed with 18 fresh Codex agents, each requesting
`gpt-6.1-sol`, no conversation history, and only one exported case plus instructions.

## Review a new sandbox PR or local commit

The workflow accepts an optional `pr_number` in this sandbox repository. Trusted
preparation fetches immutable commit objects and reads at most five changed formulae.
It never checks out or executes submitted code. Mixed non-formula changes, deletions,
large inputs and invalid IDs fail closed. PR title/body are untrusted input.
For local commits from a trusted clone:

```sh
python3 scripts/prepare_input.py --source /path/to/homebrew-core --base FULL_BASE_SHA --head FULL_HEAD_SHA --case-id local-1 --out work/input.json
python3 scripts/run_claude_code.py --input work/input.json --out work/local
```

Preparation is trusted host code; no GitHub credential enters the agent subprocess.
Reports cover static evidence and do not establish successful builds or compatibility.

## Activate in your own sandbox

The Actions file is a platform equivalent, not GitHub Agentic Workflows; no compiled
`.lock.yml` applies. It supports manual dispatch and a weekly golden replay.
GitHub requires the workflow on the repository's default branch for dispatch
registration and scheduling. The clean submission branch is allowed by the job
condition, but publishing this branch alone does not activate the workflow.
Record operator approval in OPERATORS.md, provision a dedicated provider project
key with a spending limit, and inspect the first hosted artifact before routine use.
No hosted run, required-review branch protection or provider budget is claimed here.
Do not activate it in Homebrew's repository without permission.
Monday 02:00 UTC is Monday 10:00 in Kuala Lumpur.

Submit the exact reviewed commit URL through eLearn. If private, grant the required
assessor access. Human adjudication and the student's contribution/disclosure review
remain necessary; this repository does not claim they have happened.

## Evidence layout

- `evals/golden/`: 16 historical cases and two attacks, frozen rubrics and real replays.
- `evals/archive/v1/`: original weaker evaluation, retained without rewriting its results.
- `evals/logs/`: control tests, preflight limitations and replay execution notes.
- `evidence/`: review-latency sample and compressed original commit-volume evidence.
- `IMPLEMENTATION_PLAN.md`: implemented changes and unresolved validation.

Copied Homebrew material retains LICENSE.homebrew. New configuration and scripts
use the same BSD-2-Clause license; see LICENSE.
