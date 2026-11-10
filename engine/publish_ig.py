#!/usr/bin/env python3
"""
Publicador Instagram — The Tech Room (Instagram API with Instagram Login, graph.instagram.com)

Substitui o Metricool. Publica carrosséis e reels direto na conta profissional, sem limite mensal
(limite da Meta: 100 publicações por 24 h). A mídia precisa estar em URL pública: usamos o branch
"media" (engine/media_branch.py), servido por raw.githubusercontent.com.

Variáveis de ambiente (secrets do repositório):
  IG_USER_ID        id da conta profissional (painel do app → Instagram → API setup → Gerar tokens)
  IG_ACCESS_TOKEN   token. Login unificado: SUAT, nunca expira. Login do Instagram: 60 dias (`refresh-token`)
  IG_APP_ID / IG_APP_SECRET   id e chave secreta do app (Configurações → Básico); só para `debug`
  IG_API_BASE       opcional; padrão https://graph.facebook.com/v25.0 (unificado). Fluxo antigo: https://graph.instagram.com/v25.0
  GITHUB_TOKEN      para empurrar o branch media (no Actions já existe)
  GH_PAT            opcional: token fino com "Secrets: read/write" para `refresh-token --save` gravar o novo token

Uso:
  python3 engine/publish_ig.py carousel <slug> [--dry-run]       # posts/<slug>/NN.png → JPG → carrossel
  python3 engine/publish_ig.py reel <slug> [--dry-run]           # posts/<slug>/reel.mp4 + reel_cover.jpg → reel
  python3 engine/publish_ig.py due [--dry-run]                   # publica itens vencidos de fila-publicacao/*.json
  python3 engine/publish_ig.py refresh-token [--save]            # renova o token (válido por mais 60 dias)
  python3 engine/publish_ig.py limit                             # quota usada nas últimas 24 h
  python3 engine/publish_ig.py me                                # confere conta e token
  python3 engine/publish_ig.py debug                             # inspeciona o token (tipo, escopos, validade, ids)

Item da fila (fila-publicacao/<slug>-<tipo>.json):
  {"type": "carousel" | "reel", "slug": "...", "when": "2026-11-11T10:00:00-03:00", "hold": false}
  hold=true segura o item (equivale ao "segura N"). Depois de publicar, o item vai para fila-publicacao/feito/
  e a linha do slug em posts/historico.csv recebe status "publicado" e o permalink.
"""
import csv, json, os, shutil, subprocess, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Host da API: o login unificado (apps novos, token SUAT sem expiração) usa graph.facebook.com;
# o fluxo antigo "Instagram Login" usa graph.instagram.com. Troque com IG_API_BASE.
API = os.environ.get("IG_API_BASE", "https://graph.facebook.com/v25.0").rstrip("/")
FILA = ROOT / "fila-publicacao"
sys.path.insert(0, str(ROOT / "engine"))
import media_branch  # noqa: E402

IG = os.environ.get("IG_USER_ID", "")
TOKEN = os.environ.get("IG_ACCESS_TOKEN", "")
DRY = "--dry-run" in sys.argv


# ---------- API ----------
def api(method, path, **params):
    params = {k: v for k, v in params.items() if v is not None}
    params.setdefault("access_token", TOKEN)
    data = urllib.parse.urlencode(params).encode()
    url = f"{API}/{path.lstrip('/')}"
    if method == "GET":
        url += "?" + data.decode(); data = None
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            err = json.loads(body).get("error", {})
        except ValueError:
            err = {}
        if err.get("code") == 190:
            raise SystemExit("TOKEN INVÁLIDO (erro 190): o IG_ACCESS_TOKEN foi revogado ou expirou. Gere outro em "
                             "developers.facebook.com → app → Instagram → API setup with Unified login → Gerar token, "
                             f"e atualize o secret. Detalhe: {err.get('message', '')[:300]}")
        if err.get("code") == 4 or err.get("code") == 9:
            raise SystemExit(f"LIMITE DA API (erro {err['code']}): {err.get('message', '')[:300]}. Tente mais tarde.")
        raise SystemExit(f"Instagram API {e.code} em {method} {path}: {body[:800]}")


def need_auth():
    if not IG or not TOKEN:
        raise SystemExit("faltam IG_USER_ID e/ou IG_ACCESS_TOKEN no ambiente")


