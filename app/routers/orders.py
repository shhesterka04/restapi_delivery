from fastapi import APIRouter, Depends, Body, HTTPException
from starlette import status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_session
from sqlalchemy import insert, select, update, case, and_

from app.schemas.order import Order as SchemasOrder, OrderAssignments, CourierTrip
from app.schemas.order import OrderComplete
from app.models.order import Order as ModelOrder
from app.models.courier import Courier as ModelCourier
from .utils import model_to_dict, parse_interval_time
from datetime import timedelta


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
    orders = await session.execute(select(ModelOrder).where(and_(ModelOrder.courier_id == None, ModelOrder.completed_time == None)))
    orders = orders.scalars().all()

    couriers = await session.execute(select(ModelCourier).order_by(ModelCourier.courier_type))
    couriers = couriers.scalars().all()

    order_assignments = distribute_orders(orders, couriers)

    for courier_id, assignment in order_assignments.items():
        for trip in assignment.trips:
            for order_cost in trip.orders_costs:
                order_id = order_cost[0]
                cost = order_cost[1]
                stmt = (
                    update(ModelOrder)
                    .where(ModelOrder.order_id == order_id)
                    .values(courier_id=courier_id, costs=cost)
                )

                await session.execute(stmt)

    await session.commit()

    return {"assignments": order_assignments}

def can_assign_order(courier: ModelCourier, order: ModelOrder, assigned_orders: OrderAssignments) -> bool:
    courier_type_limits = {
        "FOOT": {"max_weight": 10, "max_orders": 2, "max_regions": 1, "first_delivery_time": 25, "next_delivery_time": 10},
        "BIKE": {"max_weight": 20, "max_orders": 4, "max_regions": 2, "first_delivery_time": 12, "next_delivery_time": 8},
        "AUTO": {"max_weight": 40, "max_orders": 7, "max_regions": 3, "first_delivery_time": 8, "next_delivery_time": 4},
    }

    courier_limits = courier_type_limits[courier.courier_type]
    current_orders = assigned_orders.get(courier.courier_id, [])

    current_weight = sum(o.weight for o in current_orders)
    if current_weight + float(order.weight) > courier_limits["max_weight"]:
        return False

    if len(current_orders) >= courier_limits["max_orders"]:
        return False

    # Не совсем понятно условие - регионы определяются заранее или их также нужно распределять?
    # Из условия первого задания считаю, что регионы заранее распределны, причем с учетом ограничений типов курьера
    if order.regions not in courier.regions:
        return False

    return True

def distribute_orders(orders: List[ModelOrder], couriers: List[ModelCourier]) -> List[OrderAssignments]:
    couriers_type_limits = {
        "FOOT": {"max_orders": 2, "first_delivery_time": 25, "next_delivery_time": 10},
        "BIKE": {"max_orders": 4, "first_delivery_time": 12, "next_delivery_time": 8},
        "AUTO": {"max_orders": 7, "first_delivery_time": 8, "next_delivery_time": 4},
    }

    orders.sort(key=lambda o: parse_interval_time(o.delivery_hours)[1])

    assignments = {}

    for courier in couriers:
        courier_type_limits = couriers_type_limits[courier.courier_type]
        next_available_time, working_hours_end = parse_interval_time(courier.working_hours)

        trips = []
        trip = []
        for order in orders:
            if not can_assign_order(courier, order, assignments):
                continue

            order_start, order_end = parse_interval_time(order.delivery_hours)

            if len(trip) == 0:  # first order
                next_available_time = max(order_start, next_available_time) + timedelta(minutes=courier_type_limits["first_delivery_time"])
            else:
                next_available_time += timedelta(minutes=courier_type_limits["next_delivery_time"])
                order.costs *= 0.8 

            if next_available_time <= min(order_end, working_hours_end):
                trip.append([order.order_id, order.costs])
                orders.remove(order)

                if len(trip) >= courier_type_limits["max_orders"]:
                    trips.append(CourierTrip(courier.courier_id, trip))
                    trip = []

        if trip:  # add remaining orders
            trips.append(CourierTrip(courier.courier_id, trip))

        assignments[courier.courier_id] = OrderAssignments(courier.courier_id, trips)

    return assignments




