import myparser
import aiofiles
import asyncio
import aioconsole
from enum import IntEnum
import weakref
import os


class serviceFamily(IntEnum):
    UDP_SERVICE: int = 1
    TCPC_SERVICE: int = 2


async def tipinputaddr(target: str):
    msg: str = await aioconsole.ainput(f"<Please input {target} address>")
    msg = msg.split(":")
    return msg[0], int(msg[1])


class Data:
    trset = set()
    server = None
    bindAddr = None
    mapDict = dict()

    def reset(self):
        self.trset.clear()
        self.server = None
        self.mapDict.clear()
        self.bindAddr = None

    def listAddr(self):
        self.mapDict.clear()
        idx = 0
        for c in self.trset:
            t = c.transport
            self.mapDict[idx] = c
            print(idx, " - ", t.get_extra_info("peername"))
            idx += 1
        print("-1 - Ignore this command")

    def chooseAddr(self, opt):
        opt = int(opt)
        if opt == -1:
            return None
        return self.mapDict[opt].transport

    def chooseProt(self, opt):
        opt = int(opt)
        if opt == -1:
            return None
        return self.mapDict[opt]


data = Data()


class fileTransmit:
    def __init__(self) -> None:
        self.isRecv: bool = False
        self.isSend: bool = False

    async def firstReceive(self, trans, filename: str):
        # os.remove os.path.exist
        # 第一次接受到 "FILE 文件名"
        try:
            if os.path.exists("download") is False:
                os.mkdir("download")
            self.filename = filename.rsplit("/", maxsplit=1)[-1]

            pin = input(
                f"FILE {self.filename} from {trans.addr} , you need to type one enter first to type [yes/no]"
            )
            if pin == "no":
                print("stop received")
                trans.transport.write("STOPRECV".encode())

            if os.path.exists(f"download/{self.filename}") is True:
                pin = await aioconsole.ainput(
                    f"File {self.filename} has been existed, delete it first? [yes/no]"
                )
                if pin == "yes":
                    os.remove(f"download/{self.filename}")
                else:
                    print("File is existed, stop received")
                    trans.write("STOPRECV".encode())
            self.isRecv = True
            trans.transport.write("CONTRECV".encode())

        except EOFError:
            print("stop received")
            trans.transport.write("STOPRECV".encode())
        pass

    async def continueReceive(self, protocol, data):
        # 之后就是文件的二进制串
        if data.decode()[-4:] == "RECV":
            return
        try:
            msg = data.decode()
            if msg == "STOPSEND":
                # 停止发送
                print("stop received")
                os.remove(f"download/{self.filetr.filename}")
                self.isRecv = False
                return
            elif msg == "END":
                protocol.transport.write("CONTRECV".encode())
                self.isRecv = False
                print(f"FILE {self.filename} has storage successfully")
                return
                pass
            else:
                with open(f"download/{self.filename}", "ab") as fout:
                    fout.write(data)
                protocol.transport.write("CONTRECV".encode())
                pass
        except EOFError:
            protocol.transport.write("STOPRECV".encode())
            self.isRecv = False
            print("stop received")
            os.remove(f"download/{self.filename}")

    async def sendFile(self, trans, file: str):
        # 发送文件
        if os.path.exists(file) is False:
            print("No this file existed")
            return

        print("File is sending")
        trans.write(f"FILE {file}".encode())
        self.isSend = True
        self.sendFlag = "PAUSE"

        try:
            async with aiofiles.open(file, "rb") as fin:
                chunk = await fin.read(64 * 1024)
                while chunk:
                    while self.sendFlag == "PAUSE":
                        await asyncio.sleep(0.0001)
                        pass
                    if self.sendFlag == "STOPSEND":
                        return

                    self.sendFlag = "PAUSE"
                    trans.write(chunk)
                    chunk = await fin.read(64 * 1024)

                while self.sendFlag == "PAUSE":
                    await asyncio.sleep(0.0001)
                    pass
                trans.write("END".encode())
                self.isSend = False
                return

        except EOFError:
            trans.write("STOPSEND".encode())
            print("stop transmit")
        pass
