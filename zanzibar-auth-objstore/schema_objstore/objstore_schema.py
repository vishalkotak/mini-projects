from core_model.model import Namespace, TypeDefinition, Rewrite


def default_namespace() -> Namespace:
    """S3-like mapping bucket roles inherit to object permissions via in_bucket."""

    bucket = TypeDefinition("bucket") \
        .relation("admin", Rewrite.this_relation()) \
        .relation("writer", Rewrite.this_relation()) \
        .relation("reader", Rewrite.this_relation()) \
        .relation("self", Rewrite.this_relation())
    
    obj = TypeDefinition("object") \
        .relation("in_bucket", Rewrite.this_relation()) \
        .relation("read", Rewrite.union(
            Rewrite.this_relation(),
            Rewrite.tuple_to_userset("in_bucket", "reader"),
            Rewrite.tuple_to_userset("in_bucket", "writer"),
            Rewrite.tuple_to_userset("in_bucket", "admin")
        )) \
        .relation("write", Rewrite.union(
            Rewrite.this_relation(),
            Rewrite.tuple_to_userset("in_bucket", "writer"),
            Rewrite.tuple_to_userset("in_bucket", "admin")
        )) \
        .relation("owner", Rewrite.this_relation())
    
    return Namespace().add(bucket).add(obj)
