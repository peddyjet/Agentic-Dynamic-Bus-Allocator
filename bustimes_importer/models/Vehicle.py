from pydantic import BaseModel

class VehicleType(BaseModel):
    id: int
    name: str
    fuel: str
    double_decker: bool
    coach: bool

class Vehicle(BaseModel):
    id: int
    reg: str
    vehicle_type: VehicleType
    withdrawn: bool
