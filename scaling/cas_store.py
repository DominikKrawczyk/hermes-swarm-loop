"""In-memory CAS (compare-and-swap) store.

Thread-safe, dict-backed store supporting value-based CAS operations.
"""

import threading
from collections.abc import Hashable
from typing import Any


class CASEntry:
    """Backward-compatible CAS entry reference.

    The current CASStore is in-memory and uses raw dicts internally;
    this class exists only so ``scaling.__init__`` can import it.
    """
    def __init__(self, key=None, value=None, version=1):
        self.key = key
        self.value = value
        self.version = version


class ConflictError(Exception):
    """Backward-compatible CAS conflict error.

    Raised only by consumers that explicitly catch it; never raised
    by the current in-memory CASStore.
    """
    pass


class CASStore:
    """In-memory compare-and-swap store.

    Each key maps to a value and a monotonically increasing version number.
    CAS operations compare against the stored *value* (value-based CAS),
    not the version number.

    Thread-safe via RLock.
    """

    def __init__(self) -> None:
        self._data: dict[Hashable, dict] = {}
        self._lock = threading.RLock()

    def set(self, key: Hashable, value: Any) -> None:
        """Store a value under *key*, bumping the version on overwrite."""
        with self._lock:
            if key in self._data:
                self._data[key]["value"] = value
                self._data[key]["version"] += 1
            else:
                self._data[key] = {"value": value, "version": 1}

    def get(self, key: Hashable) -> dict | None:
        """Return dict with 'value' and 'version' keys, or None if missing."""
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            return {"value": entry["value"], "version": entry["version"]}

    @property
    def store(self) -> dict[Hashable, CASEntry]:
        """Return a snapshot of all entries as CASEntry objects."""
        with self._lock:
            return {
                k: CASEntry(key=k, value=v["value"], version=v["version"])
                for k, v in self._data.items()
            }

    def get_entry(self, key: Hashable) -> CASEntry | None:
        """Return a CASEntry for *key*, or None if missing."""
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            return CASEntry(key=key, value=entry["value"], version=entry["version"])

    def cas(
        self,
        key: Hashable,
        expected_value: Any,
        new_value: Any,
    ) -> bool:
        """Compare-and-swap. Returns True if *expected_value* matched the
        stored value and the swap succeeded."""
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return False
            if entry["value"] != expected_value:
                return False
            entry["value"] = new_value
            entry["version"] += 1
            return True

    def delete(self, key: Hashable) -> bool:
        """Delete *key*. Returns True if it existed, False otherwise."""
        with self._lock:
            if key not in self._data:
                return False
            del self._data[key]
            return True

    def exists(self, key: Hashable) -> bool:
        """Return True if *key* is stored."""
        with self._lock:
            return key in self._data

    def keys(self) -> list[Hashable]:
        """Return a snapshot of all stored keys."""
        with self._lock:
            return list(self._data.keys())

    def size(self) -> int:
        """Return the number of stored entries."""
        with self._lock:
            return len(self._data)

    def clear(self) -> None:
        """Remove all entries."""
        with self._lock:
            self._data.clear()

    def __contains__(self, key: object) -> bool:
        if isinstance(key, Hashable):
            return self.exists(key)
        return False

    def __len__(self) -> int:
        return self.size()

    def __repr__(self) -> str:
        return f"CASStore(entries={self.size()})"
