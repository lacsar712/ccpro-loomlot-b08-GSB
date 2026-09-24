from typing import List

from pydantic import BaseModel, ConfigDict, Field


class HouseVatCount(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    dye_house_id: int = Field(serialization_alias="dyeHouseId")
    name: str
    vat_count: int = Field(serialization_alias="vatCount")


class DashboardStats(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    dye_house_total: int = Field(serialization_alias="dyeHouseTotal")
    vat_ready_count: int = Field(serialization_alias="vatReadyCount")
    vat_dyeing_count: int = Field(serialization_alias="vatDyeingCount")
    lots_last_7d: int = Field(serialization_alias="lotsLast7d")
    checks_last_24h: int = Field(serialization_alias="checksLast24h")
    houses: List[HouseVatCount] = Field(serialization_alias="houses")
