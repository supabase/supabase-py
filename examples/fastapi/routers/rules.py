from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase._async.client import AsyncClient

from dependencies import get_client

router = APIRouter(prefix="/rules", tags=["rules"])


class CreateRule(BaseModel):
    label: str
    watch_column: str
    watch_value: str
    broadcast_channel: str


@router.get("/")
async def list_rules(client: AsyncClient = Depends(get_client)):
    response = await client.table("rules").select("*").execute()
    return response.data


@router.post("/")
async def create_rule(body: CreateRule, client: AsyncClient = Depends(get_client)):
    response = await client.table("rules").insert({
        "label": body.label,
        "watch_column": body.watch_column,
        "watch_value": body.watch_value,
        "broadcast_channel": body.broadcast_channel,
    }).execute()
    return response.data[0]


@router.delete("/{rule_id}")
async def delete_rule(rule_id: str, client: AsyncClient = Depends(get_client)):
    response = await client.table("rules").delete().eq("id", rule_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Rule not found or not authorized")
    return {"deleted": rule_id}
