class SetBase:
    def __init__(self) -> None:
        self._list = []
        self._dict = {}
        
    def __getitem__(self, idx):
        if isinstance(idx, int):
            # If idx is an integer, treat it as an index in the list of persons
            return self._list[idx]
        if isinstance(idx, str):
            # If idx is a string, treat it as a person ID
            return self._dict[idx]

    def keys(self):
        return self._dict.keys()

    def __contains__(self, id_person):
        return id_person in self._dict

    def add_item(self, key, item):
        self._list.append(item)
        self._dict[key] = item

    def __len__(self):
        return len(self._list)