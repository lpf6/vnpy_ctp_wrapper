#!/usr/bin/env python
#-*- coding: utf-8 -*-

import argparse
import datetime
import json
import os
import sys
import time

sys.path.append(os.path.dirname(__file__))

import rpyc
from vnpy.event.engine import HandlerType, Event, EventEngine
from vnpy.trader.constant import Exchange, Direction, OrderType
from vnpy.trader.object import SubscribeRequest, OrderRequest, CancelRequest, OrderData, QuoteRequest, BarData, \
    HistoryRequest, ContractData, LogData, QuoteData, AccountData, PositionData, TradeData, TickData

from .utils import log, is_debug
from .service import ConstraintsService, ConstraintsProxy


def print_call():
    def decorate(fn):
        log.info(fn.__name__)
        return fn
    return decorate


class EventEngineLog:
    def register(self, _type: str, handler: HandlerType) -> None:
        log.info("register %s, %s" % (_type, handler))

    def put(self, event: Event) -> None:
        log.info("put %s, %s" % (event.type, event.data))

    def get_gateway_name(self):
        log.info("get_gateway_name")


class EventEngineService(ConstraintsService):

    def __init__(self, event_engine: EventEngine, gateway_name: str):
        super(EventEngineService, self).__init__(event_engine)
        self.gateway_name = gateway_name

    def exposed_get_gateway_name(self):
        if is_debug():
            log.debug("Server[%s]: gateway_name=%s" % (self, self.gateway_name))
        return self.gateway_name

    def get_clazz(self):
        return self._obj.__class__


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Start vtp wrapper client')
    parser.add_argument('-n', "--hostname", default="0.0.0.0", type=str,
                        help='hostname')
    parser.add_argument('-p', "--port", default=18861, type=int,
                        help='port')
    args = parser.parse_args()
    log.info("Client run with args: %s" % args)

    service = EventEngineService(EventEngineLog(), "test")
    conn = rpyc.connect(args.hostname, args.port, service=service, config={"sync_request_timeout": 60*10, "allow_pickle": True})
    proxy = ConstraintsProxy(conn.root)
    print(proxy.exchanges)
    proxy.connect({'test': "connect", "time": datetime.datetime.now()})
    proxy.query_position()
    proxy.query_account()
    proxy.subscribe(SubscribeRequest("testSubscribe", Exchange.COMEX))
    proxy.send_order(OrderRequest("testOrder", Exchange.COMEX, Direction.LONG, OrderType.LIMIT, 12345, 12.23))
    proxy.cancel_order(CancelRequest("1234", "testOrder", Exchange.COMEX))
    input("Pause, enter any keys to Close.")
    proxy.close()
    conn.close()
