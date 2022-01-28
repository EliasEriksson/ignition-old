from typing import *
import asyncio


def set_timeout(func: Callable[[], Awaitable[None]], duration: float) -> asyncio.Task:
    async def task():
        await asyncio.sleep(duration)
        await func()
    t = asyncio.create_task(task())
    return t


async def foo():
    print("hello!")


async def main():
    task = set_timeout(foo, 1)
    await task


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    # loop.run_forever()
    # asyncio.run(main())

