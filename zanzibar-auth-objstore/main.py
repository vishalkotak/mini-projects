from core_model.model import ObjectRef, User, UsersetRef, Tuple
from core_storage.tuple_store import InMemoryTupleStore
from core_eval.check_engine import CheckEngine
from schema_objstore.objstore_schema import default_namespace


def scenario_1():
    """
    ONE simple scenario:
      bucket:photos
        - admin  : carol
        - writer : bob
        - reader : alice
      object:photos/cat.jpg
        - in_bucket : bucket:photos#self
        - owner     : diana
        - write     : diana
        - read      : dave   (direct)
    Prints a few checks to show: inherited read/write, direct grants, and a miss.
    """
    ns = default_namespace()
    store = InMemoryTupleStore()
    engine = CheckEngine(ns, store)

    # bucket:photos#admin@user:carol
    store.write(Tuple(ObjectRef("bucket", "photos"), "admin", User("carol")))
    
    # bucket:photos#writer@user:bob
    store.write(Tuple(ObjectRef("bucket", "photos"), "writer", User("bob")))
    
    # bucket:photos#reader@user:alice
    store.write(Tuple(ObjectRef("bucket", "photos"), "reader", User("alice")))

    # object:photos/cat.jpg#in_bucket@bucket:photos#self
    store.write(Tuple(
        ObjectRef("object", "photos/cat.jpg"),
        "in_bucket",
        UsersetRef(ObjectRef("bucket", "photos"), "self")
    ))

    # object:photos/cat.jpg#owner@user:diana
    store.write(Tuple(ObjectRef("object", "photos/cat.jpg"), "owner", User("diana")))
    
    # object:photos/cat.jpg#write@user:diana
    store.write(Tuple(ObjectRef("object", "photos/cat.jpg"), "write", User("diana")))
    
    # object:photos/cat.jpg#read@user:dave
    store.write(Tuple(ObjectRef("object", "photos/cat.jpg"), "read",  User("dave")))

    obj = ObjectRef("object", "photos/cat.jpg")
    
    def check(rel: str, uid: str, depth: int = 32):
        allowed = engine.check(obj, rel, User(uid), depth)
        print(f"{uid:5s} -> {obj.object_type}:{obj.object_id}#{rel:<5} : {allowed}")
        return allowed
    
    print("\n=== Scenario 1: default namespace, basic inheritance + direct grants ===")
    # inherited from bucket via in_bucket
    check("read",  "alice")   # True (bucket.reader)
    check("write", "bob")     # True (bucket.writer)
    check("write", "carol")   # True (bucket.admin)
    # direct THIS on object
    check("read",  "dave")    # True (direct)
    check("write", "diana")   # True (direct)
    # negative
    check("read",  "eve")     # False
    print("=== End Scenario 1 ===\n")


def main():
    scenario_1()


if __name__ == "__main__":
    main()
