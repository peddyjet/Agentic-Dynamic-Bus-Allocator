from pydantic import BaseModel

class VehicleJourney(BaseModel):
    class Vehicle:
        id: str
        reg: str

    id: str
    datetime : str
    vehicle: Vehicle
    trip_id: str
    route_name: str