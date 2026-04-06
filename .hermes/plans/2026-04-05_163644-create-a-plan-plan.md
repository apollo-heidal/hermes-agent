# Create-a-Plan Implementation Plan

> For Hermes: this is a planning artifact only. Do not execute implementation work from this document until a concrete task is chosen.

## Goal
Create a repeatable, higher-quality process for turning an ambiguous request into an execution-ready implementation plan with clear scope, ordered tasks, validation steps, and explicit unknowns.

## Architecture
This plan treats planning as a small pipeline: define the objective, inspect relevant context, constrain scope, choose an approach, break the work into sequenced tasks, and prove the plan is executable by attaching validation and open questions. The output should be specific enough that a developer can begin work without guessing.

## Tech stack
- Markdown plan documents
- Hermes read-only inspection tools when project context exists
- Repository-local plan storage in `.hermes/plans/`

---

## Current context / assumptions
- The current request is still meta-level: improve the plan itself rather than execute project work.
- No concrete feature, repository area, bug report, or acceptance criteria were supplied.
- Because the task is underspecified, the most useful iteration is to strengthen the planning framework so it can be reused for real implementation requests.
- The improved plan should optimize for clarity, handoff quality, and low ambiguity.

## Proposed approach
Upgrade the original lightweight outline into a more execution-ready planning template with:
1. a stricter intake phase,
2. clearer plan quality gates,
3. a concrete task decomposition format,
4. explicit validation requirements,
5. stronger handling of risks, dependencies, and open questions.

## Deliverable definition
A good plan produced from this workflow must answer all of the following:
- What exactly is being changed?
- Why is the change needed?
- What is in scope and out of scope?
- Which files, systems, or components are likely involved?
- What are the ordered implementation steps?
- How will the work be validated?
- What is still unknown or risky?
- What decisions must be made before execution starts?

---

## Step-by-step plan

### Phase 1: Intake and framing

#### Task 1: Define the planning target
Objective: convert the request into a single-sentence outcome statement.

Steps:
1. Rewrite the request as: "Plan how to <do specific thing>."
2. Identify the business or technical reason for the change.
3. Capture any explicit constraints such as deadline, non-goals, environment, or compatibility requirements.
4. If the request is missing core context, record assumptions rather than silently inventing details.

Exit criteria:
- The plan begins with a one-sentence goal.
- Constraints and assumptions are listed explicitly.

#### Task 2: Identify missing information early
Objective: surface ambiguity before writing implementation steps.

Steps:
1. List the inputs required to make the plan concrete.
2. Mark each input as known, unknown, or assumed.
3. Separate blocking unknowns from non-blocking unknowns.
4. If the task is too vague to plan responsibly, stop and ask a clarifying question instead of padding the plan.

Exit criteria:
- Unknowns are visible.
- The planner knows whether a useful draft can proceed.

### Phase 2: Context collection

#### Task 3: Gather relevant context
Objective: inspect only the information needed to make the plan actionable.

Steps:
1. Review the relevant code, docs, configuration, tests, and adjacent components.
2. Look for existing patterns to reuse instead of inventing new structure.
3. Capture the current system behavior and any important invariants.
4. Note likely dependencies, integration points, and ownership boundaries.

Exit criteria:
- The plan references the existing system, not an imagined one.
- Reusable patterns and dependencies are documented.

#### Task 4: Bound the scope
Objective: make the plan safe to execute by defining edges.

Steps:
1. Write a short in-scope list.
2. Write a short out-of-scope list.
3. Record blockers, upstream dependencies, and downstream effects.
4. Call out rollout or migration needs if the change affects existing behavior.

Exit criteria:
- The reader can tell what will not be done.
- Scope creep risks are visible before implementation begins.

### Phase 3: Solution design

#### Task 5: Choose the implementation approach
Objective: document the intended path before task decomposition.

Steps:
1. Summarize the preferred approach in 2-4 sentences.
2. Note at least one plausible alternative if a real tradeoff exists.
3. State why the chosen approach is preferred.
4. Keep the design DRY and YAGNI: prefer extending existing patterns over introducing new abstractions.

