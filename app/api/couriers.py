from fastapi import APIRouter, Request
from starlette import status
from typing import List

from app.schemas.courier import Courier


couriers_router = APIRouter(
    prefix="/couriers",
    tags=["Couriers"]
)


@couriers_router.post(
    "",
    name='couriers',
    status_code=status.HTTP_200_OK,
    response_model=Courier
)
async def post_couriers(request: Request):
    request = await request.json()
    for line in request:
        courier_id = line['courier_id']
        courier_type = line['courier_type']
        regions = line['regions']
        working_hours = line['working_hours']
    return None #тут должно быть добавление в базу данных


@couriers_router.get(
    "/{courier_id}",
    name='courier_info',
    status_code=status.HTTP_200_OK
)
async def get_courier_info(courier_id):
    pass

@couriers_router.get(
    "",
    name='all_couriers_info',
    status_code=status.HTTP_200_OK
)
async def get_all_couriers_info():
    pass


