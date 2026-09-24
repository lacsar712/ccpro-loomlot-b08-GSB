from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.dye_house import DyeHouse
from app.models.dye_lot import DyeLot
from app.models.fastness_check import FastnessCheck
from app.models.user import User
from app.models.vat import Vat
from app.schemas.dashboard import DashboardStats, HouseVatStat

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_stats(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    houses = db.query(DyeHouse).order_by(DyeHouse.id).all()
    # 染缸分坊计数：与 GET /api/vats?dyeHouseId= 行数同源（同按 Vat.dye_house_id）
    vat_counts = dict(
        db.query(Vat.dye_house_id, func.count(Vat.id)).group_by(Vat.dye_house_id).all()
    )
    # 染程旁路按坊汇总：染程只挂染缸主键，经染缸当前所属坊归集
    lot_counts = dict(
        db.query(Vat.dye_house_id, func.count(DyeLot.id))
        .join(DyeLot, DyeLot.vat_id == Vat.id)
        .group_by(Vat.dye_house_id)
        .all()
    )
    return DashboardStats(
        dye_house_total=db.query(func.count(DyeHouse.id)).scalar() or 0,
        vat_ready_count=db.query(func.count(Vat.id)).filter(Vat.status == "ready").scalar() or 0,
        vat_dyeing_count=db.query(func.count(Vat.id)).filter(Vat.status == "dyeing").scalar() or 0,
        lots_last_7d=(
            db.query(func.count(DyeLot.id))
            .filter(DyeLot.started_at >= now - timedelta(days=7))
            .scalar()
            or 0
        ),
        checks_last_24h=(
            db.query(func.count(FastnessCheck.id))
            .filter(FastnessCheck.checked_at >= now - timedelta(hours=24))
            .scalar()
            or 0
        ),
        house_vat_stats=[
            HouseVatStat(
                dye_house_id=h.id,
                dye_house_name=h.name,
                vat_count=vat_counts.get(h.id, 0),
                dye_lot_count=lot_counts.get(h.id, 0),
            )
            for h in houses
        ],
    )
