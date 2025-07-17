from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Test Server")

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "Test Server"}

if __name__ == "__main__":
    uvicorn.run(
        "test_server:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="debug"
    )
