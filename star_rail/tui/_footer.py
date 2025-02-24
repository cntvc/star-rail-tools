from __future__ import annotations

import typing

from textual.containers import HorizontalGroup

if typing.TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.widget import Widget


__all__ = ["Footer"]


class Footer(HorizontalGroup):
    def compose(self) -> ComposeResult:
        footer_key: list[Widget] = self.screen.FOOTER_KEY
        for key in footer_key:
            yield key()
