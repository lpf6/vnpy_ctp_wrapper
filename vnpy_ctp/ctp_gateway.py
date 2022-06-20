from typing import Dict, List

from vnpy.event import EventEngine
from vnpy.trader.gateway import BaseGateway
from vnpy.trader.object import SubscribeRequest, OrderRequest, CancelRequest


class CtpGatewayLog(BaseGateway):
    """
    VeighNa用于对接期货CTP柜台的交易接口。
    """

    default_name: str = "CTP"

    default_setting: Dict[str, str] = {
        "用户名": "",
        "密码": "",
        "经纪商代码": "",
        "交易服务器": "",
        "行情服务器": "",
        "产品名称": "",
        "授权编码": ""
    }

    exchanges: List[str] = None

    def __init__(self, event_engine: EventEngine, gateway_name: str) -> None:
        """构造函数"""
        super().__init__(event_engine, gateway_name)

    def connect(self, setting: dict) -> None:
        """连接交易接口"""
        print("connect")
        self.on_event("connect", setting)

    def subscribe(self, req: SubscribeRequest) -> None:
        """订阅行情"""
        self.on_event("subscribe", req)

    def send_order(self, req: OrderRequest) -> str:
        """委托下单"""
        self.on_event("send_order", req)

    def cancel_order(self, req: CancelRequest) -> None:
        """委托撤单"""
        self.on_event("cancel_order", req)

    def query_account(self) -> None:
        """查询资金"""
        self.on_event("query_account", None)

    def query_position(self) -> None:
        """查询持仓"""
        self.on_event("query_position", None)

    def close(self) -> None:
        """关闭接口"""
        self.on_event("close", None)

    def write_error(self, msg: str, error: dict) -> None:
        """输出错误信息日志"""
        self.on_event("write_error", [msg, error])
