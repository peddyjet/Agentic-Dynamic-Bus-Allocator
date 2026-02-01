from typing import List

from pydantic import BaseModel

class Allocation(BaseModel):
    bus_id: int
    bus_reg: str
    trip_id: int
    rationale: str

class DefaultResponse(BaseModel):
    allocations: List[Allocation]
    rationale: str

class ErrorResponse(BaseModel):
    message: str