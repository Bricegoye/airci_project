#!/usr/bin/env python3
"""
evol_price.py
Évolution des prix des vols Paris (CDG) → Abidjan (ABJ)
avec affichage des compagnies et des prix par jour
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Dossier contenant les CSV
OUTPUT_DIR = "output"

# Lister tous les fichiers CSV
csv_files = sorted([f for f in os.listdir(OUTPUT_DIR) if f.endswith(".csv")])

dates = []
best_prices = []
company_prices = {}  # dictionnaire : key=compagnie, value=liste des prix par jour

for file in csv_files:
    df = pd.read_csv(os.path.join(OUTPUT_DIR, file))
    if not df.empty:
        # Date du jour (depuis le nom du fichier)
        parts = file.split("_")
        date_str = parts[3]
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        dates.append(date_obj)

        # Prix minimum du jour
        min_price = df['price'].min()
        best_prices.append(min_price)

        # Parcourir toutes les compagnies et leurs prix
        for idx, row in df.iterrows():
            airline = row['airline']
            price = row['price']
            if airline not in company_prices:
                company_prices[airline] = []
            company_prices[airline].append((date_obj, price))

# Afficher résumé par compagnie
print("\n💡 Résumé des prix par compagnie :")
for airline, price_list in company_prices.items():
    prices_str = ", ".join([f"{p[1]}€" for p in price_list])
    print(f"{airline}: {prices_str}")

# Tracer la courbe du meilleur prix général
plt.figure(figsize=(10,5))
plt.plot(dates, best_prices, marker='o', linestyle='-', color='blue', label='Meilleur prix général')

# Tracer la courbe par compagnie
for airline, price_list in company_prices.items():
    price_dates, prices = zip(*price_list)
    plt.plot(price_dates, prices, marker='o', linestyle='--', label=airline)

plt.title("Évolution des prix des vols Paris → Abidjan par compagnie")
plt.xlabel("Date d'exécution du script")
plt.ylabel("Prix (€)")
plt.grid(True)
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()

# Afficher et sauvegarder le graphique
plt.show()
plt.savefig(os.path.join(OUTPUT_DIR, "prix_paris_abidjan_compagnies.png"))
