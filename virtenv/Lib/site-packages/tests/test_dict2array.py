from collections import defaultdict, OrderedDict

import pytest

from dictutils.dict2array import dict2array

def test_not_dict():
    with pytest.raises(TypeError):
        dict2array(None)

    with pytest.raises(TypeError):
        dict2array([])

def test_empty_dict():
    assert dict2array({}) == []

def test_empty_other_dicts():
    assert dict2array(OrderedDict()) == []
    assert dict2array(defaultdict(int)) == []
    
def test_simple_dict():
    assert dict2array({"a": "b"}) == [{"key": "a", "val": "b"}]

def test_simple_dict_with_two_keys():
    assert dict2array({"a": "b", "c": "d"}) == [{"key": "a", "val": "b"}, {"key": "c", "val": "d"}]

def test_nested_dict():
    d = {
        "a": {
            "b": 5,
            "c": 8
        },
        "x": {
            "y": 10
        }
    }

    assert dict2array(d) == [
        {"key": "a", "val": [
            {"key": "b", "val": 5},
            {"key": "c", "val": 8},
        ]},
        {"key": "x", "val": [
            {"key": "y", "val": 10}
        ]},
    ]
