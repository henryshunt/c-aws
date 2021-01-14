class SampleStore():
    def __init__(self):
        self._store0 = []
        self._store1 = []
        self._active_store = 0

    @property
    def active_store(self):
        if self._active_store == 0:
            return self._store0
        else: return self._store1
    
    @property
    def inactive_store(self):
        if self._active_store == 0:
            return self._store1
        else: return self._store0

    def switch_store(self):
        if self._active_store == 0:
            self._store1 = []
            self._active_store = 1
        else:
            self._store0 = []
            self._active_store = 0