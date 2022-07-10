from typing import Dict, List, Any

from vnpy.event import EventEngine
from vnpy.trader.constant import Exchange
from vnpy.trader.gateway import BaseGateway
from vnpy.trader.object import CancelRequest, OrderRequest, SubscribeRequest

from .utils import log


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
        self.gateway = None
        if clazz is not None:
            log.info("impl gateway is: %s" % clazz)
            self.gateway = clazz(event_engine, gateway_name)

    def __getattribute__(self, attr):
        if attr == "gateway" or attr.startswith("__"):
            return super().__getattribute__(attr)
        if self.gateway is None:
            log.error("impl gateway is None")
            return None

        val = self.gateway.__getattribute__(attr)
        if callable(val):
            def fun(*args, **kwargs):
                log.debug("func: %s, args: %s, kwargs: %s" % (val.__name__, args, kwargs))
                if self.gateway is None:
                    log.error("impl gateway is None")
                    return None
                return val(*args, **kwargs)
            return fun

        log.debug("get name: %s, val: %s" % (attr, val))
        return val

    def __setattr__(self, key, value):
        if key == "gateway" or key.startswith("__"):
            return super().__setattr__(key, value)
        return self.gateway.__setattr__(key, value)

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