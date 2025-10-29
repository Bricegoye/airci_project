#!/usr/bin/env python3
"""
merge_flight_data.py
Fusionne tous les fichiers CSV générés par le script de collecte (output/)
en un seul fichier propre, prêt pour l'analyse ou la dataviz.
"""

import os
import pandas as pd
from datetime import datetime

# --- Configuration ---
INPUT_DIR = "output"      # Dossier où se trouvent les CSV journaliers
OUTPUT_DIR = "merged"     # Dossier où sera enregistré le CSV fusionné
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Lister les fichiers CSV ---
files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".csv")]
if not files:
    raise FileNotFoundError("Aucun fichier CSV trouvé dans le dossier 'output'.")

print(f"🧾 {len(files)} fichiers trouvés :")
for f in files:
    print(f"  - {f}")

# --- Charger et fusionner les fichiers ---
dfs = []
for f in files:
    path = os.path.join(INPUT_DIR, f)
    try:
        df = pd.read_csv(path)
        # Extraire la date de collecte à partir du nom du fichier
        df["date_recolte"] = f.split("_")[-1].replace(".csv", "")
        dfs.append(df)
    except Exception as e:
        print(f"⚠️ Erreur lors de la lecture de {f}: {e}")

if not dfs:
    raise ValueError("Aucun fichier valide n’a pu être chargé.")

merged_df = pd.concat(dfs, ignore_index=True)
print(f"✅ {len(merged_df)} lignes fusionnées avec succès.")

# --- Nettoyage minimal ---
merged_df.drop_duplicates(inplace=True)
merged_df.dropna(subset=["price"], inplace=True)

# Convertir le prix en numérique
merged_df["price"] = (
    merged_df["price"]
    .astype(str)
    .str.replace("[^0-9]", "", regex=True)
    .astype(float)
)

# Convertir les dates
merged_df["date_recolte"] = pd.to_datetime(merged_df["date_recolte"], errors="coerce")

# --- Enregistrer le fichier final ---
today = datetime.now().strftime("%Y-%m-%d")
output_file = os.path.join(OUTPUT_DIR, f"vols_paris_abidjan_all_{today}.csv")
merged_df.to_csv(output_file, index=False, encoding="utf-8")

print(f"📁 Fichier fusionné enregistré dans : {output_file}")
