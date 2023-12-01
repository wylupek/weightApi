from fastapi import FastAPI
import random

app = FastAPI()

@app.get("/")
async def root():
    return {"current_weight": round(random.uniform(0,1000), 3)} # grams