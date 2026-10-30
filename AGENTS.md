# Homebrew formula review sandbox

This is an independent evaluation repository, not the Homebrew production tap.
Formula snapshots live in evals/golden/*/input.json; Formula/<letter>/<name>.rb
is Homebrew's Ruby DSL layout. Historical documentation travels with each input.
The scripts directory contains trusted host code. .claude/skills contains procedures.

## Commands
Run `python3 -m unittest discover -s tests -v` for control tests.
Run `python3 scripts/evaluate.py` to score saved reports.
Run `python3 scripts/run_agent.py --case wslay-before --out work/live` for Claude.
The latter requires ANTHROPIC_API_KEY and is a paid operation.

Human formula validation on an appropriate Homebrew machine:
`HOMEBREW_NO_INSTALL_FROM_API=1 brew install --build-from-source <formula>`
`brew test <formula>`; `brew audit --strict <formula>`; `brew style <formula>`.
For new formulae add `--new` to audit. These commands are documentation only for
this reviewer; submitted Ruby, patches, binaries and shell snippets are never run.
A Linux static review cannot establish macOS compatibility or a successful build.

## Conventions and forbidden changes
Keep formula diffs focused. Test the installed package's functional behavior.
A version/help assertion alone usually needs a stronger functional assertion.
Library tests should compile/link and exercise the installed API.
Bottles are maintained by BrewTestBot. Do not edit bottles or formula snapshots.
Do not change upstream files, labels, issues, PRs, refs, or branch protections.
Do not draft answers to Homebrew maintainer questions on behalf of contributors.
Do not turn a lack of findings into merge approval. Report only grounded concerns.
Do not read expected.json or prior outputs during an independent evaluation.
These are instructions; runner capabilities and workflow permissions enforce actions.
