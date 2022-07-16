#!/usr/bin/env python
#-*- coding: utf-8 -*-

from vnpy.event import EventEngine
from vnpy_tts import TtsGateway

username = ""
password = ""


if __name__ == "__main__":

    event_engine = EventEngine()
    gateway = TtsGateway(event_engine, "TTS")
    gateway.connect({'用户名': username, '密码': password,
                     '经纪商代码': '', '交易服务器': 'tcp://122.51.136.165:20002',
                     '行情服务器': 'tcp://122.51.136.165:20004', '产品名称': '', '授权编码': ''})
    input("Pause")
    gateway.close()
