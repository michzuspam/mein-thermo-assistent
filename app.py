# Erweiterung der streamlit_app.py – neue Tabs am Ende einfügen

# ... (vorherige Importe und Tabs 1-4 aus der letzten Antwort)

# Neue Tabs ab hier
tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
    "📋 Luftmengen DIN EN 16798",
    "💨 Druckverlustrechner",
    "📏 Kanal-Dimensionierung",
    "🌬️ Wetterschutzgitter",
    "🚪 Überströmflächen",
    "🔊 Akustik"
])

with tab5:
    st.header("Außenluftraten nach DIN EN 16798-3")
    col1, col2 = st.columns(2)
    with col1:
        laenge = st.number_input("Raumlänge [m]", value=10.0)
        breite = st.number_input("Raumbreite [m]", value=6.0)
    with col2:
        personen = st.number_input("Personenanzahl", value=12)
    flaeche = laenge * breite
    st.write(f"Raumfläche: {flaeche:.1f} m²")
    
    # IDA-Kategorien
    ida = {
        "IDA 1 (Hohe Luftqualität)": (36, 7.2),
        "IDA 2 (Mittlere Luftqualität)": (25, 5.4),
        "IDA 3 (Mäßige Luftqualität)": (25, 2.5),
        "IDA 4 (Niedrige Luftqualität)": (14, 1.1)
    }
    ergebnisse = {}
    for kat, (qp, qb) in ida.items():
        v_aussen = (personen * qp) + (flaeche * qb)
        ergebnisse[kat] = v_aussen
        st.write(f"{kat}: {v_aussen:.1f} m³/h")
    # Dynamische Verwendung: Wert für IDA 3 wird später genutzt
    st.session_state.ida3_volumen = ergebnisse["IDA 3 (Mäßige Luftqualität)"]

with tab6:
    st.header("Strang-Druckverlustrechner")
    # Eingabefelder für die Mengen der Komponenten
    st.subheader("Komponenten (Menge eintragen)")
    col1, col2 = st.columns(2)
    mengen = {}
    with col1:
        mengen['kanal_meter'] = st.number_input("Kanalstrecke [m]", value=15)
        mengen['bsk'] = st.number_input("Brandschutzklappen", value=1)
        mengen['vav'] = st.number_input("Volumenstromregler", value=1)
        mengen['konstantregler'] = st.number_input("Konstantvolumenstromregler", value=0)
        mengen['kulissend'] = st.number_input("Kulissenschalldämpfer", value=1)
    with col2:
        mengen['rohrsd'] = st.number_input("Rohrschalldämpfer", value=0)
        mengen['telefonsd'] = st.number_input("Telefonieschalldämpfer", value=2)
        mengen['bogen90'] = st.number_input("90°-Bogen", value=4)
        mengen['uebergang'] = st.number_input("Übergänge/Reduzierungen", value=2)
        mengen['t_durchgang'] = st.number_input("T-Stück Durchgang", value=1)
        mengen['t_abgang'] = st.number_input("T-Stück Abgang", value=1)
    # Richtwerte
    dp_werte = {
        'kanal_meter': 0.85, 'bsk': 10, 'vav': 25, 'konstantregler': 40,
        'kulissend': 17.5, 'rohrsd': 8.5, 'telefonsd': 10, 'bogen90': 5,
        'uebergang': 3.5, 't_durchgang': 6, 't_abgang': 11.5
    }
    # Zusätzliche Komponenten
    with st.expander("Weitere Komponenten"):
        mengen['nacherhitzer'] = st.number_input("Nacherhitzer", value=0)
        mengen['drallauslass'] = st.number_input("Drallauslass", value=2)
        mengen['weitwurfd'] = st.number_input("Weitwurfdüse", value=0)
        mengen['kanalgitter'] = st.number_input("Kanalgitter", value=0)
        mengen['gitter_schieber'] = st.number_input("Gitter mit Schieber", value=0)
        mengen['tellerventil_zu'] = st.number_input("Tellerventil Zuluft", value=0)
        mengen['tellerventil_ab'] = st.number_input("Tellerventil Abluft", value=0)
        mengen['drosselklappe'] = st.number_input("Drosselklappe", value=2)
        dp_werte.update({
            'nacherhitzer': 20, 'drallauslass': 37.5, 'weitwurfd': 45,
            'kanalgitter': 17.5, 'gitter_schieber': 25,
            'tellerventil_zu': 25, 'tellerventil_ab': 17.5, 'drosselklappe': 12.5
        })
    # Berechnung
    dp_sum = sum(mengen[k] * dp_werte[k] for k in mengen if k in dp_werte)
    sicherheit = dp_sum * 0.15
    st.metric("Netto-Druckverlust", f"{dp_sum:.1f} Pa")
    st.metric("+15% Sicherheitszuschlag", f"{sicherheit:.1f} Pa")
    st.metric("Empfohlener Mindest-Anlagendruck", f"{dp_sum + sicherheit:.1f} Pa")

