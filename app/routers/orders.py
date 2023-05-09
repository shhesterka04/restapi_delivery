from fastapi import APIRouter, Depends, Body, HTTPException
from starlette import status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_session
from sqlalchemy import insert, select, update, case

from app.schemas.order import Order as SchemasOrder
from app.schemas.order import OrderComplete
from app.models.order import Order as ModelOrder
from .utils import model_to_dict


orders_router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)


@orders_router.post(
    "",
    name='post_orders',
    status_code=status.HTTP_200_OK,
    response_model=List[SchemasOrder]
)
async def post_orders(orders_data: List[SchemasOrder] = Body(...), session: AsyncSession=Depends(get_async_session)):
    orders = []

    for order in orders_data:
        order_data = {
            'weight': str(order.weight),
            'regions': order.regions,
            'delivery_hours': order.delivery_hours,
            'costs': order.costs
        }
        orders.append(order_data)

    stmt = insert(ModelOrder).values(orders)
    await session.execute(stmt)
    await session.commit()

    return orders


@orders_router.get(
    "/{order_id}",
    name='order_info',
    status_code=status.HTTP_200_OK
)
async def get_order_info(order_id:int, session: AsyncSession=Depends(get_async_session)):
    query = select(ModelOrder).where(ModelOrder.order_id == order_id)
    result = await session.execute(query)
    order = result.scalar()
    await session.commit()

    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    else:
        return model_to_dict(order)

@orders_router.get(
    "",
    name='get_all_orders_info',
    status_code=status.HTTP_200_OK
)
async def get_all_orders_info(offset:int = 0, limit:int = 1, session: AsyncSession=Depends(get_async_session)):
    query = select(ModelOrder).offset(offset).limit(limit)
    result = await session.execute(query)
    orders = result.scalars().all()
    await session.commit()

    orders_dict_list = [model_to_dict(order) for order in orders]
    return orders_dict_list

@orders_router.post(
    "/complete",
    name='orders_complete',
    status_code=status.HTTP_200_OK
)
async def post_orders_complete(complete_orders_data: List[OrderComplete] = Body(...), session: AsyncSession=Depends(get_async_session)):
    complete_orders = []
    ans = set()

    for complete_order in complete_orders_data:
        query = select(ModelOrder).where(ModelOrder.order_id == complete_order.order_id)
        result = await session.execute(query)
        order = result.scalar_one_or_none()

        if order is None or order.courier_id != complete_order.courier_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order not found or assigned to another courier")

        comp_order_data = {
            'order_id' : complete_order.order_id,
            'completed_time' : complete_order.completed_time
        }
        complete_orders.append(comp_order_data)
        ans.add(complete_order.order_id)

    stmt = (
        update(ModelOrder).where(ModelOrder.order_id.in_([row["order_id"] for row in complete_orders]))
        .values(
            {
                "completed_time": case(
                    *[(ModelOrder.order_id == row["order_id"], row["completed_time"]) for row in complete_orders]
                )
            }
        )
    )
    await session.execute(stmt)
    await session.commit()

    return ans
        
