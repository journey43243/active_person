from collections.abc import Mapping
from typing import Mapping, Iterable

def dict2array(d: Mapping) -> Iterable[Mapping]:
    def leaf(x):
        if isinstance(x, Mapping):
            return dict2array(x)
        else:
            return x

    if not isinstance(d, Mapping):
        raise TypeError

    if len(d) == 0:
        return []

    return [{"key": k, "val": leaf(v)} for k, v in d.items()] 
