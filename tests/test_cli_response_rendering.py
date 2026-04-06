"""Tests for markdown-aware assistant response rendering in the CLI."""

from rich.markdown import Markdown
from rich.text import Text

from cli import _looks_like_markdown, _render_response_content


class TestCLIMarkdownResponseRendering:
    def test_detects_fenced_code_blocks_as_markdown(self):
        text = "Here is code:\n```python\nprint('hi')\n```"
        assert _looks_like_markdown(text) is True

    def test_detects_list_markers_as_markdown(self):
        text = "Steps:\n- one\n- two"
        assert _looks_like_markdown(text) is True

    def test_plain_text_does_not_trigger_markdown(self):
        text = "This is a plain sentence without markdown structure."
        assert _looks_like_markdown(text) is False

    def test_render_response_content_uses_markdown_for_markdownish_text(self):
        renderable = _render_response_content("# Title\n\n```python\nprint('hi')\n```")
        assert isinstance(renderable, Markdown)

    def test_render_response_content_uses_plain_text_for_plain_response(self):
        renderable = _render_response_content("Just a normal sentence.")
        assert isinstance(renderable, Text)
        assert str(renderable) == "Just a normal sentence."

    def test_render_response_content_preserves_ansi_output(self):
        renderable = _render_response_content("\x1b[31merror\x1b[0m")
        assert isinstance(renderable, Text)
        assert "error" in renderable.plain
