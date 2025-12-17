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
    df["label"] = (
        df["city"]
        + " – "
        + df["airport_name"]
        + " (" + df["iata"] + ")"
        + " – "
        + df["country"]
    )
    return df.sort_values("city")

airports_df = load_airports()

# ------------------------
# UI
# ------------------------
st.title("✈️ Analyse des prix de vols")
st.markdown("Sélectionnez votre itinéraire et vos dates")

with st.form("flight_form"):
    col1, col2 = st.columns(2)

    with col1:
        departure_label = st.selectbox(
            "Ville de départ",
            airports_df["label"],
            index=int(
                airports_df.index[airports_df["iata"] == "CDG"][0]
                if "CDG" in airports_df["iata"].values else 0
            ),
        )
        outbound_date = st.date_input("Date aller", value=date.today())

    with col2:
        arrival_label = st.selectbox(
            "Ville d'arrivée",
            airports_df["label"],
            index=int(
                airports_df.index[airports_df["iata"] == "ABJ"][0]
                if "ABJ" in airports_df["iata"].values else 0
            ),
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
            for flight in group.get("flights", []):
                flights.append({
                    "airline": flight.get("airline"),
                    "price": price,
                    "departure": flight.get("departure_airport", {}).get("id"),
                    "arrival": flight.get("arrival_airport", {}).get("id"),
                    "departure_time": flight.get("departure_airport", {}).get("time"),
                    "arrival_time": flight.get("arrival_airport", {}).get("time"),
                    "flight_number": flight.get("flight_number"),
                })

    return pd.DataFrame(flights)

# ------------------------
# Action
# ------------------------
if submit:
    if not API_KEY:
        st.error("❌ Clé API SerpAPI manquante (.env)")
        st.stop()

    departure = airports_df.loc[
        airports_df["label"] == departure_label, "iata"
    ].values[0]

    arrival = airports_df.loc[
        airports_df["label"] == arrival_label, "iata"
    ].values[0]

    if departure == arrival:
        st.warning("⚠️ Départ et arrivée identiques")
        st.stop()

    with st.spinner("Recherche des vols..."):
        df = fetch_flights(departure, arrival, outbound_date, return_date)

    if df.empty:
        st.warning("⚠️ Aucun vol trouvé")
    else:
        st.success(f"✅ {len(df)} vols trouvés")

        st.dataframe(df, use_container_width=True)

        # 📊 Prix moyen par compagnie
        avg_price = df.groupby("airline")["price"].mean().reset_index()

        fig = px.bar(
            avg_price,
            x="airline",
            y="price",
            title="💰 Prix moyen par compagnie",
        )
        st.plotly_chart(fig, use_container_width=True)
