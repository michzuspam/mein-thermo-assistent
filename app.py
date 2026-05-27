# streamlit_app.py
import streamlit as st
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="Thermodynamik-Rechner", layout="wide")
st.title("Thermodynamischer Leistungsrechner & Lüftungsassistent")

# Tabs anlegen
tab1, tab2, tab3, tab4 = st.tabs([
    "🔧 Luft- & Wasserberechnung",
    "🌡️ Lüftung & hx-Diagramm",
    "📚 Glossar",
    "📐 Herleitung Konstanten"
])

# ================== TAB 1: Luft- & Wasserberechnung ==================
with tab1:
    st.header("Heizlast- und Leistungsberechnungen")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Luft")
        V_luft = st.number_input("Volumenstrom Luft [m³/h]", value=150.0)
        deltaT_luft = st.number_input("Temperaturdifferenz Luft [K]", value=25.0)
        Q_luft = V_luft * deltaT_luft * 0.34  # W
        st.metric("Heizleistung Luft", f"{Q_luft:.0f} W")
        st.caption(f"Umrechnung: Q̇ = V̇ × ΔT × 0.34 = {V_luft} × {deltaT_luft} × 0.34 = {Q_luft:.0f} W")
    
    with col2:
        st.subheader("Wasser")
        V_wasser = st.number_input("Volumenstrom Wasser [m³/h]", value=2.5)
        deltaT_wasser = st.number_input("Spreizung Wasser [K]", value=10.0)
        Q_wasser = V_wasser * deltaT_wasser * 1.163  # kW
        st.metric("Übertragene Leistung Wasser", f"{Q_wasser:.2f} kW")
        st.caption(f"Formel: Q̇ = V̇ × ΔT × 1.163 = {V_wasser} × {deltaT_wasser} × 1.163 = {Q_wasser:.2f} kW")

    st.subheader("Lufterhitzer-Kopplung")
    V_luft_heiz = st.number_input("Gewünschte Luftmenge Lufterhitzer [m³/h]", value=1500.0)
    deltaT_luft_heiz = st.number_input("Temperaturhub Luft [K]", value=22.0)
    deltaT_ww = st.number_input("Spreizung Heizwasser [K]", value=20.0)
    
    Q_heiz = V_luft_heiz * deltaT_luft_heiz * 0.34 / 1000  # kW
    m_wasser = (Q_heiz / 1.163 / deltaT_ww) * 1000  # kg/h
    
    st.write(f"**Erforderliche Heizleistung:** {Q_heiz:.1f} kW")
    st.write(f"**Bevorzugter Wassermassenstrom:** {m_wasser:.1f} kg/h")

# ================== TAB 2: Lüftung & hx-Diagramm ==================
with tab2:
    st.header("Zustandsberechnung und Lüftungsempfehlung")
    
    # Eingabefelder
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Raumluft")
        t_raum = st.number_input("Temperatur Raum [°C]", value=23.5)
        phi_raum = st.slider("Relative Feuchte Raum [%]", 0, 100, 55)
        v_raum = st.number_input("Volumenstrom Raum [m³/h]", value=100.0)
    with col2:
        st.subheader("Außenluft")
        t_aussen = st.number_input("Temperatur Außen [°C]", value=16.0)
        phi_aussen = st.slider("Relative Feuchte Außen [%]", 0, 100, 85)
        v_aussen = st.number_input("Volumenstrom Außen [m³/h]", value=100.0)

    # Berechnungen
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

    v_ges = v_raum + v_aussen
    t_misch = (t_raum * v_raum + t_aussen * v_aussen) / v_ges if v_ges > 0 else 0
    x_misch = (x_raum * v_raum + x_aussen * v_aussen) / v_ges if v_ges > 0 else 0
    h_misch = (h_raum * v_raum + h_aussen * v_aussen) / v_ges if v_ges > 0 else 0

    psat_misch = magnus_psat(t_misch)
    pd_misch = x_misch * 101325 / (622 + x_misch)
    phi_misch = (pd_misch / psat_misch) * 100 if psat_misch > 0 else 0

    colA, colB = st.columns(2)
    with colA:
        st.subheader("Berechnete Zustandsgrößen")
        st.write(f"Raumluft: x = {x_raum:.1f} g/kg, h = {h_raum:.1f} kJ/kg")
        st.write(f"Außenluft: x = {x_aussen:.1f} g/kg, h = {h_aussen:.1f} kJ/kg")
        st.write("---")
        st.write(f"Mischluft: x = {x_misch:.1f} g/kg, h = {h_misch:.1f} kJ/kg")
        st.write(f"Mischluft: Temperatur = {t_misch:.1f} °C")
        st.write(f"Relative Feuchte Mischluft = {phi_misch:.1f} %")

    with colB:
        st.subheader("Lüftungsempfehlung (h-Regel)")
        if t_aussen > 25:
            st.error("❌ NICHT LÜFTEN – Behaglichkeitsgrenze überschritten (>25 °C)")
        elif h_aussen < h_raum:
            st.success("✅ LÜFTEN sinnvoll – Außenluft-Enthalpie niedriger")
        else:
            st.warning("❌ NICHT LÜFTEN – Außenluft-Enthalpie höher")
        # Raumkomfortstatus
        if phi_raum < 40:
            st.info("Raumluft zu trocken (<40 %)")
        elif phi_raum > 60:
            st.info("Raumluft zu feucht (>60 %)")
        else:
            st.info("Raumluft im Behaglichkeitsbereich (40–60 %)")

    # hx-Diagramm
    st.subheader("Interaktives h,x-Diagramm")
    t_range = np.linspace(-10, 50, 100)
    x_sat = [x_aus_phi_t(100, t) for t in t_range]
    phi_lines = [20, 40, 60, 80]
    phi_data = {phi: [x_aus_phi_t(phi, t) for t in t_range] for phi in phi_lines}

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_sat, y=t_range, mode='lines', name='φ=100 %', line=dict(color='black', width=2)))
    colors = ['lightblue', 'lightgreen', 'orange', 'red']
    for idx, phi in enumerate(phi_lines):
        fig.add_trace(go.Scatter(x=phi_data[phi], y=t_range, mode='lines',
                                 name=f'φ={phi} %', line=dict(color=colors[idx], width=1, dash='dash')))

    fig.add_trace(go.Scatter(x=[x_raum, x_aussen, x_misch],
                             y=[t_raum, t_aussen, t_misch],
                             mode='markers+text',
                             name='Zustandspunkte',
                             text=['Raum', 'Außen', 'Misch'],
                             textposition='top center',
                             marker=dict(size=10, color='red')))

    fig.update_layout(title="Mollier h,x-Diagramm", xaxis_title="Wassergehalt x [g/kg]",
                      yaxis_title="Temperatur [°C]", legend=dict(x=0.01, y=0.99))
    st.plotly_chart(fig, use_container_width=True)

