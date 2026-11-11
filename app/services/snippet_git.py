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


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:50] or "snippet"


def _safe_filename(name: str, used: set[str]) -> str:
    base = re.sub(r"[^\w.\- ]+", "_", Path(name.replace("\\", "/")).name).strip(". ") or "bestand.txt"
    candidate, n = base, 1
    while candidate.lower() in used or candidate.lower() == "readme.md":
        stem, dot, ext = base.rpartition(".")
        candidate = f"{stem or base}-{n}{dot}{ext}" if dot and stem else f"{base}-{n}"
        n += 1
    used.add(candidate.lower())
    return candidate


def _git(args: list[str], cwd: Path | None = None, auth: bool = False) -> str:
    cmd = ["git", "-c", "core.quotepath=off"]
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
    root = REPO_DIR / "snippets"
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    snippets = (
        db.query(Snippet).options(selectinload(Snippet.files), selectinload(Snippet.tags)).order_by(Snippet.title).all()
    )
    index = ["# Snippets", "", f"{len(snippets)} snippets, automatisch geëxporteerd uit Productivity Suite.", "",
             "| Snippet | Tags | Bestanden |", "|---|---|---|"]
    for sn in snippets:
        folder = f"{_slug(sn.title)}-{sn.id}"
        d = root / folder
        d.mkdir()
        used: set[str] = set()
        names = []
        for f in sn.files:
            fname = _safe_filename(f.filename, used)
            (d / fname).write_text(f.content or "", encoding="utf-8")
            names.append(fname)
        tags = ", ".join(sorted(t.name for t in sn.tags))
        readme = [f"# {sn.title}", ""]
        if sn.description:
            readme += [sn.description, ""]
        if tags:
            readme += [f"**Tags:** {tags}", ""]
        readme += ["**Bestanden:**", ""] + [f"- [{n}]({n})" for n in names]
        (d / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")
        index.append(f"| [{sn.title}](snippets/{folder}/README.md) | {tags} | {len(names)} |")
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
            if not _git(["status", "--porcelain"], cwd=REPO_DIR).strip():
                msg = f"Geen wijzigingen ({count} snippets staan al in de repo)."
            else:
                _git(["-c", "user.name=Productivity Suite", "-c", "user.email=productivity-suite@localhost",
                      "commit", "-m", f"Snippets bijgewerkt ({count} snippets, {datetime.now():%Y-%m-%d %H:%M})"],
                     cwd=REPO_DIR)
                _git(["push", "origin", "HEAD"], cwd=REPO_DIR, auth=True)
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
