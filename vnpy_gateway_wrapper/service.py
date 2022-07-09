import abc
import pickle
import time

import rpyc

from vnpy_gateway_wrapper.utils import log


class ConstraintsService(rpyc.Service):
    def __init__(self, obj=None):
        self._obj = obj
        self._conn = None
        self._dict_ = None
        self._format_dict = None
        self._remove_obj = True
        if obj is not None:
            self._remove_obj = False
            self.init()

    def create_obj(self):
        pass

    def remove_obj(self):
        pass

    def init(self):
        if self._obj is None:
            self._dict_ = {}
            self._format_dict = {}
            return
        all_dir = dir(self._obj)
        attr_dict = {}
        format_dict = {}
        for d in all_dir:
            if "__" in d:
                continue
            v = getattr(self._obj, d)
            attr_dict[d] = v
            format_dict[d] = "callable" if callable(v) else "variable"
        self._dict_ = attr_dict
        self._format_dict = format_dict

    def on_connect(self, conn):
        self._conn = conn
        if self._obj is None:
            self._obj = self.create_obj()
            self.init()
            if self._obj is None:
                log.error("Service[%s] on_connect a None obj! " % self.__class__.__name__)

    def on_disconnect(self, conn):
        if self._remove_obj:
            self.remove_obj()
            self._obj = None
            self._dict_ = None
            self._format_dict = None
        self._conn = None

    def exposed_get_dict(self):
        while self._format_dict is None:
            time.sleep(0.05)
        return self._format_dict

    def exposed_call(self, method, args, kwargs):
        if method in self._dict_ and callable(self._dict_[method]):
            _method = self._dict_[method]
            _args = pickle.loads(args)
            _kwargs = pickle.loads(kwargs)
            return _method(*_args, **_kwargs)

    def exposed_get(self, name):
        return getattr(self._obj, name)


class ConstraintsProxy:
    def __init__(self, service: ConstraintsService):
        self.__service = service

        self.__format_dict = None

    def __init(self):
        self.__format_dict = self.__service.get_dict()
        if self.__format_dict is None:
            self.__format_dict = {}

    def __getattribute__(self, item):
        if item.startswith("__"):
            return super().__getattribute__(item)
        if item in dir(self):
            return super().__getattribute__(item)

        if self.__format_dict is None:
            self.__init()
        if item in self.__format_dict:
            _type = self.__format_dict[item]
            if _type == "callable":
                service = self.__service

                def func(*args, **kwargs):
                    _args = pickle.dumps(args)
                    _kwargs = pickle.dumps(kwargs)
                    return service.call(item, _args, _kwargs)
                return func
            else:
                return self.__service.get(item)
