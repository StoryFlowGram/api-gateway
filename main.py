from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from router import proxy
from router.proxy import client

app = FastAPI(
    title="SFG API Gateway",
    description="Єдина точка входу",
    version="1.0.0",
    docs_url="/docs", 
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.ngrok-free\.app",  #Только для продакшина
    allow_credentials=True,       
    allow_methods=["*"],         
    allow_headers=["*"],          
)

app.include_router(proxy.router)


@app.on_event("startup")
async def startup_event():
    print("SFG API Gateway Успішно запущено !")

@app.on_event("shutdown")
async def shutdown_event():

    print("🛑 Зупинка Gateway")
    
    await client.aclose()

@app.get("/health")
async def health_check():
    return {
        "status": "ok", 
        "service": "api-gateway",
        "version": "1.0.0"
    }