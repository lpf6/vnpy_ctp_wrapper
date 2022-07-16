import copy
import dataclasses
from typing import Dict, List, Any

from vnpy.event import EventEngine, Event
from vnpy.trader.constant import Exchange
from vnpy.trader.gateway import BaseGateway
from vnpy.trader.object import CancelRequest, OrderRequest, SubscribeRequest

from .utils import log


simple_types = tuple([type(None), int, bool, float, bytes, str, complex, type(NotImplemented), type(Ellipsis)])


def to_str(value):
    if isinstance(value, simple_types):
        return value
    if isinstance(value, tuple):
        return tuple(to_str(v) for v in value)
    if isinstance(value, list):
        return list(to_str(v) for v in value)
    if isinstance(value, dict):
        return dict({to_str(k): to_str(v) for k, v in value.items()})
    if dataclasses.is_dataclass(value):
        return "%s%s" % (value.__class__.__name__, to_str(dataclasses.asdict(value)))
    if callable(value):
        return str(value)
    return "%s%s" % (value.__class__.__name__, to_str(
        dict({k: v for k, v in value.__dict__.items() if not k.startswith("__")})))



def event_to_str(event: Event):
    return "Event{%s, %s}" % (event.type, event.data)


Event.__str__ = event_to_str


def get_log_class(clazz):
    class LogGateway(GatewayLog):
        def __init__(self, event_engine: EventEngine, gateway_name: str):
            super().__init__(clazz, event_engine, gateway_name)
    return LogGateway


class GatewayLog(BaseGateway):
    """
    VeighNa用于对接期货CTP柜台的交易接口。
    """

    def __init__(self, clazz, event_engine: EventEngine, gateway_name: str) -> None:
        """构造函数"""
        self.__proxy_method = {"connect"}
        self.gateway = None
        if clazz is not None:
            log.info("impl gateway is: %s" % clazz)
            self.gateway = clazz(event_engine, gateway_name)

    def __getattribute__(self, attr):
        if attr == "gateway" or attr.startswith("__") or attr.startswith("_GatewayLog__"):
            return super().__getattribute__(attr)
        if self.gateway is None:
            log.error("impl gateway is None")
            return None

        val = self.gateway.__getattribute__(attr)
        if callable(val):
            def fun(*args, **kwargs):
                log.debug("%s.%s(args=%s, kwargs=%s)" % (self.gateway, attr, args, kwargs))
                if attr in self.__proxy_method:
                    super(GatewayLog, self).__getattribute__(attr)(*args, **kwargs)
                if self.gateway is None:
                    log.error("impl gateway is None")
                    return None
                return val(*args, **kwargs)
            return fun

        log.debug("get name: %s, val: %s" % (attr, val))
        return val

    def __setattr__(self, key, value):
        if key == "gateway" or key.startswith("__") or key.startswith("_GatewayLog__"):
            return super().__setattr__(key, value)
        return self.gateway.__setattr__(key, value)

    def connect(self, setting: dict) -> None:
        default_setting: Dict[str, str] = {
            "用户名": "",
            "密码": "",
            "经纪商代码": "",
            "交易服务器": "",
            "行情服务器": "",
            "产品名称": "",
            "授权编码": ""
        }
        for k, v in setting.items():
            if k not in default_setting:
                log.error("Unknown key for connect: %s:%s" % (k, v))

    def close(self) -> None:
        pass

    def subscribe(self, req: SubscribeRequest) -> None:
        pass

    def send_order(self, req: OrderRequest) -> str:
        pass

    def cancel_order(self, req: CancelRequest) -> None:
        pass

    def query_account(self) -> None:
        pass

    def query_position(self) -> None:
        pass


class GatewayTest(BaseGateway):
    """
    VeighNa用于对接期货CTP柜台的交易接口。
    """
    exchanges = [Exchange.SSE]

    def __init__(self, event_engine: EventEngine, gateway_name: str) -> None:
        """构造函数"""
        super().__init__(event_engine, gateway_name)

    def __getattribute__(self, attr):
        if attr.startswith("__"):
            return super().__getattribute__(attr)
        val = super().__getattribute__(attr)
        if callable(val):
            def fun(*args, **kwargs):
                log.info("func: %s, args: %s, kwargs: %s" % (val.__name__, args, kwargs))
                if val.__name__ == "connect":
                    super(GatewayTest, self).__getattribute__('event_engine').register("test", super(GatewayTest, self).__getattribute__('on_event'))
                super(GatewayTest, self).__getattribute__('on_event')(val.__name__, [args, kwargs])
                return None
            return fun
        return val

    def connect(self, setting: dict) -> None:
        pass

    def close(self) -> None:
        pass

    def subscribe(self, req: SubscribeRequest) -> None:
        pass

    def send_order(self, req: OrderRequest) -> str:
        pass

    def cancel_order(self, req: CancelRequest) -> None:
        pass

    def query_account(self) -> None:
        pass

    def query_position(self) -> None:
        pass