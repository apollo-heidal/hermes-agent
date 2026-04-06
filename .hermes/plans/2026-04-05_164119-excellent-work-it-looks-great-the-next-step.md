# Broaden terminal rendering across Hermes output surfaces

## Goal
Design a generalized terminal-rendering pipeline for Hermes so markdown-rich output — including lists, fenced code blocks, nested markdown, mermaid/UML-like blocks when supported, and syntax-highlighted code — renders consistently and readably across the CLI/TUI.

The plan should decide whether rendering should apply to:
- all assistant responses,
- diff previews,
- or both responses and diff previews,
while preserving Hermes’ current TUI behavior and graceful fallback when richer rendering is unavailable.

## Current context / assumptions
- Hermes currently has a prompt_toolkit-based interactive TUI in `cli.py`.
- Final assistant responses are displayed via Rich panels in the CLI and already pass through response-box rendering code in `cli.py`.
- Inline file edit previews are rendered separately through `agent/display.py`, which now prefers external `delta --paging=never` and falls back to Hermes’ internal ANSI diff renderer.
- The current diff-only preview is visually strong for file edits, but markdown content inside diffs is still just diff text; nested blocks are not recursively rendered.
- Hermes already has at least one existing Rich Markdown usage pattern in the repo (`hermes_cli/plugins_cmd.py` renders `after-install.md` with `rich.markdown.Markdown`), so there is precedent for in-process markdown rendering.
- The user wants a broader design, not just plan-file rendering:
  - many agent responses are already markdown,
  - many diffs contain markdown or code fences,
  - syntax highlighting would be valuable,
  - claw-code may offer ideas, but should be treated only as inspiration, not a drop-in pattern.
- This turn is planning only. No implementation should be done here.

## Proposed approach
Treat Hermes rendering as a layered display pipeline with distinct content classes:
1. assistant responses,
2. inline diff previews,
3. reasoning/tool transcript lines,
4. other markdown-bearing UI surfaces.

The core design question is not just “can we render nested markdown in diffs,” but rather:
- what output classes should be rendered as markdown-aware terminal content,
- what renderer should own each class,
- and where the boundary should be between raw transcript fidelity and rich presentation.

The likely best outcome is a hybrid design:
- assistant responses get markdown-aware rendering in the response panel,
- diff previews keep delta as the primary diff renderer,
- markdown-aware sub-rendering is layered into diffs only where it improves comprehension,
- low-level transcript/tool lines stay compact and predictable.

## Key design decision to make
Decide among these rendering scopes:

### Option A — Render only final assistant responses
Pros:
- simplest mental model,
- least invasive,
- immediate benefit because most agent answers are already markdown.

Cons:
- diff previews still do not render markdown/code blocks richly,
- plan updates and markdown-heavy file edits stay less expressive.

### Option B — Render only diff outputs richly
Pros:
- preserves current response box behavior,
- focuses effort where nested markdown/code-in-code is most relevant,
- naturally complements delta.

Cons:
- markdown-rich assistant responses still miss structure/syntax highlighting.

### Option C — Render both assistant responses and diff outputs
Pros:
- most complete user experience,
- consistent markdown/code rendering across the main Hermes surfaces,
- best match for the user’s stated direction.

Cons:
- largest implementation surface,
- greater risk of inconsistent styles between Rich response panels and delta diff output,
- requires stronger abstraction to avoid duplicated rendering logic.

### Option D — Attempt to render all transcript output
Pros:
- maximum visual richness.

Cons:
- likely too noisy,
- risky for tool progress lines and prompt_toolkit layout,
- could degrade readability of operational/status output.

Current recommendation:
- investigate Option C as the target architecture,
- but explicitly avoid rendering every transcript/status/tool-progress line.

## Step-by-step plan
1. Inventory all Hermes output surfaces.
   - Identify where assistant responses, diff previews, reasoning blocks, tool transcript lines, clarify prompts, and plugin/doc markdown are rendered.
   - Map which surfaces already use Rich, ANSI text, prompt_toolkit-native rendering, or captured subprocess output.
   - Focus initial review on:
     - `cli.py`
     - `agent/display.py`
     - `hermes_cli/plugins_cmd.py`

2. Define content classes and rendering rules.
   - Split output into categories such as:
     - final assistant response,
     - diff preview,
     - reasoning preview,
     - tool transcript/status,
     - static markdown docs/help/install notes.
   - For each class, decide whether the desired representation is:
     - plain text,
     - markdown-aware rendering,
     - syntax-highlighted code,
     - diff renderer output,
     - or a hybrid.

3. Evaluate renderer candidates.
   - In-process Rich Markdown / syntax-highlighting path:
     - strong candidate for assistant responses,
     - likely best for prompt_toolkit compatibility.
   - External delta path:
     - strong candidate for diffs,
     - already integrated.
   - Optional external markdown renderers (if considered later):
     - useful only if they fit the TUI model better than Rich.
   - Decide whether one unified renderer abstraction can dispatch to:
     - markdown renderer for responses,
     - delta for diffs,
     - fallback plain/ANSI renderers when optional tools are missing.

