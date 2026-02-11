from typing import List, Optional

from pydantic import BaseModel

class Allocation(BaseModel):
    bus_id: Optional[int]
    bus_reg: Optional[str]
    trip_id: Optional[int]
    rationale: str

class DefaultResponse(BaseModel):
    allocations: List[Allocation]
    rationale: str

class ErrorResponse(BaseModel):
    message: str