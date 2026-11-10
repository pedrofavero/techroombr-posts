#!/usr/bin/env python3
"""
Hospedagem pública de mídia sem inflar o repositório — The Tech Room

Mantém o branch órfão "media" com UM único commit (sempre reescrito) contendo os arquivos
públicos que o Instagram precisa baixar: JPGs das páginas de carrossel, MP4 e capa dos reels.
Arquivos com mais de JANELA_DIAS são removidos a cada atualização (o Instagram já copiou).

URL pública de cada arquivo (servida direto, sem redirecionamento):
  https://raw.githubusercontent.com/<owner>/<repo>/media/<nome>

Uso:
  python3 engine/media_branch.py push <arquivo> [<arquivo> ...]        # envia e imprime as URLs
  python3 engine/media_branch.py url <nome>                             # só imprime a URL
  python3 engine/media_branch.py list                                   # lista o que está publicado

Precisa de git com permissão de push no repositório (no Actions: GITHUB_TOKEN com contents: write).
"""
import json, os, shutil, subprocess, sys, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRANCH = "media"
JANELA_DIAS = 45
MANIFESTO = "_manifesto.json"


def sh(cmd, cwd=None, check=True, quiet=False):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and r.returncode:
        raise SystemExit(f"falhou: {' '.join(cmd)}\n{r.stderr[-2000:]}")
    if not quiet and r.stdout.strip():
        print(r.stdout.strip())
    return r


def repo_slug():
    """owner/repo a partir do remote origin (aceita https e ssh)."""
    url = sh(["git", "remote", "get-url", "origin"], cwd=ROOT, quiet=True).stdout.strip()
    url = url.removesuffix(".git")
    if url.startswith("git@"):
        return url.split(":", 1)[1]
    return "/".join(url.rstrip("/").split("/")[-2:])


def remote_url():
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    slug = repo_slug()
    return f"https://x-access-token:{tok}@github.com/{slug}.git" if tok else f"https://github.com/{slug}.git"


def public_url(name):
    return f"https://raw.githubusercontent.com/{repo_slug()}/{BRANCH}/{name}"


def push(files):
    files = [Path(f) for f in files]
    for f in files:
        if not f.exists():
            raise SystemExit(f"arquivo não existe: {f}")
    tmp = Path(tempfile.mkdtemp(prefix="media_"))
    try:
        # tenta trazer o estado atual do branch (um commit só); se não existir, começa vazio
        r = subprocess.run(["git", "clone", "-q", "--depth", "1", "--branch", BRANCH, remote_url(), str(tmp / "w")],
                           capture_output=True, text=True)
        w = tmp / "w"
        if r.returncode:
            w.mkdir(); sh(["git", "init", "-q", "-b", BRANCH], cwd=w, quiet=True)
            sh(["git", "remote", "add", "origin", remote_url()], cwd=w, quiet=True)
        sh(["git", "config", "user.name", "techroom-bot"], cwd=w, quiet=True)
        sh(["git", "config", "user.email", "bot@techroombr.local"], cwd=w, quiet=True)
        man_path = w / MANIFESTO
        man = json.loads(man_path.read_text()) if man_path.exists() else {}
        now = time.time()
        # remove o que passou da janela
        for name, ts in list(man.items()):
            if now - ts > JANELA_DIAS * 86400:
                (w / name).unlink(missing_ok=True); man.pop(name)
        for f in files:
            shutil.copy2(f, w / f.name); man[f.name] = now
        (w / "README.md").write_text(
            f"# media\n\nBranch órfão reescrito a cada publicação. Arquivos públicos usados pelo Instagram por até {JANELA_DIAS} dias.\n"
            "Não edite à mão; veja engine/media_branch.py no branch main.\n", encoding="utf-8")
        man_path.write_text(json.dumps(man, indent=1, sort_keys=True))
        # um único commit: recria o histórico do zero
        sh(["git", "checkout", "-q", "--orphan", "tmp_media"], cwd=w, quiet=True)
        sh(["git", "add", "-A"], cwd=w, quiet=True)
        sh(["git", "commit", "-q", "-m", f"media: {', '.join(f.name for f in files)}"], cwd=w, quiet=True)
        sh(["git", "push", "-q", "-f", "origin", f"tmp_media:{BRANCH}"], cwd=w, quiet=True)
        urls = [public_url(f.name) for f in files]
        # espera o raw.githubusercontent.com servir (cache do GitHub leva alguns segundos)
        for u in urls:
            for _ in range(20):
                code = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-r", "0-10", u],
                                      capture_output=True, text=True).stdout.strip()
                if code in ("200", "206"):
                    break
                time.sleep(6)
            print(u, f"({code})")
        return urls
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def listar():
    tmp = Path(tempfile.mkdtemp(prefix="media_"))
    try:
        sh(["git", "clone", "-q", "--depth", "1", "--branch", BRANCH, remote_url(), str(tmp / "w")], quiet=True)
        man = json.loads((tmp / "w" / MANIFESTO).read_text())
        for name, ts in sorted(man.items(), key=lambda kv: kv[1]):
            print(time.strftime("%Y-%m-%d", time.gmtime(ts)), public_url(name))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); raise SystemExit(1)
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "push":
        push(args)
    elif cmd == "url":
        print(public_url(args[0]))
    elif cmd == "list":
        listar()
    else:
        print(__doc__); raise SystemExit(1)
