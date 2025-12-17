import streamlit as st
from datetime import date
import os
from dotenv import load_dotenv
import pandas as pd
from serpapi import GoogleSearch
import plotly.express as px

# ------------------------
# Config Streamlit
# ------------------------
st.set_page_config(page_title="Flight Price Analyzer", layout="wide")

# ------------------------
# Env
# ------------------------
load_dotenv()
API_KEY = os.getenv("SERPAPI_KEY")

# ------------------------
# Load airports
# ------------------------
@st.cache_data
def load_airports():
    df = pd.read_csv("data/airports.csv")
    df = df.dropna(subset=["iata"])
    df["label"] = df["city"] + " – " + df["airport_name"] + " (" + df["iata"] + ") – " + df["country"]
    return df.sort_values("city")

airports_df = load_airports()

# ------------------------
# UI
# ------------------------
st.title("✈️ Analyse des prix de vols")
st.markdown("Comparer intelligemment les vols (prix, durée, escales)")

with st.form("flight_form"):
    col1, col2 = st.columns(2)

    with col1:
        departure_label = st.selectbox(
            "Ville de départ",
            airports_df["label"],
            index=int(airports_df.index[airports_df["iata"] == "CDG"][0]) if "CDG" in airports_df["iata"].values else 0,
        )
        outbound_date = st.date_input("Date aller", value=date.today())

    with col2:
        arrival_label = st.selectbox(
            "Ville d'arrivée",
            airports_df["label"],
            index=int(airports_df.index[airports_df["iata"] == "ABJ"][0]) if "ABJ" in airports_df["iata"].values else 0,
        )
        return_date = st.date_input("Date retour", value=date.today())

    submit = st.form_submit_button("🔍 Rechercher")

# ------------------------
# SerpAPI
# ------------------------
def fetch_flights(departure, arrival, outbound_date, return_date):
    params = {
        "engine": "google_flights",
        "departure_id": departure,
        "arrival_id": arrival,
        "outbound_date": outbound_date.strftime("%Y-%m-%d"),
        "return_date": return_date.strftime("%Y-%m-%d"),
        "currency": "EUR",
        "hl": "fr",
        "type": 1,
        "api_key": API_KEY,
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    flights = []

    for section in ["best_flights", "other_flights"]:
        for group in results.get(section, []):
            price = group.get("price")
            duration = group.get("total_duration")
            segments = group.get("flights", [])
            stops = max(len(segments) - 1, 0)
            flight_type = "Direct" if stops == 0 else "Avec escale"

            for flight in segments:
                flights.append({
                    "airline": flight.get("airline"),
                    "price": price,
                    "duration_min": duration,
                    "stops": stops,
                    "flight_type": flight_type,
                    "departure": flight.get("departure_airport", {}).get("id"),
                    "arrival": flight.get("arrival_airport", {}).get("id"),
                    "flight_number": flight.get("flight_number"),
                })

    return pd.DataFrame(flights)

# ------------------------
# Action
# ------------------------
if submit:
    if not API_KEY:
        st.error("❌ Clé API SerpAPI manquante (.env)")
    else:
        departure = airports_df.loc[airports_df["label"] == departure_label, "iata"].values[0]
        arrival = airports_df.loc[airports_df["label"] == arrival_label, "iata"].values[0]

        if departure == arrival:
            st.warning("⚠️ Départ et arrivée identiques")
        else:
            with st.spinner("Recherche des vols..."):
                df = fetch_flights(departure, arrival, outbound_date, return_date)

            if df.empty:
                st.warning("⚠️ Aucun vol trouvé")
            else:
                # ------------------------
                # Nettoyage & score
                # ------------------------
                df = df.dropna(subset=["price", "duration_min", "stops"])
                df["score"] = (df["price"]/df["price"].min()*0.5) + (df["duration_min"]/df["duration_min"].min()*0.3) + df["stops"]*0.2

                # ------------------------
                # Sidebar filtres
                # ------------------------
                st.sidebar.header("🎛️ Filtres")
                direct_only = st.sidebar.checkbox("Vols directs uniquement")
                max_stops = st.sidebar.slider("Escales max", 0, 3, 2)
                max_price = st.sidebar.slider("Budget max (€)", int(df["price"].min()), int(df["price"].max()), int(df["price"].max()))

                filtered_df = df.copy()
                if direct_only:
                    filtered_df = filtered_df[filtered_df["stops"] == 0]
                filtered_df = filtered_df[(filtered_df["stops"] <= max_stops) & (filtered_df["price"] <= max_price)]

                # ------------------------
                # Résultats
                # ------------------------
                st.success(f"✅ {len(filtered_df)} vols affichés")
                st.subheader("📋 Liste des vols")
                st.dataframe(filtered_df[["airline", "price", "duration_min", "stops", "flight_type", "flight_number"]], use_container_width=True)

                # ------------------------
                # Insight direct vs escale
                # ------------------------
                st.subheader("📌 Insight : Direct vs Escale")
                avg_price = filtered_df.groupby("flight_type")["price"].mean()
                for k, v in avg_price.items():
                    st.write(f"• **{k}** : prix moyen ≈ **{int(v)} €**")

                # ------------------------
                # Graphique prix vs durée
                # ------------------------
                st.subheader("⏱️💰 Compromis durée / prix")
                fig = px.scatter(filtered_df, x="duration_min", y="price", color="flight_type", hover_data=["airline", "stops", "flight_number"], title="Prix vs durée des vols")
                st.plotly_chart(fig, use_container_width=True)

                # ------------------------
                # Top 3 vols recommandés
                # ------------------------
                st.subheader("🏆 Top 3 vols recommandés")
                top3 = filtered_df.sort_values("score").head(3)
                st.dataframe(top3[["airline", "price", "duration_min", "stops", "flight_type", "score"]], use_container_width=True)
