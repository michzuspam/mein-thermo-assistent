import streamlit as st
import numpy as np
import requests

st.set_page_config(page_title="Lüftungs-Profi", layout="wide")
st.title("☀️ TGA Lüftungs-Prognose")

# --- THERMODYNAMIK-KERN ---
def calc_x_and_h(t, phi):
    # Magnus-Formel für Sättigungsdampfdruck
    p_sat = 610.78 * np.exp((17.08085 * t) / (234.175 + t))
    p_d = (phi / 100.0) * p_sat
    x = 622.0 * p_d / (101325.0 - p_d)
    h = 1.005 * t + (x / 1000.0) * (2501.0 + 1.86 * t)
    return x, h

def get_live_weather(city):
    try:
        geo_url = f"https://api.open-meteo.com/v1/search?name={city}&count=1&language=de&format=json"
        res = requests.get(geo_url, timeout=5).json()
        if "results" in res:
            lat, lon = res["results"][0]["latitude"], res["results"][0]["longitude"]
            w_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m"
            w = requests.get(w_url, timeout=5).json()
            return w["hourly"]["temperature_2m"][0], w["hourly"]["relative_humidity_2m"][0]
    except:
        pass
    return 18.0, 65.0

# --- EINSTELLUNGEN ---
stadt = st.text_input("Ort eingeben (Enter drücken):", value="Schwerte")
t_out_live, h_out_live = get_live_weather(stadt)

st.subheader("Außenbedingungen")
use_sensor = st.checkbox("Eigener Außensensor verwenden?", value=False)
c_out1, c_out2 = st.columns(2)

if use_sensor:
    t_out = c_out1.number_input("Sensor Temp Außen (°C):", value=t_out_live, step=0.1)
    h_out = c_out2.number_input("Sensor Feuchte Außen (%):", value=h_out_live, step=1.0)
else:
    t_out, h_out = t_out_live, h_out_live
    st.info(f"Live-Daten {stadt}: {t_out}°C / {h_out}%")

st.subheader("Innenbedingungen")
c_in1, c_in2 = st.columns(2)
t_in = c_in1.slider("Raum-Temperatur (°C)", 15.0, 30.0, 22.0, 0.1)
h_in = c_in2.slider("Raum-Feuchte (%)", 20, 90, 55, 1)

# --- BERECHNUNGEN ---
x_in, h_in_val = calc_x_and_h(t_in, h_in)
x_out, h_out_val = calc_x_and_h(t_out, h_out)

# Auskühl-Simulation: Raum kühlt um 2 Grad ab
t_sim = t_in - 2.0
p_sat_sim = 610.78 * np.exp((17.08085 * t_sim) / (234.175 + t_sim))
p_d_out = (x_out * 101325.0) / (622.0 + x_out)
rh_sim = (p_d_out / p_sat_sim) * 100

# --- DASHBOARD ---
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Enthalpie Innen", f"{h_in_val:.1f} kJ/kg")
col2.metric("Enthalpie Außen", f"{h_out_val:.1f} kJ/kg")
col3.metric("Abs. Feuchte Innen", f"{x_in:.2f} g/kg")
col4.metric("Abs. Feuchte Außen", f"{x_out:.2f} g/kg")

# --- LOGIK ---
st.markdown("---")
if t_out > 25:
    st.error("🛑 ZUMACHEN: Außenluft > 25°C (Überhitzungsschutz).")
elif x_out >= x_in:
    st.error("🛑 ZUMACHEN: Außenluft zu feucht (Lüftungsparadoxon).")
elif t_out < t_in and rh_sim >= 60.0:
    st.error(f"🛑 ZUMACHEN: Auskühl-Gefahr! Relative Feuchte würde bei Abkühlung auf {rh_sim:.1f}% steigen.")
else:
    st.success("🟢 LÜFTEN: Zustand sicher und entfeuchtend.")
