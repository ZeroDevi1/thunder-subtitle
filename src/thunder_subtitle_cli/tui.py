from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import questionary
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from .core import format_item_label, resolve_out_dir, search_items
from .formatting import print_search_table
from .models import ThunderSubtitleItem
from .selector import InteractiveSelector
from .util import ensure_unique_path, sanitize_component
from .client import ThunderClient, download_with_retries


console = Console()


def _ask_text(prompt: str, *, default: str | None = None) -> str | None:
    q = questionary.text(prompt, default=default) if default is not None else questionary.text(prompt)
    ans = q.ask()
    if ans is None:
        return None
    return str(ans)


def _ask_float(prompt: str, *, default: float | None = None) -> float | None:
    default_s = "" if default is None else str(default)
    s = _ask_text(prompt, default=default_s)
    if s is None:
        return None
    s = s.strip()
    if not s:
        return default
    return float(s)


def _ask_int(prompt: str, *, default: int) -> int | None:
    s = _ask_text(prompt, default=str(default))
    if s is None:
        return None
    s = s.strip()
    if not s:
        return default
    return int(s)


def run_tui() -> None:
    while True:
        choice = questionary.select(
            "迅雷字幕 - 功能菜单",
            choices=[
                "搜索字幕",
                "下载字幕",
                "批量下载",
                "退出",
            ],
        ).ask()
        if choice is None or choice == "退出":
            return
        if choice == "搜索字幕":
            tui_search_flow()
        elif choice == "下载字幕":
            tui_download_flow()
        elif choice == "批量下载":
            tui_batch_flow()


def tui_search_flow() -> None:
    query = _ask_text("搜索关键词（空则返回）：")
    if not query or not query.strip():
        return

    limit = _ask_int("最多显示条数 [20]：", default=20)
    if limit is None:
        return

    min_score = _ask_text("最低评分（留空不限制）：", default="")
    if min_score is None:
        return
    min_score_v = float(min_score) if min_score.strip() else None

    lang = _ask_text("语言过滤（留空不限制）：", default="")
    if lang is None:
        return
    lang_v = lang.strip() or None

    items = asyncio.run(search_items(query=query.strip(), limit=limit, min_score=min_score_v, lang=lang_v))
    print_search_table(items)

    if not items:
        questionary.confirm("没有结果，返回菜单？", default=True).ask()
        return

    next_action = questionary.select(
        "下一步：",
        choices=["返回", "从结果里下载一个", "重新搜索"],
    ).ask()
    if next_action == "从结果里下载一个":
        tui_download_from_items(items, default_query=query.strip())
    elif next_action == "重新搜索":
        tui_search_flow()


def _select_one(items: list[ThunderSubtitleItem]) -> ThunderSubtitleItem | None:
    id_map: dict[str, ThunderSubtitleItem] = {}
    choices: list[questionary.Choice] = [questionary.Choice(title="(返回)", value="__back__")]
    for it in items:
        _id = f"{it.gcid}:{it.cid}"
        id_map[_id] = it
        choices.append(questionary.Choice(title=format_item_label(it), value=_id))
    picked = questionary.select("请选择一个字幕：", choices=choices).ask()
    if not picked or picked == "__back__":
        return None
    return id_map.get(str(picked))


def tui_download_from_items(items: list[ThunderSubtitleItem], *, default_query: str | None = None) -> None:
    chosen = _select_one(items)
    if chosen is None:
        return

    out_dir_s = _ask_text("保存目录 [./subs]：", default="./subs")
    if out_dir_s is None:
        return
    out_dir = resolve_out_dir(out_dir_s, default="./subs")

    async def _run() -> Path:
        client = ThunderClient()
        safe_name = sanitize_component(chosen.name, max_len=120)
        ext = sanitize_component(chosen.ext or "srt", max_len=10)
        out_dir.mkdir(parents=True, exist_ok=True)
        path = ensure_unique_path(out_dir / f"{safe_name}.{ext}")
        data = await download_with_retries(client, url=chosen.url, timeout_s=60.0, retries=2)
        path.write_bytes(data)
        return path

    path = asyncio.run(_run())
    console.print(f"已保存：{path}")
    questionary.confirm("返回菜单？", default=True).ask()


