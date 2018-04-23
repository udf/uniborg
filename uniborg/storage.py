import os
import json


class Storage:
    class _Guard:
        def __init__(self, storage):
            self._storage = storage

        def __enter__(self):
            self._storage._autosave = False

        def __exit__(self, *args):
            self._storage._autosave = True
            self._storage._save()

    def __init__(self, root):
        self._root = root
        self._autosave = True
        self._guard = self._Guard(self)
        self._data = {}

    def bulk_save(self):
        return self._guard

    def __getattr__(self, name):
        if name.startswith('_'):
            raise ValueError('You can only access existing private members')
        return self._data.get(name, None)

    def __setattr__(self, name, value):
        if name.startswith('_'):
            self.__dict__[name] = value
        else:
            self._data[name] = value
            if self._autosave:
                self._save()

    def _save(self):
        if not os.path.isdir(self._root):
            os.makedirs(self._root, exist_ok=True)
        with open(os.path.join(self._root, 'data.json'), 'w') as fp:
            json.dump(self._data, fp)
