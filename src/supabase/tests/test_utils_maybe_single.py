from supabase._utils import maybe_single

def test_none_passthrough():
    assert maybe_single(None) is None

def test_scalar_passthrough():
    assert maybe_single(5) == 5
    assert maybe_single("x") == "x"

def test_singleton_list_unwraps():
    assert maybe_single([42]) == 42

def test_multi_item_list_stays_list():
    assert maybe_single([1, 2]) == [1, 2]

def test_tuple_behaviour():
    assert maybe_single((7,)) == 7
    assert maybe_single((7, 8)) == [7, 8]
