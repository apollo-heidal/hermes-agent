"""Tests for optional glow previews of generated plan markdown files."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from cli import HermesCLI


def _make_cli():
    cli_obj = HermesCLI.__new__(HermesCLI)
    cli_obj._pending_edit_snapshots = {}
    return cli_obj


class TestCLIPlanPreview:
    def test_plan_preview_path_accepts_successful_plan_write(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        cli_obj = _make_cli()
        plan_path = tmp_path / ".hermes" / "plans" / "plan.md"
        plan_path.parent.mkdir(parents=True)
        plan_path.write_text("# Plan\n", encoding="utf-8")

        resolved = cli_obj._plan_preview_path_from_tool_result(
            "write_file",
            {"path": ".hermes/plans/plan.md"},
            '{"bytes_written": 7}',
        )

        assert resolved == plan_path.resolve()

    def test_plan_preview_path_rejects_non_plan_write(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        cli_obj = _make_cli()
        other_path = tmp_path / "notes.md"
        other_path.write_text("# Notes\n", encoding="utf-8")

        resolved = cli_obj._plan_preview_path_from_tool_result(
            "write_file",
            {"path": "notes.md"},
            '{"bytes_written": 8}',
        )

        assert resolved is None

    def test_plan_preview_path_rejects_failed_tool_result(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        cli_obj = _make_cli()
        plan_path = tmp_path / ".hermes" / "plans" / "plan.md"
        plan_path.parent.mkdir(parents=True)
        plan_path.write_text("# Plan\n", encoding="utf-8")

        resolved = cli_obj._plan_preview_path_from_tool_result(
            "write_file",
            {"path": ".hermes/plans/plan.md"},
            '{"error": "boom"}',
        )

        assert resolved is None

    def test_preview_plan_with_glow_renders_output(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        cli_obj = _make_cli()
        plan_path = tmp_path / ".hermes" / "plans" / "plan.md"
        plan_path.parent.mkdir(parents=True)
        plan_path.write_text("# Plan\n", encoding="utf-8")

        printer = MagicMock()
        completed = SimpleNamespace(returncode=0, stdout="Rendered plan\nSecond line\n", stderr="")

        with patch("cli._cprint", printer), patch("cli.shutil.which", return_value="/usr/bin/glow"), patch(
            "subprocess.run",
            return_value=completed,
        ) as run_mock:
            rendered = cli_obj._preview_plan_with_glow(plan_path)

        assert rendered is True
        run_mock.assert_called_once_with(
            ["/usr/bin/glow", str(plan_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        lines = [call.args[0] for call in printer.call_args_list]
        assert lines[0] == "  ┊ preview plan .hermes/plans/plan.md"
        assert "Rendered plan" in lines
        assert "Second line" in lines

    def test_preview_plan_with_glow_skips_when_glow_missing(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        cli_obj = _make_cli()
        plan_path = tmp_path / ".hermes" / "plans" / "plan.md"
        plan_path.parent.mkdir(parents=True)
        plan_path.write_text("# Plan\n", encoding="utf-8")

        with patch("cli.shutil.which", return_value=None), patch("subprocess.run") as run_mock:
            rendered = cli_obj._preview_plan_with_glow(plan_path)

        assert rendered is False
        run_mock.assert_not_called()

    def test_on_tool_complete_runs_diff_then_glow_preview_for_plan(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        cli_obj = _make_cli()
        plan_path = tmp_path / ".hermes" / "plans" / "plan.md"
        plan_path.parent.mkdir(parents=True)
        plan_path.write_text("# Old\n", encoding="utf-8")
        cli_obj._pending_edit_snapshots["tool-1"] = object()
        plan_path.write_text("# New\n", encoding="utf-8")

        events = []

        def _fake_diff(*args, **kwargs):
            events.append("diff")
            return True

        def _fake_preview(path: Path):
            events.append(("glow", path))
            return True

        with patch("agent.display.render_edit_diff_with_delta", side_effect=_fake_diff):
            with patch.object(cli_obj, "_preview_plan_with_glow", side_effect=_fake_preview):
                cli_obj._on_tool_complete(
                    "tool-1",
                    "write_file",
                    {"path": ".hermes/plans/plan.md"},
                    '{"bytes_written": 6}',
                )

        assert events == ["diff", ("glow", plan_path.resolve())]
        assert "tool-1" not in cli_obj._pending_edit_snapshots
