import datetime
from dotenv import load_dotenv
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
from camel.configs import ChatGPTConfig
from bustimes_importer.environment.EnvironmentFactory import EnvironmentFactory
from cli import run_cli
from reasoning.orchestration.AgentOrchestator import AgentOrchestrator

# Create the methods for running the program on start
def run_simulator(orchestrator : AgentOrchestrator):
    raise NotImplementedError("Not implemented in this version")

def main():
    print("Loading Dotenv... (1/4)")
    load_dotenv()

    # Select what LLM you want to use as the central reasoning agent
    print("Loading Model... (2/4)")
    model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.GPT_5_MINI,
        model_config_dict=ChatGPTConfig().as_dict(),
    )

    # If using the BusTimes API, you may use the following code snippet to generate the reasoning
    # environment and ground truths. If you are doing so, please ensure the buses you are referencing
    # are also inside additional_bus_specs.json
    print("Loading Environment... (3/4)")
    national_operator_code = "BRYL"
    environment_factory = EnvironmentFactory(national_operator_code, datetime.datetime(
        year=2026,
        month=1,
        day=30,
    ), log=True)
    environment = environment_factory.get_environment()
    gt = environment_factory.get_ground_truths()

    # Create the agent orchestrator
    print("Loading Orchestrator... (4/4)")
    orchestrator = AgentOrchestrator(model, environment)

    print("Loading finished!\n")
    while True:
        choice = input("Please type 'cli' or 'simulator' to continue: ")
        if choice == "cli":
            run_cli(orchestrator)
            break
        if choice == "simulator":
            run_simulator(orchestrator)
            break
        print("Invalid option. Please try again.")
        print()


if __name__ == "__main__":
    main()