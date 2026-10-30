# Revision plan and delivery status

The goal is to make the assignment evidence reproducible and candid while retaining
Homebrew's source tree. Changes are confined to the submission configuration/evidence.

1. **Replace self-generated answers with independent replay — complete.** Freeze
   inputs/rubrics; export one neutral-ID case per fresh Codex agent; preserve actual
   responses, prompt hashes and import provenance. Archive v1 without rewriting it.
2. **Strengthen the corpus and grading — complete, human review pending.** Add four
   nuanced historical cases, contextualize both attacks, and separate structural,
   category and human semantic checks. Keep the tgenv disagreement visible.
3. **Configure an existing agent and real intake — implemented, hosted validation
   pending.** Use pinned Claude Code with tools disabled; add bounded sandbox PR and
   local-commit preparation; retain the optional direct API comparison backend.
4. **Improve workload evidence — complete.** Preserve a 30-PR sample and calculate
   review latency with bot, censoring and sampling limitations. Do not claim a backlog.
5. **Align governance and documentation — complete.** Reserve 18 scheduled cases,
   document registration on the default branch, separate drift from human approval,
   and keep DESIGN.md below 150 lines.
6. **Validate and publish — local checks complete.** Control tests, exact-source
   recollection, frozen hashes and replay records are checked. Publish as an additive
   tree overlay on the clean submission branch, preserving upstream Formula/Aliases.

Remaining human/operator work: independent semantic adjudication; verify CLI package
and model availability; provision a provider key/budget; register the workflow on the
sandbox default branch; run and inspect hosted controls; review student disclosure
and submit the chosen exact commit through eLearn. No credentials or human approvals
are fabricated to make those steps appear complete.
