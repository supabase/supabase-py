from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase._async.client import AsyncClient

from dependencies import get_client

router = APIRouter(prefix="/tasks", tags=["tasks"])

VALID_STATUSES = {"pending", "in_progress", "done"}


class CreateTask(BaseModel):
    title: str
    assigned_to: str


class UpdateTask(BaseModel):
    status: str


@router.get("/")
async def list_tasks(client: AsyncClient = Depends(get_client)):
    response = await client.table("tasks").select("*").execute()
    return response.data


@router.post("/")
async def create_task(body: CreateTask, client: AsyncClient = Depends(get_client)):
    response = await client.table("tasks").insert(
        {"title": body.title, "assigned_to": body.assigned_to, "status": "pending"}
    ).execute()
    return response.data[0]


@router.patch("/{task_id}")
async def update_task(task_id: str, body: UpdateTask, client: AsyncClient = Depends(get_client)):
    if body.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"status must be one of {sorted(VALID_STATUSES)}")
    response = await client.table("tasks").update({"status": body.status}).eq("id", task_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Task not found or not authorized")
    return response.data[0]
