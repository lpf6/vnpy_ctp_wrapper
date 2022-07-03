import rpyc
from vnpy.event import EventEngine
from vnpy.trader.gateway import BaseGateway

from .event_engine_wrapper import EventEngineService


def create_proxy_gateway(hostname: str, port: int):
    class Proxy(GatewayProxy):
        def __init__(self, event_engine: EventEngine, gateway_name: str):
            super().__init__(event_engine, gateway_name, hostname, port)

    return Proxy


class GatewayProxy:
    def __init__(self, event_engine: EventEngine, gateway_name: str, hostname: str, port: int):
        self.__gp__conn = rpyc.connect(hostname, port, service=EventEngineService(event_engine, gateway_name),
                            config={"sync_request_timeout": 60 * 10, 'allow_public_attrs': True})
        self.__gp__obj : BaseGateway = self.__gp__conn.root

    def __getattr__(self, name):
        if name.startswith("_GatewayProxy__gp__"):
            return super().__getattr__(name)
        return getattr(self.__gp__obj, name)

    def __setattr__(self, name, value):
        if name.startswith("_GatewayProxy__gp__"):
            return super().__setattr__(name, value)
        return setattr(self.__gp__obj, name, value)

    def __delattr__(self, name):
        delattr(self.__gp__obj, name)

