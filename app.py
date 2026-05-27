import streamlit as st
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="Thermodynamik-Rechner", layout="wide")
st.title("Thermodynamischer Leistungsrechner & Lüftungsplaner")

# ---------- Alle Tabs ----------
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
    "🔧 Leistungsberechnung",
    "🌡️ Lüftung & hx-Diagramm",
    "📚 Glossar",
    "📐 Herleitung Konstanten",
    "📋 Luftmengen DIN EN 16798",
    "💨 Druckverlustrechner",
    "📏 Kanal-Dimensionierung",
    "🌬️ Wetterschutzgitter",
    "🚪 Überströmflächen",
    "🔊 Akustik"
])

# ================== TAB 1: Leistungsberechnung ==================
with tab1:
    st.header("Heizlast- und Leistungsberechnungen")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Luft")
        V_luft = st.number_input("Volumenstrom Luft [m³/h]", value=150.0)
        deltaT_luft = st.number_input("Temperaturdifferenz Luft [K]", value=25.0)
        Q_luft = V_luft * deltaT_luft * 0.34
        st.metric("Heizleistung Luft", f"{Q_luft:.0f} W")
        st.latex(r"\dot{Q}_{Luft} = \dot{V} \cdot \Delta T \cdot 0{,}34")
        st.caption(f"= {V_luft} · {deltaT_luft} · 0,34 = {Q_luft:.0f} W")
    with col2:
        st.subheader("Wasser")
        V_wasser = st.number_input("Volumenstrom Wasser [m³/h]", value=2.5)
        deltaT_wasser = st.number_input("Spreizung Wasser [K]", value=10.0)
        Q_wasser = V_wasser * deltaT_wasser * 1.163
        st.metric("Übertragene Leistung Wasser", f"{Q_wasser:.2f} kW")
        st.latex(r"\dot{Q}_{Wasser} = \dot{V} \cdot \Delta T \cdot 1{,}163")
        st.caption(f"= {V_wasser} · {deltaT_wasser} · 1,163 = {Q_wasser:.2f} kW")
    st.subheader("Lufterhitzer-Kopplung")
    col3, col4 = st.columns(2)
    with col3:
        V_luft_heiz = st.number_input("Gewünschte Luftmenge Lufterhitzer [m³/h]", value=1500.0)
    with col4:
        deltaT_luft_heiz = st.number_input("Temperaturhub Luft [K]", value=22.0)
    deltaT_ww = st.number_input("Spreizung Heizwasser [K]", value=20.0)
    Q_heiz = V_luft_heiz * deltaT_luft_heiz * 0.34 / 1000
    m_wasser = (Q_heiz / 1.163 / deltaT_ww) * 1000
    st.write(f"**Erforderliche Heizleistung:** {Q_heiz:.1f} kW")
    st.latex(r"\dot{Q} = \frac{\dot{V}_{Luft} \cdot \Delta T_{Luft} \cdot 0{,}34}{1000}")
    st.write(f"**Bevorzugter Wassermassenstrom:** {m_wasser:.1f} kg/h")
    st.latex(r"\dot{m}_{Wasser} = \frac{\dot{Q}}{c_p \cdot \Delta T_{Wasser}} \cdot 1000")

