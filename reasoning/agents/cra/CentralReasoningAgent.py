import asyncio
import json
from datetime import datetime
from typing import List
from camel.agents import ChatAgent
from camel.models import BaseModelBackend
from camel.toolkits import FunctionTool
from reasoning.agents.QueueAgent import QueueAgent
from reasoning.agents.prompts.cra_rejects import CRAReject
from reasoning.agents.prompts.system_messages import SYSTEM_MESSAGES
from reasoning.agents.tools.environment_tools import environment_tools, allocated_buses_tool
from reasoning.models.agent_exposed_data import AgentExposedData
from reasoning.models.inputs import CRAInput, IncidentHandlingReferral


class CentralReasoningAgent(QueueAgent):
    def __init__(self, model: BaseModelBackend, data: AgentExposedData):
        super().__init__(agent=ChatAgent(
            system_message=SYSTEM_MESSAGES["cra"],
            model=model,
            tools=environment_tools(self) + [allocated_buses_tool(self),
                                             self.__incident_tool(),
                                             self.__allocate_buses_tool(),
                                             self.__log_incident_tool()]
        ), on_decided_step_handlers=[], name="CRA")
        self._environment = data.environment
        self._incidents = data.incident_store

        # Events
        self.refer_asa = None
        self.refer_ihsa = None

    def allocate_bus(self, trip_ids: List[int], time: datetime):
        self._log_message(f"Received allocation request for {trip_ids} at {time}")
        cra_input = CRAInput(content=f"[ALLOX] {" ".join(str(i) for i in trip_ids)}", time=time.isoformat())
        prompt = json.dumps(cra_input.model_dump())
        future = self._create_future()
        self._enqueue(("step", prompt, future))
        return future

    def send_log(self, log : str, time: datetime, by_agent : bool = False):
        self._log_message(f"Received log message: {log} at {time}")
        cra_input = CRAInput(content=f"[{'LOG' if not by_agent else 'REPORT'}] {log}", time=time.isoformat())
        prompt = json.dumps(cra_input.model_dump())
        future = self._create_future()
        self._enqueue(("step", prompt, future))
        return future

    def reject(self, reason: CRAReject, trip_id: int):
        self._log_message(f"Received rejection: {reason} for trip {trip_id}")
        name = str(reason).format(trip_id=trip_id)
        future = self._create_future()
        self._enqueue(("step", name, future))
        return future

    def __incident_tool(self):
        @FunctionTool
        def incidents():
            """
            Provides a list of all incidents that are in the incident store
            :return: every time-stamped incident in the incident store
            """
            self._log_message("Invoked incidents")
            return self._incidents().get_incidents() or "no incidents found"
        return incidents

    def __allocate_buses_tool(self):
        @FunctionTool
        def allocate_buses(trip_ids : str, notes : str = ""):
            """
            Will delegate the allocation of all trips specified to the Allocation Subagent Pool, passing notes as additional context.
            :param trip_ids: The IDs of the trip to allocate, separated by commas with no spaces in between.
            :param notes: Additional context to pass to the Allocation Subagent
            :return Nothing if everything went well, otherwise an error message
            """
            self._log_message(f"Invoked allocate_buses with trip_ids {trip_ids} and notes {notes}")
            trips = []
            for trip_str in trip_ids.split(','):
                try:
                    trip_id = int(trip_str.strip())
                    trips.append(trip_id)
                except:
                    return str(CRAReject.TripsParsedIncorrectly).format(trip_ids=trip_ids)

            for trip_id in trips:
                err = self.refer_asa(trip_id, True, notes)
                if err is not None: return str(err).format(trip_id=trip_id)
            return "success"
        return allocate_buses


    def __log_incident_tool(self):
        @FunctionTool
        def log_incident(incident : str):
            """
            Will delegate the reporting and handling of an incident to an Incident Handling Subagent
            :param incident: a concise description of the incident
            :return Nothing if everything went well, otherwise an error message
            """
            self._log_message(f"Invoked log_incident with incident {incident}")
            self.refer_ihsa(IncidentHandlingReferral(incident=incident))
            return "success"
        return log_incident