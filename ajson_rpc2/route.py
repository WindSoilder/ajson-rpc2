class RouteTable:
    def __init__(self):
        self._inner_dict = {}

    def __contains__(self, item: str):
        return item in self._inner_dict

    def __setitem__(self, key, value):
        self._inner_dict[key] = value

    def __getitem__(self, key):
        return self._inner_dict[key]
