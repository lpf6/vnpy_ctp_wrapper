#!/usr/bin/env python
#-*- coding: utf-8 -*-
from .service import ConstraintsProxy, ConstraintsService
from .utils import log
from .gateway_log import get_log_class, GatewayTest, to_str


class GatewayServices(ConstraintsService):

    def __init__(self, clazz_map, is_log=False, is_test=False):
        super().__init__()
        self._conn = None
        self._gateway = None
        self._name = None
        self._is_log = is_log
        self._is_test = is_test
        self._clazz_map = clazz_map
        self._clazz = None

    def create_obj(self):
        return self.get_clazz()(ConstraintsProxy(self._conn.root), self._name)

    def on_disconnect(self, conn):
        if self._gateway is not None:
            self._gateway.close()
        super().on_disconnect(conn)

    def get_clazz(self):
        self._name = self._conn.root.get_gateway_name()
        if self._is_test:
            self._clazz = GatewayTest
        else:
            name = self._name.lower()
            if name not in self._clazz_map:
                raise KeyError("Gateway %s not support!" % name)
            self._clazz = self._clazz_map[name]
        log.info("Get %s gateway: %s" % (self._name, to_str(self._clazz)))
        return get_log_class(self._clazz) if self._is_log else self._clazz


class CtpGatewayServices(GatewayServices):

    gateway_class = None
    is_log = False
    is_test = False

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
                       protocol_config={"sync_request_timeout": 60*10, "allow_pickle": True})
    t.start()
