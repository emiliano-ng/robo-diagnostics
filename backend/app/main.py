from fastapi import FastAPI

from app.routers import experiments

app = FastAPI(
    title="Robotics Experiment & Diagnostics Platform",
    description="API para ingerir, consultar y diagnosticar experimentos de robótica.",
    version="0.1.0",
)

app.include_router(experiments.router)


@app.get("/health")
def health():
    return {"status": "ok"}