# ================== TAB 3: Glossar ==================
with tab3:
    st.header("Thermodynamisches Glossar")
    glossary = [
        ("Spezifische Enthalpie (h)", "kJ/kg",
         "Gesamtenergieinhalt der feuchten Luft (sensibel + latent). Entscheidend für die h-Regel: Lüften nur wenn h_außen < h_innen."),
        ("h-Regel / Enthalpie-Regel", "",
         "Merkregel: Fühlt sich die Luft draußen wärmer an als drinnen? Dann nicht lüften! Technisch: Nur wenn h_außen < h_innen ist, wird Kühlenergie gespart. Obergrenze: 25 °C."),
        ("Sensible Wärme", "Wh/kW",
         "Die fühlbare Wärme, die an Temperaturänderung gekoppelt ist. Luft: 0,34 Wh/(m³·K) – geringe Speicherfähigkeit."),
        ("Latente Wärme", "Wh/kW",
         "Die im Wasserdampf gebundene Energie (Verdampfungsenthalpie). Hohe Feuchte = viel latente Wärme, blockiert körpereigene Kühlung."),
        ("Absoluter Wassergehalt (x)", "g/kg_tr",
         "Gramm Wasser pro Kilogramm trockener Luft. Der einzige echte Indikator für Entfeuchtung."),
        ("Relative Luftfeuchtigkeit (φ)", "%",
         "Verhältnis aktueller Dampfdruck zu Sättigungsdruck. Behaglichkeit: 40–60 %."),
        ("Partialdruck des Wasserdampfs (pD)", "Pa",
         "Teildruck des Wasserdampfs im Gemisch. Bestimmt Diffusionsrichtung."),
    ]
    for name, unit, desc in glossary:
        st.subheader(name)
        if unit:
            st.caption(f"Einheit: {unit}")
        st.write(desc)

# ================== TAB 4: Herleitung der Konstanten ==================
with tab4:
    st.header("Woher kommen 0,34 und 1,16?")
    st.subheader("Konstante für Luft: 0,34 Wh/(m³·K)")
    st.latex(r"\rho_{\text{Luft}} = 1{,}2\ \text{kg/m}^3")
    st.latex(r"c_{p,\text{Luft}} \approx 1{,}0\ \text{kJ/(kg·K)}")
    st.latex(r"\rho \cdot c_p = 1{,}2 \times 1{,}0 = 1{,}2\ \text{kJ/(m}^3\text{·K)}")
    st.latex(r"\text{Umrechnung: } 1\ \text{Wh} = 3{,}6\ \text{kJ}")
    st.latex(r"\frac{1{,}2\ \text{kJ/(m}^3\text{·K)}}{3{,}6\ \text{kJ/Wh}} \approx 0{,}34\ \text{Wh/(m}^3\text{·K)}")
    
    st.subheader("Konstante für Wasser: 1,163 kWh/(m³·K)")
    st.latex(r"\rho_{\text{Wasser}} = 1000\ \text{kg/m}^3")
    st.latex(r"c_{p,\text{Wasser}} = 4{,}183\ \text{kJ/(kg·K)}")
    st.latex(r"\rho \cdot c_p = 1000 \times 4{,}183 = 4183\ \text{kJ/(m}^3\text{·K)}")
    st.latex(r"\text{Umrechnung: } 1\ \text{kWh} = 3600\ \text{kJ}")
    st.latex(r"\frac{4183\ \text{kJ/(m}^3\text{·K)}}{3600\ \text{kJ/kWh}} \approx 1{,}16\ \text{kWh/(m}^3\text{·K)}")
