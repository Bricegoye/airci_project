#!/usr/bin/env python3
"""
meilleur_vol.py
Dashboard Streamlit tout-en-un
Scraping + Analyse meilleur deal ABJ → Paris (CDG)
Période : 2 premières semaines de juillet 2026 (1 → 14 juillet)
Lancer avec : streamlit run meilleur_vol.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import glob
import time
import json
from collections import defaultdict
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# ------------------------
# Config
# ------------------------
DATE_DEBUT    = datetime(2026, 7, 1)
DATE_FIN      = datetime(2026, 7, 14)
OUTPUT_DIR    = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

st.set_page_config(
    page_title="✈️ Meilleur vol ABJ → Paris",
    page_icon="✈️",
    layout="wide",
)

st.title("✈️ Meilleur vol — Abidjan → Paris")
st.caption("Juillet 2026 · Critère : meilleur rapport Prix + Durée")


# ------------------------
# Utilitaires
# ------------------------
def date_range(start, end):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)

def extract_itineraries(results: dict, date_depart: str) -> list:
    raw = []
    for section in ["best_flights", "other_flights"]:
        for group in results.get(section, []):
            price          = group.get("price")
            total_duration = group.get("total_duration")
            segments       = group.get("flights", [])
            if not segments:
                continue
            first = next((s for s in segments if s.get("departure_airport", {}).get("id") == "ABJ"), segments[0])
            last  = segments[-1]
            raw.append({
                "date_depart":     date_depart,
                "airline":         first.get("airline"),
                "price":           int(price) if price else 0,
                "departure_time":  first.get("departure_airport", {}).get("time", ""),
                "arrival_time":    last.get("arrival_airport", {}).get("time", ""),
                "arrival_airport": last.get("arrival_airport", {}).get("id", ""),
                "duration_min":    int(total_duration) if total_duration else 0,
                "duration_h":      round(int(total_duration) / 60, 1) if total_duration else 0,
                "nb_escales":      len(segments) - 1,
                "flight_numbers":  " / ".join(s.get("flight_number", "") for s in segments),
            })
    return raw

def compute_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Score combiné Prix + Durée (0 = meilleur, 100 = pire)
    Pondération : 60% prix, 40% durée
    """
    df = df.copy()
    p_min, p_max = df["price"].min(), df["price"].max()
    d_min, d_max = df["duration_min"].min(), df["duration_min"].max()

    if p_max > p_min:
        df["score_prix"] = (df["price"] - p_min) / (p_max - p_min) * 100
    else:
        df["score_prix"] = 0

    if d_max > d_min:
        df["score_duree"] = (df["duration_min"] - d_min) / (d_max - d_min) * 100
    else:
        df["score_duree"] = 0

    df["score_global"] = (df["score_prix"] * 0.6 + df["score_duree"] * 0.4).round(1)
    return df.sort_values("score_global")


# ============================================================
# SECTION 1 — Scraping
# ============================================================
st.divider()
st.header("1️⃣ Collecte des données")

existing = sorted(glob.glob(os.path.join(OUTPUT_DIR, "vols_abj_paris_juillet_*.csv")))

col_s1, col_s2 = st.columns([2, 1])
with col_s1:
    if existing:
        last_file = existing[-1]
        last_date = os.path.basename(last_file).split("_")[-1].replace(".csv", "")
        st.success(f"✅ Dernière collecte : `{last_date}` — `{os.path.basename(last_file)}`")
    else:
        st.warning("⚠️ Aucune collecte trouvée. Lance le scraping ci-dessous.")

with col_s2:
    run_scraping = st.button("🔄 Lancer le scraping", type="primary", use_container_width=True)

