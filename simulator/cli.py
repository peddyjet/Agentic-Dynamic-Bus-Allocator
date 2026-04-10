from datetime import timedelta

from reasoning.agent_interface.ComputationalAgentInterface import ComputationalAgentInterface
from reasoning.environment.Environment import Environment


def help_menu():
    print("Available commands:")
    print("log: allows for a log to be sent to the CRA on the next user input.")
    print("allox id1 id2 ... id99: sends an allocation request to the CRA")
    print("buses: dumps all bus data to the console")
    print("services: dumps all service data to the console")
    print("trip [service_id]: dumps all trip data regarding a service to the console")
    print("freeze: toggles the passage of time")
    print("help: shows this menu")
    print("exit: exits the program.")
    print("\nYou may end a line with a backslash '\\' to write over multiple lines.")
    print("By default, 10 minutes will pass every time a user input is received.")

def get_user_input(prompt = ">"):
    user_input = input(f"{prompt} ")
    if user_input == "":
        return user_input

    while user_input[len(user_input) - 1] == "\\":
        user_input = user_input[:1] + '\n'
        user_input += input("    | ")
    return user_input

async def run_cli(cai : ComputationalAgentInterface, environment : Environment):
    freeze_time = False

    print("\n=== Agentic DBA CLI ===")
    help_menu()

    while True:
        if not freeze_time:
             environment.current_time += timedelta(minutes=10)
             cai.allocate_relevant_trips(timedelta(hours=1))
             await cai.wait_for_agents()

        time = environment.current_time.strftime("%H:%M")
        user_input = get_user_input(f"[{time}] > ")

        if user_input == "":
            continue

        args = user_input.split(" ")

        if args[0] == "exit":
            return

        if args[0] == "help":
            help_menu()
            continue

        if args[0] == "log":
            new_input = get_user_input("[LOG] > ")
            print("Waiting for agent response...")
            cai.send_log(new_input)
            await cai.wait_for_agents()
            continue

        if args[0] == "allox":
            if len(args) < 2:
                print("Please provide a list of Trip IDs to allocate after the 'allox' command."
                      " These can be separated by spaces.")
                continue

            allox = args[1:]
            print("Waiting for agent response...")
            cai.allocate_buses(list(int(i) for i in allox))
            await cai.wait_for_agents()
            continue

        if args[0] == "buses":
            print(environment.buses.values())
            continue

        if args[0] == "services":
            vals = environment.services.values()
            output = [(v.id, v.route_name, [t.id for t in v.trips]) for v in vals]
            print(output)
            continue

        if args[0] == "freeze":
            freeze_time = not freeze_time
            print(f"Time has been {'Frozen' if freeze_time else 'Unfrozen'}.")
            continue

        if len(args) > 1 and args[0] == "trip":
            try:
                vals = environment.trips[int(args[1])]
                print(vals.make_llm_friendly())
            except Exception as e:
                print("Invalid trip id.")

            continue

        print("Invalid option. Please try again.")
