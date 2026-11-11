"""Snippets als leesbare bestanden naar een (privé) git-repo pushen.

Per snippet een map `snippets/<titel>-<id>/` met de echte bestanden plus een README.md
(titel, beschrijving, tags). De repo spiegelt de app: verwijderde snippets verdwijnen uit de
werkmap, de git-historie bewaart ze. Authenticatie via een token dat alleen als
HTTP-header per commando meegegeven wordt, dus nooit in .git/config of de remote-URL.
"""
from __future__ import annotations

import base64
import json
import logging
import re
import shutil
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from sqlalchemy.orm import Session, selectinload

from app.config import DATA_DIR, settings
from app.database import SessionLocal
from app.models.snippet import Snippet

log = logging.getLogger(__name__)

REPO_DIR = DATA_DIR / "snippets-git"
STATUS_FILE = DATA_DIR / "snippets-git-status.json"
_lock = threading.Lock()


class GitPushError(Exception):
    pass


def is_configured() -> bool:
    return bool(settings.snippets_git_repo)


def _safe_filename(name: str) -> str:
    return re.sub(r"[^\w.\- ]+", "_", Path(name.replace("\\", "/")).name).strip(". ") or "bestand.txt"


def _with_id(name: str, snippet_id: int) -> str:
    stem, dot, ext = name.rpartition(".")
    return f"{stem}-{snippet_id}.{ext}" if dot and stem else f"{name}-{snippet_id}"


def _git(args: list[str], cwd: Path | None = None, auth: bool = False) -> str:
    # safe.directory: op Unraid is het data-volume van 99:100 terwijl de container als root draait;
    # git weigert dan ("dubious ownership"). Dit is onze eigen werkmap, dus vertrouwen we die.
    cmd = ["git", "-c", "core.quotepath=off", "-c", f"safe.directory={REPO_DIR}"]
    if auth and settings.snippets_git_token:
        raw = base64.b64encode(f"x-access-token:{settings.snippets_git_token}".encode()).decode()
        cmd += ["-c", f"http.extraHeader=Authorization: Basic {raw}"]
    cmd += args
    env = {"GIT_TERMINAL_PROMPT": "0", "PATH": "/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin", "HOME": str(DATA_DIR)}
    try:
        res = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=180)
    except FileNotFoundError as exc:
        raise GitPushError("git is niet geïnstalleerd in deze omgeving") from exc
    except subprocess.TimeoutExpired as exc:
        raise GitPushError("git duurde te lang (time-out)") from exc
    if res.returncode != 0:
        msg = (res.stderr or res.stdout).strip()
        if settings.snippets_git_token:
            msg = msg.replace(settings.snippets_git_token, "***")
        raise GitPushError(msg[-600:] or "git-fout")
    return res.stdout


def _ensure_repo() -> None:
    if (REPO_DIR / ".git").exists():
        return
    REPO_DIR.mkdir(parents=True, exist_ok=True)
    if any(REPO_DIR.iterdir()):
        shutil.rmtree(REPO_DIR)
        REPO_DIR.mkdir(parents=True)
    _git(["clone", settings.snippets_git_repo, str(REPO_DIR)], auth=True)
    if settings.snippets_git_branch:
        _git(["checkout", "-B", settings.snippets_git_branch], cwd=REPO_DIR)


def _write_tree(db: Session) -> int:
    """Alle snippetbestanden platgeslagen in één map `snippets/`, zonder submappen. Een
    bestandsnaam die vaker voorkomt krijgt het snippet-id erachter (`naam-12.ps1`), zodat niets
    overschreven wordt. Titel/tags/beschrijving staan in de index-README in de root."""
    root = REPO_DIR / "snippets"
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    snippets = (
        db.query(Snippet).options(selectinload(Snippet.files), selectinload(Snippet.tags)).order_by(Snippet.title).all()
    )
    counts: dict[str, int] = {}
    for sn in snippets:
        for f in sn.files:
            key = _safe_filename(f.filename).lower()
            counts[key] = counts.get(key, 0) + 1
    index = ["# Snippets", "", f"{len(snippets)} snippets, automatisch geëxporteerd uit Productivity Suite.", "",
             "| Snippet | Tags | Bestanden | Beschrijving |", "|---|---|---|---|"]
    for sn in snippets:
        links = []
        used_here: set[str] = set()
        for f in sn.files:
            fname = _safe_filename(f.filename)
            if counts[fname.lower()] > 1 or fname.lower() in used_here:
                fname = _with_id(fname, sn.id)
            used_here.add(fname.lower())
            (root / fname).write_text(f.content or "", encoding="utf-8")
            links.append(f"[{fname}](snippets/{quote(fname)})")
        tags = ", ".join(sorted(t.name for t in sn.tags))
        desc = (sn.description or "").replace("\n", " ").replace("|", "\\|")
        title = sn.title.replace("|", "\\|")
        index.append(f"| {title} | {tags} | {', '.join(links)} | {desc} |")
    (REPO_DIR / "README.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    return len(snippets)


def _save_status(ok: bool, message: str) -> None:
    STATUS_FILE.write_text(json.dumps({"ok": ok, "message": message, "at": datetime.now().isoformat(timespec="seconds")}))


def last_status() -> dict | None:
    try:
        return json.loads(STATUS_FILE.read_text())
    except (OSError, ValueError):
        return None


def push_snippets(db: Session) -> str:
    """Exporteert alle snippets, commit en pusht. Geeft een melding terug of gooit GitPushError."""
    if not is_configured():
        raise GitPushError("Geen git-repo ingesteld (SNIPPETS_GIT_REPO).")
    if settings.snippets_git_token and not settings.snippets_git_repo.startswith("https://"):
        raise GitPushError("Met een token moet de repo-URL met https:// beginnen.")
    with _lock:
        try:
            _ensure_repo()
            count = _write_tree(db)
            _git(["add", "-A"], cwd=REPO_DIR)
            committed = bool(_git(["status", "--porcelain"], cwd=REPO_DIR).strip())
            if committed:
                _git(["-c", "user.name=Productivity Suite", "-c", "user.email=productivity-suite@localhost",
                      "commit", "-m", f"Snippets bijgewerkt ({count} snippets, {datetime.now():%Y-%m-%d %H:%M})"],
                     cwd=REPO_DIR)
            # Altijd pushen: een eerdere poging kan wel gecommit maar niet gepusht zijn (bv. door
            # een fout met het token); dan staat de commit lokaal klaar zonder dat er "wijzigingen" zijn.
            out = _git(["push", "--porcelain", "origin", "HEAD"], cwd=REPO_DIR, auth=True)
            if not committed and "[up to date]" in out:
                msg = f"Geen wijzigingen ({count} snippets staan al in de repo)."
            else:
                msg = f"{count} snippets gepusht naar git."
        except GitPushError as exc:
            _save_status(False, str(exc))
            raise
        _save_status(True, msg)
        return msg


def start_auto_push() -> None:
    """Dagelijks een push als SNIPPETS_GIT_REPO en SNIPPETS_GIT_AUTO aan staan."""
    if not (is_configured() and settings.snippets_git_auto):
        return

    def loop() -> None:
        while True:
            threading.Event().wait(24 * 60 * 60 if last_status() else 120)
            try:
                with SessionLocal() as db:
                    push_snippets(db)
            except Exception:
                log.exception("Automatische snippet-push mislukt")

    threading.Thread(target=loop, name="snippets-git", daemon=True).start()
