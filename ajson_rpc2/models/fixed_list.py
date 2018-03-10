''' define a list with item type limited '''
from collections import UserList


class FixedList(UserList):
    ''' A list with item type limited
    Usage example::

        list = FixedList(int)
        list.append(2)     # number 2 will append to list
        list.append("abc") # which will raise an TypeError, because "abc" is not a type of int
    '''
    def __init__(self, item_type: type):
        super(FixedList, self).__init__(self)
        self.item_type = item_type

    def append(self, item):
        ''' when append an item to list,
        the FixedList will check if the item have
        proper type, if not, the TypeError will be
        raised '''
        if isinstance(item, self.item_type) is False:
            raise TypeError(f'type of item should be {self.item_type}')
        super(FixedList, self).append(item)

    def insert(self, index, item):
        ''' when insert an item to list,
        the FixedList will check if the item have proper
        type, if not, an TypeError will be raised '''
        if isinstance(item, self.item_type) is False:
            raise TypeError(f'type of item should be {self.item_type}')
        super(FixedList, self).insert(index, item)

    def extend(self, iterable):
        '''
        extend list by appending elements from the iterable
        but the fixed list will check if each element have proper
        type '''
        tmp_list = list(iterable)
        for item in tmp_list:
            if isinstance(item, self.item_type) is False:
                raise TypeError(f'type of item should be {self.item_type}')

        super(FixedList, self).extend(iterable)
