from fastapi import APIRouter, Depends, Body, HTTPException, Query
from starlette import status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_session
from sqlalchemy import insert, select, and_, cast, DateTime

from app.schemas.courier import Courier as SchemasCourier
from app.models.courier import Courier as ModelCourier
from app.models.order import Order as ModelOrder
from .utils import model_to_dict
from datetime import datetime


couriers_router = APIRouter(
    prefix="/couriers",
    tags=["Couriers"]
)


@couriers_router.post(
    "",
    name='couriers',
    status_code=status.HTTP_200_OK,
    response_model=List[SchemasCourier]
)
async def post_couriers(couriers_data: List[SchemasCourier] = Body(...), session: AsyncSession=Depends(get_async_session)):
    couriers = []

    for person in couriers_data:
        courier_data = {
            'courier_type': person.courier_type,
            'regions': person.regions, 
            'working_hours': person.working_hours
        }
        couriers.append(courier_data)

    stmt = insert(ModelCourier).values(couriers)
    await session.execute(stmt)
    await session.commit()

    return couriers


@couriers_router.get(
    "/{courier_id}",
    name='courier_info',
    status_code=status.HTTP_200_OK
)
async def get_courier_info(courier_id:int, session: AsyncSession=Depends(get_async_session)):
    query = select(ModelCourier).where(ModelCourier.courier_id == courier_id)
    result = await session.execute(query)
    courier = result.scalar()
    await session.commit()
    
    if courier is None:
        raise HTTPException(status_code=404, detail="Courier not found")
    else:
        return model_to_dict(courier)


@couriers_router.get(
    "",
    name='all_couriers_info',
    status_code=status.HTTP_200_OK
)
async def get_all_couriers_info(offset:int=0, limit:int=1, session: AsyncSession=Depends(get_async_session)):
    query = select(ModelCourier).offset(offset).limit(limit)
    result = await session.execute(query)
    couriers = result.scalars().all()
    await session.commit()

    couriers_dict_list = [model_to_dict(courier) for courier in couriers]
    return couriers_dict_list


@couriers_router.get(
    "/meta-info/{courier_id}",
    name='metainfo_courier_info',
    status_code=status.HTTP_200_OK
)
async def get_meta_couriers_info(courier_id: int, start_date:str, end_date: str, session: AsyncSession=Depends(get_async_session)):
    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Incorrect date format. Expected format: YYYY-MM-DD")

    courier = await session.execute(select(ModelCourier).where(ModelCourier.courier_id == courier_id))
    courier = courier.scalars().first()

    if courier is None:
        raise HTTPException(status_code=400, detail="Courier not found")

    courier_type = courier.courier_type

    query = select(ModelOrder).where(
        and_(
            ModelOrder.courier_id == courier_id,
            cast(ModelOrder.completed_time, DateTime) >= start_date,
            cast(ModelOrder.completed_time, DateTime) < end_date,
        ))

    orders = await session.execute(query)
    orders = orders.scalars().all()

    if not orders:
        return None

    courier_coefficients = {"FOOT": 2, "BIKE": 3, "AUTO": 4}
    earnings_coefficient = courier_coefficients[courier_type]

    rating_coefficients = {"FOOT": 3, "BIKE": 2, "AUTO": 1}
    rating_coefficient = rating_coefficients[courier_type]

    earnings = sum(order.costs * earnings_coefficient for order in orders)

    total_hours = (end_date - start_date).total_seconds() / 3600
    rating = (len(orders) / total_hours) * rating_coefficient

    return {"earnings": earnings, "rating": rating}
    