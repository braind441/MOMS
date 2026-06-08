from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import import_playlist, download, library, upload

app = FastAPI(title="MOMS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(import_playlist.router, prefix="/playlist")
app.include_router(download.router, prefix="/downloads")
app.include_router(library.router, prefix="/library")
app.include_router(upload.router, prefix="/upload")


@app.get("/health")
async def health():
    return {"ok": True}
