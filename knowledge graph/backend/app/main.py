from fastapi import FastAPI

app = FastAPI(title="Zero to GraphRAG API")

@app.get("/")
def root():
    return {"message": "Backend is running!"}