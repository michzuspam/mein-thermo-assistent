import streamlit as st
import numpy as np
import requests
from datetime import datetime

st.set_page_config(page_title="Lüftungs-Wächter Pro", layout="wide")
st.title("☀️ TGA Lüftungs-Prognose & Automation")

# --- KERN-FUNKTIONEN ---
def calc_x_and_h(t, phi):
    """Berechnet Wassergehalt x und Enthalpie h für feuchte Luft."""
    p_sat = 610.78 * np.exp((17.08085 * t) / (234.175 + t))
    p_d = (phi / 100.0) * p_sat
    x = 622.0 * p_d / (101325.0 - p_d)
    h = 1.005 * t + (x / 1000.0) * (2501.0 + 1.86 * t)
    return x, h

# --- SIDEBAR: ORT & SENSOR-EINGABE ---
st.sidebar.header("📍 Einstellungen")

# Ort-Eingabe (Ohne Caching-Blockade)
stadt = st.sidebar.text_input("Ort (für Wetterdaten):", value="Schwerte")

# Manuelle Sensoreingabe-Option
use_manual = st.sidebar.checkbox("Eigenen Sensor verwenden?", value=False)
t_sensor, h_sensor = 22.0, 55.0
if use_manual:
    t_sensor = st.sidebar.number_input("Sensor Temperatur (°C):", value=22.0, step=0.1)
    h_sensor = st.sidebar.number_input("Sensor Feuchte (%):", value=55.0, step=1.0)

# --- DATEN-ABFRAGE ---
@st.cache_data(ttl=300)
def fetch_weather(city):
    # Geokodierung
    geo_url = f"https://api.open-meteo.com/v1/search?name={city}&count=1&language=de&format=json"
    res = requests.get(geo_url).json()
    if "results" in res:
        lat, lon = res["results"][0]["latitude"], res["results"][0]["longitude"]
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m"
        w = requests.get(weather_url).json()
        return w["hourly"]["temperature_2m"][0], w["hourly"]["relative_humidity_2m"][0]
    return 18.0, 65.0

t_out, h_out = fetch_weather(stadt)
x_in, h_in = calc_x_and_h(t_sensor, h_sensor)
x_out, h_out_val = calc_x_and_h(t_out, h_out)

# --- DASHBOARD ---
col1, col2, col3 = st.columns(3)
col1.metric("Raum (Innen)", f"{t_sensor}°C", f"{h_sensor}% rF")
col2.metric("Außen (Live)", f"{t_out}°C", f"{h_out}% rF")
col3.metric("Enthalpie-Diff (h_in - h_out)", f"{h_in - h_out_val:.2f} kJ/kg")

st.markdown("---")

# --- ENTSCHEIDUNGSLOGIK ---
if t_out > 25:
    st.error("🛑 ZUMACHEN: Außen zu heiß (>25°C).")
elif x_out >= x_in:
    st.error("🛑 ZUMACHEN: Außenluft feuchter als Raumluft (Lüftungsparadoxon).")
else:
    st.success("🟢 LÜFTEN: Außenluft entfeuchtet den Raum effizient.")

st.info(f"Basisdaten: x_in={x_in:.2f} g/kg, x_out={x_out:.2f} g/kg")
    
