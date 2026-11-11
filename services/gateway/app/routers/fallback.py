from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["gateway"])


@router.api_route(
    "/api/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
)
def unknown_api_path(path: str):
    raise HTTPException(status_code=404, detail="Route inconnue")
