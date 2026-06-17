#!/usr/bin/env bash
# Seed de démonstration : crée des lots et des mesures sur le backend Brésil
set -e

BASE_URL="${1:-http://localhost:8001}"

echo "==> Création des lots (Brésil)"
curl -s -X POST "$BASE_URL/api/lots" \
  -H "Content-Type: application/json" \
  -d '{"lot_code":"LOT-BR-001","pays":"bresil","exploitation":"Fazenda Norte","entrepot":"entrepot-1","date_stockage":"2025-01-10T08:00:00Z","statut":"conforme"}' | python -m json.tool

curl -s -X POST "$BASE_URL/api/lots" \
  -H "Content-Type: application/json" \
  -d '{"lot_code":"LOT-BR-002","pays":"bresil","exploitation":"Fazenda Sul","entrepot":"entrepot-2","date_stockage":"2025-03-05T08:00:00Z","statut":"conforme"}' | python -m json.tool

echo "==> Création d'un lot ancien (> 365 jours)"
curl -s -X POST "$BASE_URL/api/lots" \
  -H "Content-Type: application/json" \
  -d '{"lot_code":"LOT-BR-ANCIEN","pays":"bresil","exploitation":"Fazenda Norte","entrepot":"entrepot-1","date_stockage":"2024-01-01T08:00:00Z","statut":"conforme"}' | python -m json.tool

echo "==> Envoi mesure normale"
curl -s -X POST "$BASE_URL/api/mesures" \
  -H "Content-Type: application/json" \
  -d '{"pays":"bresil","entrepot":"entrepot-1","temperature":29.0,"humidite":55.0,"statut":"ok","date_mesure":"2026-06-16T10:00:00Z"}' | python -m json.tool

echo "==> Envoi mesure hors seuil (déclenchera une alerte)"
curl -s -X POST "$BASE_URL/api/mesures" \
  -H "Content-Type: application/json" \
  -d '{"pays":"bresil","entrepot":"entrepot-1","temperature":36.0,"humidite":62.0,"statut":"ok","date_mesure":"2026-06-16T11:00:00Z"}' | python -m json.tool

echo "==> Consultation des alertes"
curl -s "$BASE_URL/api/alertes" | python -m json.tool

echo "==> FIFO lots actifs"
curl -s "$BASE_URL/api/lots/fifo" | python -m json.tool

echo "==> Vérification lots anciens"
curl -s -X POST "$BASE_URL/api/alertes/check-lots-anciens" | python -m json.tool

echo "==> Consultation backend central siège"
CENTRAL_URL="${2:-http://localhost:9000}"
curl -s "$CENTRAL_URL/central/lots" | python -m json.tool
curl -s "$CENTRAL_URL/central/alertes" | python -m json.tool
