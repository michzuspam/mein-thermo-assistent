import streamlit as st
import numpy as np
import plotly.graph_objects as go
import requests

# App-Konfiguration & Design für Mobile optimiert
st.set_page_config(page_title="TGA Thermo-Assistent", layout="wide")
st.title("TGA Thermodynamik & Wetter-Assistent")

# --- Wetter API Integration (Open-Meteo) ---
@st.cache_data(ttl=600)  # Cache für 10 Minuten, um die API zu schonen
def get_live_weather(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m&hourly=temperature_2m,relative_humidity_2m&timezone=Europe%2FBerlin"
        res = requests.get(url).json()
        
        current_temp = res["current"]["temperature_2m"]
        current_rh = res["current"]["relative_humidity_2m"]
        
        # Trend für die nächsten 3 Stunden ermitteln (Aufwärmen oder Abkühlen)
        next_temps = res["hourly"]["temperature_2m"][1:4]
        avg_next_temp = sum(next_temps) / len(next_temps)
        
        if avg_next_temp > current_temp + 0.5:
            trend = "Aufwärmend (Hitzetrend)"
        elif avg_next_temp < current_temp - 0.5:
            trend = "Abendliche Abkühlung"
        else:
            trend = "Stabil"
            
        return current_temp, current_rh, trend, True
    except Exception:
        return 8.0, 85, "Keine Verbindung", False

# --- MATHEMATISCHE TGA-FUNKTIONEN ---
def calc_thermodynamics(theta, phi):
    p_sat = 610.78 * np.exp((17.08085 * theta) / (234.175 + theta))
    p_d = (phi / 100.0) * p_sat
    x = 622.0 * p_d / (101325.0 - p_d)
    h = 1.005 * theta + (x / 1000.0) * (2501.0 + 1.86 * theta)
    return x, h

# --- SIDEBAR / EINSTELLUNGEN ---
st.sidebar.header("📍 Standort & Raum-Sensoren")
# Koordinaten voreingestellt auf deine Region
lat = st.sidebar.number_input("Breitengrad (Latitude)", value=51.44, format="%.4f")
lon = st.sidebar.number_input("Längengrad (Longitude)", value=7.57, format="%.4f")

st.sidebar.markdown("---")
st.sidebar.subheader("Innenraum-Zustand")
t_innen = st.sidebar.slider("Raumtemperatur (°C)", 15.0, 30.0, 22.0, 0.5)
phi_innen = st.sidebar.slider("Relative Feuchte Innen (%)", 20, 90, 55, 5)

# Wetterdaten live abrufen
t_aussen_live, phi_aussen_live, wetter_trend, api_success = get_live_weather(lat, lon)

st.sidebar.markdown("---")
st.sidebar.subheader("Außenklima (Live-Wetter)")
if api_success:
    st.sidebar.success(f" Wetterdaten aktiv geladen!")
    t_aussen = st.sidebar.slider("Außentemperatur (°C)", -10.0, 40.0, float(t_aussen_live), 0.5)
    phi_aussen = st.sidebar.slider("Relative Feuchte Außen (%)", 20, 100, int(phi_aussen_live), 5)
else:
    st.sidebar.error("Wetter-API nicht erreichbar. Fallback-Werte aktiv.")
    t_aussen = st.sidebar.slider("Außentemperatur (°C)", -10.0, 40.0, 8.0, 0.5)
    phi_aussen = st.sidebar.slider("Relative Feuchte Außen (%)", 20, 100, 85, 5)

# --- BERECHNUNGEN DURCHFÜHREN ---
x_in, h_in = calc_thermodynamics(t_innen, phi_innen)
x_out, h_out = calc_thermodynamics(t_aussen, phi_aussen)

# --- LAYOUT ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📊 Echtzeit-Analyse")
    
    st.info(f"**Wetter-Trend:** {wetter_trend}")
    
    # Werte-Karten
    st.metric("Enthalpie Innen (h_innen)", f"{h_in:.2f} kJ/kg")
    st.metric("Enthalpie Außen (h_aussen)", f"{h_out:.2f} kJ/kg")
    st.metric("Wassergehalt Innen (x_innen)", f"{x_in:.2f} g/kg")
    st.metric("Wassergehalt Außen (x_aussen)", f"{x_out:.2f} g/kg")
    
    st.markdown("---")
    st.subheader("🔔 Lüftungsempfehlung")
    
    # Thermodynamische Entscheidungsmatrix
    if t_aussen > 25.0:
        st.error("❌ FENSTER ZU! Die Außenluft ist zu heiß (> 25°C). Du würdest dir die thermische Masse der Wände aufladen.")
    elif x_out >= x_in:
        st.warning("⚠️ FENSTER ZU! Die Außenluft ist absolut feuchter als drinnen (Lüftungsparadoxon). Dein Raum würde schwüler werden.")
    elif wetter_trend == "Aufwärmend (Hitzetrend)" and t_aussen > 22.0:
        st.error("❌ FENSTER ZU! Der Wetterbericht meldet steigende Temperaturen. Fenster jetzt schließen, um Kühle einzusperren.")
    elif h_out < h_in:
        if wetter_trend == "Abendliche Abkühlung":
            st.success("✅ JETZT STOSSLÜFTEN! Die Abendabkühlung läuft. Perfekter Zeitpunkt, um Feuchte und sensible Wärme abzuführen.")
        else:
            st.success("✅ LÜFTEN EMPFOHLEN! Die Außenluft entzieht dem Raum im Gesamtsaldo Energie (Enthalpie-Vorteil).")
    else:
        st.info("ℹ️ Keine akute Empfehlung. Luftzustände sind nahezu identisch.")

with col2:
    st.subheader("📈 hx-Diagramm (Mollier-Hintergrund)")
    
    # Sättigungskurve berechnen
    t_range = np.linspace(-10, 40, 50)
    x_sat_line = []
    for t in t_range:
        p_s = 610.78 * np.exp((17.08085 * t) / (234.175 + t))
        x_s = 622.0 * p_s / (101325.0 - p_s)
        x_sat_line.append(x_s)
        
    fig = go.Figure()
    
    # Sättigungskurve plotten
    fig.add_trace(go.Scatter(
        x=x_sat_line, y=t_range,
        mode='lines', name='Sättigungslinie (100% r.F.)',
        line=dict(color='red', width=2, dash='dash')
    ))
    
    # Zustandspunkte plotten
    fig.add_trace(go.Scatter(
        x=[x_out, x_in],
        y=[t_aussen, t_innen],
        mode='markers+lines',
        name='Luftzustände',
        marker=dict(size=12, color=['#31859C', '#1F497D']),
        line=dict(color='rgba(0,0,0,0.2)', width=2)
    ))
    
    fig.add_annotation(x=x_in, y=t_innen, text=" Raumluft", showarrow=True, arrowhead=2)
    fig.add_annotation(x=x_out, y=t_aussen, text=" Außenluft (Wetter)", showarrow=True, arrowhead=2)

    fig.update_layout(
        xaxis_title="Wassergehalt x [g/kg]",
        yaxis_title="Temperatur ϑ [°C]",
        xaxis=dict(range=[0, 20]),
        yaxis=dict(range=[-5, 35]),
        height=550,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)
