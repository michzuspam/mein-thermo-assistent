import streamlit as st
import numpy as np
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta

# App-Konfiguration für Smartphones optimiert
st.set_page_config(page_title="TGA Lüftungsprognose", layout="wide")
st.title("☀️ TGA Smart-Lüftungs-Vorhersager")

# --- Geocoding API (Ort in Koordinaten umwandeln) ---
@st.cache_data(ttl=86400) # 24 Stunden cachen
def get_coordinates_from_city(city_name):
    if not city_name:
        return 51.4400, 7.5700, "Schwerte (Standard)", True
    try:
        url = f"https://api.open-meteo.com/v1/search?name={city_name}&count=1&language=de&format=json"
        res = requests.get(url).json()
        if "results" in res and len(res["results"]) > 0:
            lat = res["results"][0]["latitude"]
            lon = res["results"][0]["longitude"]
            name = res["results"][0]["name"]
            return lat, lon, name, True
        return 51.4400, 7.5700, f"'{city_name}' nicht gefunden (Nutze Schwerte)", False
    except Exception:
        return 51.4400, 7.5700, "Schwerte (Fallback wegen Fehler)", False

# --- Wetter-API für 24h-Vorhersage ---
@st.cache_data(ttl=600)
def get_24h_forecast(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m&timezone=Europe%2FBerlin"
        res = requests.get(url).json()
        
        times_raw = res["hourly"]["time"][:24]
        temps = res["hourly"]["temperature_2m"][:24]
        rhs = res["hourly"]["relative_humidity_2m"][:24]
        
        # HIER KORRIGIERT: %M statt %O für die saubere Darstellung
        times = [datetime.strptime(t, "%Y-%m-%dT%H:%M").strftime("%H:%M Uhr") for t in times_raw]
        return times, temps, rhs, True
    except Exception:
        times = [f"{(datetime.now() + timedelta(hours=i)).strftime('%H:%M Uhr')}" for i in range(24)]
        temps = [15.0 + 5.0 * np.sin(i/3) for i in range(24)]
        rhs = [70 + 15 * np.cos(i/3) for i in range(24)]
        return times, temps, rhs, False

# --- Thermodynamische Berechnung (Mollier-Formeln) ---
def calc_x_and_h(theta, phi):
    p_sat = 610.78 * np.exp((17.08085 * theta) / (234.175 + theta))
    p_d = (phi / 100.0) * p_sat
    x = 622.0 * p_d / (101325.0 - p_d) 
    h = 1.005 * theta + (x / 1000.0) * (2501.0 + 1.86 * theta) 
    return x, h

# --- EINSTELLUNGEN DIREKT AUF DER HAUPTSEITE ---
with st.expander("⚙️ Sensoren & Standort einstellen", expanded=True):
    city_input = st.text_input("📍 Ort eingeben (z.B. Stadtname)", value="Schwerte")
    lat, lon, gefundenes_ziel, geo_success = get_coordinates_from_city(city_input)
    if city_input:
        st.caption(f"Verwendeter Standort: **{gefundenes_ziel}** (Lat: {lat:.4f}, Lon: {lon:.4f})")
    
    st.markdown("---")
    
    col_in, col_out = st.columns(2)
    with col_in:
        st.markdown("**🏠 Innensensor**")
        t_innen = st.slider("Raumtemperatur (°C)", 15.0, 28.0, 22.0, 0.5)
        phi_innen = st.slider("Hygrometer Innen (%)", 20, 90, 55, 5)
        
    with col_out:
        st.markdown("**🌳 Außensensor (Optional)**")
        use_outdoor_sensor = st.checkbox("Eigene Außensensoren nutzen", value=False, 
                                         help="Aktivieren, wenn du feste Werte deines eigenen Außensensors statt der aktuellen Wetterstation eintragen willst.")
        
        if use_outdoor_sensor:
            t_aussen_sensor = st.slider("Echte Außentemperatur (°C)", -10.0, 40.0, 15.0, 0.5)
            phi_aussen_sensor = st.slider("Echte relative Feuchte Außen (%)", 20, 100, 70, 5)
        else:
            st.info("Nutzt aktuell die Live-Wetterdaten für den Momentzustand.")

# Berechne aktuellen Innenzustand
x_innen, h_innen = calc_x_and_h(t_innen, phi_innen)

# Wettervorhersage abrufen
times, temps_out, rhs_out, api_success = get_24h_forecast(lat, lon)

# Verarbeite die 24h-Daten thermodynamisch
x_aussen_vorlauf = []
h_aussen_vorlauf = []
for t, f in zip(temps_out, rhs_out):
    x_o, h_o = calc_x_and_h(t, f)
    x_aussen_vorlauf.append(x_o)
    h_aussen_vorlauf.append(h_o)

if use_outdoor_sensor:
    x_sensor, h_sensor = calc_x_and_h(t_aussen_sensor, phi_aussen_sensor)
    t_aussen_jetzt = t_aussen_sensor
    x_aussen_jetzt = x_sensor
    temps_out[0] = t_aussen_sensor
    x_aussen_vorlauf[0] = x_sensor
else:
    t_aussen_jetzt = temps_out[0]
    x_aussen_jetzt = x_aussen_vorlauf[0]

# --- AKTUELLER STATUS ---
st.markdown("---")
st.subheader("📊 Momentane Luftbilanz")
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Absolute Feuchte Innen", f"{x_innen:.2f} g/kg")
with c2:
    status_label = "Absolute Feuchte Außen (dein Sensor)" if use_outdoor_sensor else "Absolute Feuchte Außen (Wetter)"
    st.metric(status_label, f"{x_aussen_jetzt:.2f} g/kg")
with c3:
    diff_x = x_innen - x_aussen_jetzt
    if diff_x > 0:
        st.metric("Entfeuchtungs-Potenzial", f"+{diff_x:.2f} g/kg")
    else:
        st.metric("Feuchte-Last bei Lüftung", f"{diff_x:.2f} g/kg", delta_color="inverse")

# --- PROGNOSE-GRAFIK ---
st.markdown("---")
st.subheader("📅 24-Stunden Lüftungs-Fahrplan")
st.write("Vergleicht den Feuchtegehalt deines Raumes mit der Außenluft (Erster Punkt = aktueller Zustand):")

fig_prognose = go.Figure()

fig_prognose.add_trace(go.Scatter(
    x=times, y=[x_innen]*24,
    mode='lines', name='Deine Raumluft (Soll-Grenze)',
    line=dict(color='rgba(31, 73, 125, 0.8)', width=3, dash='
    
