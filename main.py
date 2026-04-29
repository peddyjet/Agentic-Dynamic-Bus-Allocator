import sys
import datetime
import asyncio
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from dotenv import load_dotenv
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
from camel.configs import ChatGPTConfig
from bustimes_importer.environment.EnvironmentFactory import EnvironmentFactory
from profiling.DeterministicBusAllocator import DeterministicBusAllocator
from reasoning.environment.IncidentStore import IncidentStore
from reasoning.models.agent_exposed_data import AgentExposedData
from simulator.cli import run_cli
from reasoning.DynamicBusAllocationFactory import DynamicBusAllocationFactory
from reasoning.agent_interface.ComputationalAgentInterface import ComputationalAgentInterface
from reasoning.environment.Environment import Environment
from simulator.gui.MainWindow import MainWindow
from profiling.PerformanceProfiler import PerformanceProfiler

async def main():
    print("Loading Dotenv... (1/4)")
    load_dotenv()

    # Select what LLM you want to use as the central reasoning agent
    print("Loading Model... (2/4)")

    model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.GPT_5_MINI,
        model_config_dict=ChatGPTConfig().as_dict()
    )

    # If using the BusTimes API, you may use the following code snippet to generate the reasoning
    # environment and ground truths. If you are doing so, please ensure the buses you are referencing
    # are also inside additional_bus_specs.json
    print("Loading Environment... (3/4)")
    national_operator_code = "BRYL"
    depot_lat = 52.952328
    depot_lon = -0.045051

    environment_factory = EnvironmentFactory(national_operator_code, datetime.datetime(
        year=2026,
        month=1,
        day=30,
    ), depot_lat, depot_lon, log=True)
    environment = environment_factory.get_environment()
    gt = environment_factory.get_ground_truths()

    while True:
        choice = input("Please type 'agentic' or 'determ' to continue: ")
        if choice == "agentic":
            # Create the agent orchestrator
            print("Loading Reasoning System... (4/4)")
            factory = DynamicBusAllocationFactory(model, environment)
            cai = factory.construct_instance()
            break

        if choice == "determ":
            # Create the Deterministic Bus Allocator
            print("Loading Allocator... (4/4)")
            cai = DeterministicBusAllocator(AgentExposedData(environment=environment,
                                                             incident_store=IncidentStore(environment)))
            break
        print("Invalid option. Please try again.")
        print()

    profiler = PerformanceProfiler(environment, cai)

    print("Loading finished!\n")
    while True:
        choice = input("Please type 'cli' or 'simulator' to continue: ")
        if choice == "cli":
            await run_cli(cai, environment)
            break
        if choice == "simulator":
            try:
                seed = int(input("Enter passenger generation seed (default 36): ") or "36")
            except ValueError:
                seed = 36
            MainWindow.start(cai, environment, profiler, seed=seed)
            break
        print("Invalid option. Please try again.")
        print()


if __name__ == "__main__":
    asyncio.run(main())