# ================== TAB 2: Lüftung & hx-Diagramm ==================
with tab2:
    st.header("Zustandsberechnung und Lüftungsempfehlung")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Raumluft")
        t_raum = st.number_input("Temperatur Raum [°C]", value=23.5, key="t_raum")
        phi_raum = st.slider("Relative Feuchte Raum [%]", 0, 100, 55, key="phi_raum")
        v_raum = st.number_input("Volumenstrom Raum [m³/h]", value=100.0, key="v_raum")
    with col2:
        st.subheader("Außenluft")
        t_aussen = st.number_input("Temperatur Außen [°C]", value=16.0, key="t_aussen")
        phi_aussen = st.slider("Relative Feuchte Außen [%]", 0, 100, 85, key="phi_aussen")
        v_aussen = st.number_input("Volumenstrom Außen [m³/h]", value=100.0, key="v_aussen")

    def magnus_psat(t):
        return 610.78 * np.exp((17.08085 * t) / (234.175 + t))
    def x_aus_phi_t(phi, t):
        psat = magnus_psat(t)
        pd = phi / 100 * psat
        return 622 * pd / (101325 - pd)
    def enthalpie(t, x):
        return 1.005 * t + x / 1000 * (2501 + 1.86 * t)

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
        if phi_raum < 40:
            st.info("Raumluft zu trocken (<40 %)")
        elif phi_raum > 60:
            st.info("Raumluft zu feucht (>60 %)")
        else:
            st.info("Raumluft im Behaglichkeitsbereich (40–60 %)")

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
        ("Spezifische Enthalpie (h)", "kJ/kg", "Gesamtenergieinhalt der feuchten Luft (sensibel + latent)."),
        ("h-Regel", "", "Fühlt sich die Luft draußen wärmer an? Dann nicht lüften. Technisch: h_außen < h_innen → Lüften sinnvoll."),
        ("Sensible Wärme", "Wh/kW", "Fühlbare Wärme – Luft: 0,34 Wh/(m³·K)."),
        ("Latente Wärme", "Wh/kW", "Im Wasserdampf gebundene Energie."),
        ("Absoluter Wassergehalt (x)", "g/kg_tr", "Gramm Wasser pro kg trockener Luft."),
        ("Relative Luftfeuchtigkeit (φ)", "%", "Behaglichkeit: 40–60 %."),
    ]
    for name, unit, desc in glossary:
        st.subheader(name)
        if unit:
            st.caption(f"Einheit: {unit}")
        st.write(desc)

# ================== TAB 4: Herleitung ==================
with tab4:
    st.header("Herleitung der Konstanten 0,34 und 1,16")
    st.subheader("Luft: 0,34 Wh/(m³·K)")
    st.latex(r"\rho_{\text{Luft}} \cdot c_p = 1,2\,\text{kg/m}^3 \times 1,0\,\text{kJ/(kg·K)} = 1,2\,\text{kJ/(m}^3\text{·K)}")
    st.latex(r"\frac{1,2\,\text{kJ/(m}^3\text{·K)}}{3,6\,\text{kJ/Wh}} \approx 0,34\,\text{Wh/(m}^3\text{·K)}")
    st.subheader("Wasser: 1,163 kWh/(m³·K)")
    st.latex(r"\rho_{\text{Wasser}} \cdot c_p = 1000\,\text{kg/m}^3 \times 4,18\,\text{kJ/(kg·K)} = 4180\,\text{kJ/(m}^3\text{·K)}")
    st.latex(r"\frac{4180\,\text{kJ/(m}^3\text{·K)}}{3600\,\text{kJ/kWh}} \approx 1,16\,\text{kWh/(m}^3\text{·K)}")

