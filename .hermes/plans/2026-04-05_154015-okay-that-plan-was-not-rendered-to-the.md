# Fix missing glow rendering for plan-mode output in the TUI

## Goal
Fix the regression where plan-mode saves a markdown file under `.hermes/plans/` but the CLI/TUI does not render that plan through `glow` after the `write_file` tool completes.

## Current context / assumptions
- The relevant recent commit appears to be `3eed176c` (`Add optional glow preview for generated plans`).
- That commit added plan-preview helpers in `cli.py` and tests in `tests/test_cli_plan_preview.py`.
- The current implementation only previews plans from `_on_tool_complete()`.
- In `cli.py`, `tool_start_callback` and `tool_complete_callback` are both only registered when `self._inline_diffs_enabled` is true.
- The preview path logic currently resolves the written file against local `Path.cwd()` and requires `candidate.is_file()`.
- Hermes file tools are backend-aware (`tools/file_tools.py`), so `write_file` may target a non-local workspace (docker/ssh/modal/daytona/etc.), meaning a local `Path.cwd()`/`is_file()` check can reject a successful remote write even when the plan was created correctly.
- Existing tests only cover the happy-path local case and direct helper invocation; they do not cover remote/backend-aware writes or the callback-gating behavior.

## Proposed approach
Make plan preview independent from local filesystem assumptions and from the inline-diff toggle.

The likely robust fix is:
1. treat plan preview as its own CLI behavior rather than piggybacking entirely on inline diff plumbing,
2. render from the markdown content already available in `write_file` arguments instead of requiring the file to exist locally,
3. preserve the displayed path label for user context,
4. expand tests to cover the real failure modes this commit missed.

## Step-by-step plan
1. Reproduce and confirm the failure path.
   - Review how `HermesCLI` wires callbacks into `AIAgent`.
   - Confirm whether the missed preview happened because:
     - `display.inline_diffs` was off, so `_on_tool_complete` never ran, and/or
     - the plan was written in a non-local backend so `candidate.is_file()` returned false locally.

2. Refactor preview detection to avoid local-file dependence.
   - Replace or extend `_plan_preview_path_from_tool_result()` so it can identify eligible plan writes from `function_name == "write_file"` plus `function_args["path"]` alone.
   - Stop requiring the local resolved file to exist before previewing.
   - Keep the `.hermes/plans/*.md` guard so normal markdown writes elsewhere do not auto-preview.

3. Render glow from content, not from local path.
   - Add a helper that extracts markdown text from `function_args.get("content")`.
   - Update `_preview_plan_with_glow(...)` to support stdin-based rendering (for example, `glow -` or equivalent supported invocation) while still printing the intended plan path as a header line.
   - Fall back cleanly if `glow` is missing, exits non-zero, or content is unavailable.

4. Decouple plan preview from inline diff configuration.
   - Ensure `tool_complete_callback` is still registered when plan preview is desired, even if inline diffs are disabled.
   - Option A: always register `_on_tool_complete`, and let that method internally skip diff rendering when inline diffs are off while still doing plan preview.
   - Option B: split plan preview into a separate callback path/helper and register it independently.
   - Prefer the option with the smallest surface-area change in `cli.py`.

5. Tighten the CLI preview contract.
   - Define exactly when auto-preview should happen:
     - only for successful `write_file`,
     - only for `.hermes/plans/*.md`,
     - only in the CLI/TUI,
     - best-effort with no hard failure if `glow` is unavailable.
   - Confirm that preview order remains sensible relative to inline diff output.

6. Expand automated test coverage.
   - Update/add tests for:
     - successful preview for `.hermes/plans/*.md` without requiring a local file,
     - preview using markdown content from tool args,
     - remote/backend-like scenario where local file does not exist,
     - `display.inline_diffs = False` still allowing plan preview,
     - non-plan writes not previewing,
     - failed `write_file` results not previewing,
     - `glow` missing or failing.

7. Validate manually in the CLI.
   - Run a local CLI session that triggers the plan skill and verify the rendered output appears in the TUI.
   - If practical, also test with a non-local backend configuration to verify backend-aware behavior.

## Files likely to change
- `cli.py`
  - callback wiring around agent construction
  - plan-preview eligibility logic
  - glow rendering helper(s)
  - `_on_tool_complete()` behavior
- `tests/test_cli_plan_preview.py`
  - broaden coverage beyond local-path happy path
- Possibly `agent/display.py`
  - only if preview/diff responsibilities need cleaner separation

## Tests / validation
- Targeted tests:
  - `python -m pytest tests/test_cli_plan_preview.py -q`
- Broader regression checks if code paths widen:
  - `python -m pytest tests/test_cli_init.py -q`
  - `python -m pytest tests/ -q` (only after confirming with the user before long-running builds/test suites)
- Manual verification:
  - trigger `/plan` in the CLI and confirm the plan is visibly rendered via `glow` in the TUI,
  - repeat with inline diffs disabled,
  - repeat in a backend-aware workspace if available.

## Risks / tradeoffs
- Rendering from `function_args["content"]` previews exactly what the model asked to write, which is usually desirable, but it is slightly different from reading the final persisted file back from disk.
- Always registering `_on_tool_complete` could slightly broaden callback activity; the implementation should keep non-plan/non-diff work cheap.
- `glow` stdin behavior must be confirmed; if stdin handling is awkward, a temporary local mirror file may be needed instead.
- If there are other consumers of `_on_tool_complete`, refactoring must avoid changing unrelated TUI behavior.

## Open questions
- Should plan preview be controlled by its own config flag instead of implicitly following `inline_diffs`?
- Is the desired behavior to preview only plan-mode outputs, or any markdown written under `.hermes/plans/`?
- If the backend is remote, should the CLI also show an explicit note that the preview came from tool arguments rather than a locally opened file?
