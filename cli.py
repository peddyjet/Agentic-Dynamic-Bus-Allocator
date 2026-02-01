from datetime import timedelta
from reasoning.orchestration.AgentOrchestator import AgentOrchestrator

def help_menu():
    print("Available commands:")
    print("log: allows for a log to be sent to the CRA on the next user input.")
    print("allox id1 id2 ... id99: sends an allocation request to the CRA")
    print("msg: the next user input submitted will be sent directly to the CRA.")
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

def run_cli(orchestrator : AgentOrchestrator):
    freeze_time = False
    orchestrator.log_subscribe(lambda msg: print(f"(Log) {msg}"))

    print("\n=== Agentic DBA CLI ===")
    help_menu()

    while True:
        if not freeze_time:
             orchestrator.step_time(timedelta(minutes=10))

        time = orchestrator.get_environment().current_time.strftime("%H:%M")
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
            orchestrator.send_msg("[LOG] " + new_input)
            continue

        if args[0] == "allox":
            if len(args) < 2:
                print("Please provide a list of Trip IDs to allocate after the 'allox' command."
                      " These can be separated by spaces.")
                continue

            allox = args[1:]
            print("Waiting for agent response...")
            orchestrator.send_allox(allox)
            continue

        if args[0] == "msg":
            new_input = get_user_input("[MSG] > ")
            print("Waiting for agent response...")
            orchestrator.send_msg(new_input)
            continue

        if args[0] == "buses":
            print(orchestrator.get_environment().buses.values())
            continue

        if args[0] == "services":
            vals = orchestrator.get_environment().services.values()
            output = [(v.id, v.route_name, [t.id for t in v.trips]) for v in vals]
            print(output)
            continue

        if args[0] == "freeze":
            freeze_time = not freeze_time
            print(f"Time has been {'Frozen' if freeze_time else 'Unfrozen'}.")

        if len(args) > 1 and args[0] == "trip":
            try:
                vals = orchestrator.get_environment().trips[int(args[1])]
                print(vals.make_llm_friendly())
            except Exception as e:
                print("Invalid trip id.")

            continue

        print("Invalid option. Please try again.")