# ================== TAB 5: Luftmengen DIN EN 16798 ==================
with tab5:
    st.header("Außenluftraten nach DIN EN 16798-3")
    st.markdown("**Formel (Kombinationsverfahren):**")
    st.latex(r"V_{ges} = (n \cdot q_p) + (A \cdot q_B)")
    st.caption("n = Personenanzahl, q_p = Volumenstrom pro Person, A = Raumfläche, q_B = flächenbezogener Volumenstrom")

    col1, col2 = st.columns(2)
    with col1:
        laenge = st.number_input("Raumlänge [m]", value=10.0)
        breite = st.number_input("Raumbreite [m]", value=6.0)
    with col2:
        personen = st.number_input("Personenanzahl", value=12)
    flaeche = laenge * breite
    st.write(f"Raumfläche: {flaeche:.1f} m²")

    # Tabelle mit den IDA-Kategorien und den spezifischen Werten
    st.subheader("IDA-Kategorien und spezifische Volumenströme")
    ida_data = [
        ("IDA 1", "Hohe Raumluftqualität", 36, 7.2),
        ("IDA 2", "Mittlere Raumluftqualität", 25, 5.4),
        ("IDA 3", "Mäßige Raumluftqualität", 25, 2.5),
        ("IDA 4", "Niedrige Raumluftqualität", 14, 1.1)
    ]
    # Tabelle als Markdown
    st.markdown("| Kategorie | Beschreibung | qp (m³/h/Person) | qB (m³/(h·m²)) |")
    st.markdown("|-----------|--------------|-------------------|----------------|")
    for kat, desc, qp, qb in ida_data:
        st.markdown(f"| {kat} | {desc} | {qp} | {qb} |")

    # Ergebnisse für jede Kategorie dynamisch berechnen
    st.subheader("Berechneter Außenluftbedarf für Ihre Eingabe")
    ergebnisse = {}
    for kat, desc, qp, qb in ida_data:
        V_aussen = (personen * qp) + (flaeche * qb)
        ergebnisse[kat] = V_aussen
        st.write(f"**{kat} ({desc}):** {V_aussen:.1f} m³/h  (Rechnung: {personen}·{qp} + {flaeche:.1f}·{qb})")

    # Standardwert für andere Tabs (IDA 3)
    st.session_state.ida3_volumen = ergebnisse["IDA 3"]

# ================== TAB 6: Druckverlustrechner ==================
with tab6:
    st.header("Strang-Druckverlustrechner")
    st.caption("Richtwerte für übliche Komponenten bei ca. 5 m/s im Hauptkanal.")
    col1, col2 = st.columns(2)
    mengen = {}
    with col1:
        mengen['kanal_meter'] = st.number_input("Kanalstrecke [m]", value=15, key="k1")
        mengen['bsk'] = st.number_input("Brandschutzklappen", value=1, key="k2")
        mengen['vav'] = st.number_input("Volumenstromregler", value=1, key="k3")
        mengen['konstantregler'] = st.number_input("Konstantvolumenstromregler", value=0, key="k4")
        mengen['kulissend'] = st.number_input("Kulissenschalldämpfer", value=1, key="k5")
    with col2:
        mengen['rohrsd'] = st.number_input("Rohrschalldämpfer", value=0, key="k6")
        mengen['telefonsd'] = st.number_input("Telefonieschalldämpfer", value=2, key="k7")
        mengen['bogen90'] = st.number_input("90°-Bogen", value=4, key="k8")
        mengen['uebergang'] = st.number_input("Übergänge/Reduzierungen", value=2, key="k9")
        mengen['t_durchgang'] = st.number_input("T-Stück Durchgang", value=1, key="k10")
        mengen['t_abgang'] = st.number_input("T-Stück Abgang", value=1, key="k11")
    dp_werte = {
        'kanal_meter': 0.85, 'bsk': 10, 'vav': 25, 'konstantregler': 40,
        'kulissend': 17.5, 'rohrsd': 8.5, 'telefonsd': 10, 'bogen90': 5,
        'uebergang': 3.5, 't_durchgang': 6, 't_abgang': 11.5
    }
    with st.expander("Weitere Komponenten"):
        mengen['nacherhitzer'] = st.number_input("Nacherhitzer", value=0, key="k12")
        mengen['drallauslass'] = st.number_input("Drallauslass", value=2, key="k13")
        mengen['weitwurfd'] = st.number_input("Weitwurfdüse", value=0, key="k14")
        mengen['kanalgitter'] = st.number_input("Kanalgitter", value=0, key="k15")
        mengen['gitter_schieber'] = st.number_input("Gitter mit Schieber", value=0, key="k16")
        mengen['tellerventil_zu'] = st.number_input("Tellerventil Zuluft", value=0, key="k17")
        mengen['tellerventil_ab'] = st.number_input("Tellerventil Abluft", value=0, key="k18")
        mengen['drosselklappe'] = st.number_input("Drosselklappe", value=2, key="k19")
        dp_werte.update({
            'nacherhitzer': 20, 'drallauslass': 37.5, 'weitwurfd': 45,
            'kanalgitter': 17.5, 'gitter_schieber': 25,
            'tellerventil_zu': 25, 'tellerventil_ab': 17.5, 'drosselklappe': 12.5
        })
    dp_sum = sum(mengen[k] * dp_werte[k] for k in mengen if k in dp_werte)
    sicherheit = dp_sum * 0.15
    st.metric("Netto-Druckverlust", f"{dp_sum:.1f} Pa")
    st.metric("+15% Sicherheitszuschlag", f"{sicherheit:.1f} Pa")
    st.metric("Empfohlener Mindest-Anlagendruck", f"{dp_sum + sicherheit:.1f} Pa")

