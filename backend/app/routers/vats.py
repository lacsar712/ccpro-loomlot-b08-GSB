from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_admin
from app.database import get_db
from app.models.dye_house import DyeHouse
from app.models.user import User
from app.models.vat import Vat
from app.schemas.vat import VatCreate, VatUpdate, VatTransfer, VatOut

router = APIRouter(prefix="/api/vats", tags=["vats"])


@router.get("", response_model=List[VatOut])
def list_vats(
    dye_house_id: Optional[int] = Query(None, alias="dyeHouseId"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Vat)
    if dye_house_id is not None:
        q = q.filter(Vat.dye_house_id == dye_house_id)
    return q.order_by(Vat.id).all()


@router.post("", response_model=VatOut, status_code=status.HTTP_201_CREATED)
def create_vat(
    payload: VatCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    house = db.query(DyeHouse).filter(DyeHouse.id == payload.dye_house_id).first()
    if not house:
        raise HTTPException(status_code=400, detail="染坊不存在")
    item = Vat(
        dye_house_id=payload.dye_house_id,
        vat_code=payload.vat_code,
        fiber_type=payload.fiber_type,
        capacity_l=payload.capacity_l,
        status=payload.status,
    )
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="同坊染缸编号已存在")
    db.refresh(item)
    return item


@router.get("/{vat_id}", response_model=VatOut)
def get_vat(
    vat_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = db.query(Vat).filter(Vat.id == vat_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="染缸不存在")
    return item


@router.put("/{vat_id}", response_model=VatOut)
def update_vat(
    vat_id: int,
    payload: VatUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = db.query(Vat).filter(Vat.id == vat_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="染缸不存在")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(item, k, v)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="同坊染缸编号已存在")
    db.refresh(item)
    return item


@router.post("/{vat_id}/transfer", response_model=VatOut)
def transfer_vat(
    vat_id: int,
    payload: VatTransfer,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """跨坊改挂：仅染坊主管；染缸须无进行中染程（先排液）；目标坊缸号唯一。

    改挂只更新染缸的 dye_house_id（与可选缸号），染程/色牢度仍挂原缸主键，
    按坊过滤与看板分坊计数均经当前 dye_house_id 汇总，自动归入新坊。
    """
    item = db.query(Vat).filter(Vat.id == vat_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="染缸不存在")
    target = db.query(DyeHouse).filter(DyeHouse.id == payload.target_dye_house_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="目标染坊不存在")
    if item.status == "dyeing":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="染缸存在进行中的染程，请先完成排液或待染程结束后再改挂",
        )
    new_code = payload.new_vat_code.strip() if payload.new_vat_code else item.vat_code
    if not new_code:
        raise HTTPException(status_code=400, detail="新缸号不能为空")
    clash = (
        db.query(Vat)
        .filter(
            Vat.dye_house_id == target.id,
            Vat.vat_code == new_code,
            Vat.id != item.id,
        )
        .first()
    )
    if clash:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"目标染坊已存在缸号「{new_code}」，请指定其他新缸号",
        )
    item.dye_house_id = target.id
    item.vat_code = new_code
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="目标染坊已存在相同缸号",
        )
    db.refresh(item)
    return item


@router.post("/{vat_id}/drain", response_model=VatOut)
def drain_vat(
    vat_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """可选：完成排液，将染缸状态置为 drain。"""
    item = db.query(Vat).filter(Vat.id == vat_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="染缸不存在")
    if item.status == "drain":
        raise HTTPException(status_code=400, detail="染缸已在排液状态")
    item.status = "drain"
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{vat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vat(
    vat_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    item = db.query(Vat).filter(Vat.id == vat_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="染缸不存在")
    db.delete(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="该染缸仍有关联记录，无法删除")
