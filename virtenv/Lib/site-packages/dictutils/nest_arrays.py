import json
from typing import List, Iterable

def nest_arrays(lst: Iterable) -> List:
    is_list = lambda x: isinstance(x, Iterable)

    if not all(is_list(x) for x in lst):
        raise TypeError("Expected nested arrays")

    lst = [el for el in lst if is_list(el) and len(el) > 0]
    
    if len(lst) == 0:
        return []

    output = []
    for el in lst:
        if len(el) == 1:
            output.append(el[0])
        elif len(el) == 2:
            output.append({"key": el[0], "val": el[1]})
        else:
            output.append({"key": el[0], "val": nest_arrays([el[1:]])})

    return output





