import asyncio
from unittest import TestCase
from unittest.mock import Mock


class AsyncTestCase(TestCase):

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    def coro(self, coro):
        return self.loop.run_until_complete(coro)

    def make_fut(self, result):
        fut = asyncio.Future(loop=self.loop)
        fut.set_result(result)
        return fut


class AsyncMock(Mock):
    def __await__(self):
        return iter([])


class AsyncContext(Mock):
    def __init__(self, *args, context=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._context = context

    async def __aenter__(self):
        return self._context

    async def __aexit__(self, exc_type, exc, tb):
        pass