4. Research pattern ideas from claw-code without assuming direct compatibility.
   - Inspect claw-code’s TUI rendering patterns for:
     - markdown rendering strategy,
     - code syntax highlighting,
     - diff rendering approach,
     - handling of fenced blocks and diagrams.
   - Extract reusable ideas, but compare them against Hermes’ prompt_toolkit + Rich + inline transcript architecture before adopting anything.

5. Design a rendering abstraction layer.
   - Propose a small renderer interface or dispatcher in Hermes that accepts:
     - content type (`response`, `diff`, `doc`, etc.),
     - source format (`markdown`, `unified_diff`, `plain_text`),
     - optional hints (language, file path, width constraints).
   - The dispatcher should decide:
     - delta vs fallback for diffs,
     - Rich Markdown vs plain text for assistant responses,
     - whether nested fenced blocks should trigger recursive rendering.

6. Decide how responses should be rendered.
   - Determine whether Hermes should render assistant responses as markdown by default in the response panel.
   - Evaluate whether this should apply to all responses or only when markdown structure is detected.
   - Decide how code blocks should be shown:
     - Rich syntax highlighting inside panels,
     - preserved raw code fences,
     - or a configurable mode.

7. Decide how diffs should be rendered.
   - Keep delta as the top-level diff renderer when available.
   - Design whether markdown-aware sub-rendering should be appended beneath diff sections for markdown/code-rich content.
   - For markdown files, consider rendering changed fenced blocks as sidecar previews rather than attempting to parse ANSI-colored delta output directly.
   - For code files, consider whether syntax-highlighted sidecar snippets are warranted or whether delta alone is sufficient.

8. Design fallback behavior.
   - Ensure every rich path has a clear fallback:
     - no delta → Hermes internal ANSI diff renderer,
     - no markdown renderer → existing plain/Rich text behavior,
     - renderer error → raw text/diff without breaking the TUI.
   - Preserve reliable rendering in both interactive TUI and non-interactive `-q`/batch contexts.

9. Define width, truncation, and verbosity rules.
   - Rich rendering is more verbose than raw text; determine truncation and line-budget rules for:
     - responses,
     - long code fences,
     - nested markdown previews in diffs.
   - Decide what should appear in normal mode vs verbose mode.

10. Plan test coverage.
   - Add unit tests for renderer selection and fallback behavior.
   - Add CLI-facing tests for:
     - markdown response rendering,
     - code fence/syntax highlighting selection,
     - delta rendering fallback,
     - markdown-rich diff sidecar previews if implemented.
   - Preserve existing tests that verify TUI-safe output and inline diff behavior.

11. Plan manual validation scenarios.
   - Assistant response containing:
     - headings,
     - list markers,
     - fenced Python block,
     - nested markdown block,
     - mermaid/UML-like fenced block.
   - File edit diff on:
     - a markdown plan file with nested fences,
     - a Python file with code changes,
     - a non-markdown text file.
   - Compare interactive `./hermes chat` and non-interactive `./hermes chat -q ...` behavior.

## Files likely to change
- `cli.py`
  - response rendering path,
  - possibly response box content preparation,
  - possibly output-mode branching for rendered vs plain response content.
- `agent/display.py`
  - diff rendering abstraction,
  - optional nested content rendering hooks,
  - renderer selection/fallback logic.
- `hermes_cli/plugins_cmd.py`
  - useful reference for existing Rich Markdown usage; may not need changes.
- Potential new helper module if abstraction grows:
  - e.g. `agent/rendering.py` or similar, if keeping renderer logic out of `cli.py`/`agent/display.py` becomes cleaner.
- Tests likely to change/add:
  - `tests/test_display.py`
  - existing CLI rendering tests,
  - new tests for response markdown rendering if needed.

## Tests / validation
- Focused unit tests for renderer helpers and diff output selection.
- CLI-focused tests for response rendering and markdown/code-fence handling.
- Manual validation in both:
  - interactive TUI (`./hermes chat`),
  - non-interactive query mode (`./hermes chat -q ...`).
- If the final implementation expands broadly, run wider CLI test slices after focused tests pass.
- Ask before running longer/full suites, per user preference.

## Risks / tradeoffs
- Rendering all output as markdown is likely too aggressive; transcript/status/tool lines may become noisy or semantically incorrect.
- Markdown renderers and diff renderers have different strengths; forcing one renderer to solve all surfaces may produce worse results than a hybrid pipeline.
- Syntax highlighting and markdown rendering can change spacing/wrapping in ways that affect prompt_toolkit layout.
- Mermaid/UML and other exotic fenced blocks may need graceful degradation; terminal renderers vary widely in what they actually support.
- Captured subprocess output may lose some TTY-specific styling, so direct tool passthrough is not always a safe design.
- Borrowing patterns from claw-code may be useful conceptually, but their renderer assumptions may not fit Hermes’ architecture.

## Open questions
- Should markdown-aware rendering be enabled by default for all assistant responses, or only when structure is detected?
- Should code fences in assistant responses be syntax-highlighted by default?
- Should diff previews remain delta-only for most files, with richer sidecar rendering only for markdown/code-heavy content?
- Is a hybrid renderer abstraction preferable to a single universal renderer?
- Should there be a user-facing config toggle for response markdown rendering, syntax highlighting, and diff sub-rendering?
- Which claw-code ideas are actually compatible with Hermes’ prompt_toolkit + Rich display model?
