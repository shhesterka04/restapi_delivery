from fastapi import APIRouter, Depends, Body, HTTPException
from starlette import status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_session
from sqlalchemy import insert, select

from app.schemas.courier import Courier as SchemasCourier
from app.models.courier import Courier as ModelCourier
from .utils import model_to_dict


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
async def get_meta_couriers_info(start_date, end_date, session: AsyncSession=Depends(get_async_session)):
    pass