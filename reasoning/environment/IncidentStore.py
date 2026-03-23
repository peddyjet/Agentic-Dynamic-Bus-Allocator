from datetime import datetime, timedelta
from typing import List, Optional
from reasoning.environment.Environment import Environment
from reasoning.models.incident import Incident, TimeStampedIncident


class IncidentStore:
    def __init__(self, environment : Environment):
        self._incidents: List[TimeStampedIncident] = []
        self._environment = environment

    def add_incident(self, incident: TimeStampedIncident):
        self._incidents.append(incident)

    def get_incidents(self, trip_id: Optional[int] = None, date: Optional[datetime] = None):
        incidents = list(self._incidents)

        if trip_id is not None:
            incidents.extend(self._filter_by_trip_id(trip_id))

        if date is not None:
            incidents.extend(self._filter_by_date(date))

        unique = []
        seen = set()
        for incident in incidents:
            key = (incident.summary, incident.time)
            if key not in seen:
                seen.add(key)
                unique.append(incident)

        return unique

    def _filter_by_trip_id(self, trip_id : int):
        trips = []
        for incident in self._incidents:
            if incident.global_:
                trips.append(incident)
                continue
            for affected_trip_id in incident.trips:
                affected_trip = self._environment.trips[affected_trip_id]
                if affected_trip.id == trip_id:
                    trips.append(incident)
                    break

        return trips

    def _filter_by_date(self, date : datetime):
        trips = []
        for incident in self._incidents:
            if datetime.fromisoformat(incident.time) < date + timedelta(hours=incident.expiry):
                trips.append(incident)
        return trips

