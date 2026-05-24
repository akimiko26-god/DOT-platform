from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


def dist_dir() -> Path | None:
    return _DIST if _DIST.is_dir() and (_DIST / "index.html").is_file() else None


def mount_spa(app: FastAPI) -> bool:
    dist = dist_dir()
    if not dist:
        return False

    assets = dist / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="spa-assets")

    @app.get("/{spa_path:path}", include_in_schema=False)
    def spa_fallback(spa_path: str):
        if spa_path.startswith("api") or spa_path.startswith("uploads"):
            from fastapi import HTTPException

            raise HTTPException(status_code=404)
        candidate = dist / spa_path
        if spa_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(dist / "index.html")

    return True
