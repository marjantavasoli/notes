from fastapi import FastAPI
from database import life_span


app = FastAPI(life_span=life_span)