if run_scraping:
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        st.error("❌ Clé SERPAPI_KEY manquante dans le fichier `.env`")
        st.stop()

    try:
        from serpapi import GoogleSearch
    except ImportError:
        st.error("❌ Package `google-search-results` non installé. Lance : `pip install google-search-results`")
        st.stop()

    today      = datetime.now().strftime("%Y-%m-%d")
    out_file   = os.path.join(OUTPUT_DIR, f"vols_abj_paris_juillet_{today}.csv")
    dates      = list(date_range(DATE_DEBUT, DATE_FIN))
    all_itin   = []

    progress   = st.progress(0, text="Initialisation...")
    status_box = st.empty()

    for i, dt in enumerate(dates):
        date_str = dt.strftime("%Y-%m-%d")
        status_box.info(f"🔎 Recherche pour le **{date_str}** ({i+1}/{len(dates)})...")

        params = {
            "engine":        "google_flights",
            "departure_id":  "ABJ",
            "arrival_id":    "CDG",
            "outbound_date": date_str,
            "currency":      "EUR",
            "hl":            "fr",
            "gl":            "fr",
            "type":          2,
            "api_key":       api_key,
        }

        try:
            results = GoogleSearch(params).get_dict()
            itin    = extract_itineraries(results, date_str)
            all_itin.extend(itin)
            status_box.success(f"✅ {date_str} — {len(itin)} itinéraire(s) trouvé(s)")
        except Exception as e:
            status_box.warning(f"⚠️ {date_str} — Erreur : {e}")

        progress.progress((i + 1) / len(dates), text=f"{i+1}/{len(dates)} dates traitées")
        if i < len(dates) - 1:
            time.sleep(2)

    if all_itin:
        df_out = pd.DataFrame(all_itin)
        df_out.to_csv(out_file, index=False, encoding="utf-8")
        st.success(f"📁 **{len(all_itin)} itinéraires** enregistrés → `{out_file}`")
        st.rerun()
    else:
        st.error("❌ Aucun vol collecté.")


# ============================================================
# SECTION 2 — Analyse
# ============================================================
existing = sorted(glob.glob(os.path.join(OUTPUT_DIR, "vols_abj_paris_juillet_*.csv")))
if not existing:
    st.info("👆 Lance le scraping pour voir les analyses.")
    st.stop()

df_raw = pd.read_csv(existing[-1])
df     = compute_score(df_raw)
df["date_depart"] = pd.to_datetime(df["date_depart"])
df["date_str"]    = df["date_depart"].dt.strftime("%d %b")

st.divider()
st.header("2️⃣ Meilleur deal")

best = df.iloc[0]

col_b1, col_b2, col_b3, col_b4, col_b5 = st.columns(5)
col_b1.metric("📅 Meilleure date",   best["date_str"])
col_b2.metric("✈️ Compagnie",        best["airline"])
col_b3.metric("💶 Prix",             f"{best['price']} €")
col_b4.metric("⏱️ Durée",            f"{best['duration_h']}h")
col_b5.metric("🔁 Escales",          int(best["nb_escales"]))

st.info(
    f"**Vol {best['flight_numbers']}** · "
    f"Départ {best['departure_time']} → Arrivée {best['arrival_time']} ({best['arrival_airport']}) · "
    f"Score combiné prix+durée : **{best['score_global']}/100** (0 = parfait)"
)

st.divider()
st.header("3️⃣ Prix vs Durée — trouver le meilleur coin")

st.caption("💡 Le coin **en bas à gauche** = moins cher ET plus rapide. La taille des bulles = nombre d'escales.")

fig_scatter = px.scatter(
    df,
    x="duration_h",
    y="price",
    color="airline",
    size=df["nb_escales"].apply(lambda x: max(x + 1, 1)) * 8,
    hover_data=["date_str", "flight_numbers", "nb_escales", "arrival_airport"],
    labels={
        "duration_h": "Durée totale (h)",
        "price":      "Prix (€)",
        "airline":    "Compagnie",
    },
    title="Prix vs Durée par compagnie — chaque point = un itinéraire",
    text=df.apply(lambda r: f"{r['date_str']}", axis=1),
)
fig_scatter.update_traces(textposition="top center", textfont_size=9)
fig_scatter.update_layout(
    height=480,
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(gridcolor="rgba(200,200,200,0.3)"),
    yaxis=dict(gridcolor="rgba(200,200,200,0.3)"),
)
# Zone idéale : bas-gauche
fig_scatter.add_shape(
    type="rect",
    x0=df["duration_h"].min() - 0.5,
    x1=df["duration_h"].quantile(0.3),
    y0=df["price"].min() - 20,
    y1=df["price"].quantile(0.3),
    fillcolor="rgba(46, 204, 113, 0.1)",
    line=dict(color="rgba(46, 204, 113, 0.5)", dash="dot"),
)
fig_scatter.add_annotation(
    x=df["duration_h"].quantile(0.15),
    y=df["price"].quantile(0.15),
    text="✅ Zone idéale",
    showarrow=False,
    font=dict(color="green", size=11),
)
st.plotly_chart(fig_scatter, use_container_width=True)

