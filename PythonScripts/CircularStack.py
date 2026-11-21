class CircularStack:
    ## Stores items in a circular queue and overwrites oldest when full

    def __init__(self, size: int = 200):
        self.size = size
        self.entries = [None] * size   # fixed-size ring
        self.index = 0                 # next write position
        self.count = 0                 # number of valid items

    def push(self, item) -> None:
        ### ADD NEW ITEM
        ## Overwrites oldest when full

        self.entries[self.index] = item

        if self.count < self.size:
            self.count += 1

        self.index = (self.index + 1) % self.size

    def peek(self):
        ### RETURN NEWEST ITEM
        if self.count == 0:
            return None

        newest_index = (self.index - 1) % self.size
        return self.entries[newest_index]

    def pop_old(self):
        ### REMOVE AND RETURN OLDEST ITEM
        if self.count == 0:
            return None

        oldest_index = (self.index - self.count) % self.size
        item = self.entries[oldest_index]

        self.entries[oldest_index] = None
        self.count -= 1

        return item

    def pop_new(self):
        ### REMOVE AND RETURN NEWEST ITEM
        if self.count == 0:
            return None

        newest_index = (self.index - 1) % self.size
        item = self.entries[newest_index]

        self.entries[newest_index] = None
        self.index = newest_index
        self.count -= 1

        return item

    def is_empty(self) -> bool:
        ### CHECK IF EMPTY
        return self.count == 0

    def clear(self) -> None:
        ### CLEAR BUFFER
        self.entries = [None] * self.size
        self.index = 0
        self.count = 0

    def get_all(self) -> list:
        ### RETURN ALL ITEMS IN ORDER (oldest → newest)
        items = []
        for i in range(self.count):
            idx = (self.index - self.count + i) % self.size
            items.append(self.entries[idx])
        return items