import asyncio
import sys
import traceback
from typing import Callable, Any, List, Type
from camel.agents import ChatAgent
from pydantic import BaseModel

class QueueAgent:
    def __init__(self, agent : ChatAgent, name : str, on_decided_step_handlers : List[Callable[[Any, Any], None]],
                 agent_response : Type[BaseModel] | None = None):
        self._agent = agent
        self._queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: asyncio.Task | None = None
        self._name = name
        self._log_message = self.__default_logging_behavior
        self.on_step_complete_handlers = on_decided_step_handlers
        self._agent_response = agent_response
        self._busy = False

        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

    def __default_logging_behavior(self, msg):
        print(f"[{self._name.upper()}] {msg}", flush=True)
        sys.stdout.flush()

    def _create_future(self) -> asyncio.Future:
        return self._loop.create_future()

    def _ensure_worker_running(self):
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = self._loop.create_task(self._process_queue())

    async def _process_queue(self):
        while True:
            kind, payload, future = await self._queue.get()
            self._busy = True
            try:
                raw_result = self._agent.step(payload, self._agent_response)
                result = getattr(raw_result.msgs[0], "parsed", None) or getattr(raw_result.msgs[0], "content", None) or raw_result
                if not future.done():
                    future.set_result(result)
                self.on_step_complete(result)
            except Exception as e:
                if not future.done():
                    future.set_exception(e)
                self._log_message(f"Error processing task: {e}")
                self._log_message(traceback.format_exc())
            finally:
                self._queue.task_done()
                self._busy = False

    def is_working(self):
        return not self._queue.empty() or self._busy

    def queue_size(self):
        return self._queue.qsize()

    def get_name(self):
        return self._name

    def on_step_complete(self, result):
        for handler in self.on_step_complete_handlers:
            handler(self, result)