#!/usr/bin/env python3
"""
fetch_flights_generic.py
Collecte générique des prix de vols via SerpAPI (Google Flights)
"""

from google_search_results import GoogleSearch
import csv
import os
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv

# ------------------------
# Chargement variables d'environnement
# ------------------------
load_dotenv()
API_KEY = os.getenv("SERPAPI_KEY")

# ------------------------
# Arguments CLI
# ------------------------
parser = argparse.ArgumentParser(description="Analyse dynamique des vols")
parser.add_argument("--from", dest="departure", required=True, help="Aéroport départ (ex: CDG)")
parser.add_argument("--to", dest="arrival", required=True, help="Aéroport arrivée (ex: ABJ)")
parser.add_argument("--out", dest="outbound_date", required=True, help="Date aller YYYY-MM-DD")
parser.add_argument("--ret", dest="return_date", required=True, help="Date retour YYYY-MM-DD")

args = parser.parse_args()

# ------------------------
# Préparation sortie
# ------------------------
OUTPUT_DIR = "data/raw"
os.makedirs(OUTPUT_DIR, exist_ok=True)

today = datetime.now().strftime("%Y-%m-%d")
route = f"{args.departure}-{args.arrival}"

output_file = os.path.join(
    OUTPUT_DIR, f"flights_{route}_{today}.csv"
)

# ------------------------
# Paramètres SerpAPI
# ------------------------
params = {
    "engine": "google_flights",
    "departure_id": args.departure,
    "arrival_id": args.arrival,
    "outbound_date": args.outbound_date,
    "return_date": args.return_date,
    "currency": "EUR",
    "hl": "fr",
    "type": 1,
    "api_key": API_KEY,
}

print(f"🔎 Route : {route}")
print(f"📅 Aller : {args.outbound_date} | Retour : {args.return_date}")
print(f"📆 Collecte du {today}\n")

# ------------------------
# Recherche vols
# ------------------------
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
                    "route": route,
                    "search_date": today,
                    "outbound_date": args.outbound_date,
                    "return_date": args.return_date,
                    "airline": flight.get("airline"),
                    "price": price,
                    "departure_airport": flight.get("departure_airport", {}).get("id"),
                    "arrival_airport": flight.get("arrival_airport", {}).get("id"),
                    "departure_time": flight.get("departure_airport", {}).get("time"),
                    "arrival_time": flight.get("arrival_airport", {}).get("time"),
                    "duration_min": total_duration,
                    "flight_number": flight.get("flight_number"),
                })

    if not flights:
        print("⚠️ Aucun vol trouvé")
        print(json.dumps(results, indent=2))
    else:
        print(f"✅ {len(flights)} vols collectés")

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=flights[0].keys())
            writer.writeheader()
            writer.writerows(flights)

        print(f"📁 Fichier généré : {output_file}")

except Exception as e:
    print(f"❌ Erreur : {e}")
