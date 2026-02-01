from reasoning.orchestration.AgentOrchestator import AgentOrchestrator
def help_menu():
    print("Available commands:")
    print("log: allows for a log to be sent to the CRA on the next user input.")
    print("allox: allows for an allocation request to be sent to the CRA on the next user input.")
    print("msg: the next user input submitted will be sent directly to the CRA.")
    print("buses: dumps all bus data to the console")
    print("services: dumps all service data to the console")
    print("trip [service_id]: dumps all trip data regarding a service to the console")
    print("help: shows this menu")
    print("exit: exits the program.")
    print("\nYou may end a line with a backslash '\\' to write over multiple lines.")

def get_user_input(prompt = ">"):
    user_input = input(f"{prompt} ")
    if user_input == "":
        return user_input

    while user_input[len(user_input) - 1] == "\\":
        user_input = user_input[:1] + '\n'
        user_input += input("    | ")
    return user_input

def run_cli(orchestrator : AgentOrchestrator):
    print("\n=== Agentic DBA CLI ===")
    help_menu()

    while True:
        user_input = get_user_input()

        if user_input == "":
            continue

        if user_input == "exit":
            return

        if user_input == "help":
            help_menu()
            continue

        if user_input == "log":
            new_input = get_user_input("[LOG]")
            print("Waiting for agent response...")
            orchestrator.get_bus_allox("[LOG] " + new_input)
            continue

        if user_input == "allox":
            new_input = get_user_input("[ALLOX]")
            print("Waiting for agent response...")
            orchestrator.get_bus_allox("[ALLOX] " + new_input)
            continue

        if user_input == "msg":
            new_input = get_user_input("[MSG]")
            print("Waiting for agent response...")
            orchestrator.get_bus_allox(new_input)
            continue

        if user_input == "buses":
            print(orchestrator.get_environment().buses.values())
            continue

        if user_input == "services":
            vals = orchestrator.get_environment().services.values()
            output = [(v.id, v.route_name, [t.id for t in v.trips]) for v in vals]
            print(output)
            continue

        args = user_input.split(" ")
        if len(args) > 1 and args[0] == "trip":
            try:
                vals = orchestrator.get_environment().trips[int(args[1])]
                print(vals.make_llm_friendly())
            except Exception as e:
                print("Invalid trip id.")

            continue

        print("Invalid option. Please try again.")
