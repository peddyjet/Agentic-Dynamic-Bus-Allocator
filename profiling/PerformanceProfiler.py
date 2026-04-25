from typing import Dict

from pydantic import BaseModel
from reasoning.agent_interface.BusAllocatorProtocol import BusAllocatorProtocol
from reasoning.environment.Environment import Environment
from events.event_bus import default_bus
from events.EventNames import EventNames


class PerformanceProfiler:
    class Stats(BaseModel):
        min : float
        max : float
        count : int
        mean : float
        m2 : float

    def __init__(self, environment : Environment, cai : BusAllocatorProtocol):
        self.__environment = environment
        self.__cai = cai
        self.__speed_stats : Dict[str, PerformanceProfiler.Stats] = {}

        self.__abandonment_stats: PerformanceProfiler.Stats = PerformanceProfiler.Stats(min=0, max=0, count=0, mean=0, m2=0)
        self.__abandonment_sum = 0

        self.__interline_count = 0

        self.__cancellation_count = 0

        self.__delay_stats: PerformanceProfiler.Stats = PerformanceProfiler.Stats(min=0, max=0, count=0, mean=0, m2=0)
        self.__delay_sum = 0.0

        default_bus.subscribe(EventNames.STEP_COMPLETE, self.__on_step_complete)
        default_bus.subscribe(EventNames.ABANDONED_PASSENGER, self.__on_abandoned_passenger)
        default_bus.subscribe(EventNames.INTERLINED, self.__on_interlined)
        default_bus.subscribe(EventNames.TRIP_CANCELLED, self.__on_trip_cancelled)
        default_bus.subscribe(EventNames.DELAY_RECORDED, self.__on_delay_recorded)

    def get_speed_stats(self): return self.__speed_stats
    def get_abandonment_stats(self): return self.__abandonment_stats
    def get_abandonment_sum(self): return self.__abandonment_sum
    def get_interline_count(self): return self.__interline_count
    def get_cancellation_count(self): return self.__cancellation_count
    def get_delay_stats(self): return self.__delay_stats
    def get_delay_sum(self): return self.__delay_sum

    def __on_interlined(self): self.__interline_count += 1

    def __on_trip_cancelled(self): self.__cancellation_count += 1

    def __on_delay_recorded(self, delay_seconds: float):
        self.__delay_sum += delay_seconds
        s = self.__delay_stats
        new_count = s.count + 1
        delta = delay_seconds - s.mean
        new_mean = s.mean + delta / new_count
        delta_from_new_mean = delay_seconds - new_mean
        self.__delay_stats = PerformanceProfiler.Stats(
            min=delay_seconds if s.count == 0 else min(s.min, delay_seconds),
            max=delay_seconds if s.count == 0 else max(s.max, delay_seconds),
            count=new_count,
            mean=new_mean,
            m2=s.m2 + delta * delta_from_new_mean,
        )

    def __on_abandoned_passenger(self, count: int):
        self.__abandonment_sum += count
        s = self.__abandonment_stats
        new_count = s.count + 1
        delta = count - s.mean
        new_mean = s.mean + delta / new_count
        delta_from_new_mean = count - new_mean
        self.__abandonment_stats = PerformanceProfiler.Stats(
            min=count if s.count == 0 else min(s.min, count),
            max=count if s.count == 0 else max(s.max, count),
            count=new_count,
            mean=new_mean,
            m2=s.m2 + delta * delta_from_new_mean,
        )

    def __on_step_complete(self, agent: str, duration_ms: float):
        if agent not in self.__speed_stats:
            self.__speed_stats[agent] = PerformanceProfiler.Stats(
                min=duration_ms, max=duration_ms, count=1, mean=duration_ms, m2=0.0
            )
            return

        entry = self.__speed_stats[agent]

        count = entry.count + 1
        delta = duration_ms - entry.mean

        new_mean = entry.mean + delta / count
        delta_from_new_mean = duration_ms - new_mean

        self.__speed_stats[agent] = PerformanceProfiler.Stats(
            min=min(entry.min, duration_ms),
            max=max(entry.max, duration_ms),
            count=count,
            mean=new_mean,
            m2=entry.m2 + delta * delta_from_new_mean,
        )