import myparser
from mydata import data
import aioconsole
import asyncio

# global
maininput = None


class app:
    async def chat():
        pass


class Main:
    async def main():
        data.reset()
        gpt = myparser.exit()
        while True:
            await gpt.execute((await aioconsole.ainput(">")).split(maxsplit=1))
        pass


asyncio.run(main=Main.main())
