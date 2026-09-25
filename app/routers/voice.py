from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.auth.dependencies import require_user
from app.config import settings
from app.models.user import User

router = APIRouter(prefix="/voice", tags=["voice"])


@router.post("/transcribe")
async def transcribe(audio: UploadFile, user: User = Depends(require_user)) -> dict:
    """Stuurt een opgenomen audiofragment door naar een losse, self-hosted Speaches-
    container (voorheen faster-whisper-server) voor de transcriptie. Speaches praat de
    OpenAI Audio API na (`POST /v1/audio/transcriptions`, multipart-veld `file`, form-veld
    `model`), dus dezelfde aanroep werkt ook tegen een echte OpenAI-endpoint mocht iemand
    daar ooit voor kiezen. De app doet zelf geen spraakherkenning -- dat blijft in een
    aparte container zodat de hoofd-image licht blijft en er geen zware ML-dependencies in
    de Docker-image van de app zelf nodig zijn."""
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Geen audio ontvangen")

    url = f"{settings.whisper_service_url.rstrip('/')}/v1/audio/transcriptions"
    try:
        async with httpx.AsyncClient(timeout=120) as http_client:
            response = await http_client.post(
                url,
                data={"model": settings.whisper_model, "response_format": "json"},
                files={
                    "file": (
                        audio.filename or "opname.webm",
                        audio_bytes,
                        audio.content_type or "audio/webm",
                    )
                },
            )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Kan de Whisper-service niet bereiken. Controleer of de Whisper-container "
                "draait en of de WHISPER_SERVICE_URL-instelling klopt."
            ),
        ) from exc

    if response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Whisper-service gaf een foutmelding ({response.status_code}): "
                f"{response.text[:300]}. Controleer of WHISPER_MODEL ('{settings.whisper_model}') "
                "overeenkomt met een model dat in Speaches geladen is."
            ),
        )

    data = response.json()
    text = (data.get("text") or "").strip()
    return {"text": text}
