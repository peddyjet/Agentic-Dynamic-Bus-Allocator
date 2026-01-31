from camel.agents import ChatAgent
from camel.models import BaseModelBackend
from reasoning.orchestration.Environment import Environment
from reasoning.prompts.system_message import SYSTEM_MESSAGE

class AgentOrchestrator:

    def __init__(self, model_factory : BaseModelBackend, environment : Environment):
        self.__environment = environment
        self.__model_factory = model_factory
        self.__agent = ChatAgent(
            system_message=SYSTEM_MESSAGE,
            model=self.__model_factory
        )

        pass

    def get_bus_allox(self, timetable_entry):
        response = self.__agent.step(timetable_entry)
        print(response.msg.content)
        pass