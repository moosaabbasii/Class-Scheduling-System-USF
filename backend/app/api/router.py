from fastapi import APIRouter

from app.api.routes import (
    analytics,
    audits,
    exports,
    health,
    lookups,
    schedules,
    sections,
    users,
)


api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(
    lookups.catalog_router, prefix="/catalog-courses", tags=["catalog-courses"]
)
api_router.include_router(lookups.room_router, prefix="/rooms", tags=["rooms"])
api_router.include_router(
    lookups.instructor_router, prefix="/instructors", tags=["instructors"]
)
api_router.include_router(lookups.ta_router, prefix="/tas", tags=["tas"])
api_router.include_router(schedules.router, prefix="/schedules", tags=["schedules"])
api_router.include_router(sections.router, prefix="/sections", tags=["sections"])
api_router.include_router(audits.router, prefix="/audits", tags=["audits"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(exports.router, prefix="/exports", tags=["exports"])
