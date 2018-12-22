import json
import collections


class _MyDictJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, MyDict):
            return o.data
        return super().default(o)


class MyDict(collections.UserDict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def to_json(self):
        return _MyDictJSONEncoder(indent=4).encode(self)
