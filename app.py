# ================== TAB 9: Überströmflächen ==================
with tab9:
    st.header("Überströmflächen-Berechnung nach DIN 1946‑6")
    st.markdown("**Physikalische Grundlage:** Vereinfachte Bernoulli‑Gleichung für eine Blende")
    st.latex(r"\dot{V} = \alpha \cdot A \cdot \sqrt{\frac{2 \cdot \Delta p}{\rho}}")
    st.latex(r"A = \frac{\dot{V}}{\alpha \cdot \sqrt{\frac{2 \cdot \Delta p}{\rho}}}")
    
    col1, col2 = st.columns(2)
    with col1:
        V_ue = st.number_input("Volumenstrom [m³/h]", value=100, key="ue_v")
    with col2:
        rho = 1.2  # kg/m³
        st.write("Luftdichte ρ = 1,2 kg/m³")
    
    st.subheader("Zulässige Druckdifferenz Δp (wichtiger Auslegungswert!)")
    dp_wahl = st.radio(
        "Wählen Sie die passende Druckdifferenz:",
        ("2 Pa – Standard (DIN 1946‑6, freie Lüftung Wohnungsbau)",
         "4 Pa – erhöhte Anforderung (z. B. Abluftanlagen)"),
        index=0
    )
    dp = 2.0 if "2 Pa" in dp_wahl else 4.0
    st.caption(f"Verwendetes Δp = **{dp} Pa**")
    
    st.markdown("**Durchflusskennzahlen α**")
    alpha_tuer = 0.60  # scharfkantiger Spalt
    alpha_gitter = 0.72  # abgerundetes Gitter
    st.write(f"Türspalt (scharfkantig): α = {alpha_tuer}")
    st.write(f"Überströmungsgitter: α = {alpha_gitter} (günstiger, daher weniger Fläche nötig)")
    
    # Berechnung
    A_tuer = (V_ue/3600) / (alpha_tuer * np.sqrt(2*dp/rho))
    A_gitter = (V_ue/3600) / (alpha_gitter * np.sqrt(2*dp/rho))
    
    st.subheader("Ergebnisse")
    colA, colB = st.columns(2)
    with colA:
        st.metric("Freie Fläche Türspalt", f"{A_tuer*10000:.1f} cm²")
    with colB:
        st.metric("Freie Fläche Ü‑Gitter", f"{A_gitter*10000:.1f} cm²",
                  delta=f"{-100*(A_tuer-A_gitter)/A_tuer:.0f}% weniger")
    
    st.subheader("Türspalthöhe bei typischen Türbreiten")
    breiten_cm = [56.1, 68.6, 81.1, 93.6]
    labels = ["625 mm (schmal)", "750 mm", "875 mm", "1000 mm (breit)"]
    for label, breite in zip(labels, breiten_cm):
        spalthoehe = A_tuer * 10000 / breite
        st.write(f"**{label}**: {spalthoehe:.2f} cm Spalthöhe erforderlich")
    st.caption("Bei zu großem Spalt → Ü‑Gitter einbauen oder größeren α‑Wert nutzen.")
    
    st.subheader("Überströmungsgitter dimensionieren")
    gitter_b = st.number_input("Gitterbreite [mm]", value=400, key="gitter_b2")
    gitter_h = st.number_input("Gitterhöhe [mm]", value=150, key="gitter_h2")
    geom_flaeche = gitter_b * gitter_h / 100  # cm²
    freier_q = st.number_input("Freier Querschnitt des Gitters (Herstellerangabe)", value=0.65)
    eff_flaeche = geom_flaeche * freier_q
    if eff_flaeche >= A_gitter * 10000:
        st.success(f"Eff. Fläche {eff_flaeche:.1f} cm² ≥ {A_gitter*10000:.1f} cm² – ausreichend")
    else:
        st.error(f"Eff. Fläche {eff_flaeche:.1f} cm² < {A_gitter*10000:.1f} cm² – **Gitter zu klein!**")
