#!/usr/bin/env python3
"""
evol_price.py
Analyse de l'évolution des prix des vols Paris (CDG) → Abidjan (ABJ)
Affiche la tendance du meilleur prix général et des compagnies aériennes
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# ------------------------------
# Configuration
# ------------------------------
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Lister tous les fichiers CSV disponibles
csv_files = sorted([f for f in os.listdir(OUTPUT_DIR) if f.endswith(".csv")])
if not csv_files:
    raise FileNotFoundError("Aucun fichier CSV trouvé dans le dossier 'output'.")

print(f"🧾 {len(csv_files)} fichiers trouvés :")
for f in csv_files:
    print(f"  - {f}")

# ------------------------------
# Initialisation des structures
# ------------------------------
dates = []
best_prices = []
company_prices = {}

# ------------------------------
# Lecture et agrégation
# ------------------------------
for file in csv_files:
    path = os.path.join(OUTPUT_DIR, file)
    df = pd.read_csv(path)

    if df.empty:
        continue

    # Extraire la date de collecte depuis le nom du fichier
    date_str = file.replace(".csv", "").split("_")[-1]
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print(f"⚠️ Nom de fichier inattendu : {file}")
        continue

    # Nettoyer les prix
    df["price"] = (
        df["price"].astype(str)
        .str.replace("[^0-9]", "", regex=True)
        .astype(float)
    )

    # Enregistrer la date
    dates.append(date_obj)

    # Prix minimum du jour
    best_prices.append(df["price"].min())

    # Prix par compagnie
    for airline, group in df.groupby("airline"):
        mean_price = group["price"].mean()
        if airline not in company_prices:
            company_prices[airline] = []
        company_prices[airline].append((date_obj, mean_price))

# ------------------------------
# Afficher un résumé rapide
# ------------------------------
print("\n💡 Résumé des prix moyens par compagnie :")
for airline, values in company_prices.items():
    prices = [round(p[1], 2) for p in values]
    print(f"  {airline}: {prices}")

# ------------------------------
# Tri des dates
# ------------------------------
dates, best_prices = zip(*sorted(zip(dates, best_prices)))

# ------------------------------
# Tracé du graphique
# ------------------------------
plt.figure(figsize=(12,6))

# Courbe du meilleur prix global
plt.plot(dates, best_prices, marker='o', linestyle='-', color='black', linewidth=2, label='Meilleur prix global')

# Courbes des compagnies
for airline, values in company_prices.items():
    values_sorted = sorted(values, key=lambda x: x[0])
    date_series, price_series = zip(*values_sorted)
    plt.plot(date_series, price_series, marker='o', linestyle='--', label=airline)

# Mise en forme
plt.title("📉 Évolution des prix des vols Paris → Abidjan (par compagnie)")
plt.xlabel("Date de collecte")
plt.ylabel("Prix (€)")
plt.grid(True, linestyle="--", alpha=0.6)
plt.xticks(rotation=45)
plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
plt.tight_layout()

# Sauvegarde + affichage
output_img = os.path.join(OUTPUT_DIR, "prix_paris_abidjan_compagnies.png")
plt.savefig(output_img, dpi=150)
plt.show()

print(f"\n📊 Graphique enregistré dans : {output_img}")
