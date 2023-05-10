import re
from pydantic import BaseModel, Field, validator
from dateutil.parser import isoparse
from typing import Optional
from datetime import datetime


class Order(BaseModel):
    weight: float = Field(ge=0)
    regions: int = Field(ge=0)
    delivery_hours: str = Field(length=11)

    @validator("delivery_hours")
    def check_time_range_format(cls, delivery_hours: str) -> str:
        pattern = r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]-([0-1]?[0-9]|2[0-3]):[0-5][0-9]$"
        if not re.match(pattern, delivery_hours):
            raise ValueError("Invalid time range format. Expected format: 'HH:MM-HH:MM'")
        return delivery_hours

    costs: int = Field(ge=1)
    completed_time: Optional[datetime] = None

    @validator("completed_time", pre=True)
    def check_time_completed_format(cls, value: Optional[str]) -> Optional[datetime]:
        if value:
            try:
                print(f"Parsed datetime: {isoparse(value)}")
                return isoparse(value)
            except (ValueError, TypeError):
                print(f"Invalid value: {value}")
                raise ValueError("Invalid ISO 8601 format")
        return None

    courier_id: Optional[int] = Field(ge=1)



class OrderComplete(BaseModel):
    courier_id : int = Field(ge=1)
    order_id: int = Field(ge=1)
    completed_time : str

    @validator("completed_time")
    def check_time_completed_format(cls, value: str) -> datetime:
        try:
            dt = isoparse(value)
            print(f"Parsed datetime: {dt}")
        except (ValueError, TypeError):
            print(f"Invalid value: {value}")
            raise ValueError("Invalid ISO 8601 format")
        return dt