import asyncio
from typing import Any
import myparser
from mydata import data
from mydata import fileTransmit
import os

taskset = set()


class TCPServerProtocolFactory(asyncio.Protocol):
    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.filetr = fileTransmit()
        self.addr = transport.get_extra_info("peername")
        print(f"LINK Connected to{self.addr}")
        self.transport = transport
        data.trset.add(self)
        # loop = asyncio.get_running_loop()
        # self.task = loop.create_task(self.circularHearts())

    def eof_received(self) -> bool | None:
        print(f"EXIT {self.addr}")
        data.trset.discard(self.transport)
        self.transport.close()

    def connection_lost(self, exc: Exception | None) -> None:
        print(f"LINK {self.addr} is lost")
        if self.filetr.isRecv is True:
            print("stop received")
            os.remove(f"download/{self.filetr.filename}")
            self.filetr.isRecv = False
        if self.filetr.isSend is True:
            print("stop send")
            self.filetr.isSend = False
            self.filetr.sendFlag = "STOPSEND"

    def data_received(self, data: bytes) -> None:
        if self.filetr.isRecv is True:
            # if FILE recv flag is True
            loop = asyncio.get_running_loop()
            newt = loop.create_task(self.filetr.continueReceive(self, data))
            taskset.add(newt)
            newt.add_done_callback(taskset.discard)
            return
        if self.filetr.isSend is True:
            msg = data.decode()
            if msg == "CONTRECV":
                self.filetr.sendFlag = "CONTSEND"
            elif msg == "STOPRECV":
                self.filetr.sendFlag = "STOPSEND"
            return

        pre = data.decode().split(maxsplit=1)
        if pre[0] == "FILE":
            loop = asyncio.get_running_loop()
            newt = loop.create_task(self.filetr.firstReceive(self, pre[1]))
            taskset.add(newt)
            newt.add_done_callback(taskset.discard)
            return
        print(f"RECEIVED {data.decode()} FROM {self.addr}")


class TCPClientProtocol(asyncio.Protocol):
    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.filetr = fileTransmit()
        self.addr = transport.get_extra_info("peername")
        self.transport = transport
        print("LINK Connected to", self.addr)

    def data_received(self, data: bytes) -> None:
        if self.filetr.isRecv is True:
            # if FILE recv flag is True
            loop = asyncio.get_running_loop()
            newt = loop.create_task(self.filetr.continueReceive(self, data))
            taskset.add(newt)
            newt.add_done_callback(taskset.discard)
            return
        if self.filetr.isSend is True:
            msg = data.decode()
            if msg == "CONTRECV":
                self.filetr.sendFlag = "CONTSEND"
            elif msg == "STOPRECV":
                self.filetr.sendFlag = "STOPSEND"
            return

        pre = data.decode().split(maxsplit=1)
        if pre[0] == "FILE":
            loop = asyncio.get_running_loop()
            newt = loop.create_task(self.filetr.firstReceive(self, pre[1]))
            taskset.add(newt)
            newt.add_done_callback(taskset.discard)
            return
        print(f"RECEIVED {data.decode()} FROM {self.addr}")

    def eof_received(self) -> bool | None:
        print("WARNING server is closed")

    def connection_lost(self, exc: Exception | None) -> None:
        print("CLOSED connection is closed successfully")
        if self.filetr.isRecv is True:
            print("stop received")
            os.remove(f"download/{self.filetr.filename}")
            self.filetr.isRecv = False
        if self.filetr.isSend is True:
            print("stop send")
            self.filetr.isSend = False
            self.filetr.sendFlag = "STOPSEND"


class UDProtocolFactory(asyncio.DatagramProtocol):
    def connection_made(self, transport) -> None:
        print("TIPS Connection successfully made!")

    def datagram_received(self, data: bytes, addr: tuple[str | Any, int]) -> None:
        """
        收到信息时，将addr拉入清单
        """
        print("RECIEVED", data.decode(), "FROM", addr)

    def connection_lost(self, exc: Exception | None) -> None:
        print("CLOSED connection is closed successfully")
