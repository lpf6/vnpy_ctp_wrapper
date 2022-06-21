class Hello:

    def __getattribute__(self, attr):
        val = super().__getattribute__(attr)
        if callable(val):
            def fun(**kwargs):
                print("func: %s, args: %s" % (val.__name__, kwargs))
                val(**kwargs)
            return fun
        return val

    def __getattr__(self, item):
        return self.__dict__[item]

    def get_x(self):
        return 10

h = Hello()
h.get_x()
h.get_y()