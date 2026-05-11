import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import create_tables, get_connection
from data_loader import load_all_data
from engine_runner import run_engine
import programs  # triggers PROGRAM_REGISTRY population via __init__.py
from router import router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup() -> None:
    create_tables()
    conn = get_connection()
    load_all_data(conn)
    run_engine(conn)
    conn.close()


app.include_router(router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
