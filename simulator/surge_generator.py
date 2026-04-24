from datetime import timedelta
from reasoning.agent_interface.ComputationalAgentInterface import ComputationalAgentInterface
from reasoning.environment.Environment import Environment

SURGE_REASONS = [
    "a football match ending",
    "a conference ending",
    "a school trip using the bus without prior notice",
    "a train cancellation",
    "several families turning up to the bus stop at the same time",
]

SURGE_MIN = 14
SURGE_MAX = 120

def surge_generator(cai: ComputationalAgentInterface, environment: Environment,
                    rand1: float, rand2: float, rand3: float):
    non_depot = [s for s in environment.stops.values() if not s.is_depot]
    if not non_depot:
        return

    reason = SURGE_REASONS[int((len(SURGE_REASONS) - 1) * rand1)]
    number_of_pax = int(SURGE_MIN + (SURGE_MAX - SURGE_MIN) * rand2)
    stop = non_depot[int((len(non_depot) - 1) * rand3)]

    # Find the next upcoming trip serving this stop
    lookahead = timedelta(hours=2)
    upcoming = [
        t for t in environment.trips.values()
        if environment.current_time <= t.end_time(as_date=True) <= environment.current_time + lookahead
        and any(cp.stop.id == stop.id for cp in t.calling_points)
    ]
    upcoming.sort(key=lambda t: t.start_time(as_date=True))
    affected_trip = upcoming[0] if upcoming else None

    if affected_trip is not None:
        cp = next((c for c in affected_trip.calling_points if c.stop.id == stop.id), None)
        if cp is not None:
            cp.waiting_passengers += number_of_pax

    route_info = f" on route {affected_trip.service.route_name} (Trip ID {affected_trip.id})" if affected_trip else ""
    prompt = (f"There has been {reason}, at {stop.name} (Stop ID {stop.id}){route_info},"
              f" resulting in {number_of_pax} additional passengers waiting")
    cai.send_log(prompt)