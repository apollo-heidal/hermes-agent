# Fix markdown rendering gaps and make diff colors theme-relative across Hermes output

## Goal
Resolve the remaining rendering gaps so that:
1. assistant responses and reasoning output that contain markdown actually render as markdown in normal CLI/TUI use,
2. inline diff colors are chosen from the active Hermes theme in a way that fits the theme palette instead of being painfully bright or too dim,
3. content inside diff previews — markdown, code, mermaid/UML-like blocks, and other fenced content where feasible — is rendered more intelligently than plain diff text.

## Current context / assumptions
- Hermes already has a markdown-aware response helper in `cli.py`:
  - `_looks_like_markdown(...)`
  - `_render_response_content(...)`
- Final non-streamed response panels use `_render_response_content(response)`, but streamed responses still appear to bypass that final markdown-aware rendering path.
- Reasoning output is still printed via `_cprint(...)` with raw/dim text and custom border lines, so markdown inside reasoning is not currently rendered.
- Inline file edit previews are rendered through `agent/display.py` and currently prefer external `delta`.
- Hermes recently changed delta colors to derive directly from `ui_ok` and `ui_error`, but that is still too naive:
  - some themes have very bright status colors that are painful on dark backgrounds,
  - some themes have low-contrast defaults that may not fit diff rendering well,
  - theme status colors are not necessarily the right colors for diff hunk backgrounds.
- The user wants diff highlight colors to be theme-relative rather than hardcoded, with these constraints:
  - use the theme palette rather than unrelated colors,
  - additions and deletions should differ from each other,
  - for dark themes, use darker theme-adjacent colors,
  - for light themes, use lighter theme-adjacent colors,
  - the chosen colors should not be wildly different in brightness from the surrounding theme background impression,
  - the colors still need to contrast each other and remain legible.
- The current built-in skins in `hermes_cli/skin_engine.py` expose palette entries such as:
  - `banner_border`
  - `banner_title`
  - `banner_accent`
  - `banner_dim`
  - `banner_text`
  - `ui_accent`
  - `ui_label`
  - `ui_ok`
  - `ui_error`
  - `response_border`
- The user also wants richer rendering inside diff blocks themselves:
  - markdown,
  - code,
  - mermaid/UML-like blocks,
  - and similar structured content.
- This turn is planning only; no implementation should be done here.

## Proposed approach
Treat this as a broader rendering integration task with three connected workstreams:
1. response/reasoning markdown rendering integration,
2. theme-relative diff palette derivation,
3. structured-content rendering inside diff previews.

Rather than simply mapping delta plus/minus to `ui_ok`/`ui_error`, Hermes should derive a diff palette from the current skin’s overall luminance and available palette colors, then choose add/remove colors that are:
- theme-consistent,
- mutually distinct,
- and close enough in brightness to the theme’s visual field that they do not visually scream against the background.

For rendering, Hermes should not attempt to make *all* transcript lines markdown-aware. Instead, it should target the user-visible rich-content surfaces:
- final assistant responses,
- reasoning boxes,
- diff preview content.

## Step-by-step plan
1. Fix the response-path integration gap.
   - Review the response rendering logic in `cli.py` around:
     - `_render_response_content(...)`
     - streamed response handling,
     - `already_streamed` / `response_previewed` branching,
     - response panel rendering.
   - Confirm which normal CLI path is preventing markdown-aware rendering from appearing when content was streamed.
   - Decide on the final UX for streamed responses:
     - keep live streaming plain for responsiveness,
     - then render a markdown-aware final pass at completion,
     - or redesign the finalization step so the completed content can replace the plain streamed representation without ugly duplication.

2. Fix reasoning rendering integration.
   - Replace the current raw `_cprint(...)` reasoning body with a renderable path that can display markdown-aware content.
   - Keep the reasoning box/frame if it still fits Hermes visually.
   - Ensure truncation is compatible with fenced code blocks and structured markdown.
   - Decide whether reasoning should use the same markdown heuristic as assistant responses or a stricter one.

3. Design a shared structured-content renderer.
   - Generalize the current response helper into a broader renderable selector that can classify content as:
     - ANSI-bearing text,
     - markdown-rich text,
     - plain text,
     - code/fenced blocks where special handling is needed.
   - Make this helper reusable across:
     - assistant responses,
     - reasoning output,
     - diff sidecar/sub-rendering.

4. Rework diff color selection to be theme-relative instead of status-color-relative.
   - Inspect the available theme palette fields in `hermes_cli/skin_engine.py`.
   - Define a palette-selection strategy that derives add/remove colors from multiple theme colors, not just `ui_ok` / `ui_error`.
   - Likely candidates to consider when deriving colors:
     - `banner_text`
     - `banner_dim`
     - `ui_accent`
     - `ui_label`
     - `response_border`
     - `ui_ok`
     - `ui_error`
   - Decide whether Hermes should:
     - use two existing palette colors directly, or
     - derive slightly adjusted variants from theme colors while still staying visibly inside the theme family.
   - Prefer subtle, theme-fitting colors over highly saturated status colors.

5. Add theme brightness classification.
   - Determine whether the active theme is effectively dark or light based on theme color luminance.
   - Use that classification to choose appropriate diff colors:
     - dark theme → darker but distinguishable add/remove colors,
     - light theme → lighter but distinguishable add/remove colors.
   - Constrain the chosen colors so they do not differ too strongly in brightness from the theme context.
   - Ensure add/remove colors also contrast each other enough to remain legible.

