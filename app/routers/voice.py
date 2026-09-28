from __future__ import annotations

import json

import httpx
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile

from app.auth.dependencies import require_user
from app.config import settings
from app.models.user import User

router = APIRouter(prefix="/voice", tags=["voice"])

# Fase 2 (zie BACKLOG.md): het model dat bepaalt welk type item het transcript moet
# worden -- bewust een klein/goedkoop model, want dit is een simpele classificatietaak
# (geen lange generatie).
_CLASSIFY_MODEL = "gpt-4o-mini"
_CLASSIFY_TYPES = {"task", "note", "kanban_card", "snippet"}
_CLASSIFY_SYSTEM_PROMPT = (
    "Je bepaalt welk type item een gesproken transcript uit een persoonlijke "
    "productivity-app moet worden. Het transcript kan Nederlands of Engels zijn. "
    "Antwoord ALLEEN met geldige JSON, zonder uitleg erbuiten, in dit exacte formaat: "
    '{"type": "task" | "note" | "kanban_card" | "snippet", '
    '"title": "korte titel, max ~60 tekens, zelfde taal als het transcript", '
    '"tags": ["los", "trefwoord"]}. '
    "Kies 'task' voor een concrete actie/to-do. Kies 'kanban_card' alleen als het "
    "transcript expliciet een project- of bordcontext noemt (bv. 'zet op het bord ...'). "
    "Kies 'snippet' alleen als het transcript letterlijk code, een commando of "
    "configuratie bevat. Kies in alle andere gevallen 'note' -- dat is de veilige "
    "standaardkeuze bij twijfel. Verzin geen tags die niet in het transcript passen; "
    "een lege tags-lijst mag."
)


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


@router.post("/classify")
async def classify(transcript: str = Form(...), user: User = Depends(require_user)) -> dict:
    """Fase 2 (zie BACKLOG.md): laat ChatGPT bepalen welk type item het transcript moet
    worden (taak/notitie/kanban-kaart/snippet) i.p.v. dat de gebruiker dat altijd zelf via
    de "Opslaan als"-keuzelijst kiest. Bepaalt bewust ALLEEN type/titel/tags -- de inhoud
    zelf blijft het transcript dat de gebruiker net gecontroleerd/gecorrigeerd heeft (de
    bevestigingsstap uit fase 1), zodat er geen tweede laag AI-herschrijving boven op de
    spraakherkenning komt. Dit hele resultaat is een suggestie: opslaan gebeurt pas als de
    gebruiker zelf op de "Opslaan als ..."-knop klikt, met de velden die op dat moment in
    het formulier staan."""
    if not transcript.strip():
        raise HTTPException(status_code=400, detail="Geen tekst om te classificeren")
    if not user.openai_api_key:
        raise HTTPException(
            status_code=400,
            detail="Stel eerst een OpenAI API-sleutel in via Account → OpenAI API-sleutel.",
        )

    try:
        async with httpx.AsyncClient(timeout=30) as http_client:
            response = await http_client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {user.openai_api_key}"},
                json={
                    "model": _CLASSIFY_MODEL,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": _CLASSIFY_SYSTEM_PROMPT},
                        {"role": "user", "content": transcript},
                    ],
                },
            )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="Kan de OpenAI API niet bereiken.") from exc

    if response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"OpenAI gaf een foutmelding ({response.status_code}): {response.text[:300]}",
        )

    try:
        raw_content = response.json()["choices"][0]["message"]["content"]
        parsed = json.loads(raw_content)
    except (KeyError, IndexError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Kon het antwoord van OpenAI niet lezen.") from exc

    item_type = parsed.get("type") if parsed.get("type") in _CLASSIFY_TYPES else "note"
    title = (parsed.get("title") or "").strip()[:200] or "Voice-item"
    raw_tags = parsed.get("tags") or []
    if isinstance(raw_tags, list):
        tags = ", ".join(str(t).strip() for t in raw_tags if str(t).strip())
    else:
        tags = str(raw_tags).strip()

    return {"type": item_type, "title": title, "tags": tags}
