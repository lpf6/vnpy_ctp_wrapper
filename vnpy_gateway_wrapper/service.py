import abc
import pickle
import time

import rpyc

from vnpy_gateway_wrapper.utils import log


class ConstraintsService(rpyc.Service):
    def __init__(self, obj=None, clazz=None):
        self._clazz = clazz
        self._obj = obj
        self._conn = None
        self._format_dict = None
        self._remove_obj = True
        if obj is not None or clazz is not None:
            self._remove_obj = (obj is not None)

    def get_clazz(self):
        pass

    def create_obj(self):
        pass

    def remove_obj(self):
        pass

    def _init_obj(self):
        if self._obj is None:
            log.debug("Create new obj")
            self._obj = self.create_obj()
            if self._obj is None:
                log.error("Service[%s] on_connect a None obj! " % self.__class__.__name__)

    @property
    def obj(self):
        if self._obj is None:
            self._init_obj()
        return self._obj

    @property
    def clazz(self):
        if self._clazz is None:
            if self._obj is not None:
                log.debug("Get clazz from obj")
                self._clazz = self._obj.__class__
            else:
                log.debug("Get clazz")
                self._clazz = self.get_clazz()
                log.debug("Get clazz success")
        return self._clazz

    def _init_format_dict(self):
        if self.clazz is None:
            log.debug("Get dict class is None!")
            self._format_dict = {}
            return

        all_dir = dir(self.clazz)
        format_dict = {}
        for d in all_dir:
            if "__" in d:
                continue
            v = getattr(self.clazz, d)
            format_dict[d] = "callable" if callable(v) else "variable"
        self._format_dict = format_dict
        log.debug("Get dict class is None! %s" % self._format_dict)

    @property
    def format_dict(self):
        if self._format_dict is not None:
            return self._format_dict
        self._init_format_dict()
        return self._format_dict

    def on_connect(self, conn):
        self._conn = conn

    def on_disconnect(self, conn):
        if self._remove_obj:
            self.remove_obj()
            self._obj = None
            self._format_dict = None
        self._conn = None

    def exposed_get_dict(self):
        log.debug("Server Get dict")
        return self.format_dict

    def exposed_call(self, method, args, kwargs):
        if method in self.format_dict:
            value = getattr(self.obj, method)
            if callable(value):
                _method = value
                _args = pickle.loads(args)
                _kwargs = pickle.loads(kwargs)
                return _method(*_args, **_kwargs)
            else:
                raise ValueError("Method %s is not callable!" % method)
        raise ValueError("Method %s is not found!" % method)

    def exposed_get(self, name):
        return getattr(self.obj, name)


class ConstraintsProxy:
    def __init__(self, service: ConstraintsService):
        self.__service = service

        self.__format_dict = None
        self.__name = self.__class__.__name__

    def __init(self):
        log.debug("Get dict")
        self.__format_dict = self.__service.get_dict()
        if self.__format_dict is None:
            self.__format_dict = {}

    @property
    def format_dict(self):
        if self.__format_dict is None:
            self.__init()
        return self.__format_dict

    def __getattribute__(self, item):
        if item.startswith("__"):
            return super().__getattribute__(item)
        if item in dir(self):
            return super().__getattribute__(item)

        if self.format_dict is None:
            self.__init()
        if item in self.format_dict:
            _type = self.format_dict[item]
            if _type == "callable":
                log.debug("Server[%s]: Get remote callable %s success" % (self.__name, item))
                service = self.__service

                def func(*args, **kwargs):
                    log.debug("Server[%s]: Call remote callable %s success" % (self.__name, item))
                    _args = pickle.dumps(args)
                    _kwargs = pickle.dumps(kwargs)
                    return service.call(item, _args, _kwargs)
                return func
            else:
                log.debug("Server[%s]: Get remote variable %s success" % (self.__name, item))
                return self.__service.get(item)
        else:
            raise AttributeError("Unknown attr %s!" % item)
