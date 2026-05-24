import streamlit as st
import numpy as np
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Lüftung", layout="wide")
st.title("☀️ TGA Lüftungs-Prognose")

# --- ORTS-SUCHE ---
@st.cache_data(ttl=86400)
def get_geo(city):
    if not city:
        return 51.4400, 7.5700, "Schwerte"
    try:
        url = f"https://api.open-meteo.com/v1/search?name={city}&count=1&language=de&format=json"
        r = requests.get(url).json()
        if "results" in r:
            res = r["results"][0]
            return res["latitude"], res["longitude"], res["name"]
        return 51.4400, 7.5700, "Schwerte"
    except:
        return 51.4400, 7.5700, "Schwerte"

# --- WEATHER FORECAST ---
@st.cache_data(ttl=600)
def get_weather(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m&timezone=Europe%2FBerlin"
        r = requests.get(url).json()
        t_raw = r["hourly"]["time"][:24]
        temps = r["hourly"]["temperature_2m"][:24]
        rh = r["hourly"]["relative_humidity_2m"][:24]
        times = [datetime.strptime(x, "%Y-%m-%dT%H:%M").strftime("%H:%M") for x in t_raw]
        return times, temps, rh
    except:
        times = [f"{i:02d}:00" for i in range(24)]
        temps = [18.0] * 24
        rh = [65.0] * 24
        return times, temps, rh

# --- MOLLIER RECHNUNG ---
def calc_x_and_h(t, phi):
    p_sat = 610.78 * np.exp((17.08085 * t) / (234.175 + t))
    p_d = (phi / 100.0) * p_sat
    x = 622.0 * p_d / (101325.0 - p_d)
    h = 1.005 * t + (x / 1000.0) * (2501.0 + 1.86 * t)
    return x, h

# --- PROGNOSE RELATIVE FEUCHTE NACH ABKÜHLUNG ---
def predict_rh_after_cooling(t_target, x_target):
    p_sat_target = 610.78 * np.exp((17.08085 * t_target) / (234.175 + t_target))
    p_d_target = (x_target * 101325.0) / (622.0 + x_target)
    return (p_d_target / p_sat_target) * 100.0

# --- EINSTELLUNGEN ---
with st.expander("⚙️ Einstellungen", expanded=True):
    stadt = st.text_input("📍 Ort", value="Schwerte")
    lat, lon, stadt_name = get_geo(stadt)
    st.caption(f"Ort: {stadt_name} ({lat:.2f}, {lon:.2f})")
    
    st.markdown("---")
    t_in = st.slider("Raum-Temp (°C)", 15.0, 28.0, 22.0, 0.1)
    h_in = st.slider("Hygrometer Innen (%)", 20, 90, 55, 1)
    
    st.markdown("---")
    use_sensor = st.checkbox("Eigener Außensensor")
    if use_sensor:
        t_out_s = st.slider("Sensor-Temp Außen (°C)", -10.0, 40.0, 15.0, 0.1)
        h_out_s = st.slider("Sensor Feuchte Außen (%)", 20, 100, 70, 1)

# Werte berechnen
x_in, h_in_val = calc_x_and_h(t_in, h_in)
times, temps_out, rh_out = get_weather(lat, lon)

x_out_list = []
for t, f in zip(temps_out, rh_out):
    x_o, _ = calc_x_and_h(t, f)
    x_out_list.append(x_o)

if use_sensor:
    t_act_out = t_out_s
    x_act_out, h_act_out = calc_x_and_h(t_out_s, h_out_s)
    temps_out[0] = t_out_s
    x_out_list[0] = x_act_out
else:
    t_act_out = temps_out[0]
    x_act_out, h_act_out = calc_x_and_h(temps_out[0], rh_out[0])

# --- STATUS ---
st.markdown("---")
st.subheader("📊 Thermodynamische Luftbilanz")

st.markdown("**🧪 Absolute Feuchte (Wassergehalt):**")
col1, col2, col3 = st.columns(3)
col1.metric("Innen (x)", f"{x_in:.2f} g/kg")
col2.metric("Außen (x)", f"{x_act_out:.2f} g/kg")
diff_x = x_in - x_act_out
if diff_x > 0:
    col3.metric("Entfeuchtungs-Potenzial", f"+{diff_x:.2f} g/kg")
else:
    col3.metric("Feuchtelast", f"{diff_x:.2f} g/kg", delta_color="inverse")

st.markdown("**🔥 Spezifische Enthalpie (Energiegehalt):**")
col4, col5, col6 = st.columns(3)
col4.metric("Innen (h)", f"{h_in_val:.2f} kJ/kg")
col5.metric("Außen (h)", f"{h_act_out:.2f} kJ/kg")
diff_h = h_in_val - h_act_out
col6.metric("Energie-Differenz (Δh)", f"{diff_h:.2f} kJ/kg")

# --- GRAFIK ---
st.markdown("---")
st.subheader("📅 24-Stunden Verlauf (Absolute Feuchte)")

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=times, y=[x_in]*24, mode='lines', 
    name='Innen', line=dict(color='blue', width=2, dash='dash')
))
fig.add_trace(go.Scatter(
    x=times, y=x_out_list, mode='lines+markers', 
    name='Außen (Trend)', line=dict(color='cyan', width=2)
))

fig.update_layout(
    xaxis_title="Uhrzeit", yaxis_title="Wassergehalt x [g/kg]",
    height=350, margin=dict(l=10, r=10, t=10, b=10)
)
st.plotly_chart(fig, use_container_width=True)

# --- AMPEL LOGIK MIT AUSKÜHL-SCHUTZ ---
st.markdown("---")
st.subheader("⏱️ Empfehlung")

# Simulation: Raum kühlt durch Lüften hypothetisch um 2°C ab
t_sim_room = t_in - 2.0
rh_simulated = predict_rh_after_cooling(t_sim_room, x_act_out)

if t_act_out > 25.0:
    st.error("❌ ZU HEISS: Außen über 25°C. Gefahr von sommerlicher Überhitzung!")
elif x_act_out >= x_in:
    st.warning("⚠️ SCHWÜL: Außenluft bringt zusätzliche absolute Feuchte (Lüftungsparadoxon).")
elif h_in >= 55 and t_act_out < t_in and rh_simulated >= 60.0:
    st.error(f"🛑 AUSKÜHL-WARNUNG: Absolute Feuchte ist zwar niedriger, aber durch die kalte Außenluft würde die relative Raumfeuchte beim Abkühlen auf kritische {rh_simulated:.1f}% ansteigen (Schimmelgefahr am Abend/nachts)!")
else:
    st.success(f"✅ JETZT LÜFTEN: Außenluft entfeuchtet effektiv. (Erwartete Feuchte nach Abkühlung: {rh_simulated:.1f}%)")

# Stündliche Vorschau (berücksichtigt jetzt auch das Auskühllimit)
ok_hours = []
for i in range(24):
    x_forecast = x_out_list[i]
    t_forecast = temps_out[i]
    rh_forecast_sim = predict_rh_after_cooling(t_in - 2.0, x_forecast)
    
    if x_forecast < x_in and t_forecast <= 25.0:
        if not (h_in >= 55 and t_forecast < t_in and rh_forecast_sim >= 60.0):
            ok_hours.append(times[i])

if ok_hours:
    st.info(f"🟢 Sichere Lüftungsstunden: {', '.join(ok_hours[:6])}")
else:
    st.error("🔴 Keine sicheren Lüftungsfenster in Sicht (Gefahr von Schwüle oder Raum-Auskühlung).")
