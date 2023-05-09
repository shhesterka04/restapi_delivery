from fastapi import APIRouter, Request
from starlette import status


orders_router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)


@orders_router.post(
    "",
    name='post_orders',
    status_code=status.HTTP_200_OK
)
async def post_orders(request: Request):
    pass

@orders_router.get(
    "/{order_id}",
    name='order_info',
    status_code=status.HTTP_200_OK
)
async def get_order_info(order_id):
    pass

@orders_router.get(
    "",
    name='get_all_orders_info',
    status_code=status.HTTP_200_OK
)
async def get_all_orders_info():
    pass

@orders_router.post(
    "/complete",
    name='orders_complete',
    status_code=status.HTTP_200_OK
)
async def post_orders_complete(request: Request):
    pass