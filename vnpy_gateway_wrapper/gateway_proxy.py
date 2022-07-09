from typing import Callable

import rpyc
from vnpy.event import EventEngine
from vnpy.trader.gateway import BaseGateway
from vnpy.trader.object import CancelRequest, OrderRequest, SubscribeRequest

from .event_engine_wrapper import EventEngineService


def create_proxy_gateway(hostname: str, port: int):
    class Proxy(GatewayProxy):
        def __init__(self, event_engine: EventEngine, gateway_name: str):
            super().__init__(event_engine, gateway_name, hostname, port)

    return Proxy


class GatewayProxy(BaseGateway):
    def __init__(self, event_engine: EventEngine, gateway_name: str, hostname: str, port: int):
        super().__init__(None, None)
        self.__gp__conn = rpyc.connect(hostname, port, service=EventEngineService(event_engine, gateway_name),
                            config={"sync_request_timeout": 60 * 10, 'allow_public_attrs': True})
        self.__gp__obj : BaseGateway = self.__gp__conn.root

    def __getattr__(self, name):
        if name.startswith("_GatewayProxy__gp__"):
            return super().__getattr__(name)
        val = super().__getattr__(name)
        if isinstance(val, Callable):
            origin_val = getattr(self.__gp__obj, name)
            def func(*args, **kwargs):

                return origin_val()
        return getattr(self.__gp__obj, name)

    def __setattr__(self, name, value):
        if name.startswith("_GatewayProxy__gp__"):
            return super().__setattr__(name, value)
        return setattr(self.__gp__obj, name, value)

    def __delattr__(self, name):
        delattr(self.__gp__obj, name)

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



