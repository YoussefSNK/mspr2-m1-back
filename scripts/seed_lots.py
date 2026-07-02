"""
Alimente les backends pays avec un jeu de lots de démonstration, via l'API REST
(POST /api/lots). Les lots remontent automatiquement dans le backend central
(/central/lots), donc le front FutureKawa les affiche sans autre manipulation.

Usage :
    python scripts/seed_lots.py            # crée les lots (idempotent : ignore les 409)
    python scripts/seed_lots.py --purge    # supprime d'abord tous les lots existants

Prérequis : `docker compose up` (backends pays exposés sur 8001/8002/8003).
"""
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

# Ports exposés par docker-compose pour chaque backend pays
PAYS_PORTS = {"bresil": 8001, "equateur": 8002, "colombie": 8003}

now = datetime.now(timezone.utc)


def iso(days_ago: int) -> str:
    return (now - timedelta(days=days_ago)).isoformat()


# Jeu de lots : on varie `date_stockage` pour couvrir les 3 statuts métier
#   - récent            -> conforme
#   - > 365 j           -> périmé (le front classe sur l'âge)
#   - statut en_alerte  -> forcé pour montrer une alerte
LOTS = [
    # --- Brésil (Minas Gerais) ---
    {"lot_code": "BR-2511", "pays": "bresil", "exploitation": "Fazenda Bom Jardim",  "entrepot": "Entrepôt Santos A1",   "date_stockage": iso(12)},
    {"lot_code": "BR-2503", "pays": "bresil", "exploitation": "Fazenda Serra Verde", "entrepot": "Entrepôt Santos A2",   "date_stockage": iso(28)},
    {"lot_code": "BR-2419", "pays": "bresil", "exploitation": "Fazenda Bom Jardim",  "entrepot": "Entrepôt Santos B1",   "date_stockage": iso(96)},
    {"lot_code": "BR-2406", "pays": "bresil", "exploitation": "Fazenda Serra Verde", "entrepot": "Entrepôt Varginha C1",  "date_stockage": iso(158), "statut": "en_alerte"},
    {"lot_code": "BR-2347", "pays": "bresil", "exploitation": "Sítio Aurora",        "entrepot": "Entrepôt Varginha C1",  "date_stockage": iso(372)},
    # --- Équateur (Loja) ---
    {"lot_code": "EC-2509", "pays": "equateur", "exploitation": "Hacienda Vilcabamba", "entrepot": "Entrepôt Loja 2",     "date_stockage": iso(19)},
    {"lot_code": "EC-2502", "pays": "equateur", "exploitation": "Hacienda Loja Alta",  "entrepot": "Entrepôt Loja 1",     "date_stockage": iso(34)},
    {"lot_code": "EC-2438", "pays": "equateur", "exploitation": "Finca El Cisne",      "entrepot": "Entrepôt Loja 2",     "date_stockage": iso(80),  "statut": "en_alerte"},
    {"lot_code": "EC-2410", "pays": "equateur", "exploitation": "Hacienda Loja Alta",  "entrepot": "Entrepôt Catamayo 1", "date_stockage": iso(142)},
    {"lot_code": "EC-2351", "pays": "equateur", "exploitation": "Finca El Cisne",      "entrepot": "Entrepôt Loja 1",     "date_stockage": iso(388)},
    # --- Colombie (Huila) ---
    {"lot_code": "CO-2508", "pays": "colombie", "exploitation": "Hacienda Pitalito",   "entrepot": "Entrepôt Huila 2",    "date_stockage": iso(23)},
    {"lot_code": "CO-2504", "pays": "colombie", "exploitation": "Finca La Esperanza",  "entrepot": "Entrepôt Huila 1",    "date_stockage": iso(41)},
    {"lot_code": "CO-2461", "pays": "colombie", "exploitation": "Finca El Roble",      "entrepot": "Entrepôt Neiva 1",    "date_stockage": iso(67)},
    {"lot_code": "CO-2427", "pays": "colombie", "exploitation": "Hacienda Pitalito",   "entrepot": "Entrepôt Huila 2",    "date_stockage": iso(104)},
    {"lot_code": "CO-2413", "pays": "colombie", "exploitation": "Finca La Esperanza",  "entrepot": "Entrepôt Neiva 1",    "date_stockage": iso(165), "statut": "en_alerte"},
    {"lot_code": "CO-2342", "pays": "colombie", "exploitation": "Finca El Roble",      "entrepot": "Entrepôt Huila 1",    "date_stockage": iso(401)},
]


def req(method: str, url: str, body: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method,
                               headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=8) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        return e.code, None


def purge():
    for pays, port in PAYS_PORTS.items():
        status, lots = req("GET", f"http://localhost:{port}/api/lots")
        for lot in (lots or []):
            req("DELETE", f"http://localhost:{port}/api/lots/{lot['id']}")
        print(f"[purge] {pays}: {len(lots or [])} lot(s) supprimé(s)")


def seed():
    ok = skip = err = 0
    for lot in LOTS:
        port = PAYS_PORTS[lot["pays"]]
        status, _ = req("POST", f"http://localhost:{port}/api/lots", lot)
        if status == 201:
            ok += 1
        elif status == 409:
            skip += 1  # existe déjà
        else:
            err += 1
            print(f"[erreur] {lot['lot_code']} -> HTTP {status}")
    print(f"[seed] créés={ok}  déjà présents={skip}  erreurs={err}")


if __name__ == "__main__":
    if "--purge" in sys.argv:
        purge()
    seed()
    print("Terminé. Rafraîchis le front FutureKawa pour voir les lots.")
