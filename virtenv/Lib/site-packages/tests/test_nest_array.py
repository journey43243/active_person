import pytest

from dictutils.nest_arrays import nest_arrays

def test_empty():
   arr = [] 
   assert nest_arrays(arr) == []

def test_requires_nested_array():
    arr = [1,2,3]

    with pytest.raises(TypeError):
        nest_arrays(arr)

def test_nested_empty_arrays():
    assert nest_arrays([[]]) == []


def test_single_element_array():
    arr = [[1], [2], [3]]
    assert(nest_arrays(arr)) == [1, 2, 3]

def test_two_value_array():
    arr = [["a", 1], ["b", 2], ["c", 3]]
    assert(nest_arrays(arr)) == [
        {"key": "a", "val": 1},
        {"key": "b", "val": 2},
        {"key": "c", "val": 3},
    ]

def test_three_value_array():
    arr = [["x", "y", "z"], ["a", "b", "c"], [1, 2, 3]]
    assert(nest_arrays(arr)) == [
        {"key": "x", "val": [{"key": "y", "val": "z"}]},
        {"key": "a", "val": [{"key": "b", "val": "c"}]},
        {"key": 1,   "val": [{"key":  2,  "val": 3  }]},
    ]
    
def test_three_value_array():
    arr = [["x", "y", "z", "w"], ["a", "b", "c", "d"], [1, 2, 3, 4]]
    assert(nest_arrays(arr)) == [
        {"key": "x", "val": [{"key": "y", "val": [{"key": "z", "val": "w"}]}]},
        {"key": "a", "val": [{"key": "b", "val": [{"key": "c", "val": "d"}]}]},
        {"key": 1,   "val": [{"key":  2,  "val": [{"key": 3, "val":    4 }]}]},
    ]

    def test_stuff():
        arr = {
            "race": {
                "Other": {
                    "Afrikaans": {
                        "count": 11060,
                        "children": {
                            "KZN": 261,
                            "LIM": 123,
                            "MP": 248,
                            "NW": 266,
                            "NC": 1329,
                            "EC": 1033,
                            "FS": 317,
                            "GT": 2404,
                            "WC": 5080
                        }
                    },
                    "English": {
                        "count": 27637,
                        "children": {
                            "KZN": 3709,
                            "LIM": 605,
                            "MP": 763,
                            "NW": 1002,
                        } 
                    }
                }
            }
        }