Exit criteria:
- The plan has a clear recommended direction.
- Major tradeoffs are acknowledged.

#### Task 6: Identify change surfaces
Objective: make execution concrete by naming the likely touchpoints.

Steps:
1. List exact file paths when known.
2. If file paths are not yet known, list the exact subsystem or directory to inspect next.
3. Map each file or component to its likely responsibility in the change.
4. Include related tests and documentation that should be updated.

Exit criteria:
- The implementer knows where to start looking.
- Validation surfaces are identified alongside code surfaces.

### Phase 4: Execution-ready decomposition

#### Task 7: Break the work into ordered tasks
Objective: transform the approach into a sequence that can be executed without guessing.

Steps:
1. Order tasks from setup to core implementation to validation to cleanup.
2. Keep each task small and outcome-oriented.
3. For each task, state the purpose, affected files, and expected result.
4. Separate discovery tasks from implementation tasks and implementation tasks from validation tasks.

Recommended task template:
- Task name
- Objective
- Inputs / prerequisites
- Files likely to change
- Action
- Expected output
- Validation step

Exit criteria:
- Tasks are sequential.
- Each task has a visible completion condition.

#### Task 8: Add validation for every major workstream
Objective: make the plan testable before execution begins.

Steps:
1. List automated tests to run, if any.
2. List manual checks required for user-visible or operational behavior.
3. Define acceptance criteria in observable terms.
4. Note any environment-specific verification requirements.

Exit criteria:
- Success can be measured.
- Validation is specific, not hand-wavy.

### Phase 5: Review and handoff

#### Task 9: Record risks, tradeoffs, and decisions needed
Objective: reduce implementation surprises.

Steps:
1. List technical risks.
2. List delivery or coordination risks.
3. Document tradeoffs in complexity, speed, maintainability, and compatibility.
4. Write any decisions that must be confirmed before implementation starts.

Exit criteria:
- The implementer knows what to watch for.
- Open questions are easy to escalate.

#### Task 10: Run a final plan quality check
Objective: ensure the plan is truly actionable.

Checklist:
- Does the plan define the goal clearly?
- Does it capture assumptions and constraints?
- Does it identify likely files/components?
- Does it give ordered tasks with completion criteria?
- Does it define concrete validation?
- Does it call out risks and unknowns?
- Could another developer begin work without needing a second planning pass?

Exit criteria:
- If any checklist item fails, revise the plan before handoff.

---

## Suggested reusable output template

```md
# <Feature or Change Name> Implementation Plan

## Goal
<One-sentence outcome>

## Context / assumptions
- ...

## In scope
- ...

## Out of scope
- ...

## Proposed approach
<2-4 paragraph or bullet summary>

## Task breakdown
### Task 1: ...
- Objective:
- Files:
- Action:
- Validation:

### Task 2: ...
- Objective:
- Files:
- Action:
- Validation:

## Tests / verification
- Automated:
- Manual:
- Acceptance criteria:

## Risks / tradeoffs
- ...

## Open questions
- ...
```

## Files likely to change
- `.hermes/plans/2026-04-05_163644-create-a-plan-plan.md`
- For future real tasks, likely additional changes would include:
  - affected source files in the target subsystem
  - corresponding test files
  - docs or operator notes if behavior changes

## Tests / validation
For this meta-plan iteration, validation is document-quality validation:
- The revised plan is more specific than the original.
- It includes a stronger structure for intake, scope, decomposition, and review.
- It provides a reusable output template.
- It defines quality gates so future plans can be judged for completeness.

## Risks, tradeoffs, and open questions

### Risks
- Without a real task, the plan can only optimize the planning method, not project-specific execution details.
- Over-structuring may make lightweight tasks feel heavier than necessary.

### Tradeoffs
- A stricter planning framework improves handoff quality but costs a little more upfront time.
- A reusable template scales well across tasks but may need trimming for trivial changes.

### Open questions
- Should the next iteration optimize for a specific repository workflow, such as feature work, bugfixes, refactors, or infra changes?
- Do you want future plans to be concise checklists or deeply prescriptive implementation guides?
- Should this plan be turned into a reusable internal planning template or skill later?
