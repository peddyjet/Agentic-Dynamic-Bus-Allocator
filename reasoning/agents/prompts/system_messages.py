SYSTEM_MESSAGES = {}

def add_system_message(name):
    with open(f"reasoning/agents/prompts/{name}.md", "r", encoding="utf-8") as f:
        SYSTEM_MESSAGES[name] = f.read()

add_system_message("asa")
add_system_message("cra")
add_system_message("ihsa")
