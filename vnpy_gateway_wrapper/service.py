import abc
import copy
import dataclasses
import pickle
from typing import Callable, Dict, List

import rpyc

from .gateway_log import to_str, simple_types
from .utils import log


callable_index = 0


def get_and_increase_index():
    global callable_index
    callable_index+=1
    return callable_index


@dataclasses.dataclass
class Key:
    index = get_and_increase_index()

    def __hash__(self):
        return self.index

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return self.index == other.index


@dataclasses.dataclass
class CallableKey(Key):
    def __hash__(self):
        return super().__hash__()


@dataclasses.dataclass
class VariableKey(Key):
    def __hash__(self):
        return super().__hash__()


class CallableProxy:
    def __init__(self, server, key: CallableKey):
        self.__key = key
        self.__server = server

    def __call__(self, *args, **kwargs):
        self.__server.call_callable(self.__key, *args, **kwargs)


class CallableCallback(abc.ABC):

    @abc.abstractmethod
    def callback_callable(self, key: CallableKey, *args, **kwargs):
        pass


def encode(value, nopickle_data: Dict[int, None]):
    if isinstance(value, simple_types):
        return value
    if isinstance(value, tuple):
        return tuple(encode(v, nopickle_data) for v in value)
    if isinstance(value, list):
        return list(encode(v, nopickle_data) for v in value)
    if isinstance(value, dict):
        return dict({encode(k, nopickle_data): encode(v, nopickle_data) for k, v in value.items()})
    if dataclasses.is_dataclass(value):
        return value.__class__(**encode(dataclasses.asdict(value), nopickle_data))
    if callable(value):
        key = CallableKey()
        nopickle_data[key.index] = value
        return key
    value = copy.deepcopy(value)
    value.__dict__ = encode(value.__dict__, nopickle_data)
    return value


def decode(value, nopickle_data: Dict[int, None]):
    if isinstance(value, simple_types):
        return value
    if isinstance(value, tuple):
        return tuple(decode(v, nopickle_data) for v in value)
    if isinstance(value, list):
        return list(decode(v, nopickle_data) for v in value)
    if isinstance(value, dict):
        return dict({decode(k, nopickle_data):decode(v, nopickle_data) for k, v in value.items()})
    if isinstance(value, Key):
        if value.index in nopickle_data:
            return nopickle_data[value.index]
        raise ValueError("Not found key %s" % value.index)
    if dataclasses.is_dataclass(value):
        return value.__class__(**decode(dataclasses.asdict(value), nopickle_data))

    value = copy.deepcopy(value)
    d = {k: decode(v, nopickle_data) for k, v in value.__dict__.items() if not k.startswith("__")}
    value.__dict__.update(d)
    return value


def load_value(value, no_pickle_data):
    ret = pickle.loads(value)
    return decode(ret, no_pickle_data)


def dump_value(value, no_pickle_data=None):
    if no_pickle_data is None:
        no_pickle_data = {}
    value = encode(value, no_pickle_data)
    return pickle.dumps(value), no_pickle_data


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
                self._clazz = self._obj.__class__
                log.debug("Get clazz %s from obj" % self._clazz)
            else:
                self._clazz = self.get_clazz()
                log.debug("Get clazz %s success" % self._clazz)
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
        log.debug("Get dict class is ! %s" % self._format_dict)

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
        format_dict = self.format_dict
        log.debug("Server Get dict %s" % format_dict)
        return pickle.dumps(format_dict)

    def exposed_call(self, method, no_pickle_data, args, kwargs):
        if method in self.format_dict:
            value = getattr(self.obj, method)
            if callable(value):
                _method = value
                _args = load_value(args, no_pickle_data)
                _kwargs = load_value(kwargs, no_pickle_data)
                _ret = _method(*_args, **_kwargs)

                return dump_value(_ret)
            else:
                raise ValueError("Method %s is not callable!" % method)
        raise ValueError("Method %s is not found!" % method)

    def exposed_get(self, name):
        value = getattr(self.obj, name)
        return pickle.dumps(value)


class ConstraintsProxy:
    def __init__(self, service: ConstraintsService):
        self.__service = service

        self.__format_dict = None
        self.__name = self.__class__.__name__

    def __init(self):
        p_format_dict = self.__service.get_dict()
        self.__format_dict = pickle.loads(p_format_dict)
        log.debug("Get dict %s" % self.__format_dict)
        if self.__format_dict is None:
            self.__format_dict = {}

    @property
    def format_dict(self):
        if self.__format_dict is None:
            self.__init()
        return self.__format_dict

    def get_remote_attr(self, item):
        if item in self.format_dict:
            _type = self.format_dict[item]
            if _type == "callable":
                service = self.__service

                def func(*args, **kwargs):
                    log.debug("Server[%s]: Call remote callable %s success, args:%s, kwargs:%s"
                              % (self.__name, item, to_str(args), to_str(kwargs)))
                    _args, no_pickle_data = dump_value(args)
                    _kwargs, no_pickle_data = dump_value(kwargs, no_pickle_data)
                    _ret, ret_no_pickle_data = service.call(item, no_pickle_data, _args, _kwargs)
                    return load_value(_ret, ret_no_pickle_data)
                return func
            else:
                log.debug("Server[%s]: Get remote variable %s success" % (self.__name, item))
                value = self.__service.get(item)
                return pickle.loads(value)
        else:
            raise AttributeError("Server[%s]: Unknown remote attr %s!" % (self.__name, item))

    def __getattribute__(self, item):
        if item.startswith("__"):
            return super().__getattribute__(item)
        if item in dir(self):
            return super().__getattribute__(item)

        if self.format_dict is None:
            self.__init()
        return self.get_remote_attr(item)