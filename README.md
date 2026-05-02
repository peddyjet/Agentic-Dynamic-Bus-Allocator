# Agentic Dynamic Bus Allocator

This is the repository regarding the Agentic DBA system, defined in "Agentic Artificial Intelligence applied to Dynamic Bus Allocation", by Katie Page, 2026 (submitted in part for BSc Computer Science at the university of lincoln).

The bustimes\_importer system uses the BusTimes API, which retrieves data from the Bus Open Data Service (BODS), under the Open Government License (OGL)

# Running the program
To run the program, the following dependencies must be met:
```md
- camel-ai
- python-dotenv
- numpy
- PyQt6
- requests
- haversine
- pydantic
- qtawesome
```

It is highly recommended that you run the project inside a python virtual environment (venv) to maintain consistency between dependency locations.

By default, the system uses `GPT-5-mini` (by OpenAI) for its reasoning agent. Consequently, a `OPENAI_API_KEY` must be stored inside a `.env` file in the base directory of the project. **Do not include the .env file in any fork of the project, as this will compromise your key.**

## Quickstart
```bash
echo OPENAI_API_KEY=your_api_key > .env
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

All other runs, you may run
```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python main.py
```