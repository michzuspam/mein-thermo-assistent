import streamlit as st
import numpy as np
import requests
from datetime import datetime

st.set_page_config(page_title="Lüftungs-Wächter", layout="wide")
st.title("☀️ TGA Lüftungs-Prognose")

# --- KERN-FUNKTIONEN ---
def calc_x_and_h(t, phi):
    p_sat = 610.78 * np.exp((17.08085 * t) / (234.175 + t))
    p_d = (phi / 100.0) * p_sat
    x = 622.0 * p_d / (101325.0 - p_d)
    h = 1.005 * t + (x / 1000.0) * (2501.0 + 1.86 * t)
    return x, h

# --- DATEN-ABFRAGE MIT OPTIMIERTEM CACHING ---
@st.cache_data(ttl=300)
def fetch_weather(city):
    geo_url = f"https://api.open-meteo.com/v1/search?name={city}&count=1&language=de&format=json"
    res = requests.get(geo_url).json()
    if "results" in res:
        lat, lon = res["results"][0]["latitude"], res["results"][0]["longitude"]
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m"
        w = requests.get(weather_url).json()
        return w["hourly"]["temperature_2m"][0], w["hourly"]["relative_humidity_2m"][0]
    return 18.0, 65.0

# --- SIDEBAR & EINSTELLUNGEN ---
with st.sidebar:
    st.header("⚙️ Konfiguration")
    stadt = st.text_input("Ort (für Wetterdaten):", value="Schwerte")
    
    st.markdown("---")
    use_ext_sensor = st.checkbox("Eigener Außensensor vorhanden?", value=False)
    
    t_out_live, h_out_live = fetch_weather(stadt)
    
    if use_ext_sensor:
        t_out = st.number_input("Sensor Temperatur Außen (°C):", value=t_out_live, step=0.1)
        h_out = st.number_input("Sensor Feuchte Außen (%):", value=h_out_live, step=1.0)
    else:
        t_out, h_out = t_out_live, h_out_live
        st.info(f"Wetter-Service: {t_out}°C / {h_out}%")

# --- HAUPT-SLIDER (Innen) ---
col_in1, col_in2 = st.columns(2)
t_in = col_in1.slider("Raum-Temperatur (°C)", 15.0, 30.0, 22.0, 0.1)
h_in = col_in2.slider("Raum-Feuchte (%)", 20, 90, 55, 1)

# --- BERECHNUNGEN ---
x_in, h_in_val = calc_x_and_h(t_in, h_in)
x_out, h_out_val = calc_x_and_h(t_out, h_out)

# --- DASHBOARD ---
st.markdown("---")
c1, c2, c3 = st.columns(3)
c1.metric("Innen (x / h)", f"{x_in:.2f} g/kg", f"{h_in_val:.1f} kJ/kg")
c2.metric("Außen (x / h)", f"{x_out:.2f} g/kg", f"{h_out_val:.1f} kJ/kg")
c3.metric("Enthalpie-Differenz", f"{h_in_val - h_out_val:.2f} kJ/kg")

# --- ENTSCHEIDUNG ---
st.markdown("---")
if t_out > 25:
    st.error("🛑 ZUMACHEN: Außenluft ist mit über 25°C zu warm (Überhitzungsgefahr).")
elif x_out >= x_in:
    st.error("🛑 ZUMACHEN: Außenluft ist absolut feuchter als die Innenluft (Lüftungsparadoxon).")
else:
    st.success("🟢 LÜFTEN: Außenluft entfeuchtet den Raum effizient.")
        
