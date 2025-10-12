from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Union

# ---------- Data primitives ----------------

@dataclass(frozen=True)
class ObjectRef:
    """Identifies a concrete entity (eg: bucket:photos, object:photos/cat.jpg)"""
    object_type: str
    object_id: str


class Principal:
    """Right-hand side of a tuple: either a concrete user or a userset reference."""


@dataclass(frozen=True)
class User(Principal):
    """Conrete user principal (eg: 'alice')"""
    user_id : str


@dataclass(frozen=True)
class UsersetRef(Principal):   
    """Reference to another object's relation (eg: bucket:photos#reader)"""
    object: ObjectRef
    relation: str


@dataclass(frozen=True)
class Tuple:
    """A relationship edge: object#relation@principal."""
    object: ObjectRef
    relation: str
    principal: Principal


# ----------- Schema (rewrite AST) --------------

class OpType:
    THIS = "THIS"
    UNION = "UNION"
    TUPLE_TO_USERSET = "TUPLE_TO_USERSET"


@dataclass(frozen=True)
class Rewrite:
    """Describes how a relation is computed."""
    op: str
    children: List["Rewrite"] = field(default_factory=list)
    tuples_on: str | None = None
    computed_userset_rel : str | None = None

    @staticmethod
    def this_relation() -> "Rewrite":
        return Rewrite(op=OpType.THIS)
    
    @staticmethod
    def union(*kids: "Rewrite") -> "Rewrite":
        return Rewrite(op=OpType.UNION, children=list(kids))
    
    @staticmethod
    def tuple_to_userset(tuples_on: str, computed_userset_rel: str) -> "Rewrite":
        return Rewrite(op=OpType.TUPLE_TO_USERSET, 
                       tuples_on=tuples_on, computed_userset_rel=computed_userset_rel)
    


@dataclass
class TypeDefinition:
    """All relations and rewrites for a single object type."""
    type: str
    relations: Dict[str, Rewrite] = field(default_factory=dict)

    def relation(self, name: str, rewrite: Rewrite) -> "TypeDefinition":
        self.relations[name] = rewrite
        return self
    
    def rewrite_of(self, relation: str) -> Rewrite | None:
        return self.relations.get(relation)
    

@dataclass
class Namespace:
    """Map of type name -> TypeDefintion."""
    types: Dict[str, TypeDefinition] = field(default_factory=dict)

    def add(self, td: TypeDefinition) -> "Namespace":
        self.types[td.type] = td
        return self
    
    def get(self, type_name: str) -> TypeDefinition | None:
        return self.types.get(type_name)
    



