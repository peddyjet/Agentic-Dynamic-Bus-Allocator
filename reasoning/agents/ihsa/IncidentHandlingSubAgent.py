import asyncio
import json
from datetime import datetime
from camel.agents import ChatAgent
from camel.models import BaseModelBackend
from camel.toolkits import FunctionTool
from reasoning.agents.QueueAgent import QueueAgent
from reasoning.agents.prompts.asa_rejects import ASAReject
from reasoning.agents.prompts.ihsa_rejects import IHSAReject
from reasoning.agents.prompts.system_messages import SYSTEM_MESSAGES
import reasoning.agents.tools.environment_tools as e
from reasoning.models.agent_exposed_data import AgentExposedData
from reasoning.models.inputs import AllocationContext, IncidentHandlingContext
from reasoning.models.responses import IncidentResponse

class IncidentHandlingSubAgent(QueueAgent):
    def __init__(self, name: str, model: BaseModelBackend, data: AgentExposedData):
        super().__init__(agent=ChatAgent(
            system_message=SYSTEM_MESSAGES["ihsa"],
            model=model,
            tools=[
                e.trip_info_tool(self),
                e.calculate_distance_tool(self),
                e.trips_tool(self),
                self.__withdraw_bus_tool(),
                self.__allocate_bus_tool(),
                self.__remove_bus_tool(),
                self.__cancel_trip_tool()
            ]
        ), on_decided_step_handlers=[self.__on_step_complete], name=name, agent_response=IncidentResponse)
        self._environment = data.environment
        self._incidents = data.incident_store

        # Events
        self.cra_report = None
        self.cancel_trip = None
        self.remove_bus = None
        self.withdraw_bus = None
        self.refer_asa = None
        self.add_log = None

    def handle_incident(self, incident: str, time: datetime):
        prompt = self.__get_prompt(incident, time).model_dump_json()
        future = self._create_future()
        self._queue.put_nowait(("step", prompt, future))
        self._ensure_worker_running()
        return future

    def reject(self, reason: IHSAReject, bus_id: int, trip_id: int):
        name = str(reason).format(bus_id=bus_id, trip_id=trip_id)
        future = self._create_future()
        self._queue.put_nowait(("step", name, future))
        self._ensure_worker_running()
        return future

    def __on_step_complete(self, _, result : IncidentResponse):
        self.add_log(result.incident)


    def __get_prompt(self, incident: str, time: datetime):
        return IncidentHandlingContext(
            incident=incident,
            services=list(map(lambda s: s.make_llm_friendly(), self._environment().services.values())),
            incidents=self._incidents().get_incidents(None, time),
            time=time.isoformat(),
            bus_dict=self._environment().find_buses_on_trips()
        )

    def __allocate_bus_tool(self):
        @FunctionTool
        def allocate_bus(trip_id : int, notes : str = ""):
            """
            Will delegate the allocation of a trip to an Allocation Subagent, passing notes as additional context.
            :param trip_id: The ID of the trip to allocate
            :param notes: Additional context to pass to the Allocation Subagent
            :return  A generic success message if everything went well, otherwise an error message
            """

            self._log_message(f"Invoked allocate_bus with trip_id {trip_id} and notes {notes}")
            err = self.refer_asa(trip_id, False, notes)
            if err is not None: return str(err).format(trip_id=trip_id)
            return "success"
        return allocate_bus

    def __cancel_trip_tool(self):
        @FunctionTool
        def cancel_trip(trip_id : int):
            """
            Cancels the trip with the given trip ID.

            :param trip_id: ID of the trip to be cancelled.
            :return:  A generic success message if everything went well, otherwise an error message.
            """

            self._log_message(f"Invoked cancel_trip with trip_id {trip_id}")
            err = self.cancel_trip(trip_id)
            if err is not None: return str(err).format(trip_id=trip_id)
            return "success"
        return cancel_trip

    def __remove_bus_tool(self):
        @FunctionTool
        def remove_bus(bus_id: int, trip_id : int):
            """
            Relives a bus from the trip_id specified.

            :param bus_id: ID of the bus to be relieved from the trip.
            :param trip_id: ID of the trip to remove the bus from.
            :return: A generic success message if everything went well, otherwise an error message.
            """

            self._log_message(f"Invoked remove_bus with bus_id {bus_id} and trip_id {trip_id}")
            err = self.remove_bus(bus_id, trip_id)
            if err is not None: return str(err).format(bus_id=bus_id)
            return "Success"
        return remove_bus

    def __withdraw_bus_tool(self):
        @FunctionTool
        def withdraw_bus(bus_id: int):
            """
            Withdraws a bus from the network for the rest of the day. This automatically relieves it from all its trips.

            :param bus_id: ID of the bus to be withdrawn from the network.
            :return: A generic success message if everything went well, otherwise an error message.
            """

            self._log_message(f"Invoked withdraw_bus with bus_id {bus_id}")
            err = self.withdraw_bus(bus_id)
            if err is not None: return str(err).format(bus_id=bus_id)
            return "Success"
        return withdraw_bus