6. Define a deterministic diff-palette algorithm.
   - Specify a stable selection/derivation process such as:
     - infer theme luminance from `banner_text` / `banner_dim` / `response_border`,
     - select a candidate pair from the palette or derive a pair from palette anchors,
     - reject pairs that are too close together,
     - reject pairs that are too far in luminance from the theme context,
     - fall back to a safe theme-relative default pair if needed.
   - Keep the algorithm testable and independent from the actual delta subprocess call.

7. Extend diff rendering beyond plain delta text.
   - Keep delta as the top-level diff renderer when available.
   - Add a second rendering layer for the *content* inside diff hunks.
   - For markdown and fenced structured content, evaluate whether Hermes should append sidecar render previews beneath the delta diff rather than trying to parse ANSI-colored delta output directly.
   - Prefer operating on raw diff/content before or beside the delta-rendered text, not on delta’s ANSI output.

8. Decide the scope of diff content rendering.
   - Start by targeting the most valuable structured cases:
     - markdown files (`*.md`),
     - fenced code blocks with language tags,
     - fenced `markdown`,
     - fenced `mermaid` or other diagram/UML-like blocks where graceful textual rendering is possible.
   - Decide whether to render:
     - only changed/added fenced blocks,
     - or relevant structured sections from the post-edit content.
   - Prefer a strategy that avoids brittle hunk parsing where possible.

9. Choose the rendering behavior for fenced content inside diffs.
   - For markdown blocks:
     - render via the same markdown-aware in-process renderer used for responses/reasoning.
   - For code fences:
     - use syntax highlighting if supported by the chosen renderer.
   - For mermaid/UML-like blocks:
     - if true diagram rendering is not feasible in terminal form, at minimum preserve them as clearly fenced, syntax-highlighted blocks rather than raw diff lines.
   - Decide whether these sub-renders should appear:
     - inline beneath each relevant diff section,
     - or as a grouped “rendered preview” sidecar section.

10. Add tests for the missing integration points.
   - Expand tests to cover:
     - streamed response markdown rendering,
     - reasoning markdown rendering,
     - theme-based delta color derivation,
     - dark-theme and light-theme diff palette behavior,
     - fallback behavior when suitable contrasting theme colors cannot be found,
     - diff sidecar rendering for markdown/code/mermaid-like fenced content.
   - Likely files:
     - `tests/test_cli_response_rendering.py`
     - `tests/test_display.py`
     - possibly a new CLI integration rendering test file.

11. Validate manually in the real CLI.
   - Test assistant responses containing:
     - headings,
     - list markers,
     - fenced Python blocks,
     - nested fenced markdown,
     - fenced mermaid/UML-like content.
   - Test reasoning output with similar structure.
   - Test diff previews on:
     - markdown plan files,
     - code files,
     - markdown files containing nested fenced content.
   - Compare dark-theme and light-theme skins to ensure the derived diff colors remain theme-consistent and comfortable to read.

## Files likely to change
- `cli.py`
  - streamed response finalization path
  - response panel rendering logic
  - reasoning box rendering
  - possibly a generalized structured-content render helper
- `agent/display.py`
  - delta color derivation logic
  - theme brightness / palette selection helpers
  - diff content sub-rendering hooks
  - delta/fallback integration
- `hermes_cli/skin_engine.py`
  - possibly only used as a source of palette values; may not need code changes unless helper utilities are added there
- Tests likely to change/add:
  - `tests/test_cli_response_rendering.py`
  - `tests/test_display.py`
  - possibly a new CLI integration rendering test file

## Tests / validation
- Focused tests for response/reasoning rendering:
  - `python -m pytest tests/test_cli_response_rendering.py -q`
- Focused tests for delta palette derivation and diff rendering:
  - `python -m pytest tests/test_display.py -q`
- Combined targeted run after integration work:
  - `python -m pytest tests/test_cli_response_rendering.py tests/test_display.py tests/test_cli_plan_command.py -q`
- Manual validation:
  - run `./hermes chat` in interactive mode,
  - verify markdown-rich responses render properly,
  - enable reasoning display and verify markdown-aware reasoning rendering,
  - verify diff colors look theme-consistent and not painfully bright on dark themes,
  - verify structured content inside diffs gets a richer rendering path.
- Ask before running longer/full suites, per user preference.

## Risks / tradeoffs
- Rendering the final response after streaming may duplicate content unless Hermes adopts a clear replacement/finalization strategy.
- Delta color derivation from theme colors can become overly clever; the algorithm should remain deterministic and easy to reason about.
- Some themes may not contain an obviously good pair of diff colors, requiring derived variants or safe fallbacks.
- Markdown/code/mermaid rendering inside diffs can get noisy if shown for every change; scope and truncation rules will matter.
- Parsing or reconstructing structured content from diffs is more complex than rendering final response text.
- Truncating reasoning or diff sidecars mid-fence may produce awkward rendering unless truncation becomes structure-aware.

## Open questions
- Should Hermes derive diff colors strictly from existing palette entries, or is it acceptable to compute slight variants of those colors while staying theme-faithful?
- Should streamed responses always get a markdown-aware final pass, even if that means some duplication?
- Should reasoning use the exact same structured-content renderer as assistant responses?
- For diff previews, should rendered structured content appear inline beneath each hunk or in a single grouped preview section?
- For mermaid/UML-like blocks, is syntax-highlighted fenced rendering sufficient, or is a more specialized terminal rendering desired later?
