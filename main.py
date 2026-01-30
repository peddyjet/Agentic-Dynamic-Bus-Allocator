from dotenv import load_dotenv
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
from camel.configs import ChatGPTConfig
from reasoning_agent.CentralReasoningAgent import CentralReasoningAgent

load_dotenv()

model = ModelFactory.create(
    model_platform=ModelPlatformType.OPENAI,
    model_type=ModelType.GPT_5_MINI,
    model_config_dict=ChatGPTConfig().as_dict(),
)
with open("prompt.txt", "r", encoding="utf-8") as f:
    msg = f.read()
    CentralReasoningAgent(model).get_bus_allox(msg)