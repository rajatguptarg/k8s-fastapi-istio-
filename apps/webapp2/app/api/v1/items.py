from typing import Annotated, List

import httpx
from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.models.item import Item, ItemCreate
from app.services.item_service import ItemService

router = APIRouter(prefix="/items", tags=["items"])


def get_item_service() -> ItemService:
    return ItemService()


ServiceDep = Annotated[ItemService, Depends(get_item_service)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.get("/", response_model=List[Item])
async def list_items(service: ServiceDep):
    return service.list_items()


@router.post("/", response_model=Item, status_code=201)
async def create_item(item_in: ItemCreate, service: ServiceDep):
    return service.create_item(item_in)


@router.get("/call-webapp1")
async def call_webapp1(settings: SettingsDep):
    async with httpx.AsyncClient(follow_redirects=True) as client:
        resp = await client.get(f"{settings.webapp1_base_url}/api/v1/users/")
        resp.raise_for_status()
        return {"from": "webapp2", "webapp1_response": resp.json()}
