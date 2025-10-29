AirCI Project – Suivi des prix des vols Paris → Abidjan

🚀 Description du projet

Ce projet est un dashboard interactif permettant de suivre l’évolution quotidienne des prix des vols entre Paris (CDG) et Abidjan (ABJ) sur une période donnée.
Les données sont collectées automatiquement via SerpAPI (Google Flights) et enregistrées quotidiennement dans des fichiers CSV.

Ce projet illustre mes compétences en Data Analysis, Data Cleaning, Visualisation et Déploiement d’outil interactif.

🧰 Technologies utilisées

Python 3.x

Pandas : traitement et nettoyage des données

Plotly Express : visualisations interactives

Streamlit : dashboard interactif

CSV : stockage des données collectées

📁 Structure du projet
airci_project/
├─ scripts/
│  ├─ fetch_serapi_daily.py      # Collecte quotidienne des prix
│  └─ clean_data.py              # Nettoyage des données
├─ output/                       # Fichiers CSV collectés
├─ streamlit_app_final.py        # Dashboard interactif
├─ requirements.txt              # Librairies Python nécessaires
└─ README.md                     # Documentation

⚙️ Installation et préparation

Cloner le projet

git clone https://github.com/Bricegoye/airci_project.git
cd airci_project


Créer un environnement virtuel et installer les dépendances

python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate    # Windows
pip install -r requirements.txt


Ajout  clé SerpAPI
Créez un fichier .env (ou utilisez les Secrets sur Streamlit Cloud) :

SERPAPI_KEY=Votre_cle_API


Exécuter la collecte des données (optionnel si vous avez déjà les CSV)

python scripts/fetch_serapi_daily.py

🌐 Lancer le dashboard Streamlit localement
streamlit run streamlit_app_final.py


Vous pouvez filtrer les données par compagnie aérienne.

Explorer les graphiques interactifs et le tableau des données.

🌐 Déployer sur Streamlit Cloud

Connectez-vous sur https://share.streamlit.io
 avec GitHub.

Créez une nouvelle app, sélectionnez votre dépôt airci_project, branche main, fichier streamlit_app_final.py.

Ajoutez votre clé API dans Secrets pour qu’elle reste sécurisée.

Déployez. Vous obtiendrez un lien du type :

[https://share.streamlit.io/bricegoye/airci_project/main/streamlit_app_final.py](https://airciproject-bgoye.streamlit.app/)

📊 Insights possibles

Comparer prix moyen par jour pour identifier le meilleur moment pour acheter un billet.

Identifier la compagnie la plus économique.

Visualiser les variations de prix et la distribution des tarifs.

Observer la relation entre durée de vol et prix.

Carte interactive pour une vue géographique intuitive.

🧠 Synthèse

Le projet montre :

Collecte automatisée de données

Nettoyage et analyse avec Pandas

Visualisations interactives avec Plotly et Streamlit

Insights décisionnels pour choisir le meilleur jour et la meilleure compagnie
