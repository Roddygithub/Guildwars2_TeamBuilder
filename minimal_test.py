from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
async def read_root():
    return {"Hello": "World"}

if __name__ == "__main__":
    print("Démarrage du serveur sur http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
