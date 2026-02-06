from __future__ import annotations

from thunder_subtitle_cli.cli import app


def main() -> None:
    # Typer app is a Click command; calling it runs the CLI.
    app()


if __name__ == "__main__":
    main()
