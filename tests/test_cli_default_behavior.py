from __future__ import annotations

from typer.testing import CliRunner

import thunder_subtitle_cli.cli as cli_mod


def test_no_args_prints_help_when_not_tty(monkeypatch) -> None:
    runner = CliRunner()

    def _false() -> bool:
        return False

    monkeypatch.setattr(cli_mod, "is_tty", _false)

    res = runner.invoke(cli_mod.app, [])
    assert res.exit_code == 0
    assert "Commands" in res.output