def wait_container(cid, max_s=900, every=15):
    """Espera o contêiner ficar FINISHED. Vídeos levam de 30 s a alguns minutos."""
    t0 = time.time()
    while True:
        st = api("GET", cid, fields="status_code,status")
        code = st.get("status_code")
        if code == "FINISHED":
            return
        if code in ("ERROR", "EXPIRED"):
            raise SystemExit(f"contêiner {cid} com status {code}: {st.get('status')}")
        if time.time() - t0 > max_s:
            raise SystemExit(f"contêiner {cid} não ficou pronto em {max_s}s (status {code})")
        print(f"  aguardando processamento ({code}) …"); time.sleep(every)


def publish_container(cid):
    res = api("POST", f"{IG}/media_publish", creation_id=cid)
    mid = res["id"]
    info = api("GET", mid, fields="permalink,media_type,timestamp")
    return mid, info.get("permalink", "")


def comment(media_id, text):
    try:
        res = api("POST", f"{media_id}/comments", message=text)
        print(f"  comentário publicado: {res.get('id')}")
    except SystemExit as e:
        print(f"  AVISO: não consegui publicar o comentário com as fontes ({e}). Coloque-as na legenda ou comente à mão.")


# ---------- preparação de mídia ----------
def to_jpgs(slug):
    """Converte posts/<slug>/NN.png em JPGs (o Instagram só aceita JPEG) e devolve os caminhos."""
    from PIL import Image
    src = sorted((ROOT / "posts" / slug).glob("[0-9][0-9].png"))
    if not src:
        raise SystemExit(f"nenhuma página NN.png em posts/{slug}")
    out = ROOT / "posts" / slug / "_ig"; out.mkdir(exist_ok=True)
    jpgs = []
    for p in src:
        j = out / f"{slug}-{p.stem}.jpg"
        if not j.exists() or j.stat().st_mtime < p.stat().st_mtime:
            Image.open(p).convert("RGB").save(j, "JPEG", quality=90, optimize=True, progressive=True)
        jpgs.append(j)
    return jpgs


def read_caption(slug, name="legenda.txt"):
    p = ROOT / "posts" / slug / name
    if not p.exists():
        raise SystemExit(f"falta posts/{slug}/{name}")
    cap = p.read_text(encoding="utf-8").strip()
    if len(cap) > 2200:
        raise SystemExit(f"legenda com {len(cap)} caracteres; o Instagram aceita 2.200")
    return cap


# ---------- publicações ----------
def publish_carousel(slug):
    DRY or need_auth()
    jpgs = to_jpgs(slug); cap = read_caption(slug)
    print(f"carrossel {slug}: {len(jpgs)} páginas")
    if DRY:
        print("  [dry-run] legenda:", cap[:120].replace("\n", " "), "…"); return None, ""
    urls = media_branch.push(jpgs)
    children = []
    for u in urls:
        c = api("POST", f"{IG}/media", image_url=u, is_carousel_item="true")
        children.append(c["id"])
    for c in children:
        wait_container(c, max_s=180, every=5)
    cont = api("POST", f"{IG}/media", media_type="CAROUSEL", children=",".join(children), caption=cap)
    wait_container(cont["id"], max_s=300, every=10)
    mid, link = publish_container(cont["id"])
    print(f"  publicado: {link}")
    return mid, link


def publish_reel(slug):
    DRY or need_auth()
    d = ROOT / "posts" / slug
    mp4, cover = d / "reel.mp4", d / "reel_cover.jpg"
    if not mp4.exists():
        raise SystemExit(f"falta {mp4}")
    cap = read_caption(slug, "reel_legenda.txt")
    fontes = (d / "reel_fontes.txt").read_text(encoding="utf-8").strip() if (d / "reel_fontes.txt").exists() else ""
    print(f"reel {slug}: {mp4.stat().st_size/1e6:.1f} MB")
    if DRY:
        print("  [dry-run] legenda:", cap[:120].replace("\n", " "), "…"); return None, ""
    files = [mp4] + ([cover] if cover.exists() else [])
    # nomes únicos no branch media (slug no nome)
    tmp = d / "_ig"; tmp.mkdir(exist_ok=True)
    named = []
    for f in files:
        t = tmp / f"{slug}-{f.name}"; shutil.copy2(f, t); named.append(t)
    urls = media_branch.push(named)
    params = dict(media_type="REELS", video_url=urls[0], caption=cap, share_to_feed="true")
    if cover.exists():
        params["cover_url"] = urls[1]
    cont = api("POST", f"{IG}/media", **params)
    wait_container(cont["id"], max_s=1200, every=20)
    mid, link = publish_container(cont["id"])
    print(f"  publicado: {link}")
    if fontes:
        comment(mid, fontes)
    return mid, link


