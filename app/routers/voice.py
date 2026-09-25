from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile

from app.auth.dependencies import require_user
from app.config import settings
from app.models.user import User

router = APIRouter(prefix="/voice", tags=["voice"])


def _resolve_whisper_config(user: User, url_override: str = "", model_override: str = "") -> tuple[str, str]:
    """De URL/model die daadwerkelijk gebruikt worden: een expliciet meegegeven waarde
    (bv. vanuit het testformulier, nog niet per se opgeslagen) wint van de opgeslagen
    per-gebruiker instelling, die op zijn beurt wint van de env var/app-default."""
    url = url_override.strip() or user.whisper_service_url or settings.whisper_service_url
    model = model_override.strip() or user.whisper_model or settings.whisper_model
    return url.rstrip("/"), model


@router.post("/transcribe")
async def transcribe(audio: UploadFile, language: str = Form(""), user: User = Depends(require_user)) -> dict:
    """Stuurt een opgenomen audiofragment door naar een losse, self-hosted Speaches-
    container (voorheen faster-whisper-server) voor de transcriptie. Speaches praat de
    OpenAI Audio API na (`POST /v1/audio/transcriptions`, multipart-veld `file`, form-veld
    `model`), dus dezelfde aanroep werkt ook tegen een echte OpenAI-endpoint mocht iemand
    daar ooit voor kiezen. De app doet zelf geen spraakherkenning -- dat blijft in een
    aparte container zodat de hoofd-image licht blijft en er geen zware ML-dependencies in
    de Docker-image van de app zelf nodig zijn.

    `language` is optioneel (leeg = Whisper laat het zelf detecteren). Met name kleinere
    modellen ("tiny") detecteren de taal bij korte fragmenten nog weleens verkeerd of
    mixen talen door elkaar -- expliciet meegeven (bv. "nl" of "en") maakt de transcriptie
    een stuk betrouwbaarder zonder dat je aan één vaste taal vastzit."""
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Geen audio ontvangen")

    base_url, model = _resolve_whisper_config(user)
    url = f"{base_url}/v1/audio/transcriptions"
    request_data = {"model": model, "response_format": "json"}
    if language.strip():
        request_data["language"] = language.strip()
    try:
        async with httpx.AsyncClient(timeout=120) as http_client:
            response = await http_client.post(
                url,
                data=request_data,
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
                "draait en of de instelling voor de service-URL klopt."
            ),
        ) from exc

    if response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Whisper-service gaf een foutmelding ({response.status_code}): "
                f"{response.text[:300]}. Controleer of het ingestelde model ('{model}') "
                "overeenkomt met een model dat in Speaches geladen is."
            ),
        )

    data = response.json()
    text = (data.get("text") or "").strip()
    return {"text": text}


@router.post("/test-connection")
async def test_connection(
    whisper_service_url: str = Form(""),
    whisper_model: str = Form(""),
    user: User = Depends(require_user),
) -> dict:
    """Test de URL/het model die in het formulier staan (nog niet per se opgeslagen) tegen
    Speaches' OpenAI-compatibele modellenlijst -- bevestigt niet alleen dat de service
    bereikbaar is, maar ook of het ingestelde model daar echt bij staat."""
    base_url, model = _resolve_whisper_config(user, whisper_service_url, whisper_model)
    if not base_url:
        return {"valid": False, "message": "Vul eerst een service-URL in."}

    try:
        async with httpx.AsyncClient(timeout=15) as http_client:
            response = await http_client.get(f"{base_url}/v1/models")
    except httpx.HTTPError:
        return {"valid": False, "message": f"Kon geen verbinding maken met {base_url}."}

    if response.status_code >= 400:
        return {"valid": False, "message": f"Service gaf een foutmelding ({response.status_code})."}

    try:
        model_ids = [item.get("id") for item in response.json().get("data", [])]
    except ValueError:
        return {"valid": False, "message": "Verbinding gelukt, maar het antwoord kon niet gelezen worden."}

    if model in model_ids:
        return {"valid": True, "message": f"Verbinding gelukt, model '{model}' is geladen."}
    if model_ids:
        return {
            "valid": False,
            "message": f"Verbinding gelukt, maar model '{model}' staat er niet bij. Geladen: {', '.join(model_ids)}.",
        }
    return {"valid": True, "message": "Verbinding gelukt (geen modellenlijst ontvangen om te vergelijken)."}
