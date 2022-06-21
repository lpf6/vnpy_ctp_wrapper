from typing import Dict, List, Any

import rpyc
from vnpy.trader.object import SubscribeRequest, OrderRequest, CancelRequest, OrderData, QuoteRequest, BarData, \
    HistoryRequest


class CtpGatewayServices(rpyc.Service):

    ctp_gateway_class = None

    @staticmethod
    def get_ctp_gateway_class():
        if CtpGatewayServices.ctp_gateway_class is None:
            from vnpy_ctp import CtpGateway
            CtpGatewayServices.ctp_gateway_class = CtpGateway
        return CtpGatewayServices.ctp_gateway_class

    @staticmethod
    def set_ctp_gateway_class(clazz):
        CtpGatewayServices.ctp_gateway_class = clazz

    def __init__(self):
        self._conn = None
        self._ctp_gateway = None

    def on_connect(self, conn):
        self._conn = conn
        self._conn.root.get_ctp_gateway_name()

    def on_disconnect(self, conn):
        if self._ctp_gateway is not None:
            self.exposed_close()
        self._conn = None

    def get_ctp_gateway(self):
        if self._ctp_gateway is None and self._conn is not None:
            self._ctp_gateway = CtpGatewayServices.get_ctp_gateway_class()(self._conn.root, self._conn.root.get_ctp_gateway_name())
        return self._ctp_gateway

    def exposed_connect(self, setting: dict) -> None:
        """连接交易接口"""
        return self.get_ctp_gateway().connect(setting)

    def exposed_subscribe(self, req: SubscribeRequest) -> None:
        """订阅行情"""
        return self.get_ctp_gateway().subscribe(req)

    def exposed_send_order(self, req: OrderRequest) -> str:
        """委托下单"""
        return self.get_ctp_gateway().send_order(req)

    def exposed_cancel_order(self, req: CancelRequest) -> None:
        """委托撤单"""
        return self.get_ctp_gateway().cancel_order(req)

    def exposed_query_account(self) -> None:
        """查询资金"""
        return self.get_ctp_gateway().query_account()

    def exposed_query_position(self) -> None:
        """查询持仓"""
        return self.get_ctp_gateway().query_position()

    def exposed_close(self) -> None:
        """关闭接口"""
        if self._ctp_gateway is not None:
            self._ctp_gateway.close()
            self._ctp_gateway = None

    def exposed_on_order(self, order: OrderData) -> None:
        return self.get_ctp_gateway().on_order(order)

    def exposed_send_quote(self, req: QuoteRequest) -> str:
        return self.get_ctp_gateway().send_quote(req)

    def exposed_cancel_quote(self, req: CancelRequest) -> None:
        return self.get_ctp_gateway().cancel_quote(req)

    def exposed_query_history(self, req: HistoryRequest) -> List[BarData]:
        return self.get_ctp_gateway().query_history(req)

    def exposed_get_default_setting(self) -> Dict[str, Any]:
        return self.get_ctp_gateway().get_default_setting()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Start vtp wrapper server')
    parser.add_argument('-t', "--test", default=False, action="store_true",
                        help='Enable test callback')
    parser.add_argument('-v', "--verbose", default=False, action="store_true",
                        help='Enable log')
    args = parser.parse_args()
    from rpyc.utils.server import ThreadedServer
    if args.test:
        from ctp_gateway_log import CtpGatewayTest
        CtpGatewayServices.set_ctp_gateway_class(CtpGatewayTest)
    elif args.verbose:
        from ctp_gateway_log import CtpGatewayLog
        CtpGatewayServices.set_ctp_gateway_class(CtpGatewayLog)

    t = ThreadedServer(CtpGatewayServices, port=18861, listener_timeout=60*10, protocol_config={"sync_request_timeout": 60*10, 'allow_public_attrs': True})
    t.start()