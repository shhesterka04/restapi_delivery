from app.api.couriers import couriers_router
from app.api.orders import orders_router

from fastapi import FastAPI


def get_application() -> FastAPI:
    application = FastAPI()
    application.include_router(couriers_router)
    application.include_router(couriers_router)

    return application


app = get_application()
