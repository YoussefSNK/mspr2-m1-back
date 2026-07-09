"""
Simule le Raspberry Pi en envoyant des messages MQTT vers un backend pays.

Mode one-shot (défaut) — envoie UNE mesure puis s'arrête :
    python scripts/simulate_pi.py                  # bresil, valeurs normales
    python scripts/simulate_pi.py equateur         # equateur
    python scripts/simulate_pi.py bresil anomalie  # bresil, valeurs hors seuil

Mode boucle — envoie une mesure toutes les N secondes (Ctrl+C pour arrêter) :
    python scripts/simulate_pi.py --loop                   # bresil, toutes les 5 s
    python scripts/simulate_pi.py bresil --loop            # idem
    python scripts/simulate_pi.py equateur anomalie --loop # equateur hors seuil, en boucle
    python scripts/simulate_pi.py bresil --loop 2          # toutes les 2 s

En mode boucle, les valeurs varient légèrement autour de la base pour rendre
les courbes température/humidité « vivantes » côté frontend.
"""
import sys
import time
import json
import random
import paho.mqtt.client as mqtt

# ── Parsing des arguments (on isole les flags des arguments positionnels) ──
args = sys.argv[1:]
LOOP = "--loop" in args
if LOOP:
    idx = args.index("--loop")
    # Intervalle optionnel juste après --loop (ex: --loop 2)
    if idx + 1 < len(args) and args[idx + 1].replace(".", "", 1).isdigit():
        INTERVAL = float(args[idx + 1])
        del args[idx:idx + 2]
    else:
        INTERVAL = 5.0
        del args[idx]

PAYS = args[0] if len(args) > 0 else "bresil"
MODE = args[1] if len(args) > 1 else "normal"

# Ports exposés par docker-compose
BROKER_PORTS = {"bresil": 1883, "equateur": 1884, "colombie": 1885}

# Valeurs normales vs hors seuil par pays
SCENARIOS = {
    "bresil": {
        "normal":   {"temperature": 28.4, "humidity": 54.0, "status": "OK"},
        "anomalie": {"temperature": 36.0, "humidity": 68.0, "status": "WARNING"},
    },
    "equateur": {
        "normal":   {"temperature": 30.5, "humidity": 59.0, "status": "OK"},
        "anomalie": {"temperature": 38.0, "humidity": 72.0, "status": "WARNING"},
    },
    "colombie": {
        "normal":   {"temperature": 25.0, "humidity": 78.0, "status": "OK"},
        "anomalie": {"temperature": 32.0, "humidity": 90.0, "status": "WARNING"},
    },
}

port = BROKER_PORTS.get(PAYS, 1883)
base = SCENARIOS.get(PAYS, SCENARIOS["bresil"])[MODE]
topic = f"futurkawa/entrepot/{PAYS}"


def build_payload() -> dict:
    """Construit un payload. En mode boucle, applique une petite variation
    aléatoire (±0.5 °C / ±1 %) pour que les courbes ne soient pas plates."""
    temperature = base["temperature"]
    humidity = base["humidity"]
    if LOOP:
        temperature = round(temperature + random.uniform(-0.5, 0.5), 1)
        humidity = round(humidity + random.uniform(-1.0, 1.0), 1)
    return {
        "timestamp": int(time.time()),
        "temperature": temperature,
        "humidity": humidity,
        "status": base["status"],
    }


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect("localhost", port, keepalive=60)

if not LOOP:
    # ── Mode one-shot : un seul message, puis on quitte ──
    msg = json.dumps(build_payload())
    client.publish(topic, msg)
    client.disconnect()
    print(f"[OK] Publié sur {topic}:{port}")
    print(f"     Payload : {msg}")
else:
    # ── Mode boucle : publie jusqu'à Ctrl+C ──
    client.loop_start()  # gère le réseau MQTT en tâche de fond
    print(f"[LOOP] Publication sur {topic}:{port} toutes les {INTERVAL}s "
          f"(mode={MODE}) — Ctrl+C pour arrêter")
    n = 0
    try:
        while True:
            msg = json.dumps(build_payload())
            client.publish(topic, msg)
            n += 1
            print(f"[{n:04d}] {msg}")
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print(f"\n[STOP] {n} mesure(s) publiée(s). Arrêt propre.")
    finally:
        client.loop_stop()
        client.disconnect()
