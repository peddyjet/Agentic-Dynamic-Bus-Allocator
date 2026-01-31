from pydantic import BaseModel

class Vehicle(BaseModel):
    class VehicleType(BaseModel):
        id: str
        name: str
        fuel: str
        double_decker: bool
        coach: bool

    id: str
    reg: str
    vehicle_type: VehicleType
    withdrawn: bool
