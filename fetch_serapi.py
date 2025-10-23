#!/usr/bin/env python3
"""
fetch_serapi_paris_abidjan_dec2025.py
Recherche aller-retour Paris (CDG) → Abidjan (ABJ)
Période : 22 décembre 2025 au 14 janvier 2026
"""

from serpapi import GoogleSearch
import csv
import os
import json

# ✅ Ta clé API SerpApi
API_KEY = "e5bd8b53e35e2c6ba927d5b127d834b83ee7eb07b1366bd7f66c249a481fa265"

# 🗓️ Période du voyage
date_depart = "2025-12-22"
date_retour = "2026-01-14"

# 🧳 Paramètres de recherche
params = {
    "engine": "google_flights",
    "departure_id": "CDG",   # Paris
    "arrival_id": "ABJ",     # Abidjan
    "outbound_date": date_depart,
    "return_date": date_retour,
    "currency": "EUR",
    "hl": "fr",
    "type": 1,  # Aller-retour
    "api_key": API_KEY,
}

print(f"🔎 Recherche de vols Paris (CDG) → Abidjan (ABJ)")
print(f"📅 Départ : {date_depart} | Retour : {date_retour}\n")

# 📂 Dossier de sortie
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

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
        print(f"✅ {len(flights)} vols trouvés !\n")

        for f in flights[:5]:
            print(
                f"✈️ {f['airline']} | {f['departure_airport']} → {f['arrival_airport']} "
                f"({f['departure_time']} → {f['arrival_time']}) | "
                f"Durée: {f['duration']} min | Prix: {f['price']} €"
            )

        # 💾 Sauvegarde CSV
        output_file = os.path.join(
            OUTPUT_DIR, f"vols_paris_abidjan_{date_depart}_retour_{date_retour}.csv"
        )

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

        print(f"\n📁 Résultats enregistrés dans : {output_file}")

except Exception as e:
    print(f"❌ Erreur : {e}")
