from fastapi import APIRouter, Depends, Body, HTTPException
from starlette import status
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_session
from sqlalchemy import insert, select, update, case

from app.schemas.order import Order as SchemasOrder, OrderAssignments
from app.schemas.order import OrderComplete
from app.models.order import Order as ModelOrder
from app.models.courier import Courier as ModelCourier
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
        
@orders_router.post(
    "/assign",
    name='orders_assign',
    status_code=status.HTTP_200_OK
)
async def post_assign_orders(session: AsyncSession=Depends(get_async_session)):
    orders = await session.execute(select(ModelOrder).where(ModelOrder.courier_id == None))
    orders = orders.scalars().all()

    couriers = await session.execute(select(ModelCourier))
    couriers = couriers.scalars().all()

    #order_assignments = distribute_orders(orders, couriers)

    for assignment in order_assignments:
        order = await session.get(ModelOrder, assignment.order_id)
        order.courier_id = assignment.courier_id

    await session.commit()

    return {"assignments": order_assignments}

# def can_assign_order(courier: ModelCourier, order: ModelOrder, assigned_orders: OrderAssignments) -> bool:
#     courier_type_limits = {
#         "FOOT": {"max_weight": 10, "max_orders": 2, "max_regions": 1},
#         "BIKE": {"max_weight": 20, "max_orders": 4, "max_regions": 2},
#         "AUTO": {"max_weight": 40, "max_orders": 7, "max_regions": 3},
#     }

#     courier_limits = courier_type_limits[courier.courier_type]
#     current_orders = assigned_orders.get(courier.courier_id, [])

#     current_weight = sum(o.weight for o in current_orders)
#     if current_weight + order.weight > courier_limits["max_weight"]:
#         return False

#     if len(current_orders) >= courier_limits["max_orders"]:
#         return False

#     current_regions = set(o.region for o in current_orders)
#     if len(current_regions) >= courier_limits["max_regions"] and order.region not in current_regions:
#         return False

#     return True

# def distribute_orders(orders: List[ModelOrder], couriers: List[ModelCourier]) -> List[OrderAssignments]:
#     order_assignments = []
#     assigned_orders: Dict[int, List[ModelOrder]] = {}

#     for courier in couriers:
#         for order in orders:
#             if order.courier_id is None and can_assign_order(courier, order, assigned_orders):
#                 current_orders = assigned_orders.get(courier.courier_id, [])
#                 cost = order.costs * (1 if len(current_orders) == 0 else 0.8)

#                 order_assignments.append(OrderAssignments(order_id=order.order_id, courier_id=courier.courier_id))
#                 order.courier_id = courier.courier_id

#                 if courier.courier_id not in assigned_orders:
#                     assigned_orders[courier.courier_id] = []

#                 assigned_orders[courier.courier_id].append(order)

#     return order_assignments


