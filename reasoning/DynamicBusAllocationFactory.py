from typing import Callable
from camel.models import BaseModelBackend
from reasoning.agent_interface.ComputationalAgentInterface import ComputationalAgentInterface
from reasoning.agents.AgentPool import AgentPool
from reasoning.agents.asa.AllocationSubAgent import AllocationSubAgent
from reasoning.agents.cra.CentralReasoningAgent import CentralReasoningAgent
from reasoning.agents.ihsa.IncidentHandlingSubAgent import IncidentHandlingSubAgent
from reasoning.environment.Environment import Environment
from reasoning.environment.IncidentStore import IncidentStore
from reasoning.models.agent_exposed_data import AgentExposedData
from reasoning.models.inputs import SimplifiedAllocationContext, IncidentHandlingReferral

class DynamicBusAllocationFactory:
    def __init__(self, ai_model : BaseModelBackend, environment : Environment,
                 asa_pool_size : int = 4, ihsa_pool_size : int = 4):
        self._ai_model = ai_model
        self._agent_data = AgentExposedData(environment=environment,
                                            incident_store=IncidentStore(environment))
        self._asa_pool_size = asa_pool_size
        self._ihsa_pool_size = ihsa_pool_size

    # noinspection PyProtectedMember
    def construct_instance(self):
        # Instantiate CRA
        cra = CentralReasoningAgent(self._ai_model, self._agent_data)

        # Instantiate ASA Pool
        asa_agents = [
            AllocationSubAgent(name=f"ASA_{i}", model=self._ai_model, data=self._agent_data)
            for i in range(self._asa_pool_size)
        ]
        asa_pool = (
            AgentPool[AllocationSubAgent, SimplifiedAllocationContext](agents=asa_agents,
                             step_function=lambda agent, props: agent.allocate_bus(props.trip_id, props.time)))

        # Instantiate IHSA Pool
        ihsa_agents = [
            IncidentHandlingSubAgent(name=f"IHSA_{i}", model=self._ai_model, data=self._agent_data)
            for i in range(self._ihsa_pool_size)
        ]

        ihsa_pool = (
            AgentPool[IncidentHandlingSubAgent, IncidentHandlingReferral](agents=ihsa_agents,
                             step_function=lambda agent, props: agent.handle_incident(props.incident,
                                                                                      time=self._agent_data.environment().current_time)))

        # Instantiate CAI
        cai = ComputationalAgentInterface(self._agent_data, asa_pool, ihsa_pool, cra)

        # Create default step complete
        step_complete_handler = self.__on_step_complete(cai)

        # Connect events
        ## CRA
        cra.refer_asa = cai._step_asa
        cra.refer_ihsa = cai._step_ihsa
        cra.on_step_complete_handlers.append(step_complete_handler)

        ## ASA
        for asa in asa_agents:
            asa.actuate_allox = cai._deploy_bus
            asa.cra_report = cai._cra_report
            asa.cancel_trip = cai._cancel_trip
            asa.on_step_complete_handlers.append(step_complete_handler)

        ## IHSA
        for ihsa in ihsa_agents:
            ihsa.cancel_trip = cai._cancel_trip
            ihsa.cra_report = cai._cra_report
            ihsa.remove_bus = cai._remove_bus
            ihsa.refer_asa = cai._step_asa
            ihsa.add_log = cai._add_log
            ihsa.on_step_complete_handlers.append(step_complete_handler)

        return cai

    @staticmethod
    def __on_step_complete(cai):
        # noinspection PyProtectedMember
        def res(agent, response):
            agent._log_message(str(response))
            cai.flush_delegation_requests()
        return res
