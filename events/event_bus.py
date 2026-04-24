from typing import Callable, Dict, List
from events.EventNames import EventNames

class EventBus:
    bus : Dict[EventNames, List[Callable]]

    def __init__(self):
        self.bus = {}

    def emit(self, event_type: EventNames, *args, **kwargs):
        for callback in self.bus.get(event_type, []):
            callback(*args, **kwargs)

    def subscribe(self, event_type: EventNames, callback: Callable):
        self.bus.setdefault(event_type, []).append(callback)

    def unsubscribe(self, event_type: EventNames, callback: Callable):
        if event_type in self.bus:
            self.bus[event_type] = [cb for cb in self.bus[event_type] if cb is not callback]

default_bus = EventBus()