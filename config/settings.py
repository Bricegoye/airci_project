import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY_SERPAPI")
DEPARTURE_ID = os.getenv("DEPARTURE_ID", "CDG")
ARRIVAL_ID = os.getenv("ARRIVAL_ID", "ABJ")
CURRENCY = os.getenv("CURRENCY", "EUR")
LANG = os.getenv("LANG", "fr")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "data/raw_flights")
LOG_FILE = os.getenv("LOG_FILE", "logs/fetch.log")
START_DATE = os.getenv("START_DATE")
END_DATE = os.getenv("END_DATE")