# ================== TAB 7: Kanal-Dimensionierung ==================
with tab7:
    st.header("Kanal-Dimensionierung (Kontinuitätsgleichung)")
    st.markdown("**Formel:**")
    st.latex(r"V = v \cdot A \cdot 3600 \quad \Rightarrow \quad A = \frac{V}{v \cdot 3600}")
    st.caption("V in m³/h, v in m/s, A in m²")

    if 'ida3_volumen' in st.session_state:
        V_kan = st.number_input("Volumenstrom [m³/h]", value=st.session_state.ida3_volumen)
    else:
        V_kan = st.number_input("Volumenstrom [m³/h]", value=450.0)
    v = st.number_input("Ziel-Geschwindigkeit [m/s]", value=5.0)
    A = (V_kan/3600) / v
    st.write(f"Erforderliche Kanalfläche: {A:.4f} m²")
    seite = (A**0.5) * 1000
    st.write(f"Quadratisch: {seite:.0f} x {seite:.0f} mm, v = {V_kan/((seite/1000)**2 * 3600):.2f} m/s")
    h_13 = (A/3)**0.5 * 1000
    b_13 = h_13 * 3
    st.write(f"1:3: {h_13:.0f} x {b_13:.0f} mm, v = {V_kan/((h_13/1000)*(b_13/1000)*3600):.2f} m/s")
    h_ind = st.number_input("Individuelle Höhe [mm]", value=200)
    if h_ind > 0:
        b_ind = (A / (h_ind/1000)) * 1000
        st.write(f"Individuell: {h_ind:.0f} x {b_ind:.0f} mm, v = {V_kan/((h_ind/1000)*(b_ind/1000)*3600):.2f} m/s")
    durchmesser = ((4*A)/np.pi)**0.5 * 1000
    st.write(f"Rund: Ø {durchmesser:.0f} mm, v = {V_kan/(np.pi*(durchmesser/1000)**2/4 * 3600):.2f} m/s")

# ================== TAB 8: Wetterschutzgitter ==================
with tab8:
    st.header("🌬️ Wetterschutzgitter (WSG) – Auslegung & Strömungsgeschwindigkeit")
    st.markdown("**Formel:** $v_{eff} = \\frac{\\dot{V}}{B \\cdot H \\cdot \\varepsilon}$")
    if 'ida3_volumen' in st.session_state:
        V_wsg = st.number_input("Volumenstrom [m³/h]", value=st.session_state.ida3_volumen, key="wsg_v")
    else:
        V_wsg = st.number_input("Volumenstrom [m³/h]", value=450.0, key="wsg_v")
    eps = st.number_input("Freier Querschnitt ε (0,5–0,7 je nach Gitter)", value=0.6)

    st.subheader("Empfohlene Maximalgeschwindigkeiten")
    v_max = st.radio(
        "Einsatzbereich:",
        ("Wohnung / geräuschsensibel → 1,5 m/s", "Gewerbe / Großanlage → 2,5 m/s"),
        index=1
    )
    v_max_wert = 1.5 if "1,5" in v_max else 2.5
    st.caption(f"Maximal zulässige Anströmgeschwindigkeit: **{v_max_wert} m/s**")
    st.markdown("""
    **Hintergrund:**
    - **2,5 m/s**: Standard für gewerbliche Anlagen – Kompromiss aus Gittergröße, Druckverlust und Regenschutz.
    - **1,5 m/s**: Für Wohnungslüftung oder schallkritische Räume – nahezu kein Eigengeräusch, maximale Sicherheit gegen Regen.
    """)

    st.subheader("Automatische Breite (Ziel 2,3 m/s)")
    hoehe = st.number_input("Höhe [mm]", value=500, key="wsg_h")
    if hoehe > 0:
        breite = (((V_wsg/3600) / 2.3) / eps) / (hoehe/1000) * 1000
        st.write(f"Für v = 2,3 m/s: **Breite ≈ {breite:.0f} mm**")

    st.subheader("Manuelle Prüfung")
    man_h = st.number_input("Manuelle Höhe [mm]", value=500, key="man_h2")
    man_b = st.number_input("Manuelle Breite [mm]", value=1000, key="man_b2")
    A_frei = (man_h/1000) * (man_b/1000) * eps
    v_eff = (V_wsg/3600) / A_frei if A_frei > 0 else float('inf')
    if v_eff <= v_max_wert:
        st.success(f"v_eff = **{v_eff:.2f} m/s** ≤ {v_max_wert} m/s – OK")
    else:
        st.error(f"v_eff = **{v_eff:.2f} m/s** > {v_max_wert} m/s – **Gefahr von Regeneintrieb / Geräuschen!**")

