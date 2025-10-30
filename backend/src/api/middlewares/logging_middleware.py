import logging
from fastapi import Request

logger = logging.getLogger(__name__)

async def logging_middleware(request: Request, call_next):
    logger.info(f"Request headers: {request.headers}")
    response = await call_next(request)
    logger.info(f"Response headers: {response.headers}")
    return response
