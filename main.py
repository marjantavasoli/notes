from fastapi import FastAPI
from database import lifespan


app = FastAPI(life_span=lifespan)

@app.get("/")
async def root():
    return {"hello": "world"}