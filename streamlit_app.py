#!/usr/bin/env python3
# streamlit_app_final_dark.py
# Dashboard interactif : Suivi des prix Paris → Abidjan
# Version finale avec Dark Mode et synthèse visuelle

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

# Thème Dark Streamlit
st.markdown(
    """
    <style>
    .main {background-color: #0e1117;}
    .css-18e3th9 {color: #ffffff;}
    </style>
    """,
    unsafe_allow_html=True
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
    markers=True,
    template="plotly_dark"
)
st.plotly_chart(fig_jours, use_container_width=True)

# -----------------------------
# 📊 VISUALISATIONS
# -----------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 Évolution", "📊 Distribution", "⏱️ Durée vs Prix", 
    "📋 Données brutes", "🗺️ Carte", "📉 Tendance par compagnie"
])

# --- ÉVOLUTION ---
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
        template="plotly_dark"
    )
    fig1.update_layout(legend_title_text="Compagnie", hovermode="x unified")
    st.plotly_chart(fig1, use_container_width=True)

# --- DISTRIBUTION ---
with tab2:
    st.subheader("Distribution des prix par compagnie")
    fig2 = px.box(
        filtered,
        x="airline",
        y="price",
        color="airline",
        title="Distribution des prix observés",
        template="plotly_dark"
    )
    st.plotly_chart(fig2, use_container_width=True)

# --- DURÉE VS PRIX ---
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
        template="plotly_dark"
    )
    st.plotly_chart(fig3, use_container_width=True)

# --- DONNÉES BRUTES ---
with tab4:
    st.subheader("🧾 Données brutes filtrées")
    st.dataframe(filtered.sort_values("date_collecte", ascending=False))
    st.download_button(
        "📥 Télécharger les données filtrées (CSV)",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name=f"flights_filtered_{datetime.now().strftime('%Y-%m-%d')}.csv",
        mime="text/csv",
    )

# --- CARTE ---
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
        template="plotly_dark"
    )
    fig_map.add_trace(
        px.line_geo(
            lat=[coords["Paris"]["lat"], coords["Abidjan"]["lat"]],
            lon=[coords["Paris"]["lon"], coords["Abidjan"]["lon"]],
        ).data[0]
    )
    st.plotly_chart(fig_map, use_container_width=True)

# --- TENDANCE PAR COMPAGNIE ---
with tab6:
    st.subheader("📈 Tendance, prix bas et hauts par compagnie")

    # Calcul prix moyens par jour et par compagnie
    prix_par_jour_compagnie = (
        filtered.groupby(["airline", "date_collecte"])["price"]
        .mean()
        .reset_index()
        .sort_values(["airline", "date_collecte"])
    )

    # Calcul des extrêmes
    extremes = filtered.groupby("airline")["price"].agg(["min", "max", "mean"]).reset_index()
    extremes.columns = ["Compagnie", "Prix minimum (€)", "Prix maximum (€)", "Prix moyen (€)"]

    # Calcul des tendances (%)
    def compute_trend(df):
        if len(df) < 2:
            return 0
        return (df["price"].iloc[-1] - df["price"].iloc[0]) / df["price"].iloc[0] * 100

    tendances = prix_par_jour_compagnie.groupby("airline").apply(compute_trend).reset_index(name="Tendance (%)")
    extremes = extremes.merge(tendances, left_on="Compagnie", right_on="airline", how="left").drop(columns="airline")

    # Tableau des résultats
    st.dataframe(extremes.sort_values("Prix moyen (€)"), use_container_width=True)

    # Interprétation automatique
    st.markdown("### 🧭 Interprétation automatique")
    for _, row in extremes.iterrows():
        tendance = row["Tendance (%)"]
        symbole = "📈" if tendance > 0 else ("📉" if tendance < 0 else "⚖️")
        st.write(
            f"- **{row['Compagnie']}** : {symbole} tendance de {tendance:+.1f}% | "
            f"Min : {row['Prix minimum (€)']:.0f} € | Max : {row['Prix maximum (€)']:.0f} € | "
            f"Moyenne : {row['Prix moyen (€)']:.0f} €"
        )

    # Graphique de tendance
    fig_tendance = px.line(
        prix_par_jour_compagnie,
        x="date_collecte",
        y="price",
        color="airline",
        markers=True,
        title="Tendance des prix moyens par compagnie",
        labels={"price": "Prix moyen (€)", "date_collecte": "Date de collecte"},
        template="plotly_dark"
    )
    fig_tendance.update_layout(hovermode="x unified")
    st.plotly_chart(fig_tendance, use_container_width=True)

# -----------------------------
# 🧠 SYNTHÈSE VISUELLE FINALE
# -----------------------------
st.markdown("---")
st.subheader("🧠 Synthèse finale")

# Compagnie la plus économique
best_airline = filtered.groupby("airline")["price"].mean().sort_values().index[0]

# Jour moyen le plus bas
jour_le_moins_cher = prix_moyen_par_jour.loc[prix_moyen_par_jour["price"].idxmin(), "date_collecte"]

# Prix le plus bas toutes compagnies confondues
record_min_row = filtered.loc[filtered["price"].idxmin()]
record_date = record_min_row["date_collecte"]
record_airline = record_min_row["airline"]
record_price = record_min_row["price"]

# Colonnes synthèse
col1, col2, col3 = st.columns(3)
col1.metric("💶 Compagnie la plus économique", best_airline)
col2.metric("📉 Jour prix moyen le plus bas", jour_le_moins_cher.strftime('%A %d %B %Y'))
col3.metric("🏆 Prix le plus bas", f"{record_price:.0f} €", delta=f"{record_airline} le {record_date.strftime('%d/%m/%Y')}")

# Phrase récapitulative
# ✅ Affichage enrichi avec sauts de ligne et meilleure présentation
st.success(
    f"✅ **Compagnie la plus économique en moyenne :** {best_airline}\n\n"
    f"📉 **Jour avec prix moyen le plus bas :** {jour_le_moins_cher.strftime('%A %d %B %Y')}\n\n"
    f"🏆 **Prix le plus bas observé :** {record_price:.0f} €\n"
    f"✈️ **Compagnie :** {record_airline}\n"
    f"📅 **Date de collecte :** {record_date.strftime('%A %d %B %Y')}"
)
