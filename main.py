from fastapi import FastAPI
from database import lifespan


app = FastAPI(life_span=lifespan)