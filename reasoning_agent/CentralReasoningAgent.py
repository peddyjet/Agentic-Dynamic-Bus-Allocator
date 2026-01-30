from camel.agents import ChatAgent
from reasoning_agent.prompts.system_message import SYSTEM_MESSAGE

class CentralReasoningAgent:

    def __init__(self, model_factory):
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