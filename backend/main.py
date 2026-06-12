"""BidSense backend — AI-Powered Bid & Proposal Response Engine (CUST Hackathon 2026)."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from db import database


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    # make sure data, embeddings and the win-probability model exist
    if not database.get_capabilities():
        from db import seed
        seed.main()
    from winprob.train import MODEL_PATH
    if not MODEL_PATH.exists():
        from winprob.train import train
        train()
    yield


app = FastAPI(title="BidSense API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
