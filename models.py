# pyright: basic
from __future__ import annotations
from pydantic import BaseModel, Field


class PowerData(BaseModel, extra="ignore"):
    Description: str
    PowerSupplies: list[PSUModel] = Field(default_factory=list)


class PSUModel(BaseModel, extra="ignore"):
    MemberId: str
    Name: str
    Status: StatusModel
    LineInputVoltage: float
    PowerInputWatts: float
    PowerOutputWatts: float
    PowerOutputVoltage: float
    PowerTemperature: float


class StatusModel(BaseModel):
    State: str
