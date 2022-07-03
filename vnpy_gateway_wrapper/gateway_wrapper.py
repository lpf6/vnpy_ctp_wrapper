import dataclasses
import logging
from typing import Dict, List, Any

import rpyc
from vnpy.trader.gateway import BaseGateway
from vnpy.trader.object import SubscribeRequest, OrderRequest, CancelRequest, OrderData, QuoteRequest, BarData, \
    HistoryRequest, ContractData, LogData, QuoteData, AccountData, PositionData, TradeData, TickData

from utils import log
from vnpy_gateway_wrapper.gateway_log import get_log_class, GatewayTest


class GatewayServices(rpyc.Service):

    def __init__(self, clazz_map, is_log=False, is_test=False):
        self._conn = None
        self._gateway = None
        self._name = None
        self._is_log = is_log
        self._is_test = is_test
        self._clazz_map = clazz_map
        self._clazz = None
        self.exposed_exchanges = []
        self.exposed_default_name: str = ""
        self.exposed_default_setting: Dict[str, Any] = {}
        self.exposed_gateway_name: str = ""

    def on_connect(self, conn):
        self._conn = conn
        self.exposed_exchanges = self.get_gateway().exchanges
        self.exposed_default_name = self.get_gateway().default_name
        self.exposed_default_setting: Dict[str, Any] = self.get_gateway().default_setting
        self.exposed_gateway_name: str = self.get_gateway().gateway_name

    def on_disconnect(self, conn):
        if self._gateway is not None:
            self.exposed_close()
        self._conn = None
        self.exposed_exchanges = []
        self.exposed_default_name: str = ""
        self.exposed_default_setting: Dict[str, Any] = {}
        self.exposed_gateway_name: str = ""

    def get_gateway(self) -> BaseGateway:
        if self._gateway is None and self._conn is not None:
            self._gateway = self.get_clazz()(self._conn.root, self._conn.root.get_gateway_name())
        return self._gateway

    def get_clazz(self):
        if self._is_test:
            return GatewayTest
        self._name: str = self._conn.root.get_gateway_name()
        if self._name is not None:
            self._name = self._name.lower()
        if self._name not in self._clazz_map:
            raise KeyError("Gateway %s not support!" % self._name)
        self._clazz = self._clazz_map[self._name]
        return get_log_class(self._clazz) if self._is_log else self._clazz

    def exposed_on_event(self, type: str, data: Any = None) -> None:
        return self.get_gateway().on_event(type, data)

    def exposed_on_tick(self, tick: TickData) -> None:
        return self.get_gateway().on_tick(tick)

    def exposed_on_trade(self, trade: TradeData) -> None:
        return self.get_gateway().on_trade(trade)

    def exposed_on_order(self, order: OrderData) -> None:
        return self.get_gateway().on_order(order)

    def exposed_on_position(self, position: PositionData) -> None:
        return self.get_gateway().on_position(position)

    def exposed_on_account(self, account: AccountData) -> None:
        return self.get_gateway().on_account(account)

    def exposed_on_quote(self, quote: QuoteData) -> None:
        return self.get_gateway().on_quote(quote)

    def exposed_on_log(self, log: LogData) -> None:
        return self.get_gateway().on_log(log)

    def exposed_on_contract(self, contract: ContractData) -> None:
        return self.get_gateway().on_contract(contract)

    def exposed_write_log(self, msg: str) -> None:
        return self.get_gateway().write_log(msg)

    def exposed_connect(self, setting: dict) -> None:
        """连接交易接口"""
        return self.get_gateway().connect(setting)

    def exposed_subscribe(self, req: SubscribeRequest) -> None:
        """订阅行情"""
        return self.get_gateway().subscribe(req)

    def exposed_send_order(self, req: OrderRequest) -> str:
        """委托下单"""
        return self.get_gateway().send_order(req)

    def exposed_cancel_order(self, req: CancelRequest) -> None:
        """委托撤单"""
        return self.get_gateway().cancel_order(req)

    def exposed_query_account(self) -> None:
        """查询资金"""
        return self.get_gateway().query_account()

    def exposed_query_position(self) -> None:
        """查询持仓"""
        return self.get_gateway().query_position()

    def exposed_close(self) -> None:
        """关闭接口"""
        if self._gateway is not None:
            self._gateway.close()
            self._gateway = None

    def exposed_on_order(self, order: OrderData) -> None:
        return self.get_gateway().on_order(order)

    def exposed_send_quote(self, req: QuoteRequest) -> str:
        return self.get_gateway().send_quote(req)

    def exposed_cancel_quote(self, req: CancelRequest) -> None:
        return self.get_gateway().cancel_quote(req)

    def exposed_query_history(self, req: HistoryRequest) -> List[BarData]:
        return self.get_gateway().query_history(req)

    def exposed_get_default_setting(self) -> Dict[str, Any]:
        return self.get_gateway().get_default_setting()


class CtpGatewayServices(GatewayServices):

    gateway_class = None
    is_log = False
    is_test = False

    def __getattr__(self, name):
        try:
            return super().__getattr__(name)
        except AttributeError as e:
            try:
                return getattr(self.get_gateway(), name)
            except AttributeError:
                raise e

    @staticmethod
    def get_gateway_class_map() -> dict:
        if CtpGatewayServices.gateway_class is None:
            CtpGatewayServices.gateway_class = {}
            try:
                from vnpy_ctp import CtpGateway
                CtpGatewayServices.gateway_class["ctp"] = CtpGateway
            except ImportError:
                log.error("Not install vnpy-ctp")
            try:
                from vnpy_tts import TtsGateway
                CtpGatewayServices.gateway_class["tts"] = TtsGateway
            except ImportError:
                log.error("Not install vnpy-tts")
            CtpGatewayServices.gateway_class["test"] = GatewayTest

        return CtpGatewayServices.gateway_class

    @staticmethod
    def set_gateway_class(clazz):
        CtpGatewayServices.gateway_class = clazz

    def __init__(self):
        super().__init__(CtpGatewayServices.get_gateway_class_map(), CtpGatewayServices.is_log, CtpGatewayServices.is_test)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Start vtp wrapper server')
    parser.add_argument('-t', "--test", default=False, action="store_true",
                        help='Enable test callback')
    parser.add_argument('-v', "--verbose", default=False, action="store_true",
                        help='Enable log')
    parser.add_argument('-n', "--hostname", default="0.0.0.0", type=str,
                        help='hostname')
    parser.add_argument('-p', "--port", default=18861, type=int,
                        help='port')
    parser.add_argument('-l', "--listener_timeout", default=60*10, type=int,
                        help='port')
    args = parser.parse_args()
    log.info("Server run with args: %s" % args)
    from rpyc.utils.server import ThreadedServer

    CtpGatewayServices.is_log = args.verbose
    CtpGatewayServices.is_test = args.test

    t = ThreadedServer(CtpGatewayServices, hostname=args.hostname, port=args.port,
                       listener_timeout=args.listener_timeout,
                       protocol_config={"sync_request_timeout": 60*10, 'allow_public_attrs': True})
    t.start()
