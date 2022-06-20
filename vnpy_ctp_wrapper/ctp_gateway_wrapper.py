from typing import Dict, List, Any

import rpyc
from vnpy.trader.object import SubscribeRequest, OrderRequest, CancelRequest, OrderData, QuoteRequest, BarData, \
    HistoryRequest

from vnpy_ctp import CtpGatewayLog as CtpGateway


class CtpGatewayServices(rpyc.Service):

    def __init__(self):
        self._conn = None
        self._ctp_gateway: CtpGateway = None

    def on_connect(self, conn):
        self._conn = conn
        self._conn.root.get_ctp_gateway_name()

    def on_disconnect(self, conn):
        if self._ctp_gateway is not None:
            self.exposed_close()
        self._conn = None

    def get_ctp_gateway(self):
        if self._ctp_gateway is None and self._conn is not None:
            self._ctp_gateway = CtpGateway(self._conn.root, self._conn.root.get_ctp_gateway_name())
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

    def exposed_write_error(self, msg: str, error: dict) -> None:
        """输出错误信息日志"""
        return self.get_ctp_gateway().write_error(msg, error)

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
    from rpyc.utils.server import ThreadedServer

    t = ThreadedServer(CtpGatewayServices, port=18861, listener_timeout=60*10, protocol_config={"sync_request_timeout": 60*10, 'allow_public_attrs': True})
    t.start()
