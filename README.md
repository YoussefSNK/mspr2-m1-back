# FutureKawa — Backend (MSPR Bloc 4)

Solution de suivi des stocks et conditions de stockage de café vert. Architecture distribuée multi-pays (Brésil, Équateur, Colombie) + siège central.

## Architecture

```
IoT (capteur) → MQTT (Mosquitto) → Backend pays (FastAPI) → PostgreSQL
                                         ↓
                              Backend central siège (FastAPI)
                                         ↓
                                    Frontend Web
```

Chaque pays dispose de son propre backend, broker MQTT et base PostgreSQL. Le backend central agrège les données via API REST.

## Lancement rapide

```bash
cp .env.example .env
docker compose up --build
```

| Service             | URL locale              |
|---------------------|-------------------------|
| Backend Brésil      | http://localhost:8001   |
| Backend Équateur    | http://localhost:8002   |
| Backend Colombie    | http://localhost:8003   |
| Backend Central     | http://localhost:9000   |
| Docs API (Swagger)  | http://localhost:8001/docs |

## Scénario de démo

```bash
bash scripts/seed_demo.sh
```

Ce script : crée des lots, envoie des mesures (normale + hors seuil), consulte les alertes, affiche le FIFO, appelle le backend central.

## Tests

### Backend pays (TDD)

```bash
cd backend-pays
pip install -e ".[test]"
pytest tests/ -v
```

### Backend central

```bash
cd backend-central
pip install -e ".[test]"
pytest tests/ -v
```

### Couverture

```bash
pytest tests/ --cov=app --cov-report=term-missing
```

## Règles métier

| Pays     | Temp. idéale | Humidité idéale | Tolérance temp. | Tolérance hum. |
|----------|-------------|-----------------|-----------------|----------------|
| Brésil   | 29 °C       | 55 %            | ± 3 °C          | ± 2 %          |
| Équateur | 31 °C       | 60 %            | ± 3 °C          | ± 2 %          |
| Colombie | 26 °C       | 80 %            | ± 3 °C          | ± 2 %          |

Un lot stocké depuis **plus de 365 jours** déclenche une alerte `lot_trop_ancien` et passe au statut `perime`.

## MQTT — Raspberry Pi

| Paramètre | Valeur |
|-----------|--------|
| Adresse IP | `10.3.141.1` (fallback : `172.20.10.11`) |
| Port | `1883` |
| Topic | `futurkawa/entrepot/bresil` |

> **Attention** : le topic utilise `futurkawa` (sans 'e'), pas `futurekawa`.

Le pays et l'entrepôt sont extraits automatiquement du topic — ils ne font **pas** partie du payload.

Payload JSON envoyé par le Raspberry Pi :
```json
{
  "timestamp": 1718615743,
  "temperature": 28.4,
  "humidity": 55.2,
  "status": "OK"
}
```

Mapping interne : `humidity` → `humidite`, `status` → `statut`, `timestamp` (Unix) → `date_mesure` (datetime UTC).

## Principales routes API

### Backend pays (`/api/...`)

| Méthode | Route                          | Description                        |
|---------|--------------------------------|------------------------------------|
| GET     | /api/lots                      | Liste tous les lots (tri date)      |
| GET     | /api/lots/fifo                 | Lots actifs triés FIFO             |
| POST    | /api/lots                      | Créer un lot                        |
| PUT     | /api/lots/{id}                 | Mettre à jour un lot               |
| DELETE  | /api/lots/{id}                 | Supprimer un lot                    |
| GET     | /api/lots/{id}/mesures         | Mesures d'un lot                   |
| GET     | /api/mesures                   | Mesures (filtre pays/entrepot)     |
| POST    | /api/mesures                   | Simuler une mesure IoT             |
| GET     | /api/alertes                   | Liste des alertes                  |
| PUT     | /api/alertes/{id}/resoudre     | Résoudre une alerte                |
| POST    | /api/alertes/check-lots-anciens| Vérifier les lots périmés          |

### Backend central (`/central/...`)

| Méthode | Route                          | Description                    |
|---------|--------------------------------|--------------------------------|
| GET     | /central/stocks                | Stocks FIFO consolidés         |
| GET     | /central/lots                  | Tous les lots                  |
| GET     | /central/mesures               | Toutes les mesures             |
| GET     | /central/alertes               | Toutes les alertes             |
| GET     | /central/pays/{pays}/lots      | Lots d'un pays                 |
| GET     | /central/pays/{pays}/alertes   | Alertes d'un pays              |

## CI/CD

Le `Jenkinsfile` à la racine orchestre : install → lint (ruff) → tests → build Docker → archive artefacts.

## Variables d'environnement

Voir `.env.example` pour la liste complète.
