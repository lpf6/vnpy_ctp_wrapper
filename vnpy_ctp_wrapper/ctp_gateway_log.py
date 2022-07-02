from typing import Dict, List, Any

from vnpy.event import EventEngine
from vnpy.trader.gateway import BaseGateway
from vnpy.trader.object import CancelRequest, OrderRequest, SubscribeRequest

from utils import log
class CtpGatewayLog(BaseGateway):
    """
    VeighNa用于对接期货CTP柜台的交易接口。
    """

    def __init__(self, event_engine: EventEngine, gateway_name: str) -> None:
        """构造函数"""
        super().__init__(event_engine, gateway_name)
        self.ctp_gateway = None
        try:
            from vnpy_ctp import CtpGateway
            self.ctp_gateway = CtpGateway(event_engine, gateway_name)
        except ImportError as e:
            pass

    def __getattribute__(self, attr):
        val = super().__getattribute__(attr)
        if callable(val):
            def fun(*args, **kwargs):
                log.debug("func: %s, args: %s, kwargs: %s" % (val.__name__, args, kwargs))
                if self.ctp_gateway is None:
                    log.error("impl ctp_gateway is None")
                    return None
                return self.ctp_gateway.__getattribute__(attr)(*args, **kwargs)
            return fun
        if attr == "ctp_gateway" or attr.startswith("__"):
            return val

        log.debug("get name: %s, val: %s" % (attr, val))
        if self.ctp_gateway is None:
            log.error("impl ctp_gateway is None")
            return None
        return self.ctp_gateway.__getattribute__(attr)

    def __setattr__(self, key, value):
        if key == "ctp_gateway" or key.startswith("__"):
            return super().__setattr__(key, value)
        return self.ctp_gateway.__setattr__(key, value)

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


class CtpGatewayTest(BaseGateway):
    """
    VeighNa用于对接期货CTP柜台的交易接口。
    """

    def __init__(self, event_engine: EventEngine, gateway_name: str) -> None:
        """构造函数"""
        super().__init__(event_engine, gateway_name)

    def __getattribute__(self, attr):
        val = super().__getattribute__(attr)
        if callable(val):
            def fun(*args, **kwargs):
                log.info("func: %s, args: %s, kwargs: %s" % (val.__name__, args, kwargs))
                super(CtpGatewayTest, self).__getattribute__('on_event')(val.__name__, [args, kwargs])
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