"""
Simule le Raspberry Pi en envoyant des messages MQTT vers un backend pays.
Usage :
    python scripts/simulate_pi.py                  # bresil, valeurs normales
    python scripts/simulate_pi.py equateur         # equateur
    python scripts/simulate_pi.py bresil anomalie  # bresil, valeurs hors seuil
"""
import sys
import time
import json
import paho.mqtt.client as mqtt

PAYS = sys.argv[1] if len(sys.argv) > 1 else "bresil"
MODE = sys.argv[2] if len(sys.argv) > 2 else "normal"

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
valeurs = SCENARIOS.get(PAYS, SCENARIOS["bresil"])[MODE]
topic = f"futurkawa/entrepot/{PAYS}"

payload = {
    "timestamp": int(time.time()),
    **valeurs,
}

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect("localhost", port, keepalive=10)

msg = json.dumps(payload)
client.publish(topic, msg)
client.disconnect()

print(f"[OK] Publié sur {topic}:{port}")
print(f"     Payload : {msg}")
