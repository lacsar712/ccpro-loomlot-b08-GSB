from typing import List

from pydantic import BaseModel, ConfigDict, Field


class HouseVatStat(BaseModel):
    """分坊对照：染缸数按 Vat.dye_house_id 计，染程数经染缸现属坊汇总。"""

    model_config = ConfigDict(populate_by_name=True)

    dye_house_id: int = Field(serialization_alias="dyeHouseId")
    dye_house_name: str = Field(serialization_alias="dyeHouseName")
    vat_count: int = Field(serialization_alias="vatCount")
    dye_lot_count: int = Field(serialization_alias="dyeLotCount")


class DashboardStats(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    dye_house_total: int = Field(serialization_alias="dyeHouseTotal")
    vat_ready_count: int = Field(serialization_alias="vatReadyCount")
    vat_dyeing_count: int = Field(serialization_alias="vatDyeingCount")
    lots_last_7d: int = Field(serialization_alias="lotsLast7d")
    checks_last_24h: int = Field(serialization_alias="checksLast24h")
    house_vat_stats: List[HouseVatStat] = Field(serialization_alias="houseVatStats")
