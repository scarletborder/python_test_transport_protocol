from abc import ABCMeta, abstractmethod
import weakref
import asyncio
import sys
import contextvars
import aioconsole
import re
import socket


import myprotocol
import mydata

"""
文件结构有问题，parser应该只起到识别首cmd之后跳转，而不是继续负担执行的功能。

"""


class Handle(metaclass=ABCMeta):
    @abstractmethod
    async def execute(self, data):
        pass


class exit(Handle):
    def __init__(self) -> None:
        self.next = build()

    async def execute(self, data):
        if len(data) == 0:
            return
        if data[0] == "EXIT":
            if mydata.data.server is not None:
                await self.next.next.execute(["CLOSE"])
            sys.exit(0)
            return
        else:
            await self.next.execute(data=data)


class build(Handle):
    def __init__(self) -> None:
        self.next = close()

    async def execute(self, data):
        if data[0] in ("UDP", "TCPS", "TCPC"):
            if mydata.data.server is not None:
                print("ERROR Connection is still running, close before make a new one")
                return
            else:
                loop = asyncio.get_running_loop()
                if data[0] == "UDP":
                    try:
                        transport, protocol = await loop.create_datagram_endpoint(
                            lambda: myprotocol.UDProtocolFactory(),
                            local_addr=await mydata.tipinputaddr("local"),
                        )
                    except:
                        print("Unexpected error", sys.exc_info()[0])
                        return
                    mydata.data.trset.add(transport)
                    mydata.data.server = mydata.serviceFamily.UDP_SERVICE
                    return
                elif data[0] == "TCPS":
                    host, port = await mydata.tipinputaddr("local")
                    try:
                        server = await loop.create_server(
                            lambda: myprotocol.TCPServerProtocolFactory(), host, port
                        )
                        await server.start_serving()
                    except:
                        print("Unexpected error", sys.exc_info()[0])
                        return
                    mydata.data.server = server
                    return
                else:
                    host, port = await mydata.tipinputaddr("remote")
                    try:
                        transport, protocol = await loop.create_connection(
                            lambda: myprotocol.TCPClientProtocol(),
                            host,
                            port,
                            local_addr=await mydata.tipinputaddr("local"),
                        )
                    except:
                        print("Unexpected error", sys.exc_info()[0])
                        return
                    mydata.data.trset.add(protocol)
                    mydata.data.server = mydata.serviceFamily.TCPC_SERVICE
                    return
        else:
            await self.next.execute(data=data)


class close(Handle):
    def __init__(self) -> None:
        self.next = bind()

    async def execute(self, data):
        if data[0] == "CLOSE":
            if mydata.data.server is not None:
                if mydata.data.server in (
                    mydata.serviceFamily.UDP_SERVICE,
                    mydata.serviceFamily.TCPC_SERVICE,
                ):
                    for t in mydata.data.trset:
                        if mydata.data.server == mydata.serviceFamily.TCPC_SERVICE:
                            t.transport.write_eof()
                        t.close()
                else:
                    for t in mydata.data.trset:
                        t.transport.write_eof()
                    mydata.data.trset.clear()
                    mydata.data.server.close()

            mydata.data.reset()
            print("Connection has been closed")
        else:
            await self.next.execute(data)


class bind(Handle):
    def __init__(self) -> None:
        self.next = sendMsg()

    async def execute(self, data):
        if data[0] == "BIND":
            data = data[1].split(":")
            mydata.data.bindAddr = (data[0], int(data[1]))
            return
        else:
            await self.next.execute(data)


class sendMsg(Handle):
    def __init__(self) -> None:
        self.next = sendFile()

    async def execute(self, data):
        if data[0] == "MSG":
            if mydata.data.server is None:
                print("No connection has been made")
                return
            if mydata.data.server == mydata.serviceFamily.UDP_SERVICE:
                if mydata.data.bindAddr is None:
                    print("ERROR Please bind address first")
                    return
                else:
                    for t in mydata.data.trset:
                        t.sendto(data[1].encode(), addr=mydata.data.bindAddr)
            elif mydata.data.server == mydata.serviceFamily.TCPC_SERVICE:
                for t in mydata.data.trset:
                    if t.filetr.isRecv is True or t.filetr.isSend is True:
                        print("receiving or sending file, message is forbidden")
                        return
                    t.transport.write(data[1].encode())
            else:
                mydata.data.listAddr()
                print("<Please choose one option>")
                res = mydata.data.chooseAddr(await aioconsole.ainput("\n opt>"))
                if res is None:
                    print("IGNORE this command is skipped")
                else:
                    if res.isFile is True:
                        print("receiving file, message is forbidden")
                        return
                    res.write(data[1].encode())

        else:
            await self.next.execute(data)
        pass


class sendFile(Handle):
    def __init__(self) -> None:
        self.next = endparser()

    async def execute(self, data):
        if data[0] == "FILE":
            if mydata.data.server == mydata.serviceFamily.UDP_SERVICE:
                print("Not support")
                return
            elif mydata.data.server == mydata.serviceFamily.TCPC_SERVICE:
                for t in mydata.data.trset:
                    protocol = t
                pass
            else:
                mydata.data.listAddr()
                print("<Please choose one option>")
                res = mydata.data.chooseProt(await aioconsole.ainput("\n opt>"))
                if res is None:
                    print("IGNORE this command is skipped")
                else:
                    protocol = res
            # tran is the transport
            await protocol.filetr.sendFile(protocol.transport, data[1])

        else:
            await self.next.execute(data)


class endparser(Handle):
    async def execute(self, data):
        print("No such Command")
        return
