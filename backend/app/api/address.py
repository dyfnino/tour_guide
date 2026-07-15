from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from typing import List

from ..database.session import get_db
from ..models.address import Address
from ..models.user import User
from ..schemas.address import (
    Address as AddressSchema,
    AddressCreate,
    AddressUpdate,
)
from .auth import get_current_user

router = APIRouter(prefix="/addresses", tags=["addresses"])


async def _get_owned_address(db: AsyncSession, user_id: int, address_id: int) -> Address:
    result = await db.execute(
        select(Address).where(Address.id == address_id, Address.user_id == user_id)
    )
    addr = result.scalar_one_or_none()
    if not addr:
        raise HTTPException(status_code=404, detail="地址不存在")
    return addr


async def _clear_default(db: AsyncSession, user_id: int, exclude_id: int = None):
    """把该用户的其它地址取消默认标记"""
    stmt = update(Address).where(Address.user_id == user_id).values(is_default=False)
    if exclude_id is not None:
        stmt = stmt.where(Address.id != exclude_id)
    await db.execute(stmt)


@router.get("", response_model=List[AddressSchema])
async def list_addresses(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """当前用户的收货地址列表（默认地址置顶）"""
    result = await db.execute(
        select(Address)
        .where(Address.user_id == user.id)
        .order_by(Address.is_default.desc(), Address.updated_at.desc(), Address.id.desc())
    )
    return result.scalars().all()


@router.post("", response_model=AddressSchema)
async def create_address(
    data: AddressCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """新增收货地址；若为首个地址或标记默认，则设为默认"""
    result = await db.execute(select(Address).where(Address.user_id == user.id))
    existing = result.scalars().all()
    is_default = data.is_default or len(existing) == 0

    if is_default:
        await _clear_default(db, user.id)

    addr = Address(
        user_id=user.id,
        name=data.name,
        phone=data.phone,
        province=data.province,
        city=data.city,
        district=data.district,
        detail=data.detail,
        is_default=is_default,
    )
    db.add(addr)
    await db.commit()
    await db.refresh(addr)
    return addr


@router.put("/{address_id}", response_model=AddressSchema)
async def update_address(
    address_id: int,
    data: AddressUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """更新收货地址"""
    addr = await _get_owned_address(db, user.id, address_id)
    payload = data.model_dump(exclude_unset=True)

    if payload.get("is_default") is True:
        await _clear_default(db, user.id, exclude_id=address_id)

    for field, value in payload.items():
        setattr(addr, field, value)

    await db.commit()
    await db.refresh(addr)
    return addr


@router.post("/{address_id}/default", response_model=AddressSchema)
async def set_default_address(
    address_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """设为默认地址"""
    addr = await _get_owned_address(db, user.id, address_id)
    await _clear_default(db, user.id, exclude_id=address_id)
    addr.is_default = True
    await db.commit()
    await db.refresh(addr)
    return addr


@router.delete("/{address_id}")
async def delete_address(
    address_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """删除收货地址；若删的是默认地址，则把最近的一条设为默认"""
    addr = await _get_owned_address(db, user.id, address_id)
    was_default = addr.is_default
    await db.delete(addr)
    await db.commit()

    if was_default:
        result = await db.execute(
            select(Address)
            .where(Address.user_id == user.id)
            .order_by(Address.updated_at.desc(), Address.id.desc())
        )
        nxt = result.scalars().first()
        if nxt:
            nxt.is_default = True
            await db.commit()

    return {"success": True}