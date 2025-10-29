#!/usr/bin/env python3
# streamlit_app.py
# Dashboard interactif : Évolution des prix Paris → Abidjan

import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# -----------------------------
# CONFIGURATION GLOBALE
# -----------------------------
st.set_page_config(
    page_title="Suivi des prix Paris → Abidjan",
    page_icon="✈️",
    layout="wide",
)

DATA_DIR = "output"

# -----------------------------
# CHARGEMENT DES DONNÉES
# -----------------------------
@st.cache_data
def load_data():
    files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith(".csv")])
    dfs = []
    for f in files:
        df = pd.read_csv(os.path.join(DATA_DIR, f))
        df["date_collecte"] = f.replace(".csv", "").split("_")[-1]
        df["date_collecte"] = pd.to_datetime(df["date_collecte"], errors="coerce")
        dfs.append(df)
    data = pd.concat(dfs, ignore_index=True)

    # Nettoyage
    data["price"] = (
        data["price"].astype(str)
        .str.replace("[^0-9]", "", regex=True)
        .astype(float)
    )
    data["duration"] = data["duration"].astype(str)
    return data

data = load_data()

# -----------------------------
# EN-TÊTE
# -----------------------------
st.title("✈️ Suivi des prix des vols Paris (CDG) → Abidjan (ABJ)")
st.markdown(
    """
    Ce tableau de bord présente l’évolution quotidienne des prix des vols entre **Paris et Abidjan**.
    Les données sont extraites automatiquement via **SerpAPI (Google Flights)**.
    """
)

# -----------------------------
# FILTRES
# -----------------------------
compagnies = sorted(data["airline"].dropna().unique())
compagnie_select = st.multiselect(
    "Filtrer par compagnie aérienne",
    options=compagnies,
    default=compagnies,
)

filtered = data[data["airline"].isin(compagnie_select)]

# -----------------------------
# INDICATEURS CLÉS
# -----------------------------
col1, col2, col3 = st.columns(3)

prix_moyen = filtered["price"].mean()
prix_min = filtered["price"].min()
prix_max = filtered["price"].max()

col1.metric("💶 Prix moyen", f"{prix_moyen:,.0f} €")
col2.metric("🔻 Meilleur prix observé", f"{prix_min:,.0f} €")
col3.metric("🔺 Prix max observé", f"{prix_max:,.0f} €")

# -----------------------------
# GRAPHIQUES
# -----------------------------

# 1️⃣ Évolution des prix par compagnie
st.subheader("📉 Évolution des prix dans le temps")
fig1 = px.line(
    filtered,
    x="date_collecte",
    y="price",
    color="airline",
    markers=True,
    title="Évolution des prix par compagnie",
    labels={"price": "Prix (€)", "date_collecte": "Date de collecte"},
)
fig1.update_layout(legend_title_text="Compagnie", hovermode="x unified")
st.plotly_chart(fig1, use_container_width=True)

# 2️⃣ Distribution des prix
st.subheader("📊 Distribution des prix par compagnie")
fig2 = px.box(
    filtered,
    x="airline",
    y="price",
    color="airline",
    title="Distribution des prix observés",
)
st.plotly_chart(fig2, use_container_width=True)

# 3️⃣ Durée vs Prix
st.subheader("⏱️ Relation entre durée de vol et prix")
filtered["duration_hours"] = (
    filtered["duration"].str.extract(r"(\d+)h").astype(float)
)
fig3 = px.scatter(
    filtered,
    x="duration_hours",
    y="price",
    color="airline",
    title="Durée de vol vs Prix",
    labels={"duration_hours": "Durée (heures)", "price": "Prix (€)"},
)
st.plotly_chart(fig3, use_container_width=True)

# -----------------------------
# TABLEAU DÉTAILLÉ
# -----------------------------
st.subheader("🧾 Données brutes filtrées")
st.dataframe(filtered.sort_values("date_collecte", ascending=False))

# -----------------------------
# EXPORT CSV
# -----------------------------
st.download_button(
    "📥 Télécharger les données filtrées (CSV)",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="flights_filtered.csv",
    mime="text/csv",
)
