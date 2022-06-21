import argparse

import rpyc
from vnpy.event.engine import HandlerType, Event, EventEngine
from vnpy.trader.constant import Exchange, Direction, OrderType
from vnpy.trader.gateway import BaseGateway
from vnpy.trader.object import CancelRequest, OrderRequest, SubscribeRequest

from vnpy_ctp_wrapper.utils import log


def print_call():
    def decorate(fn):
        print(fn.__name__)
        return fn
    return decorate


class EventEngineLog:

    def register(self, _type: str, handler: HandlerType) -> None:
        print("register %s, %s" % (_type, handler))

    def put(self, event: Event) -> None:
        print("put %s, %s" % (event.type, event.data))

    def get_ctp_gateway_name(self):
        print("get_ctp_gateway_name")


class EventEngineService(rpyc.Service):

    def __init__(self, event_engine: EventEngine, gateway_name: str):
        self.event_engine = event_engine
        self.gateway_name = gateway_name

    def exposed_register(self, _type: str, handler: HandlerType) -> None:
        self.event_engine.register(_type, handler)

    def exposed_put(self, event: Event) -> None:
        self.event_engine.put(event)

    def exposed_get_ctp_gateway_name(self):
        return self.gateway_name


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Start vtp wrapper client')
    parser.add_argument('-n', "--hostname", default="0.0.0.0", type=str,
                        help='hostname')
    parser.add_argument('-p', "--port", default=18861, type=int,
                        help='port')
    args = parser.parse_args()
    log.info("Client run with args: %s" % args)

    service = EventEngineService(EventEngineLog(), "test")
    conn = rpyc.connect(args.hostname, args.port, service=service, config={"sync_request_timeout": 60*10, 'allow_public_attrs': True})
    conn.root.connect({"test": "connect"})
    conn.root.query_position()
    conn.root.query_account()
    conn.root.subscribe(SubscribeRequest("testSubscribe", Exchange.COMEX))
    conn.root.send_order(OrderRequest("testOrder", Exchange.COMEX, Direction.LONG, OrderType.LIMIT, 12345, 12.23))
    conn.root.cancel_order(CancelRequest("1234", "testOrder", Exchange.COMEX))
    conn.root.close()
