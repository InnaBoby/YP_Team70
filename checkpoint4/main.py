import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict
from api import api_route

app = FastAPI(
    title="checkpoint-4",
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
)


class StatusResponse(BaseModel):
    status: str
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"status": "App healthy"}]}
    )

@app.get("/", response_model=StatusResponse)
async def root():
    return StatusResponse(status='App healthy')


app.include_router(api_route.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)