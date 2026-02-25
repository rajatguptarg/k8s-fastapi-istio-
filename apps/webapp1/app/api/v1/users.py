from typing import Annotated, List

import httpx
from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.models.user import User, UserCreate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service() -> UserService:
    # for now, new instance per request; can be swapped for a shared instance or DB-backed later
    return UserService()


ServiceDep = Annotated[UserService, Depends(get_user_service)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.get("/", response_model=List[User])
async def list_users(service: ServiceDep):
    return service.list_users()


@router.post("/", response_model=User, status_code=201)
async def create_user(user_in: UserCreate, service: ServiceDep):
    return service.create_user(user_in)


@router.get("/call-webapp2")
async def call_webapp2(settings: SettingsDep):
    async with httpx.AsyncClient(follow_redirects=True) as client:
        resp = await client.get(f"{settings.webapp2_base_url}/api/v1/items/")
        resp.raise_for_status()
        return {"from": "webapp1", "webapp2_response": resp.json()}
