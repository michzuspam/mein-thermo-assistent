import streamlit as st
import numpy as np
import plotly.graph_objects as go
import requests
from datetime import datetime

st.set_page_config(page_title="Lüftung", layout="wide")
st.title("☀️ TGA Lüftungs-Prognose")

# --- KORRIGIERTE ORTS-SUCHE (Ohne Caching-Sperre bei State-Wechsel) ---
def get_geo_live(city_name):
    if not city_name or city_name.strip() == "":
        return 51.4400, 7.5700, "Schwerte"
    try:
        url = f"https://api.open-meteo.com/v1/search?name={requests.utils.quote(city_name)}&count=1&language=de&format=json"
        r = requests.get(url, timeout=5).json()
        if "results" in r and len(r["results"]) > 0:
            res = r["results"][0]
            return float(res["latitude"]), float(res["longitude"]), res["name"]
    except Exception as e:
        st.sidebar.error(f"Fehler bei Ortssuche: {e}")
    return 51.4400, 7.5700, "Schwerte"

@st.cache_data(ttl=600)
def get_weather(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m&timezone=Europe%2FBerlin"
        r = requests.get(url, timeout=5).json()
        t_raw = r["hourly"]["time"][:24]
        temps = r["hourly"]["temperature_2m"][:24]
        rh = r["hourly"]["relative_humidity_2m"][:24]
        times = [datetime.strptime(x, "%Y-%m-%dT%H:%M").strftime("%H:%M") for x in t_raw]
        return times, temps, rh
    except:
        return [f"{i:02d}:00" for i in range(24)], [18.0] * 24, [65.0] * 24

def calc_x_and_h(t, phi):
    p_sat = 610.78 * np.exp((17.08085 * t) / (234.175 + t))
    p_d = (phi / 100.0) * p_sat
    x = 622.0 * p_d / (101325.0 - p_d)
    h = 1.005 * t + (x / 1000.0) * (2501.0 + 1.86 * t)
    return x, h

def predict_rh_after_cooling(t_target, x_target):
    p_sat_target = 610.78 * np.exp((17.08085 * t_target) / (234.175 + t_target))
    p_d_target = (x_target * 101325.0) / (622.0 + x_target)
    return (p_d_target / p_sat_target) * 100.0

# --- BENUTZEROBERFLÄCHE ---
with st.sidebar:
    st.header("📍 Standort & Sensor")
    # Live-Eingabe ohne blockierendes Caching bei Textänderung
    stadt_eingabe = st.text_input("Ort eingeben:", value="Schwerte")
    lat, lon, stadt_name = get_geo_live(stadt_eingabe)
    st.success(f"Aktiviert: {stadt_name} ({lat:.2f}°N, {lon:.2f}°E)")

st.subheader(f"Haus-Klima-Analyse für {stadt_name}")

col_in1, col_in2 = st.columns(2)
with col_in1:
    t_in = st.slider("Raum-Temp (°C)", 15.0, 28.0, 22.0, 0.1)
with col_in2:
    h_in = st.slider("Hygrometer Innen (%)", 20, 90, 55, 1)

# Wetter & Berechnung
times, temps_out, rh_out = get_weather(lat, lon)
x_in, h_in_val = calc_x_and_h(t_in, h_in)

t_act_out = temps_out[0]
h_act_out_val = rh_out[0]
x_act_out, h_act_out = calc_x_and_h(t_act_out, h_act_out_val)

x_out_list = [calc_x_and_h(t, f)[0] for t, f in zip(temps_out, rh_out)]

# Simulation der Abkühlung
t_sim_room = t_in - 2.0
rh_simulated = predict_rh_after_cooling(t_sim_room, x_act_out)

# --- ENTSCHEIDUNGS-LOGIK FÜR DIE AUTOMATION ---
status_code = "INTERN"
empfehlung_text = ""

if t_act_out > 25.0:
    status_code = "ZUMACHEN"
    empfehlung_text = "🛑 JETZT ZUMACHEN: Außenluft über 25°C (Überhitzungsgefahr!)."
elif x_act_out >= x_in:
    status_code = "ZUMACHEN"
    empfehlung_text = "🛑 JETZT ZUMACHEN: Außenluft bringt absolute Feuchte rein (Lüftungsparadoxon)."
elif h_in >= 55 and t_act_out < t_in and rh_simulated >= 60.0:
    status_code = "ZUMACHEN"
    empfehlung_text = f"🛑 JETZT ZUMACHEN / ZULASSEN: Kalte Luft treibt die relative Raumfeuchte beim Abkühlen auf kritische {rh_simulated:.1f}%!"
else:
    status_code = "AUFMACHEN"
    empfehlung_text = f"🟢 JETZT AUFMACHEN: Effektive Entfeuchtung läuft. Ziel-Feuchte nach Abkühlung unbedenklich ({rh_simulated:.1f}%)."

# Großes visuelles Signal auf der Oberfläche
if status_code == "AUFMACHEN":
    st.success(f"### {empfehlung_text}")
else:
    st.error(f"### {empfehlung_text}")

# --- ENTHALPIE-METRIKEN ---
st.markdown("---")
c1, c2, c3 = st.columns(3)
c1.metric("Absolute Feuchte Innen (x)", f"{x_in:.2f} g/kg")
c2.metric("Absolute Feuchte Außen (x)", f"{x_act_out:.2f} g/kg")
c3.metric("Potenzial", f"{x_in - x_act_out:.2f} g/kg (Entfeuchtung)" if x_in > x_act_out else f"{x_in - x_act_out:.2f} g/kg (Befeuchtung)", delta=round(x_in - x_act_out, 2))

# 24h Trend-Chart
fig = go.Figure()
fig.add_trace(go.Scatter(x=times, y=[x_in]*24, mode='lines', name='Innen absolute Feuchte', line=dict(color='orange', dash='dash')))
fig.add_trace(go.Scatter(x=times, y=x_out_list, mode='lines+markers', name='Außen absolute Feuchte (Prognose)', line=dict(color='cyan')))
fig.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
st.plotly_chart(fig, use_container_width=True)
