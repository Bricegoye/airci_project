#!/usr/bin/env python3
"""
fetch_serapi_paris_abidjan_daily.py
Recherche complète Paris (CDG) → Abidjan (ABJ)
Période fixe : départ 22 décembre 2025, retour 14 janvier 2026
Un fichier CSV par jour
"""

from serpapi import GoogleSearch
import csv
import os
import json
from datetime import datetime

# ------------------------
# Configuration utilisateur
# ------------------------
API_KEY = "e5bd8b53e35e2c6ba927d5b127d834b83ee7eb07b1366bd7f66c249a481fa265"
DATE_DEPART = "2025-12-22"
DATE_RETOUR = "2026-01-14"

# ------------------------
# Préparation dossier et CSV
# ------------------------
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
today = datetime.now().strftime("%Y-%m-%d")
output_file = os.path.join(OUTPUT_DIR, f"vols_paris_abidjan_{today}.csv")

# ------------------------
# Recherche des vols
# ------------------------
params = {
    "engine": "google_flights",
    "departure_id": "CDG",
    "arrival_id": "ABJ",
    "outbound_date": DATE_DEPART,
    "return_date": DATE_RETOUR,
    "currency": "EUR",
    "hl": "fr",
    "type": 1,
    "api_key": API_KEY,
}

print(f"🔎 Suivi complet du vol Paris (CDG) → Abidjan (ABJ)")
print(f"📅 Départ : {DATE_DEPART} | Retour : {DATE_RETOUR}")
print(f"📆 Exécution du {today}\n")

try:
    search = GoogleSearch(params)
    results = search.get_dict()
    flights = []

    for section in ["best_flights", "other_flights"]:
        for group in results.get(section, []):
            price = group.get("price")
            total_duration = group.get("total_duration")
            for flight in group.get("flights", []):
                flights.append({
                    "airline": flight.get("airline"),
                    "price": price,
                    "departure_airport": flight.get("departure_airport", {}).get("id"),
                    "arrival_airport": flight.get("arrival_airport", {}).get("id"),
                    "departure_time": flight.get("departure_airport", {}).get("time"),
                    "arrival_time": flight.get("arrival_airport", {}).get("time"),
                    "duration": total_duration,
                    "flight_number": flight.get("flight_number"),
                })

    if not flights:
        print("⚠️ Aucun vol trouvé. Voici la réponse brute :")
        print(json.dumps(results, indent=2))
    else:
        print(f"✅ {len(flights)} vols trouvés !")

        # 💾 Sauvegarde CSV du jour
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "airline", "price", "departure_airport", "arrival_airport",
                    "departure_time", "arrival_time", "duration", "flight_number",
                ],
            )
            writer.writeheader()
            writer.writerows(flights)

        print(f"📁 Résultats enregistrés dans : {output_file}")

except Exception as e:
    print(f"❌ Erreur : {e}")