# ================== TAB 9: Überströmflächen ==================
with tab9:
    st.header("🚪 Überströmflächen-Berechnung (Türspalt & Gitter)")
    st.markdown("**Physikalische Grundlage:** Vereinfachte Bernoulli-Gleichung")
    st.latex(r"\dot{V} = \alpha \cdot A \cdot \sqrt{\frac{2 \Delta p}{\rho}}")
    st.latex(r"A = \frac{\dot{V}}{\alpha \cdot \sqrt{2 \Delta p / \rho}}")
    st.caption("α = Durchflussbeiwert (Türspalt ≈ 0,6; Gitter ≈ 0,72)")

    col1, col2 = st.columns(2)
    with col1:
        V_ue = st.number_input("Volumenstrom [m³/h]", value=100, key="ue_v")
    with col2:
        rho = 1.2
        st.write(f"Luftdichte ρ = {rho} kg/m³")

    st.subheader("Zulässige Druckdifferenz Δp (nach DIN 1946-6)")
    dp_wahl = st.radio(
        "Lage des Gebäudes:",
        ("Windschwach (Standard) → Δp = 2 Pa", "Windstark (exponiert) → Δp = 4 Pa"),
        index=0
    )
    dp = 2.0 if "2 Pa" in dp_wahl else 4.0
    st.caption(f"Auslegungs-Druckdifferenz: **{dp} Pa**")

    alpha_tuer = 0.60
    alpha_gitter = 0.72
    st.write(f"α Türspalt = {alpha_tuer},  α Gitter = {alpha_gitter}")

    A_tuer = (V_ue/3600) / (alpha_tuer * np.sqrt(2*dp/rho))
    A_gitter = (V_ue/3600) / (alpha_gitter * np.sqrt(2*dp/rho))

    v_tuer = (V_ue/3600) / A_tuer if A_tuer > 0 else 0
    v_gitter = (V_ue/3600) / A_gitter if A_gitter > 0 else 0

    st.subheader("Ergebnis: Benötigter freier Querschnitt")
    colA, colB = st.columns(2)
    with colA:
        st.metric("Freie Fläche Türspalt", f"{A_tuer*10000:.1f} cm²")
        st.caption(f"→ resultierende Geschwindigkeit: **{v_tuer:.2f} m/s**")
        if v_tuer <= 1.5:
            st.success("✅ ≤ 1,5 m/s – Komfortgrenze eingehalten")
        else:
            st.warning(f"⚠️ {v_tuer:.2f} m/s > 1,5 m/s – Gefahr von Pfeifgeräuschen!")
    with colB:
        st.metric("Freie Fläche Ü‑Gitter", f"{A_gitter*10000:.1f} cm²",
                  delta=f"{-100*(A_tuer-A_gitter)/A_tuer:.0f}% weniger")
        st.caption(f"→ resultierende Geschwindigkeit: **{v_gitter:.2f} m/s**")
        if v_gitter <= 1.0:
            st.success("✅ ≤ 1,0 m/s – akustisch neutral")
        else:
            st.warning(f"⚠️ {v_gitter:.2f} m/s > 1,0 m/s – kann hörbar sein!")

    st.info(
        "**Maximal empfohlene Strömungsgeschwindigkeiten:**\n"
        "- **Türspalt**: ≤ **1,5 m/s** – höhere Geschwindigkeiten können Pfeifgeräusche verursachen.\n"
        "- **Überströmgitter**: ≤ **1,0 m/s** – für einen akustisch neutralen Betrieb (ca. 1 Pa Druckabfall)."
    )

    st.subheader("🔧 Überströmungsgitter dimensionieren")
    dim_modus = st.radio("Vorgabe wählen:", ("Breite vorgeben", "Höhe vorgeben"), index=0)
    eps_gitter = st.number_input("Freier Querschnitt des Gitters (Hersteller)", value=0.65, key="eps_gitter_dim")
    A_req_cm2 = A_gitter * 10000

    if dim_modus == "Breite vorgeben":
        b_vor = st.number_input("Gewünschte Breite [mm]", value=400, step=10, key="b_vor")
        if b_vor > 0 and eps_gitter > 0:
            geom_flaeche_cm2 = A_req_cm2 / eps_gitter
            hoehe_cm = geom_flaeche_cm2 / (b_vor/10)
            hoehe_mm = hoehe_cm * 10
            st.write(f"**Ergebnis:** Breite = {b_vor} mm → benötigte Höhe = **{hoehe_mm:.0f} mm**")
            st.caption(f"Geometrische Fläche = {geom_flaeche_cm2:.1f} cm² (davon {eps_gitter*100:.0f}% frei = {A_req_cm2:.1f} cm²)")
    else:
        h_vor = st.number_input("Gewünschte Höhe [mm]", value=150, step=10, key="h_vor")
        if h_vor > 0 and eps_gitter > 0:
            geom_flaeche_cm2 = A_req_cm2 / eps_gitter
            breite_cm = geom_flaeche_cm2 / (h_vor/10)
            breite_mm = breite_cm * 10
            st.write(f"**Ergebnis:** Höhe = {h_vor} mm → benötigte Breite = **{breite_mm:.0f} mm**")
            st.caption(f"Geometrische Fläche = {geom_flaeche_cm2:.1f} cm² (davon {eps_gitter*100:.0f}% frei = {A_req_cm2:.1f} cm²)")

    st.subheader("Türspalthöhe bei typischen Türbreiten")
    breiten_cm = [56.1, 68.6, 81.1, 93.6]
    labels = ["625 mm (schmal)", "750 mm", "875 mm", "1000 mm (breit)"]
    for label, breite in zip(labels, breiten_cm):
        spalthoehe = A_tuer * 10000 / breite
        st.write(f"**{label}**: {spalthoehe:.2f} cm Spalthöhe erforderlich")

# ================== TAB 10: Akustik ==================
with tab10:
    st.header("Akustischer Abstandsrechner für Außenluftgitter")
    st.markdown("**Formel (halbe Kugelabstrahlung):**")
    st.latex(r"L_p = L_{wA} - 20 \cdot \log_{10}(r) - 8")
    st.caption("L_p = Schalldruckpegel am Immissionsort [dB(A)], L_wA = Schallleistungspegel [dB(A)], r = Abstand [m]")

    L_wA = st.number_input("Schallleistungspegel Gitter [dB(A)]", value=56)
    r = st.number_input("Abstand zum nächsten Nachbarn [m]", value=15)
    L_p = L_wA - 20 * np.log10(r) - 8
    st.write(f"Schalldruckpegel beim Nachbarn: **{L_p:.1f} dB(A)**")
    st.caption("Vereinfachte Näherung für Freifeldbedingungen (Q=2).")
