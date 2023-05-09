from app.routers.couriers import couriers_router
from app.routers.orders import orders_router

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded

from fastapi import FastAPI


def get_application() -> FastAPI:
    limiter = Limiter(key_func=get_remote_address, default_limits=["10/minute"])

    application = FastAPI()

    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    application.add_middleware(SlowAPIMiddleware)
    
    application.include_router(couriers_router)
    application.include_router(orders_router)

    return application

app = get_application()
