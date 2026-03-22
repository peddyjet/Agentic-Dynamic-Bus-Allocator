from typing import Any, List
import asyncio
from reasoning.agents.AgentPool import AgentPool
from reasoning.agents.asa.AllocationSubAgent import AllocationSubAgent
from reasoning.agents.cra.CentralReasoningAgent import CentralReasoningAgent
from reasoning.agents.ihsa.IncidentHandlingSubAgent import IncidentHandlingSubAgent
from reasoning.agents.prompts.asa_rejects import CAPACITY_ERROR_THRESHOLD, ASAReject
from reasoning.agents.prompts.cra_rejects import CRAReject
from reasoning.agents.prompts.ihsa_rejects import IHSAReject
from reasoning.models.agent_exposed_data import AgentExposedData
from reasoning.models.incident import Incident, TimeStampedIncident
from reasoning.models.inputs import SimplifiedAllocationContext, IncidentHandlingReferral


class ComputationalAgentInterface:
    """
    A computational interface for interacting with the Central Reasoning Agent (CRA) and its
    Allocation Sub Agents (ASAs), acting as the endpoint for all calls to get buses allocated and for
    incident reporting.
    """
    def __init__(self, 
                data : AgentExposedData,
                asa_pool : AgentPool[AllocationSubAgent, SimplifiedAllocationContext],
                ihsa_pool : AgentPool[IncidentHandlingSubAgent, IncidentHandlingReferral],
                cra : CentralReasoningAgent):
        self._data = data
        self._asa_pool = asa_pool
        self._ihsa_pool = ihsa_pool
        self._cra = cra
        pass

    """
    The following functions are used to interact with the agentic system, as a human or simulator.
    """
    async def allocate_buses(self, trip_ids : List[int]):
        """
        Allocates the buses of the given trip IDs
        :param trip_ids: The trip IDs to allocate buses for
        """
        self._cra.allocate_bus(trip_ids, self._data.environment.current_time)

        while self._cra.is_working():
            await asyncio.sleep(0.05)

    async def send_log(self, msg : str):
        """
        Sends a log message to the CRA, allowing the CRA to write to the incident store, allocate,
         reallocate, or cancel services as needed.
        :param msg: The log message to send
        """

        self._cra.send_log(msg, self._data.environment.current_time)

        while self._cra.is_working():
            await asyncio.sleep(0.05)

    """
    The following functions are used to interact with other agents, and are called through programmatic tools.
    """
    def _step_asa(self, trip_id : int, is_cra : bool, note : str):
        """
        Steps an ASA in the ASA pool, allowing it to allocate buses or cancel the trip.
        This is to be provisioned to the CRA and IHSAs.
        :param trip_id: The trip ID to allocate
        :param is_cra: Whether the request is coming from the CRA or IHSA
        :param note: A note to give to the ASA
        :returns None if the request can be made, or a reject message upon failure
        """

        trip = self._data.environment.trips.get(trip_id)
        if trip is None:
            return IHSAReject.TripDoesntExist if not is_cra else CRAReject.TripDoesntExist
        self._asa_pool.step(SimplifiedAllocationContext(trip_id=trip_id,
                                                        time=self._data.environment.current_time.isoformat(),
                                                        note=note))
        return None

    def _step_ihsa(self, referral : IncidentHandlingReferral):
        """
        Steps an IHSA in the IHSA pool, allowing it to handle an incident.
        This is to be provisioned exclusively to the CRA.
        :param referral: The incident referral to give to the IHSA
        """
        self._ihsa_pool.step(referral)

    def _cra_report(self, report : str):
        """
        Reports an incident to the CRA, given by a subagent.
        :param report: The report to submit
        """
        self._cra.send_log(report, self._data.environment.current_time, True)


    """
    The following functions are used to interact with the environment, and are called by programmatic tools inside the 
    various agents.
    """
    def _deploy_bus(self, bus_id : int, trip_id : int):
        """
        Deploys a bus to the environment, based off a decision made by an ASA.
        Returns nothing on a success, or a reject message upon failure.
        :param bus_id: The bus ID to deploy
        :param trip_id: The trip ID to deploy to
        """
        validation = self.__validate_bus_allocation(bus_id, trip_id)
        if validation is not None: return validation

        bus = self._data.environment.buses[bus_id]

        if bus.current_trip_id_queue is None:
            bus.current_trip_id_queue = []
        
        bus.current_trip_id_queue.append(trip_id)

        return None

    def _remove_bus(self, bus_id : int):
        """
            Removes a bus from passenger service, based off a decision made by an IHSA.
            :param bus_id: The bus ID to relieve
            :returns: None if the removal is valid, otherwise an error message.
        """
        bus = self._data.environment.buses.get(bus_id)
        if bus is None:
            return IHSAReject.BusDoesntExist
        bus.current_trip_id_queue = []
        return None

    def _cancel_trip(self, trip_id : int):
        """
            Cancels a trip, based off a decision made by an IHSA.
            :param trip_id: The trip ID to cancel
            :returns: None if the cancellation is valid, otherwise an error message.
        """
        trip = self._data.environment.trips.get(trip_id)
        if trip is None:
            return IHSAReject.TripDoesntExist

        for bus in self._data.environment.buses.values():
            if trip_id in bus.current_trip_id_queue:
                bus.current_trip_id_queue.remove(trip_id)

        return None
    
    def _add_log(self, incident : Incident):
        self._data.incident_store.add_incident(TimeStampedIncident(
            summary=incident.summary,
            description=incident.description,
            actions=incident.actions,
            trips=incident.trips,
            buses=incident.buses,
            global_=incident.global_,
            expiry=incident.expiry,
            time=self._data.environment.current_time
        ))

    def __validate_bus_allocation(self, bus_id : int, trip_id : int):
        """
            Validates the allocation of buses to services, ensuring that the allocation is valid and
            that the buses are available for deployment.
            :param bus_id: The bus ID to validate
            :param trip_id: The trip ID to validate
            :returns: None if the allocation is valid, otherwise an error message.
        """
        
        bus = self._data.environment.buses.get(bus_id)
        if bus is None:
            return ASAReject.BusDoesntExist

        if len(bus.faults) > 0:
            return ASAReject.BusWithdrawn
        
        trip = self._data.environment.trips.get(trip_id)
        if trip is None:
            raise IndexError("No trips were found. This should not happen at line 77.")
        
        if bus.capacity < trip.average_passenger_loading() * CAPACITY_ERROR_THRESHOLD:
            return ASAReject.BusTooSmall

        if len(trip.calling_points) > 0 and bus.current_trip_id_queue is not None:
            for trip_queue in bus.current_trip_id_queue:
                queued_trip = self._data.environment.trips[trip_queue]
                if len(queued_trip.calling_points) == 0:
                    continue

                if queued_trip.calling_points[0].timestamp < trip.calling_points[-1].timestamp and \
                        queued_trip.calling_points[-1].timestamp > trip.calling_points[0].timestamp:
                    return ASAReject.BusConflict,trip_queue

        return None