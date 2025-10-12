from __future__ import annotations
from typing import Iterable, Dict, Set
from dataclasses import dataclass
from threading import RLock

from core_model.model import ObjectRef, Tuple

class TupleStore:
    """Abstract storage for tuples: optimized read-by (object#relation)."""
    def write(self, t: Tuple) -> None: raise NotImplementedError
    def delete(self, t: Tuple) -> None: raise NotImplementedError
    def read(self, o: ObjectRef, relation: str) -> Iterable[Tuple]: raise NotImplementedError


class InMemoryTupleStore(TupleStore):
    """Thread-safe in-memory index: key='type|id|rel' -> set[Tuple]."""

    def __init__(self) -> None:
        self._index: Dict[str, Set[Tuple]] = {}
        self._lock = RLock()

    @staticmethod
    def _key(o: ObjectRef, rel: str) -> str:
        key_str =  f"{o.object_type}|{o.object_id}|{rel}"
        print(key_str)
        return key_str
    
    def write(self, t: Tuple) -> None:
        with self._lock:
            k = self._key(t.object, t.relation)
            self._index.setdefault(k, set()).add(t)
            print(self._index[k])

    def delete(self, t: Tuple) -> None:
        with self._lock:
            k = self._key(t.object, t.relation)
            s = self._index.get(k)
            if s:
                s.discard(t)

    def read(self, o: ObjectRef, relation: str):
        with self._lock:
            return tuple(self._index.get(self._key(o, relation), ()))
        
    