def tui_download_flow() -> None:
    query = _ask_text("搜索关键词（空则返回）：")
    if not query or not query.strip():
        return

    limit = _ask_int("最多显示条数 [20]：", default=20)
    if limit is None:
        return

    items = asyncio.run(search_items(query=query.strip(), limit=limit))
    print_search_table(items)
    if not items:
        questionary.confirm("没有结果，返回菜单？", default=True).ask()
        return
    tui_download_from_items(items, default_query=query.strip())


def tui_batch_flow() -> None:
    console.print("请输入多个搜索关键词（每行一个），直接回车空行结束。")
    queries: list[str] = []
    while True:
        q = _ask_text("关键词：", default="")
        if q is None:
            return
        q = q.strip()
        if not q:
            break
        queries.append(q)

    if not queries:
        return

    out_dir_s = _ask_text("保存目录 [./subs]：", default="./subs")
    if out_dir_s is None:
        return
    out_dir = resolve_out_dir(out_dir_s, default="./subs")

    limit = _ask_int("每个关键词最多显示条数 [20]：", default=20)
    if limit is None:
        return

    min_score_txt = _ask_text("最低评分（留空不限制）：", default="")
    if min_score_txt is None:
        return
    min_score = float(min_score_txt) if min_score_txt.strip() else None

    lang_txt = _ask_text("语言过滤（留空不限制）：", default="")
    if lang_txt is None:
        return
    lang = lang_txt.strip() or None

    timeout = _ask_float("下载超时（秒）[60]：", default=60.0)
    if timeout is None:
        return

    retries = _ask_int("重试次数 [2]：", default=2)
    if retries is None:
        return

    concurrency = _ask_int("并发数 [3]：", default=3)
    if concurrency is None:
        return

    selector = InteractiveSelector()
    client = ThunderClient()

    total_ok = 0
    total_fail = 0
    all_errs: list[str] = []

    async def _search(q: str) -> list[ThunderSubtitleItem]:
        items = await client.search(query=q, timeout_s=20.0)
        items = sorted(items, key=lambda x: x.score, reverse=True)
        from .core import apply_filters

        return apply_filters(items, min_score=min_score, lang=lang)[:limit]

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
                    data = await download_with_retries(client, url=it.url, timeout_s=float(timeout), retries=int(retries))
                    path.write_bytes(data)
                except Exception as e:
                    errs.append(f"{q}: {it.name}: {e}")
                finally:
                    progress.advance(task_id, 1)

        await asyncio.gather(*[_one(i) for i in selected_items])
        return errs

    for q in queries:
        items = asyncio.run(_search(q))
        console.print(f"搜索: {q} (匹配 {len(items)}，显示 {len(items)})")
        print_search_table(items)
        selected = selector.select(query=q, items=items)
        selected_items = [s.item for s in selected]
        if not selected_items:
            console.print("  （未选择任何字幕）")
            continue

        q_dir = out_dir / sanitize_component(q, max_len=80)

        ok = questionary.confirm(f"下载 {len(selected_items)} 个字幕到 {q_dir}？", default=True).ask()
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
            errs = asyncio.run(_download_selected(q=q, q_dir=q_dir, selected_items=selected_items, progress=progress, task_id=task_id))

        total_ok += len(selected_items) - len(errs)
        total_fail += len(errs)
        all_errs.extend(errs)

    console.print(f"完成。成功={total_ok} 失败={total_fail}")
    if all_errs:
        console.print("失败列表：")
        for e in all_errs[:50]:
            console.print(f"  - {e}")
    questionary.confirm("返回菜单？", default=True).ask()