st.divider()
st.header("4️⃣ Heatmap — Quel jour, quelle compagnie ?")

st.caption("💡 Les cases **vertes foncées** = combinaisons date × compagnie les moins chères.")

# Prix minimum par (date, compagnie)
heatmap_data = (
    df.groupby(["date_str", "airline"])["price"]
    .min()
    .reset_index()
    .pivot(index="airline", columns="date_str", values="price")
)

# Réordonner les colonnes par date chronologique
date_order = df.sort_values("date_depart")["date_str"].unique().tolist()
heatmap_data = heatmap_data.reindex(columns=[d for d in date_order if d in heatmap_data.columns])

fig_heat = go.Figure(data=go.Heatmap(
    z=heatmap_data.values,
    x=heatmap_data.columns.tolist(),
    y=heatmap_data.index.tolist(),
    colorscale="RdYlGn_r",
    text=[[f"{v:.0f}€" if not pd.isna(v) else "—" for v in row] for row in heatmap_data.values],
    texttemplate="%{text}",
    textfont=dict(size=11),
    hoverongaps=False,
    colorbar=dict(title="Prix (€)"),
))
fig_heat.update_layout(
    title="Prix minimum (€) par date de départ × compagnie",
    xaxis_title="Date de départ",
    yaxis_title="Compagnie",
    height=max(300, len(heatmap_data.index) * 55 + 100),
    plot_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(fig_heat, use_container_width=True)


st.divider()
st.header("4️⃣ Prix minimum par date")

prix_date = (
    df.groupby("date_str")["price"]
    .min()
    .reset_index()
    .rename(columns={"price": "prix_min"})
)

fig_prix = px.bar(
    prix_date,
    x="date_str",
    y="prix_min",
    color="prix_min",
    color_continuous_scale="RdYlGn_r",
    labels={"date_str": "Date de départ", "prix_min": "Prix min (€)"},
    title="Prix minimum disponible par date de départ",
    text="prix_min",
)
fig_prix.update_traces(texttemplate="%{text}€", textposition="outside")
fig_prix.update_layout(
    coloraxis_showscale=False,
    height=380,
    plot_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(fig_prix, use_container_width=True)


st.divider()
st.header("5️⃣ Tous les itinéraires")

col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    airlines = st.multiselect("Compagnie", sorted(df["airline"].unique()), default=sorted(df["airline"].unique()))
with col_f2:
    price_range = st.slider("Prix (€)", int(df["price"].min()), int(df["price"].max()), (int(df["price"].min()), int(df["price"].max())))
with col_f3:
    max_escales = st.selectbox("Escales max", [0, 1, 2, 3], index=2)

df_f = df[
    (df["airline"].isin(airlines)) &
    (df["price"].between(*price_range)) &
    (df["nb_escales"] <= max_escales)
].sort_values("score_global")

st.dataframe(
    df_f[[
        "date_str", "airline", "price", "duration_h",
        "nb_escales", "arrival_airport", "departure_time",
        "arrival_time", "flight_numbers", "score_global"
    ]].rename(columns={
        "date_str":        "Date",
        "airline":         "Compagnie",
        "price":           "Prix (€)",
        "duration_h":      "Durée (h)",
        "nb_escales":      "Escales",
        "arrival_airport": "Arrivée",
        "departure_time":  "Départ",
        "arrival_time":    "Arrivée heure",
        "flight_numbers":  "N° vols",
        "score_global":    "Score",
    }),
    use_container_width=True,
    hide_index=True,
)