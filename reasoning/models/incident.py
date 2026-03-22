from datetime import datetime
from pydantic import BaseModel, Field, AliasPath
from typing import List

class Incident(BaseModel):
    summary: str
    description: str
    actions: str
    trips: List[int] = []
    buses: List[int] = []
    global_: bool = Field(validation_alias=AliasPath('global'))
    expiry: int

    class Config:
        populate_by_name = True

class TimeStampedIncident(Incident):
    time : datetime