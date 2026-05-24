import streamlit as st
import numpy as np
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta

# App-Konfiguration für Smartphones optimiert
st.set_page_config(page_title="TGA Lüftungsprognose", layout="wide")
st.title("☀️ TGA Smart-Lüftungs-Vorhersager")

# --- Wetter-API für 24h-Vorhersage ---
@st.cache_data(ttl=600)
def get_24h_forecast(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m&timezone=Europe%2FBerlin"
        res = requests.get(url).json()
        
        times_raw = res["hourly"]["time"][:24]
        temps = res["hourly"]["temperature_2m"][:24]
        rhs = res["hourly"]["relative_humidity_2m"][:24]
        
        # Zeiten in lesbare Stunden formatieren
        times = [datetime.strptime(t, "%Y-%m-%dT%H:%M").strftime("%H:%O Uhr") for t in times_raw]
        return times, temps, rhs, True
    except Exception:
        # Fallback-Daten falls API offline
        times = [f"{(datetime.now() + timedelta(hours=i)).strftime('%H:00')}" for i in range(24)]
        temps = [15.0 + 5.0 * np.sin(i/3) for i in range(24)]
        rhs = [70 + 15 * np.cos(i/3) for i in range(24)]
        return times, temps, rhs, False

# --- Thermodynamische Berechnung (Mollier-Formeln) ---
def calc_x_and_h(theta, phi):
    # theta: Temp in °C, phi: rel. Feuchte in %
    p_sat = 610.78 * np.exp((17.08085 * theta) / (234.175 + theta))
    p_d = (phi / 100.0) * p_sat
    x = 622.0 * p_d / (101325.0 - p_d) # g/kg trockene Luft
    h = 1.005 * theta + (x / 1000.0) * (2501.0 + 1.86 * theta) # kJ/kg
    return x, h

# --- EINSTELLUNGEN DIREKT AUF DER HAUPTSEITE (Mobil optimiert) ---
with st.expander("⚙️ Sensoren & Standort einstellen", expanded=True):
    col_geo, col_room = st.columns(2)
    with col_geo:
        st.markdown("**📍 Wetter-Standort**")
        # Standardkoordinaten für Schwerte hinterlegt
        lat = st.number_input("Breitengrad (Latitude)", value=51.4400, format="%.4f")
        lon = st.number_input("Längengrad (Longitude)", value=7.5700, format="%.4f")
    with col_room:
        st.markdown("**🏠 Aktuelles Raumklima**")
        t_innen = st.slider("Raumtemperatur (°C)", 15.0, 28.0, 22.0, 0.5)
        phi_innen = st.slider("Hygrometer Innen (%)", 20, 90, 55, 5)

# Berechne aktuellen Innenzustand
x_innen, h_innen = calc_x_and_h(t_innen, phi_innen)

# Wettervorhersage abrufen
times, temps_out, rhs_out, api_success = get_24h_forecast(lat, lon)

if not api_success:
    st.warning("⚠️ Live-Wetterdaten konnten nicht geladen werden. Nutze thermodynamische Demo-Vorhersage.")

# Berechne thermodynamische Werte für den Außen-Verlauf
x_aussen_vorlauf = []
h_aussen_vorlauf = []
for t, f in zip(temps_out, rhs_out):
    x_o, h_o = calc_x_and_h(t, f)
    x_aussen_vorlauf.append(x_o)
    h_aussen_vorlauf.append(h_o)

# Aktuelle Werte (Stunde 0)
t_aussen_jetzt = temps_out[0]
phi_aussen_jetzt = rhs_out[0]
x_aussen_jetzt = x_aussen_vorlauf[0]

# --- AKTUELLER STATUS ---
st.markdown("---")
st.subheader("📊 Momentane Luftbilanz")
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Absolute Feuchte Innen", f"{x_innen:.2f} g/kg")
with c2:
    st.metric("Absolute Feuchte Außen (Jetzt)", f"{x_aussen_jetzt:.2f} g/kg")
with c3:
    # Differenz bestimmen
    diff_x = x_innen - x_aussen_jetzt
    if diff_x > 0:
        st.metric("Entfeuchtungs-Potenzial", f"+{diff_x:.2f} g/kg", delta_color="normal")
    else:
        st.metric("Feuchte-Last bei Lüftung", f"{diff_x:.2f} g/kg", delta_color="inverse")

# --- PROGNOSE-GRAFIK (DIE ZEITVORHERSAGE) ---
st.markdown("---")
st.subheader("📅 24-Stunden Lüftungs-Fahrplan")
st.write("Vergleicht den konstanten Feuchtegehalt deines Raumes mit der dynamischen Außenluft-Vorhersage:")

# Erstelle den zeitlichen Linien-Plot
fig_prognose = go.Figure()

# Raumluft-Linie (Konstant als Referenz)
fig_prognose.add_trace(go.Scatter(
    x=times, y=[x_innen]*24,
    mode='lines', name='Deine Raumluft (Soll-Grenze)',
    line=dict(color='rgba(31, 73, 125, 0.8)', width=3, dash='dash')
))

# Außenluft-Feuchtigkeitsverlauf
fig_prognose.add_trace(go.Scatter(
    x=times, y=x_aussen_vorlauf,
    mode='lines+markers', name='Vorhersage Außenluft (Feuchte x)',
    line=dict(color='#31859C', width=3),
    marker=dict(size=6)
))

fig_prognose.update_layout(
    xaxis_title="Uhrzeit (Nächste 24 Stunden)",
    yaxis_title="Wassergehalt x [g/kg trockene Luft]",
    height=400,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=10, r=10, t=10, b=10)
)
st.plotly_chart(fig_prognose, use_container_width=True)

# --- STÜNDLICHE LÜFTUNGS-AMPEL ---
st.subheader("⏱️ Wann macht das Fensteröffnen Sinn?")

# Analyse der optimalen Stunden
optimale_stunden = []
for i in range(24):
    # Bedingung: Absolut trockener UND Außenluft nicht zu heiß (Sommerlicher Wärmeschutz < 25°C)
    if x_aussen_vorlauf[i] < x_innen and temps_out[i] <= 25.0:
        optimale_stunden.append(times[i])

if optimale_stunden:
    st.success(f"🟢 **Perfekte Lüftungs-Fenster in den nächsten 24h:** {', '.join(optimale_stunden[:6])}...")
    st.info("💡 **Tipp:** In diesen grün markierten Phasen ist die Außenluft absolut trockener als deine Raumluft. Ein Stoßlüften transportiert effektiv Feuchtigkeit nach draußen, ohne die Räume zu überhitzen.")
else:
    st.error("🔴 In den nächsten 24 Stunden gibt es keine energetisch sinnvollen Lüftungsfenster. Die Außenluft transportiert entweder zusätzliche Feuchtigkeit hinein oder ist zu heiß (>25°C). Fenster geschlossen halten!")
