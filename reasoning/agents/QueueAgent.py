import asyncio
from typing import Callable, Any, List
from camel.agents import ChatAgent


class QueueAgent:
    def __init__(self, agent : ChatAgent, name : str, on_decided_step_handlers : List[Callable[[Any, Any], None]]):
        self._agent = agent
        self._queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: asyncio.Task | None = None
        self._name = name
        self._log_message = lambda msg: print(f"[{self._name.upper()}] {msg}")
        self.on_step_complete_handlers = on_decided_step_handlers

    def _ensure_worker_running(self):
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._process_queue())

    async def _process_queue(self):
        while not self._queue.empty():
            kind, payload, future = await self._queue.get()
            try:
                result = await self._agent.astep(payload)
                if not future.done():
                    future.set_result(result)
                self.on_step_complete(result)
            except Exception as e:
                if not future.done():
                    future.set_exception(e)
                self._log_message(f"Error processing task: {e}")
            finally:
                self._queue.task_done()

    def is_working(self):
        return not self._queue.empty() or (
                self._worker_task is not None and not self._worker_task.done()
        )

    def queue_size(self):
        return self._queue.qsize()

    def get_name(self):
        return self._name

    def on_step_complete(self, result):
        for handler in self.on_step_complete_handlers:
            handler(self, result)