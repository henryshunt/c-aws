class MutableValue():    
    def __init__(self):
        self.__value = None

    def getValue(self):
        return self.__value

    def setValue(self, value):
        self.__value = value