# ---------- histórico e fila ----------
def marcar_historico(slug, link):
    p = ROOT / "posts" / "historico.csv"
    if not p.exists():
        return
    rows = list(csv.reader(p.open(encoding="utf-8")))
    changed = False
    for r in rows[1:]:
        if len(r) >= 8 and r[3] == slug:
            r[5] = "publicado"; r[7] = link or r[7]; changed = True
    if changed:
        with p.open("w", encoding="utf-8", newline="") as f:
            csv.writer(f, lineterminator="\n").writerows(rows)


def due():
    FILA.mkdir(exist_ok=True); (FILA / "feito").mkdir(exist_ok=True)
    now = datetime.now(timezone.utc)
    items = sorted(FILA.glob("*.json"))
    if not items:
        print("fila vazia"); return
    for it in items:
        d = json.loads(it.read_text(encoding="utf-8"))
        when = datetime.fromisoformat(d["when"])
        if when.tzinfo is None:
            raise SystemExit(f"{it.name}: 'when' precisa de fuso, ex. 2026-11-11T10:00:00-03:00")
        if d.get("hold"):
            print(f"segurado: {it.name}"); continue
        if when > now:
            print(f"ainda não: {it.name} ({d['when']})"); continue
        if DRY:
            print(f"[dry-run] publicaria {d['type']} {d['slug']}"); continue
        mid, link = publish_reel(d["slug"]) if d["type"] == "reel" else publish_carousel(d["slug"])
        d.update(published_at=datetime.now().astimezone().isoformat(timespec="seconds"), media_id=mid, permalink=link)
        (FILA / "feito" / it.name).write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        it.unlink(); marcar_historico(d["slug"], link)


def debug_token():
    """GET /debug_token: mostra tipo (USER/SYSTEM_USER), escopos, expiração e ids com acesso."""
    app_id, secret = os.environ.get("IG_APP_ID"), os.environ.get("IG_APP_SECRET")
    if not (TOKEN and app_id and secret):
        raise SystemExit("debug precisa de IG_ACCESS_TOKEN, IG_APP_ID e IG_APP_SECRET")
    res = api("GET", "debug_token", input_token=TOKEN, access_token=f"{app_id}|{secret}")
    print(json.dumps(res, indent=1, ensure_ascii=False))


def refresh_token(save=False):
    if "graph.facebook.com" in API:
        print("Token SUAT do login unificado não expira; renovação não se aplica."); return
    if not TOKEN:
        raise SystemExit("falta IG_ACCESS_TOKEN")
    res = api("GET", "refresh_access_token", grant_type="ig_refresh_token")
    new, days = res["access_token"], res.get("expires_in", 0) // 86400
    print(f"novo token válido por {days} dias")
    if save:
        pat = os.environ.get("GH_PAT")
        if not pat:
            raise SystemExit("--save precisa de GH_PAT (token fino com Secrets: read/write)")
        slug = media_branch.repo_slug()
        r = subprocess.run(["gh", "secret", "set", "IG_ACCESS_TOKEN", "--repo", slug], input=new, text=True,
                           capture_output=True, env={**os.environ, "GH_TOKEN": pat})
        if r.returncode:
            raise SystemExit(f"gh secret set falhou: {r.stderr}")
        print("secret IG_ACCESS_TOKEN atualizado")
    else:
        print(new)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__); raise SystemExit(1)
    cmd = args[0]
    if cmd == "carousel":
        mid, link = publish_carousel(args[1]); mid and marcar_historico(args[1], link)
    elif cmd == "reel":
        mid, link = publish_reel(args[1]); mid and marcar_historico(args[1], link)
    elif cmd == "due":
        due()
    elif cmd == "refresh-token":
        refresh_token(save="--save" in sys.argv)
    elif cmd == "limit":
        need_auth(); print(json.dumps(api("GET", f"{IG}/content_publishing_limit", fields="quota_usage,config"), indent=1))
    elif cmd == "debug":
        debug_token()
    elif cmd == "me":
        need_auth()
        # account_type só existe em graph.instagram.com (fluxo antigo); no login unificado dá erro 100
        campos = "id,username,media_count,followers_count" if "graph.facebook.com" in API else "id,username,account_type,media_count,followers_count"
        print(json.dumps(api("GET", IG, fields=campos), indent=1))
    else:
        print(__doc__); raise SystemExit(1)


if __name__ == "__main__":
    main()
