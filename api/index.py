from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok", "service": "CosmoFolio Backend"}

@app.get("/api/health")
async def api_health():
    return {"status": "healthy", "service": "ArchPortfolio API"}
