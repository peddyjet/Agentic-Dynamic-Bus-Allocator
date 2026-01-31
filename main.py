import datetime
from dotenv import load_dotenv
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
from camel.configs import ChatGPTConfig
from bustimes_importer.environment.EnvironmentFactory import EnvironmentFactory
from reasoning.orchestration.AgentOrchestator import AgentOrchestrator

load_dotenv()

# Select what LLM you want to use as the central reasoning agent
model = ModelFactory.create(
    model_platform=ModelPlatformType.OPENAI,
    model_type=ModelType.GPT_5_MINI,
    model_config_dict=ChatGPTConfig().as_dict(),
)

# If using the BusTimes API, you may use the following code snippet to generate the reasoning
# environment and ground truths. If you are doing so, please ensure the buses you are referencing
# are also inside additional_bus_specs.json
national_operator_code = "BRYL"
environment_factory = EnvironmentFactory(national_operator_code, datetime.datetime(
    year=2026,
    month=1,
    day=30,
))
environment = environment_factory.get_environment()

with open("prompt.txt", "r", encoding="utf-8") as f:
    msg = f.read()
    AgentOrchestrator(model, environment).get_bus_allox(msg)