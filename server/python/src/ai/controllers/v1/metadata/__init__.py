from fastapi import APIRouter
from ai.controllers.v1.metadata.feedback import router as feedback_router
from ai.controllers.v1.metadata.stats import router as stats_router

router = APIRouter(prefix="/metadata", tags=["元数据"])
router.include_router(feedback_router)
router.include_router(stats_router)