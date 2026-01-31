from pydantic import BaseModel

class VehicleJourneyVehicle(BaseModel):
    id: int
    reg: str

class VehicleJourney(BaseModel):
    id: int
    datetime : str
    vehicle: VehicleJourneyVehicle
    trip_id: str
    route_name: str