from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from .client import ThunderClient, download_with_retries
from .core import apply_filters as _apply_filters
from .formatting import print_search_table, to_json
from .models import ThunderSubtitleItem
from .selector import InteractiveSelector, DeterministicSelector, Selector
from .util import (
    compute_item_id,
    ensure_unique_path,
    is_tty,
    parse_select_spec,
    sanitize_component,
)


app = typer.Typer(add_completion=False, no_args_is_help=False)


@app.callback(invoke_without_command=True)
def _main(ctx: typer.Context) -> None:
    # Default behavior: enter TUI when running in an interactive terminal.
    if ctx.invoked_subcommand is None:
        if is_tty():
            from .tui import run_tui

            run_tui()
            raise typer.Exit(code=0)

        typer.echo(ctx.get_help())
        raise typer.Exit(code=0)


@app.command()
def tui() -> None:
    """进入 TUI 模式（交互菜单）。"""
    if not is_tty():
        raise typer.BadParameter("TUI 需要在交互式终端（TTY）中运行。")
    from .tui import run_tui

    run_tui()


@app.command()
def search(
    query: str,
    limit: int = typer.Option(20, "--limit", min=1, max=200),
    min_score: Optional[float] = typer.Option(None, "--min-score"),
    lang: Optional[str] = typer.Option(None, "--lang"),
    timeout: float = typer.Option(20.0, "--timeout"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """
    搜索字幕（只列出结果，不下载）。
    """

    async def _run() -> list[ThunderSubtitleItem]:
        client = ThunderClient()
        items = await client.search(query=query, timeout_s=timeout)
        items = sorted(items, key=lambda x: x.score, reverse=True)
        items = _apply_filters(items, min_score=min_score, lang=lang)
        return items[:limit]

    items = asyncio.run(_run())
    if json_out:
        typer.echo(to_json(items))
        raise typer.Exit(code=0 if items else 2)
    print_search_table(items)
    raise typer.Exit(code=0 if items else 2)


@app.command()
def download(
    query: str,
    out_dir: Path = typer.Option(Path("."), "--out-dir", dir_okay=True, file_okay=False),
    index: Optional[int] = typer.Option(None, "--index", min=0),
    id_: Optional[str] = typer.Option(None, "--id"),
    best: bool = typer.Option(True, "--best/--no-best"),
    limit: int = typer.Option(20, "--limit", min=1, max=200),
    min_score: Optional[float] = typer.Option(None, "--min-score"),
    lang: Optional[str] = typer.Option(None, "--lang"),
    timeout: float = typer.Option(60.0, "--timeout"),
    retries: int = typer.Option(2, "--retries", min=0, max=10),
    overwrite: bool = typer.Option(False, "--overwrite/--no-overwrite"),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """
    下载单个字幕（默认下载评分最高的一个）。
    """

    async def _run() -> dict:
        client = ThunderClient()
        items = await client.search(query=query, timeout_s=20.0)
        items = sorted(items, key=lambda x: x.score, reverse=True)
        items = _apply_filters(items, min_score=min_score, lang=lang)[:limit]
        if not items:
            raise typer.Exit(code=2)

        chosen: ThunderSubtitleItem | None = None
        if id_:
            for it in items:
                if compute_item_id(gcid=it.gcid, cid=it.cid) == id_:
                    chosen = it
                    break
        elif index is not None:
            if 0 <= index < len(items):
                chosen = items[index]
        elif best:
            chosen = items[0]

        if chosen is None:
            raise typer.Exit(code=1)

        safe_name = sanitize_component(chosen.name, max_len=120)
        ext = sanitize_component(chosen.ext or "srt", max_len=10)
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{safe_name}.{ext}"
        if not overwrite:
            path = ensure_unique_path(path)

        data = await download_with_retries(client, url=chosen.url, timeout_s=timeout, retries=retries)
        path.write_bytes(data)
        return {
            "saved_path": str(path),
            "selected": {"id": compute_item_id(gcid=chosen.gcid, cid=chosen.cid), "name": chosen.name, "ext": chosen.ext, "score": chosen.score},
        }

    res = asyncio.run(_run())
    if json_out:
        typer.echo(json.dumps(res, ensure_ascii=False, indent=2))
        raise typer.Exit(code=0)
    Console().print(f"已保存：{res['saved_path']}")


@app.command()
def batch(
    queries: list[str] = typer.Argument(...),
    out_dir: Path = typer.Option(Path("."), "--out-dir", dir_okay=True, file_okay=False),
    interactive: bool = typer.Option(True, "--interactive/--no-interactive"),
    limit: int = typer.Option(20, "--limit", min=1, max=200),
    min_score: Optional[float] = typer.Option(None, "--min-score"),
    lang: Optional[str] = typer.Option(None, "--lang"),
    timeout: float = typer.Option(60.0, "--timeout"),
    retries: int = typer.Option(2, "--retries", min=0, max=10),
    concurrency: int = typer.Option(3, "--concurrency", min=1, max=20),
    select: Optional[str] = typer.Option(None, "--select", help="Non-interactive selection, e.g. 1,3,5 or 1-4,9"),
    select_id: list[str] = typer.Option([], "--select-id", help="Non-interactive selection by id (repeatable)"),
    yes: bool = typer.Option(False, "--yes", help="Skip confirmation prompt (still requires a selection)."),
) -> None:
    """
    批量交互式多选下载（每个 query 单独选择）。
    """

    if interactive:
        if not is_tty():
            raise typer.BadParameter("交互模式需要 TTY。请使用 --no-interactive 并配合 --select/--select-id。")
        selector: Selector = InteractiveSelector()
    else:
        indices = parse_select_spec(select or "")
        if not indices and not select_id:
            raise typer.BadParameter("非交互模式需要 --select 或 --select-id。")
        selector = DeterministicSelector(indices=indices, ids=select_id)

    client = ThunderClient()
    console = Console()
    total_ok = 0
    total_fail = 0
    all_errs: list[str] = []

    async def _search_one(q: str) -> list[ThunderSubtitleItem]:
        items_all = await client.search(query=q, timeout_s=20.0)
        items_all = sorted(items_all, key=lambda x: x.score, reverse=True)
        return _apply_filters(items_all, min_score=min_score, lang=lang)

    async def _download_selected(
        *,
        q: str,
        q_dir: Path,
        selected_items: list[ThunderSubtitleItem],
        progress: Progress,
        task_id: int,
    ) -> list[str]:
        sem = asyncio.Semaphore(concurrency)
        errs: list[str] = []

        async def _one(it: ThunderSubtitleItem) -> None:
            async with sem:
                safe_name = sanitize_component(it.name, max_len=120)
                ext = sanitize_component(it.ext or "srt", max_len=10)
                q_dir.mkdir(parents=True, exist_ok=True)
                path = ensure_unique_path(q_dir / f"{safe_name}.{ext}")
                try:
                    data = await download_with_retries(client, url=it.url, timeout_s=timeout, retries=retries)
                    path.write_bytes(data)
                except Exception as e:
                    errs.append(f"{q}: {it.name}: {e}")
                finally:
                    progress.advance(task_id, 1)

        await asyncio.gather(*[_one(i) for i in selected_items])
        return errs

    for q in queries:
        # Run network search outside the questionary prompt. (prompt-toolkit uses asyncio internally)
        items_filtered = asyncio.run(_search_one(q))
        found = len(items_filtered)
        items = items_filtered[:limit]

        console.print(f"搜索: {q} (匹配 {found}，显示 {len(items)})")

        # IMPORTANT: keep this synchronous (questionary/prompt-toolkit starts its own event loop).
        selected = selector.select(query=q, items=items)
        selected_items = [s.item for s in selected]
        if not selected_items:
            console.print("  （未选择任何字幕）")
            continue

        safe_q = sanitize_component(q, max_len=80)
        q_dir = out_dir / safe_q

        if not yes and interactive:
            ok = typer.confirm(f"下载 {len(selected_items)} 个字幕到 {q_dir}？", default=True)
            if not ok:
                console.print("  （已跳过）")
                continue

        with Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task_id = progress.add_task(f"Downloading {len(selected_items)} file(s)...", total=len(selected_items))
            errs = asyncio.run(
                _download_selected(
                    q=q,
                    q_dir=q_dir,
                    selected_items=selected_items,
                    progress=progress,
                    task_id=task_id,
                )
            )

        total_ok += len(selected_items) - len(errs)
        total_fail += len(errs)
        all_errs.extend(errs)

    console.print(f"完成。成功={total_ok} 失败={total_fail}")
    if all_errs:
        console.print("失败列表：")
        for e in all_errs[:50]:
            console.print(f"  - {e}")

    code = 0 if total_ok > 0 and total_fail == 0 else (1 if total_fail else 2)
    raise typer.Exit(code=code)
