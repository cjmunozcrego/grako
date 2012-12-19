from collections import OrderedDict, Mapping
import json

class AST(Mapping):
    def __init__(self, **kwargs):
        self._elements = OrderedDict(**kwargs)

    def add(self, key, value):
        previous = self._elements.get(key, None)
        if previous is None:
            self._elements[key] = value
        elif isinstance(previous, list):
#            if isinstance(value, list):
#                previous.extend(value)
#            else:
            previous.append(value)
        else:
#            if isinstance(value, list):
#                self._elements[key] = [previous] + value
#            else:
            self._elements[key] = [previous, value]

    def update(self, *args, **kwargs):
        for dct in args:
            for k, v in dct:
                self.add(k, v)
        for k, v in kwargs.items():
            self.add(k, v)

    @property
    def first(self):
        key = self.elements.keys[0]
        return self.elements[key]

    def __iter__(self):
        return iter(self._elements)

    def __contains__(self, key):
        return key in self._elements

    def __len__(self):
        return len(self._elements)

    def __getitem__(self, key):
        if key not in self._elements:
            self._elements[key] = list()
        return self._elements[key]

    def __getattr__(self, key):
        return self.__getitem__(key)
        if key in self._elements:
            return self.__getitem__(key)
        raise KeyError(key)

    @staticmethod
    def serializable(obj):
        if isinstance(obj, AST):
            return obj._elements
        return obj

    def __repr__(self):
        return json.dumps(self._elements, indent=4, default=self.serializable)

