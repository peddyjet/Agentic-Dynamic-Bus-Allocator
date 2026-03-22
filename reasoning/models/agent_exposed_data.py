from pydantic import BaseModel
from reasoning.environment.IncidentStore import IncidentStore
from reasoning.environment.Environment import Environment

class AgentExposedData(BaseModel):
    environment : Environment
    incident_store : IncidentStore

    class Config:
        arbitrary_types_allowed = True
    