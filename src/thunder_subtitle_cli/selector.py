from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

import questionary

from .models import ThunderSubtitleItem
from .util import compute_item_id


@dataclass(frozen=True, slots=True)
class SelectedItem:
    id: str
    item: ThunderSubtitleItem


class Selector(Protocol):
    def select(self, *, query: str, items: Sequence[ThunderSubtitleItem]) -> list[SelectedItem]: ...


class InteractiveSelector:
    def select(self, *, query: str, items: Sequence[ThunderSubtitleItem]) -> list[SelectedItem]:
        if not items:
            return []

        # Precompute stable IDs and labels; keep mapping to avoid any ambiguity.
        id_to_item: dict[str, ThunderSubtitleItem] = {}
        ordered_ids: list[str] = []
        labels: dict[str, str] = {}
        for it in items:
            _id = compute_item_id(gcid=it.gcid, cid=it.cid)
            id_to_item[_id] = it
            ordered_ids.append(_id)
            labels[_id] = f"[{it.score:0.2f}] {it.name} ({it.ext}) {it.extra_name} lang={','.join(it.languages)}"

        ACTION_SKIP = "__skip__"
        ACTION_ALL = "__all__"
        ACTION_NONE = "__none__"
        ACTION_INVERT = "__invert__"

        checked: set[str] = set()
        while True:
            choices: list[questionary.Choice] = [
                questionary.Choice(title="(跳过本次)", value=ACTION_SKIP, checked=False),
                questionary.Choice(title="(全选)", value=ACTION_ALL, checked=False),
                questionary.Choice(title="(全不选)", value=ACTION_NONE, checked=False),
                questionary.Choice(title="(反选)", value=ACTION_INVERT, checked=False),
            ]
            for _id in ordered_ids:
                choices.append(
                    questionary.Choice(
                        title=labels[_id],
                        value=_id,
                        checked=_id in checked,
                    )
                )

            answer = questionary.checkbox(
                f"搜索: {query} (空格勾选，回车确认)",
                choices=choices,
            ).ask()

            if not answer or ACTION_SKIP in answer:
                return []

            # If user picked one of the actions, update defaults and reprompt.
            if ACTION_ALL in answer:
                checked = set(ordered_ids)
                continue
            if ACTION_NONE in answer:
                checked = set()
                continue
            if ACTION_INVERT in answer:
                checked = set(ordered_ids) - checked
                continue

            # Otherwise this is the final selection.
            out: list[SelectedItem] = []
            for _id in answer:
                it = id_to_item.get(_id)
                if it is None:
                    continue
                out.append(SelectedItem(id=_id, item=it))
            return out


class DeterministicSelector:
    def __init__(self, *, indices: list[int] | None = None, ids: list[str] | None = None) -> None:
        self._indices = indices or []
        self._ids = ids or []

    def select(self, *, query: str, items: Sequence[ThunderSubtitleItem]) -> list[SelectedItem]:
        out: list[SelectedItem] = []
        if self._ids:
            id_map = {compute_item_id(gcid=i.gcid, cid=i.cid): i for i in items}
            for _id in self._ids:
                it = id_map.get(_id)
                if it is not None:
                    out.append(SelectedItem(id=_id, item=it))
            return out
        for idx in self._indices:
            if 0 <= idx < len(items):
                it = items[idx]
                _id = compute_item_id(gcid=it.gcid, cid=it.cid)
                out.append(SelectedItem(id=_id, item=it))
        return out
