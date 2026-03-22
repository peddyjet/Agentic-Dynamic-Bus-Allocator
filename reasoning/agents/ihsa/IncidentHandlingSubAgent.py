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
                self.__allocate_bus_tool(),


            ]
        ), on_decided_step_handlers=[self.__on_step_complete], name=name)
        self.__environment = data.environment
        self.__incidents = data.incident_store

        # Events
        self.cra_report = None
        self.cancel_trip = None
        self.remove_bus = None
        self.refer_asa = None
        self.add_log = None

    def handle_incident(self, incident: str, time: datetime):
        prompt = json.dumps(self.__get_prompt(incident, time))
        future = asyncio.get_event_loop().create_future()
        self._queue.put_nowait(("step", prompt, future))
        self._ensure_worker_running()
        return future

    def reject(self, reason: IHSAReject, bus_id: int, trip_id: int):
        name = str(reason).format(bus_id=bus_id, trip_id=trip_id)
        future = asyncio.get_event_loop().create_future()
        self._queue.put_nowait(("step", name, future))
        self._ensure_worker_running()
        return future

    def __on_step_complete(self, _, result : IncidentResponse):
        self.add_log(result)
        if result.report is not None:
            self.cra_report(result.report)


    def __get_prompt(self, incident: str, time: datetime):
        return IncidentHandlingContext(
            incident=incident,
            services=list(map( lambda s: s.make_llm_friendly(), self.__environment.services.values())),
            incidents=self.__incidents.get_incidents(None, time),
            time=time.strftime("%H:%M"),
            bus_dict=self.__environment.find_buses_on_trips()
        )

    def __allocate_bus_tool(self):
        @FunctionTool
        def allocate_bus(trip_id : int, notes : str = ""):
            """
            Will delegate the allocation of a trip to an Allocation Subagent, passing notes as additional context.
            :param trip_id: The ID of the trip to allocate
            :param notes: Additional context to pass to the Allocation Subagent
            :return Nothing if everything went well, otherwise an error message
            """

            err = self.refer_asa(trip_id, False, notes)
            if err is not None: return str(err).format(trip_id=trip_id)
            return None
        return allocate_bus

    def __cancel_trip_tool(self):
        @FunctionTool
        def cancel_trip(trip_id : int):
            """
            Cancels the trip with the given trip ID.

            :param trip_id: ID of the trip to be cancelled.
            :return: Nothing if everything went well, otherwise an error message.
            """

            err = self.cancel_trip(trip_id)
            if err is not None: return str(err).format(trip_id=trip_id)
            return None
        return cancel_trip

    def __remove_bus_tool(self):
        @FunctionTool
        def remove_bus(bus_id: int):
            """
            Relives a bus from all of its trips.

            :param bus_id: ID of the bus to be relieved.
            :return: Nothing if everything went well, otherwise an error message.
            """

            err = self.remove_bus(bus_id)
            if err is not None: return str(err).format(bus_id=bus_id)
            return None
        return remove_bus
