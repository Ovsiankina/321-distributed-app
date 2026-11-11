from fastapi import APIRouter

router = APIRouter(tags=["gateway"])


@router.get("/api/home")
def home_stub():
    # E0-05 : enveloppe stable, contenu des sections hors contrat
    return {"sections": []}
