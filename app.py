# streamlit_app.py
import streamlit as st
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="Lüftungsrechner & Mollier", layout="wide")
st.title("Thermodynamischer Lüftungsrechner mit h,x-Diagramm")

# --- Seitenleiste: Eingaben ---
st.sidebar.header("Raumluft")
t_raum = st.sidebar.number_input("Temperatur Raum [°C]", value=23.5)
phi_raum = st.sidebar.slider("Relative Feuchte Raum [%]", 0, 100, 55)
v_raum = st.sidebar.number_input("Volumenstrom Raum [m³/h]", value=100.0)

st.sidebar.header("Außenluft")
t_aussen = st.sidebar.number_input("Temperatur Außen [°C]", value=16.0)
phi_aussen = st.sidebar.slider("Relative Feuchte Außen [%]", 0, 100, 85)
v_aussen = st.sidebar.number_input("Volumenstrom Außen [m³/h]", value=100.0)

# --- Berechnungen ---
def magnus_psat(t):
    return 610.78 * np.exp((17.08085 * t) / (234.175 + t))

def x_aus_phi_t(phi, t):
    psat = magnus_psat(t)
    pd = phi / 100 * psat
    return 622 * pd / (101325 - pd)  # g/kg

def enthalpie(t, x):
    return 1.005 * t + x / 1000 * (2501 + 1.86 * t)  # kJ/kg

x_raum = x_aus_phi_t(phi_raum, t_raum)
x_aussen = x_aus_phi_t(phi_aussen, t_aussen)
h_raum = enthalpie(t_raum, x_raum)
h_aussen = enthalpie(t_aussen, x_aussen)

# Mischung
v_ges = v_raum + v_aussen
t_misch = (t_raum * v_raum + t_aussen * v_aussen) / v_ges if v_ges > 0 else 0
x_misch = (x_raum * v_raum + x_aussen * v_aussen) / v_ges if v_ges > 0 else 0
h_misch = (h_raum * v_raum + h_aussen * v_aussen) / v_ges if v_ges > 0 else 0

# Relative Feuchte der Mischluft
psat_misch = magnus_psat(t_misch)
pd_misch = x_misch * 101325 / (622 + x_misch)
phi_misch = (pd_misch / psat_misch) * 100 if psat_misch > 0 else 0

# --- Lüftungsempfehlung ---
def empfehlung(t_a, h_a, h_i):
    if t_a > 25:
        return "❌ NICHT LÜFTEN – Behaglichkeitsgrenze (>25 °C)"
    if h_a < h_i:
        return "✅ LÜFTEN sinnvoll – Außenluft-Enthalpie niedriger"
    else:
        return "❌ NICHT LÜFTEN – Außenluft-Enthalpie höher"

# --- Darstellung ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("Zustandsgrößen")
    st.write(f"**Raumluft**: x = {x_raum:.1f} g/kg, h = {h_raum:.1f} kJ/kg")
    st.write(f"**Außenluft**: x = {x_aussen:.1f} g/kg, h = {h_aussen:.1f} kJ/kg")
    st.subheader("Mischluft")
    st.write(f"Temperatur = {t_misch:.1f} °C")
    st.write(f"Abs. Feuchte = {x_misch:.1f} g/kg")
    st.write(f"Relative Feuchte = {phi_misch:.1f} %")
    st.write(f"Enthalpie = {h_misch:.1f} kJ/kg")

with col2:
    st.subheader("Lüftungsempfehlung")
    st.markdown(f"### {empfehlung(t_aussen, h_aussen, h_raum)}")
    # Behaglichkeitsstatus Raum
    if phi_raum < 40:
        st.warning("Raumluft zu trocken (<40 %)")
    elif phi_raum > 60:
        st.warning("Raumluft zu feucht (>60 %)")
    else:
        st.success("Raumluft im Behaglichkeitsbereich (40–60 %)")

# --- hx-Diagramm (Plotly) ---
st.subheader("Interaktives h,x-Diagramm (Mollier)")

# Sättigungslinie
t_range = np.linspace(-10, 50, 100)
x_sat = [x_aus_phi_t(100, t) for t in t_range]

# Linien konstanter relativer Feuchte (20 %, 40 %, 60 %, 80 %)
phi_lines = [20, 40, 60, 80]
phi_data = {}
for phi in phi_lines:
    x_vals = [x_aus_phi_t(phi, t) for t in t_range]
    phi_data[phi] = x_vals

fig = go.Figure()

# Sättigung
fig.add_trace(go.Scatter(x=x_sat, y=t_range, mode='lines', name='φ=100 %',
                         line=dict(color='black', width=2)))

# Weitere φ-Linien
colors = ['lightblue', 'lightgreen', 'orange', 'red']
for idx, phi in enumerate(phi_lines):
    fig.add_trace(go.Scatter(x=phi_data[phi], y=t_range, mode='lines',
                             name=f'φ={phi} %',
                             line=dict(color=colors[idx], width=1, dash='dash')))

# Zustandspunkte
fig.add_trace(go.Scatter(x=[x_raum, x_aussen, x_misch],
                         y=[t_raum, t_aussen, t_misch],
                         mode='markers+text',
                         name='Zustandspunkte',
                         text=['Raum', 'Außen', 'Misch'],
                         textposition='top center',
                         marker=dict(size=10, color='red')))

fig.update_layout(
    title="h,x-Diagramm mit Zustandspunkten",
    xaxis_title="Wassergehalt x [g/kg]",
    yaxis_title="Temperatur [°C]",
    legend=dict(x=0.01, y=0.99),
    margin=dict(l=40, r=40, t=40, b=40)
)

st.plotly_chart(fig, use_container_width=True)
