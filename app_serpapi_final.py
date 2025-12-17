import streamlit as st
from datetime import date
import os
from dotenv import load_dotenv
import pandas as pd
from google_search_results import GoogleSearch
import plotly.express as px

# ------------------------
# Config Streamlit
# ------------------------
st.set_page_config(page_title="Flight Price Analyzer Pro", layout="wide")

# ------------------------
# Env
# ------------------------
load_dotenv()
API_KEY = os.getenv("SERPAPI_KEY")

# ------------------------
# Load airports dataset
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
st.title("✈️ Flight Price Analyzer Pro")
st.markdown("Sélectionnez votre itinéraire, vos dates et options de filtre")

with st.form("flight_form"):
    col1, col2, col3 = st.columns(3)

    with col1:
        departure_index = int(
            airports_df.index[airports_df["iata"] == "CDG"][0]
            if "CDG" in airports_df["iata"].values else 0
        )
        departure_label = st.selectbox(
            "Ville de départ",
            airports_df["label"],
            index=departure_index
        )
        outbound_date = st.date_input("Date aller", value=date.today())

    with col2:
        arrival_labels = st.multiselect(
            "Ville(s) d'arrivée",
            airports_df["label"],
            default=[airports_df.loc[airports_df["iata"]=="ABJ", "label"].values[0]]
        )
        return_date = st.date_input("Date retour", value=date.today())

    with col3:
        max_price = st.number_input("Prix max (€)", min_value=0, value=1000)
        airlines_filter = st.text_input("Filtrer compagnies (séparées par ,)", value="")

    submit = st.form_submit_button("🔍 Rechercher")

# ------------------------
# SerpAPI logic
# ------------------------
def fetch_flights(departure, arrival, outbound_date, return_date):
    client = SerpApiClient(api_key=API_KEY)
    params = {
        "engine": "google_flights",
        "departure_id": departure,
        "arrival_id": arrival,
        "outbound_date": outbound_date.strftime("%Y-%m-%d"),
        "return_date": return_date.strftime("%Y-%m-%d"),
        "currency": "EUR",
        "hl": "fr",
        "type": 1,
    }
    results = client.get_dict(params)
    flights = []

    for section in ["best_flights", "other_flights"]:
        for group in results.get(section, []):
            price = group.get("price")
            duration = group.get("total_duration")
            for flight in group.get("flights", []):
                flights.append({
                    "airline": flight.get("airline"),
                    "price": price,
                    "departure": flight.get("departure_airport", {}).get("id"),
                    "arrival": flight.get("arrival_airport", {}).get("id"),
                    "departure_time": flight.get("departure_airport", {}).get("time"),
                    "arrival_time": flight.get("arrival_airport", {}).get("time"),
                    "duration_min": duration,
                    "flight_number": flight.get("flight_number"),
                })
    return pd.DataFrame(flights)

# ------------------------
# Action
# ------------------------
if submit:
    if not API_KEY:
        st.error("❌ Clé API SerpAPI manquante dans le fichier .env")
    else:
        all_dfs = []
        for arrival_label in arrival_labels:
            departure_iata = airports_df.loc[airports_df["label"]==departure_label, "iata"].values[0]
            arrival_iata = airports_df.loc[airports_df["label"]==arrival_label, "iata"].values[0]

            if departure_iata == arrival_iata:
                st.warning(f"⚠️ Départ et arrivée identiques pour {arrival_label}, ignoré")
                continue

            with st.spinner(f"Recherche vols {departure_iata} → {arrival_iata}..."):
                df = fetch_flights(departure_iata, arrival_iata, outbound_date, return_date)
                if not df.empty:
                    df["arrival_city"] = arrival_label
                    all_dfs.append(df)

        if not all_dfs:
            st.warning("⚠️ Aucun vol trouvé")
        else:
            final_df = pd.concat(all_dfs, ignore_index=True)

            # Filtrage par prix
            final_df = final_df[final_df["price"] <= max_price]

            # Filtrage par compagnie si renseigné
            if airlines_filter.strip():
                allowed_airlines = [a.strip() for a in airlines_filter.split(",")]
                final_df = final_df[final_df["airline"].isin(allowed_airlines)]

            st.success(f"✅ {len(final_df)} vols trouvés après filtrage")

            # Sauvegarde CSV automatique
            os.makedirs("history", exist_ok=True)
            filename = f"history/flights_{departure_iata}_{date.today()}.csv"
            final_df.to_csv(filename, index=False)
            st.info(f"💾 Résultats sauvegardés dans : {filename}")

            # Affichage DataFrame
            st.dataframe(final_df, use_container_width=True)

            # --------- Graphique 1 : Prix moyen par compagnie et destination ---------
            if not final_df.empty:
                st.subheader("📊 Prix moyen par compagnie et par destination")
                mean_prices = final_df.groupby(["arrival_city", "airline"])["price"].mean().reset_index()
                fig1 = px.bar(
                    mean_prices,
                    x="arrival_city",
                    y="price",
                    color="airline",
                    barmode="group",
                    labels={"price":"Prix moyen (€)", "arrival_city":"Destination"}
                )
                st.plotly_chart(fig1, use_container_width=True)

            # --------- Graphique 2 : Histogramme comparatif des destinations ---------
            if not final_df.empty:
                st.subheader("📊 Distribution des prix par destination")
                fig2 = px.histogram(
                    final_df,
                    x="price",
                    color="arrival_city",
                    barmode="overlay",
                    nbins=20,
                    labels={"price":"Prix (€)", "arrival_city":"Destination"}
                )
                st.plotly_chart(fig2, use_container_width=True)
