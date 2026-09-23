from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.auth.dependencies import require_user
from app.config import settings
from app.models.user import User

router = APIRouter(prefix="/voice", tags=["voice"])


@router.post("/transcribe")
async def transcribe(audio: UploadFile, user: User = Depends(require_user)) -> dict:
    """Stuurt een opgenomen audiofragment door naar de losse, self-hosted
    Whisper-container (bv. ahmetoner/whisper-asr-webservice, zie
    WHISPER_SERVICE_URL in app/config.py) en geeft de transcriptie terug. De
    app doet zelf geen spraakherkenning -- dat blijft in een aparte container
    zodat de hoofd-image licht blijft en er geen zware ML-dependencies in de
    Docker-image van de app zelf nodig zijn."""
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Geen audio ontvangen")

    url = f"{settings.whisper_service_url.rstrip('/')}/asr"
    try:
        async with httpx.AsyncClient(timeout=120) as http_client:
            response = await http_client.post(
                url,
                params={"output": "json", "task": "transcribe"},
                files={
                    "audio_file": (
                        audio.filename or "opname.webm",
                        audio_bytes,
                        audio.content_type or "audio/webm",
                    )
                },
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Kan de Whisper-service niet bereiken. Controleer of de Whisper-container "
                "draait en of de WHISPER_SERVICE_URL-instelling klopt."
            ),
        ) from exc

    data = response.json()
    text = (data.get("text") or "").strip()
    return {"text": text}
