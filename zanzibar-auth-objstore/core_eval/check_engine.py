from __future__ import annotations
from typing import Set

from core_model.model import (
    Namespace, ObjectRef, User, UsersetRef, Tuple, Rewrite, OpType
)
from core_storage.tuple_store import TupleStore

class CheckEngine:
    """Zanzibar-style membership evaluator with cycle detection and a depth budget."""

    def __init__(self, ns: Namespace, store: TupleStore) -> None:
        self._ns = ns
        self._store = store

    def check(self, obj: ObjectRef, relation: str, user: User, max_depth: int = 32) -> bool:
        """
        Public entry for the evalutator.

        Args:
            obj: The object to check (eg: ObjectRef("document", "doc1"))
            relation: The relation to check (eg: "viewer")
            user: The user we're checking access for (eg: User("alice"))
            max_depth: recurision limit to prevent infinite loops

        Returns:
            True if the user has the relation, False otherwise.
        """
        budget = 32 if max_depth <= 0 else max_depth
        return self._eval(obj, relation, user, 0, budget, set())
    
    def _eval(self, obj: ObjectRef, relation: str, user: User, 
              depth: int, max_depth: int, visited: Set[str]) -> bool:
        """
        Recursive core that actually traverses the Rewrite tree.

        Args:
            obj: Object we are checking
            relation: The relation we are evaluating
            user: The user we are evaluating for
            depth: Current recursion depth
            max_depth: Limit to avoid runway recursion
            visited: Tracks which nodes we've visited
        """

        if depth > max_depth:
            return False
        
        # Fetch the TypeDefinition for this object's type from the namespace.
        type_def = self._ns.get(obj.object_type)
        if not type_def:
            return False

        # Get the rewrite (definition) for this relation.
        rewrite = type_def.rewrite_of(relation=relation)
        if not rewrite:
            return False
        
        # Build a key for cycle detection.
        frame = f"{obj.object_type}:{obj.object_id}#{relation}->{user.user_id}"
        if frame in visited:
            return False
        
        visited.add(frame)
        try:
            if rewrite.op == OpType.THIS:
                # Direct membership: just check tuples on object#relation
                return self._eval_this(obj, relation, user, depth, max_depth, visited)
            
            elif rewrite.op == OpType.UNION:
                # UNION = logical OR; check each child rewrite, succeed on first True
                return any(self._eval_rewrite(obj, relation, user, depth, max_depth, visited, c) for c in rewrite.children)
            
            elif rewrite.op == OpType.TUPLE_TO_USERSET:
                # TUPLE_TO_USERSET = follow indirect through tuples.
                # Example: tupleToUserset("owner", "member") means:
                # read tuples on object#owner
                # for each userset reference (like group:X#member),
                # check membership in that userset relation.
                return self._eval_tuple_to_userset(obj, rewrite.tuples_on, rewrite.computed_userset_rel, 
                                                   user, depth, max_depth, visited)
            
            else:
                return False
        finally:
            visited.remove(frame)


    def _eval_rewrite(self, obj: ObjectRef, relation: str, user: User, 
                      depth: int, max_depth: int, visited: Set[str], r: Rewrite) -> bool:
        
        """
        Helper to evaluate a child rewrite mode (used by UNION.)
        """
        if r.op == OpType.THIS:
            return self._eval_this(obj, relation, user, depth, max_depth, visited)
        if r.op == OpType.UNION:
            return any(self._eval_rewrite(obj, relation, user, depth, max_depth, visited, c) for c in r.children)
        if r.op == OpType.TUPLE_TO_USERSET:
            return self._eval_tuple_to_userset(obj, r.tuples_on, r.computed_userset_rel, user, depth, max_depth, visited)
        return False
        

    
    def _eval_this(self, obj: ObjectRef, relation: str, user: User, 
                   depth: int, max_depth: int, visited: Set[str]) -> bool:
        
        """
        Evaluate the simplest case: direct tuples on object#relation

        Example:
            document:doc1#viewer@user:alice -> alice belongs to viewer(doc1)
        """
        for t in self._store.read(obj, relation):
            # Case 1: tuple points to a user.
            if isinstance(t.principal, User) and t.principal == user:
                return True
            
            # Case 2: tuple points to a userset reference
            if isinstance(t.principal, UsersetRef):
                # Follow that userset: check membership recursively
                # eg: document:doc1#viewer@group:eng#member
                #          -> check if user belongs to group:eng#member
                if self._eval(t.principal.object, t.principal.relation, user,
                              depth + 1, max_depth, visited):
                    return True
        return False
                

    def _eval_tuple_to_userset(self, obj: ObjectRef, tuples_on: str | None, computed_rel: str | None,
                                user: User, depth: int, max_depth: int, visited: Set[str]) -> bool:
        
        """
        Evaluate TUPLE_TO_USERSET

        Example:
            tupleToUserset("owner", "member") means:
                - read all tuples on object#owner
                - for reach userset ref (eg: group:eng#member)
                - check membership in group:eng#member
        """
        if not tuples_on or not computed_rel:
            return False
        for t in self._store.read(obj, tuples_on):
            if isinstance(t.principal, UsersetRef):
                if self._eval(t.principal.object, computed_rel, user, depth + 1, max_depth, visited):
                    return True
        return False