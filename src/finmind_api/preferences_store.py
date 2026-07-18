from threading import RLock
from typing import Literal, TypeAlias


LanguageSelection: TypeAlias = Literal["auto", "vi", "en"]


class LanguagePreferenceStore:
    """Server-side language selections keyed by authenticated username."""

    def __init__(self) -> None:
        self._selections: dict[str, LanguageSelection] = {}
        self._lock = RLock()

    def get(self, username: str) -> LanguageSelection:
        with self._lock:
            return self._selections.setdefault(username, "auto")

    def save(
        self,
        username: str,
        selection: LanguageSelection,
    ) -> LanguageSelection:
        with self._lock:
            self._selections[username] = selection
            return selection
