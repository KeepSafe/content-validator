import asyncio
from unittest import TestCase


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
