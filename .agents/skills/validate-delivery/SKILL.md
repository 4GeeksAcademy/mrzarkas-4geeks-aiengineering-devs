---
name: validate-delivery
description: Validate completed HealthCore repository changes before commit or PR preparation. Use to review acceptance criteria, architecture, existing agent rules, tests, security and delivery readiness. Do not use to implement features or change project files.
---

# validate-delivery

## Purpose

Produce one verifiable Markdown report stating whether a completed HealthCore change is ready for delivery. This skill is read-only with respect to repository code and configuration. It does not implement or repair the task.

## Inputs

### Required

- Task description.
- Task acceptance criteria.
- Modified file list and complete relevant diff, including new or untracked files.
- Repository context: current checkout and the mandatory context documents.
- Applicable `.agents/rules/` files and their scope.

Identify each missing required input before evaluating. Do not infer missing task criteria from prior conversations. If an input is essential and cannot be obtained from the checkout, return `BLOCKED` and name it.

### Contextual

- Git branch or change reference.
- Test and validation commands documented for the affected component.
- Applicable architecture documentation and local README files.
- Test output or other verification evidence.
- Explicit approvals for changes to protected files or operations.

## Execution instructions

Perform these steps in order and record evidence as you go:

1. Read `CONTEXT.md`, `AGENTS.md`, `memory-bank/product-context.md`, `memory-bank/technology-stack.md` and `memory-bank/current-state.md`. Read other Memory Bank documents relevant to the task.
2. Identify applicable Rules from `.agents/rules/README.md` and the matching Rules' `alwaysApply`/`globs`; do not modify them. If the runtime does not expose a skill invocation mechanism, read this file explicitly and do not claim automatic discovery.
3. Compare the task description, acceptance criteria, approved scope and modified file list. Separate business needs, proposed functionality and implemented behavior.
4. Obtain and inspect the complete change: branch/reference, Git status, staged and unstaged diffs, and contents of new/untracked files. Do not assume `git diff` includes untracked files.
5. Check architectural boundaries against the actual tree and relevant README files. `/uis/website` is a planned location but is absent in the inspected tree; `/uis/backoffice` and `/services/central-api` exist. Verify rather than treating a planned path as implemented.
6. Check HealthCore business and security constraints against `CONTEXT.md`, `AGENTS.md` and approved documentation: least privilege; no real patient data or disabled controls; HIPAA and UK GDPR treated as distinct; no US/UK health-data transfer without a validated legal and technical basis; and no external processor of patient data without approval. For privacy, PHI, audit, retention or international-transfer impacts, require evidence of review by Compliance and Data Governance, led by Claire Whitfield. Do not turn proposed capabilities into implemented or approved ones.
7. Identify protected paths and operations. Require explicit approval evidence for any protected change. A confirmed unauthorized change is a failure; absent or ambiguous approval evidence is a blocker.
8. Inspect the changed content for secrets, credentials, PHI, patient identifiers and unnecessary sensitive data. Use available scanning tools where appropriate, review the diff, and never reproduce secret values in the report. Use only synthetic data in validation examples.
9. Run available, relevant, non-destructive validations documented by the repository. Do not run tests against real data or shared production systems. Before running a command, assess whether it may change repository files, databases or other state; do not run it unless its effects are isolated and safe. If no safe execution is available, report the command as not run with the reason; do not represent documentary review as an executed test. Compare Git status before and after validation.
10. Evaluate each task acceptance criterion and AC-01 through AC-10 individually using evidence, not an agent's assertion. Mark inapplicable criteria with a concrete reason and identify who accepts that disposition.
11. Produce the report in the format below. Do not write the report into the repository unless separately authorized.

Never run destructive tests or operations that mutate real data. If a test may touch shared state and isolation cannot be proven, do not execute it and return `BLOCKED` when it is mandatory.

## Verifiable acceptance criteria

For every criterion, include the verification method and observed evidence. A claim without inspectable evidence cannot pass.

