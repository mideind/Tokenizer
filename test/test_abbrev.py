# type: ignore

from tokenizer.abbrev import OrderedSet


def test_ordered_set():
    # Test empty set
    s_empty = OrderedSet()
    assert list(s_empty) == []
    assert 1 not in s_empty
    assert repr(s_empty) == "OrderedSet([])"

    # Test add and iteration order
    s_order = OrderedSet()
    s_order.add(1)
    s_order.add("a")
    s_order.add(3.0)
    assert list(s_order) == [1, "a", 3.0]

    # Test add existing item preserves order and uniqueness
    s_existing = OrderedSet()
    s_existing.add(10)
    s_existing.add(20)
    s_existing.add(10)  # Add existing
    assert list(s_existing) == [10, 20]

    # Test contains
    s_contains = OrderedSet()
    s_contains.add("x")
    s_contains.add("y")
    assert "x" in s_contains
    assert "y" in s_contains
    assert "z" not in s_contains
    assert "a" not in s_contains

    # Test repr non-empty
    s_repr = OrderedSet()
    s_repr.add(1)
    s_repr.add("foo")
    assert repr(s_repr) == "OrderedSet([1, 'foo'])"
