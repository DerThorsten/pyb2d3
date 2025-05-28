import asyncio
import time


# an async contex t manager to run a block of code
# and then async sleep for a given time
# st. the total runtime is equal to an expected time


class WaitIfNeeded:
    def __init__(self, expected_time: float):
        self.expected_time = expected_time
        self.start_time = None

    async def __aenter__(self):
        self.start_time = time.time()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        elapsed_time = time.time() - self.start_time
        sleep_time = max(0, self.expected_time - elapsed_time)
        await asyncio.sleep(sleep_time)
        return False
