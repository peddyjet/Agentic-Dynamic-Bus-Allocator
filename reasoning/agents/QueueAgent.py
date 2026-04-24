import asyncio
import threading
import traceback
from typing import Callable, Any, List, Type
from camel.agents import ChatAgent
from pydantic import BaseModel
from events.event_bus import default_bus
from events.EventNames import EventNames

class QueueAgent:
    def __init__(self, agent : ChatAgent, name : str, on_decided_step_handlers : List[Callable[[Any, Any], None]],
                 agent_response : Type[BaseModel] | None = None, stateless : bool = False):
        self._agent = agent
        self._stateless = stateless
        self._queue: asyncio.Queue = asyncio.Queue()
        self._worker_task = None
        self._name = name
        self.on_step_complete_handlers = on_decided_step_handlers
        self._agent_response = agent_response
        self._busy = False
        self._pending = 0
        self._loop = asyncio.new_event_loop()
        self._loop_lock = threading.Lock()

    def _log_message(self, msg: str):
        default_bus.emit(EventNames.LOG_MESSAGE, source=self._name, message=msg)

    def _create_future(self) -> asyncio.Future:
        return self._loop.create_future()

    def _enqueue(self, item):
        self._pending += 1
        self._ensure_worker_running()
        self._loop.call_soon_threadsafe(self._queue.put_nowait, item)

    def _ensure_worker_running(self):
        with self._loop_lock:
            if not self._loop.is_running():
                threading.Thread(target=self._loop.run_forever, daemon=True).start()
            if self._worker_task is None or self._worker_task.done():
                self._worker_task = asyncio.run_coroutine_threadsafe(
                    self._process_queue(), self._loop
                )

    async def _process_queue(self):
        while True:
            kind, payload, future = await self._queue.get()
            self._busy = True
            default_bus.emit(EventNames.AGENT_BUSY, agent=self._name, queue_depth=self._pending)
            try:
                if self._stateless:
                    self._agent.reset()
                raw_result = self._agent.step(payload() if callable(payload) else payload, self._agent_response)
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
                self._pending -= 1
                default_bus.emit(EventNames.AGENT_BUSY, agent=self._name, queue_depth=self._pending)

    def is_working(self):
        return self._pending > 0

    def queue_size(self):
        return self._pending

    def get_name(self):
        return self._name

    def on_step_complete(self, result):
        for handler in self.on_step_complete_handlers:
            handler(self, result)
