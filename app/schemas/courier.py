import re
from pydantic import BaseModel, Field, validator
from enum import Enum
from typing import List

class CourierType(str, Enum):
    foot = "FOOT"
    bike = "BIKE"
    auto = "AUTO"

class Courier(BaseModel):
    courier_type: CourierType
    regions: List[int]

    @validator("regions", each_item=True)
    def check_positive_int(cls, number: int) -> int:
        if number <= 0:
            raise ValueError("All numbers must be positive integers")
        return number

    working_hours: str = Field(length=11)

    @validator("working_hours")
    def check_time_range_format(cls, working_hours: str) -> str:
        pattern = r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]-([0-1]?[0-9]|2[0-3]):[0-5][0-9]$"
        if not re.match(pattern, working_hours):
            raise ValueError("Invalid time range format. Expected format: 'HH:MM-HH:MM'")
        return working_hours