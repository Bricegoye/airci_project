#!/usr/bin/env python3
# streamlit_app_final.py
# Dashboard interactif : Suivi des prix Paris → Abidjan

import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# -----------------------------
# ⚙️ CONFIGURATION DE LA PAGE
# -----------------------------
st.set_page_config(
    page_title="Suivi des prix Paris → Abidjan",
    page_icon="✈️",
    layout="wide",
)

# -----------------------------
# 📂 CHARGEMENT DES DONNÉES
# -----------------------------
DATA_DIR = "output"

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
    data["duration_hours"] = data["duration"].astype(str).str.extract(r"(\d+)").astype(float)
    data["airline"] = data["airline"].fillna("Inconnue")
    return data

data = load_data()

# -----------------------------
# 🧭 BARRE LATÉRALE
# -----------------------------
st.sidebar.header("⚙️ Paramètres du tableau de bord")
compagnies = sorted(data["airline"].unique())
compagnie_select = st.sidebar.multiselect(
    "✈️ Choisir les compagnies à afficher",
    options=compagnies,
    default=compagnies,
)
filtered = data[data["airline"].isin(compagnie_select)]

# -----------------------------
# 🏠 EN-TÊTE
# -----------------------------
st.title("✈️ Suivi des prix des vols Paris (CDG) → Abidjan (ABJ)")
st.markdown(
    """
    Ce tableau de bord présente l’évolution quotidienne des prix des vols entre **Paris et Abidjan**.
    Les données sont extraites automatiquement via **SerpAPI (Google Flights)**.
    """
)

# -----------------------------
# 💡 INDICATEURS CLÉS
# -----------------------------
col1, col2, col3, col4 = st.columns(4)
prix_moyen = filtered["price"].mean()
prix_min = filtered["price"].min()
prix_max = filtered["price"].max()
nb_vols = len(filtered)
col1.metric("💶 Prix moyen", f"{prix_moyen:,.0f} €")
col2.metric("📉 Prix minimum", f"{prix_min:,.0f} €")
col3.metric("📈 Prix maximum", f"{prix_max:,.0f} €")
col4.metric("🛫 Nombre total de vols", nb_vols)

# -----------------------------
# 📅 ANALYSE PAR JOUR
# -----------------------------
st.subheader("📊 Analyse des prix par jour de collecte")
prix_moyen_par_jour = filtered.groupby("date_collecte")["price"].mean().reset_index()
jour_le_moins_cher = prix_moyen_par_jour.loc[prix_moyen_par_jour["price"].idxmin(), "date_collecte"]
jour_le_plus_cher = prix_moyen_par_jour.loc[prix_moyen_par_jour["price"].idxmax(), "date_collecte"]
st.info(f"✅ Jour avec prix moyen le plus bas : {jour_le_moins_cher.strftime('%A %d %B %Y')}")
st.warning(f"⚠️ Jour avec prix moyen le plus élevé : {jour_le_plus_cher.strftime('%A %d %B %Y')}")

fig_jours = px.line(
    prix_moyen_par_jour,
    x="date_collecte",
    y="price",
    title="Évolution des prix moyens par jour",
    labels={"price": "Prix moyen (€)", "date_collecte": "Date"},
    markers=True
)
st.plotly_chart(fig_jours, use_container_width=True)

# -----------------------------
# 📊 VISUALISATIONS
# -----------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Évolution", "📊 Distribution", "⏱️ Durée vs Prix", "📋 Données brutes", "🗺️ Carte"])

with tab1:
    st.subheader("Évolution des prix par compagnie")
    fig1 = px.line(
        filtered,
        x="date_collecte",
        y="price",
        color="airline",
        markers=True,
        title="Tendance des prix par compagnie",
        labels={"price": "Prix (€)", "date_collecte": "Date de collecte"},
    )
    fig1.update_layout(legend_title_text="Compagnie", hovermode="x unified")
    st.plotly_chart(fig1, use_container_width=True)

with tab2:
    st.subheader("Distribution des prix par compagnie")
    fig2 = px.box(
        filtered,
        x="airline",
        y="price",
        color="airline",
        title="Distribution des prix observés",
    )
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    st.subheader("Durée du vol vs Prix")
    fig3 = px.scatter(
        filtered,
        x="duration_hours",
        y="price",
        color="airline",
        size="price",
        hover_data=["departure_time", "arrival_time"],
        title="Relation entre durée du vol et prix",
        labels={"duration_hours": "Durée (heures)", "price": "Prix (€)"},
    )
    st.plotly_chart(fig3, use_container_width=True)

with tab4:
    st.subheader("🧾 Données brutes filtrées")
    st.dataframe(filtered.sort_values("date_collecte", ascending=False))
    st.download_button(
        "📥 Télécharger les données filtrées (CSV)",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name=f"flights_filtered_{datetime.now().strftime('%Y-%m-%d')}.csv",
        mime="text/csv",
    )

with tab5:
    st.subheader("Carte interactive : Paris → Abidjan")
    coords = {"Paris": {"lat": 48.8566, "lon": 2.3522}, "Abidjan": {"lat": 5.35995, "lon": -4.00826}}
    map_data = pd.DataFrame({
        "city": ["Paris", "Abidjan"],
        "lat": [coords["Paris"]["lat"], coords["Abidjan"]["lat"]],
        "lon": [coords["Paris"]["lon"], coords["Abidjan"]["lon"]],
        "price": [prix_moyen_par_jour["price"].mean(), prix_moyen_par_jour["price"].mean()]
    })

    fig_map = px.scatter_geo(
        map_data,
        lat="lat",
        lon="lon",
        text="city",
        size="price",
        size_max=40,
        color="price",
        color_continuous_scale="Viridis",
        projection="natural earth",
        title="Trajet Paris → Abidjan et prix moyens",
    )
    fig_map.add_trace(
        px.line_geo(
            lat=[coords["Paris"]["lat"], coords["Abidjan"]["lat"]],
            lon=[coords["Paris"]["lon"], coords["Abidjan"]["lon"]],
        ).data[0]
    )
    st.plotly_chart(fig_map, use_container_width=True)

# -----------------------------
# 🧠 SYNTHÈSE AUTOMATIQUE
# -----------------------------
st.markdown("---")
st.subheader("🧠 Synthèse automatique")

best_airline = (
    filtered.groupby("airline")["price"]
    .mean()
    .sort_values()
    .index[0]
)

st.success(
    f"✅ La compagnie la plus économique est **{best_airline}**.\n"
    f"Le jour où les prix moyens étaient les plus bas : **{jour_le_moins_cher.strftime('%A %d %B %Y')}**."
)