| ID | Criterion | Verification method | Required evidence | Success | Failure or blocker |
| --- | --- | --- | --- | --- | --- |
| AC-01 | Mandatory context was consulted. | Inspect session evidence/read list and the referenced files in the checkout. | `CONTEXT.md`, `AGENTS.md`, the three mandatory Memory Bank documents, plus task-relevant context. | All required documents exist and were actually read. | `FAIL` if evidence proves a required source was skipped; `BLOCKED` if a required source is unavailable or reading cannot be evidenced. |
| AC-02 | Changes are coherent with HealthCore's business. | Compare behavior and terminology with `CONTEXT.md` and approved product context; check that proposals are not represented as delivered. | Relevant business facts and exact changed lines/behavior. | No contradiction or unsupported claim is found. | `FAIL` for a confirmed contradiction; `BLOCKED` if business meaning or approval is essential but unclear. |
| AC-03 | Existing architecture is respected. | Inspect actual paths, ownership and local README/architecture guidance. | Tree paths, relevant README sections and changed-file paths. | Changes stay in the correct existing application/service boundary. | `FAIL` for a confirmed boundary violation; `BLOCKED` when the target boundary cannot be established. |
| AC-04 | Applicable Rules are followed. | Match changed paths against Rule `globs`; include always-active Rules and inspect relevant requirements. | `.agents/rules/README.md`, applicable Rule files and change evidence. | Every applicable requirement is met, with no Rule altered or disabled without approval. | `FAIL` for a confirmed violation; `BLOCKED` if the applicable Rules or their activation scope cannot be determined. |
| AC-05 | No protected file was modified without authorization. | Compare changed paths with protected paths and inspect explicit approval evidence. | Complete changed-file list and approval record when needed. | No protected change exists, or every such change has explicit approval. | `FAIL` when an unauthorized protected change is confirmed; `BLOCKED` when approval is absent or ambiguous. |
| AC-06 | No credential, secret or inappropriate health data is included. | Review all changed content and available secret-scanning output; redact findings. | Diff/file review and scanner output if available. | No secret, real patient data, unnecessary PHI or patient identifier is present. | `FAIL` for confirmed exposure; `BLOCKED` if content cannot be safely inspected or the scan is mandatory but unavailable. |
| AC-07 | Required tests and validations passed. | Derive required commands from task and local docs; execute only safe, relevant commands. | Exact command, exit status and output summary for each run. | Every mandatory applicable check ran and passed. | `FAIL` for an executed failing mandatory check; `BLOCKED` when a mandatory check cannot safely run or evidence is missing. |
| AC-08 | Task acceptance criteria are satisfied. | Map each criterion to implementation evidence and a test/check. | Criterion-by-criterion result and corresponding evidence. | Every required criterion is verified. | `FAIL` for a confirmed unmet criterion; `BLOCKED` for missing criteria, unresolved interpretation or insufficient evidence. |
| AC-09 | Diff contains only approved-scope changes. | Compare all staged, unstaged and untracked files with the agreed scope. | Approved scope and exhaustive changed-file list. | Every change is authorized and in scope. | `FAIL` for a confirmed out-of-scope change; `BLOCKED` if scope or file status is incomplete. |
| AC-10 | Conclusions have verifiable evidence. | Trace every pass/fail statement to files, diff lines, command output or an approval record. | File paths/sections, redacted command results and approval references. | All conclusions are independently checkable. | `FAIL` for a conclusion contradicted by evidence; `BLOCKED` where evidence is absent or unverifiable. |

## Output format

Return a Markdown report with these sections:

1. **Task:** identifier and concise description.
2. **Change reference:** branch, commit or other reference; say when unavailable.
3. **Files inspected:** list the files, diffs and relevant documents actually inspected.
4. **Acceptance matrix:** task criteria and AC-01–AC-10, each with status, method and evidence.
5. **Validation commands:** exact command, `PASS`/`FAIL`/`NOT RUN`, exit status when run, and concise result. Do not claim an unrun command passed.
6. **Risks:** confirmed risks and unresolved items.
7. **Corrective recommendations:** actionable next steps, or `None` when none are evidenced.
8. **Final status:** exactly one of `PASS`, `FAIL` or `BLOCKED`, with rationale.

Overall states:

- `PASS`: every mandatory criterion is verified with evidence; no mandatory validation or approval is outstanding.
- `FAIL`: at least one confirmed mandatory criterion is violated or a mandatory validation failed.
- `BLOCKED`: essential input, evidence, permission, approval or safe validation is unavailable and no confirmed failure already determines the result.

`BLOCKED` is not `PASS`. Never claim readiness on a blocked or failed result. If a confirmed failure coexists with blockers, use `FAIL` and list the blockers separately.

## Synthetic examples (illustrative, not executions)

### Example A — PASS

**Synthetic scenario:** a documentation-only change describes the existing OperationalIncident backoffice queue. The change does not modify protected files, does not claim pilot/production approval, its acceptance criteria are explicit, and the documented relevant checks have recorded successful output. All changed files and evidence are available for inspection.

**Result:** `PASS` only after AC-01–AC-10 and each task criterion have matching evidence. This example is not a claim that any real change or test was run.

### Example B — FAIL or BLOCKED

**Synthetic scenario:** a proposed change transfers patient data between a synthetic US clinic and a synthetic UK clinic and also changes an existing protected Rule. No Cumplimiento/Gobierno del Dato review or protected-file authorization is provided.

**Result:** `FAIL` if the unauthorized protected modification or unvalidated transfer is confirmed. Use `BLOCKED` instead only when the relevant approval status or transfer details cannot be established. In either case, do not reproduce patient data and do not treat `BLOCKED` as ready. This example is not a real transfer or repository modification.

## Constraints

- Do not modify code, project documentation, configuration, Rules or Memory Bank files.
- Do not create or change repository files, including tests or this report.
- Do not create commits, push, create PRs, merge PRs or deploy services.
- Do not disclose credentials or secret values.
- Do not process real health data unless strictly necessary, authorized and controlled; prefer synthetic data.
- Do not declare a criterion passed without inspectable evidence.