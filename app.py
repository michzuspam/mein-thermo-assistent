import streamlit as st
import numpy as np
import requests

st.set_page_config(page_title="Lüftungs-Profi", layout="wide")
st.title("☀️ TGA Lüftungs-Prognose (Vollständig)")

# --- THERMODYNAMIK-KERN ---
def calc_x_and_h(t, phi):
    p_sat = 610.78 * np.exp((17.08085 * t) / (234.175 + t))
    p_d = (phi / 100.0) * p_sat
    x = 622.0 * p_d / (101325.0 - p_d)
    h = 1.005 * t + (x / 1000.0) * (2501.0 + 1.86 * t)
    return x, h

def predict_rh_after_cooling(t_new, x_val):
    # Berechnet die neue relative Feuchte nach Abkühlung bei gleichem x
    p_sat_new = 610.78 * np.exp((17.08085 * t_new) / (234.175 + t_new))
    p_d = (x_val * 101325.0) / (622.0 + x_val)
    return (p_d / p_sat_new) * 100.0

# --- DATEN-ABFRAGE ---
@st.cache_data(ttl=60)
def fetch_weather_data(city):
    geo_url = f"https://api.open-meteo.com/v1/search?name={city}&count=1&language=de&format=json"
    res = requests.get(geo_url).json()
    if "results" in res:
        lat, lon = res["results"][0]["latitude"], res["results"][0]["longitude"]
        w_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m"
        w = requests.get(w_url).json()
        return w["hourly"]["temperature_2m"][0], w["hourly"]["relative_humidity_2m"][0]
    return 18.0, 65.0

# --- EINSTELLUNGEN ---
with st.sidebar:
    st.header("⚙️ Konfiguration")
    city = st.text_input("Ort eingeben:", value="Schwerte")
    use_sensor = st.checkbox("Eigener Außensensor", value=False)
    
    t_out_live, h_out_live = fetch_weather_data(city)
    
    if use_sensor:
        t_out = st.number_input("Sensor Temp Außen (°C):", value=t_out_live, step=0.1)
        h_out = st.number_input("Sensor Feuchte Außen (%):", value=h_out_live, step=1.0)
    else:
        t_out, h_out = t_out_live, h_out_live
        st.info(f"Live-Wetter: {t_out}°C / {h_out}%")

# --- HAUPT-SLIDER (INNEN) ---
c1, c2 = st.columns(2)
t_in = c1.slider("Raum-Temperatur (°C)", 15.0, 30.0, 22.0, 0.1)
h_in = c2.slider("Raum-Feuchte (%)", 20, 90, 55, 1)

# --- BERECHNUNG ---
x_in, h_in_val = calc_x_and_h(t_in, h_in)
x_out, h_out_val = calc_x_and_h(t_out, h_out)

# Die kritische Simulation: Abkühlen um 2 Grad
rh_sim = predict_rh_after_cooling(t_in - 2.0, x_out)

# --- LOGIK MIT DER 60%-BEDINGUNG ---
st.markdown("---")
if t_out > 25:
    st.error("🛑 ZUMACHEN: Außenluft über 25°C (Überhitzungsgefahr).")
elif x_out >= x_in:
    st.error("🛑 ZUMACHEN: Außenluft bringt Feuchtigkeit ein (Lüftungsparadoxon).")
elif t_out < t_in and rh_sim >= 60.0:
    st.error(f"🛑 ZUMACHEN: Auskühl-Gefahr! Relative Feuchte würde beim Abkühlen auf {rh_sim:.1f}% steigen.")
else:
    st.success("🟢 LÜFTEN: Luft-Zustand ist für Entfeuchtung und Behaglichkeit sicher.")

# --- METRIKEN ---
col1, col2, col3 = st.columns(3)
col1.metric("Abs. Feuchte Außen", f"{x_out:.2f} g/kg")
col2.metric("Abs. Feuchte Innen", f"{x_in:.2f} g/kg")
col3.metric("Feuchte-Differenz", f"{x_in - x_out:.2f} g/kg")