with tab7:
    st.header("Kanal-Dimensionierung (Kontinuitätsgleichung)")
    # Volumenstrom aus IDA3 übernehmen
    if 'ida3_volumen' in st.session_state:
        V = st.number_input("Volumenstrom [m³/h]", value=st.session_state.ida3_volumen)
    else:
        V = st.number_input("Volumenstrom [m³/h]", value=450.0)
    v = st.number_input("Ziel-Geschwindigkeit [m/s]", value=5.0)
    A = (V/3600) / v
    st.write(f"Erforderliche Kanalfläche: {A:.4f} m²")
    # Formen
    st.subheader("Quadratischer Kanal")
    seite = (A**0.5) * 1000
    st.write(f"Höhe = Breite = {seite:.0f} mm, Geschwindigkeit = {V/((seite/1000)**2 * 3600):.2f} m/s")
    st.subheader("Rechteckkanal 1:3")
    h_13 = (A/3)**0.5 * 1000
    b_13 = h_13 * 3
    st.write(f"Höhe = {h_13:.0f} mm, Breite = {b_13:.0f} mm, Geschwindigkeit = {V/((h_13/1000)*(b_13/1000)*3600):.2f} m/s")
    st.subheader("Individuelle Höhe (mm)")
    h_ind = st.number_input("Höhe [mm]", value=200)
    if h_ind > 0:
        b_ind = (A / (h_ind/1000)) * 1000
        st.write(f"Resultierende Breite = {b_ind:.0f} mm, Geschwindigkeit = {V/((h_ind/1000)*(b_ind/1000)*3600):.2f} m/s")
    st.subheader("Rundkanal")
    durchmesser = ((4*A)/3.1416)**0.5 * 1000
    st.write(f"Durchmesser = {durchmesser:.0f} mm, Geschwindigkeit = {V/(3.1416*(durchmesser/1000)**2/4 * 3600):.2f} m/s")

with tab8:
    st.header("Wetterschutzgitter (WSG) Auslegung")
    if 'ida3_volumen' in st.session_state:
        V_wsg = st.number_input("Volumenstrom [m³/h]", value=st.session_state.ida3_volumen)
    else:
        V_wsg = st.number_input("Volumenstrom [m³/h]", value=450.0)
    eps = st.number_input("Freier Querschnitt ε", value=0.6)
    v_max = 2.5
    # Autobreite für v=2.3
    hoehe = st.number_input("Höhe [mm]", value=500)
    if hoehe > 0:
        breite = (((V_wsg/3600) / 2.3) / eps) / (hoehe/1000) * 1000
        st.write(f"Für v=2.3 m/s: Breite = {breite:.0f} mm")
    # Manuell
    man_hoehe = st.number_input("Manuelle Höhe [mm]", value=500, key="man_h")
    man_breite = st.number_input("Manuelle Breite [mm]", value=1000, key="man_b")
    A_frei = (man_hoehe/1000) * (man_breite/1000) * eps
    v_eff = (V_wsg/3600) / A_frei if A_frei > 0 else float('inf')
    if v_eff > v_max:
        st.error(f"v_eff = {v_eff:.2f} m/s – KRITISCH! Regeneintriebsgefahr!")
    else:
        st.success(f"v_eff = {v_eff:.2f} m/s – OK.")

with tab9:
    st.header("Überströmflächen-Berechnung")
    V_ue = st.number_input("Volumenstrom [m³/h]", value=100)
    dp = st.number_input("Druckdifferenz [Pa]", value=2)
    alpha_tuer = 0.6
    alpha_gitter = 0.72
    rho = 1.2
    A_tuer = (V_ue/3600) / (alpha_tuer * (2*dp/rho)**0.5)
    A_gitter = (V_ue/3600) / (alpha_gitter * (2*dp/rho)**0.5)
    st.write(f"Erforderliche freie Fläche Türspalt: {A_tuer*10000:.1f} cm²")
    st.write(f"Erforderliche freie Fläche Ü-Gitter: {A_gitter*10000:.1f} cm² (≈ {100*(A_tuer-A_gitter)/A_tuer:.0f}% weniger)")

    st.subheader("Türspalthöhe bei Standard-Türbreiten")
    breiten_cm = [56.1, 68.6, 81.1, 93.6]  # Effektive Lichtebreiten
    labels = ["625mm (schmal)", "750mm", "875mm", "1000mm (breit)"]
    for label, breite in zip(labels, breiten_cm):
        spalthoehe = A_tuer * 10000 / breite
        st.write(f"{label}: {spalthoehe:.2f} cm Spalthöhe")
    
    st.subheader("Überströmungsgitter prüfen")
    gitter_breite = st.number_input("Gitterbreite [mm]", value=400)
    gitter_hoehe = st.number_input("Gitterhöhe [mm]", value=150)
    geom_flaeche = gitter_breite * gitter_hoehe / 100  # cm²
    freier_q = 0.65
    eff_flaeche = geom_flaeche * freier_q
    if eff_flaeche >= A_gitter * 10000:
        st.success(f"Eff. Fläche {eff_flaeche:.1f} cm² ≥ {A_gitter*10000:.1f} cm² – OK")
    else:
        st.error(f"Eff. Fläche {eff_flaeche:.1f} cm² < {A_gitter*10000:.1f} cm² – zu klein")

with tab10:
    st.header("Akustischer Abstandsrechner")
    L_wA = st.number_input("Schallleistungspegel Gitter [dB(A)]", value=56)
    r = st.number_input("Abstand [m]", value=15)
    L_p = L_wA - 20 * np.log10(r) - 8
    st.write(f"Schalldruckpegel beim Nachbarn: {L_p:.1f} dB(A)")
