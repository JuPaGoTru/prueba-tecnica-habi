from fastapi import FastAPI

from app.api.routers import auth, workspaces

app = FastAPI(title="Habi Financial Planner API", version="1.0.0")

app.include_router(auth.router, prefix="/api/v1")
app.include_router(workspaces.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
