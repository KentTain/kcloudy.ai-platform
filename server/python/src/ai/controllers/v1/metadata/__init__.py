from fastapi import APIRouter
from ai.controllers.v1.metadata.feedback import router as feedback_router

router = APIRouter(prefix="/metadata", tags=["元数据"])
router.include_router(feedback_router)