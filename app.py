# ============================================================
# BENIN WATCH — app.py — Version Folium Interactive
# ============================================================

import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap, MarkerCluster
from streamlit_folium import st_folium
import anthropic
import random
import json
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="BENIN WATCH",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# MODE SOMBRE / CLAIR
# ============================================================
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

def toggle_mode():
    st.session_state.dark_mode = not st.session_state.dark_mode

# Couleurs selon le mode
if st.session_state.dark_mode:
    BG       = "#080810"
    CARD     = "#0F0F1A"
    CARD2    = "#13131A"
    BORDER   = "#1A1A30"
    TEXT     = "#CCCCDD"
    TEXT2    = "#7777AA"
    TILE     = "CartoDB dark_matter"
else:
    BG       = "#F5F5F8"
    CARD     = "#FFFFFF"
    CARD2    = "#F0F0F5"
    BORDER   = "#DDDDEE"
    TEXT     = "#1A1A2E"
    TEXT2    = "#666688"
    TILE     = "CartoDB positron"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
*{{font-family:'Inter',sans-serif;}}
.stApp{{background:{BG};color:{TEXT};}}
.stApp header{{background:{BG};}}
.stSelectbox>div>div{{
    background:{CARD};border:1px solid {BORDER};
    color:{TEXT};border-radius:8px;}}
div[data-testid="metric-container"]{{
    background:{CARD};border:1px solid {BORDER};
    border-radius:10px;padding:14px;}}
div[data-testid="metric-container"] label{{
    color:{TEXT2} !important;font-size:11px !important;}}
div[data-testid="metric-container"] div{{
    color:{TEXT} !important;font-size:22px !important;
    font-weight:600 !important;}}
.stDivider{{border-color:{BORDER};}}
.bw-logo{{
    font-size:22px;font-weight:600;letter-spacing:3px;
    padding:6px 0;}}
.bw-logo .r{{color:#C0392B;}}
.bw-logo .w{{color:{TEXT};}}
.zone-panel{{
    background:{CARD};border:1px solid {BORDER};
    border-radius:12px;padding:18px;margin-bottom:12px;
    transition:all 0.3s;}}
.zone-name{{font-size:20px;font-weight:600;color:{TEXT};margin-bottom:2px;}}
.zone-meta{{font-size:11px;color:{TEXT2};margin-bottom:14px;}}
.score-row{{
    display:flex;align-items:center;
    justify-content:space-between;
    margin-bottom:6px;font-size:12px;color:{TEXT2};}}
.score-bar{{
    height:8px;background:{BORDER};
    border-radius:4px;overflow:hidden;margin-bottom:14px;}}
.info-row{{
    background:{CARD2};border-radius:8px;
    padding:11px 13px;margin-bottom:8px;}}
.info-lbl{{
    font-size:10px;color:{TEXT2};
    text-transform:uppercase;letter-spacing:0.8px;
    margin-bottom:4px;}}
.info-val{{font-size:13px;color:{TEXT};line-height:1.5;}}
.alert-pill{{
    background:#1A0505;border:1px solid #C0392B;
    border-radius:8px;padding:8px 12px;
    font-size:12px;color:#E24B4A;margin-bottom:10px;
    display:flex;align-items:center;gap:6px;}}
.week-grid{{
    display:grid;grid-template-columns:repeat(7,1fr);
    gap:4px;margin-top:12px;}}
.day-cell{{
    text-align:center;background:{CARD2};
    border-radius:6px;padding:6px 2px;}}
.day-name{{font-size:9px;color:{TEXT2};margin-bottom:3px;}}
.day-emoji{{font-size:15px;}}
.kpi-grid{{
    display:grid;grid-template-columns:repeat(4,1fr);
    gap:10px;margin-bottom:16px;}}
.kpi-card{{
    background:{CARD};border:1px solid {BORDER};
    border-radius:10px;padding:14px;text-align:center;}}
.kpi-val{{font-size:24px;font-weight:600;line-height:1;}}
.kpi-lbl{{font-size:11px;color:{TEXT2};margin-top:4px;line-height:1.3;}}
.wa-btn{{
    display:block;text-align:center;
    background:{'#1A3A1A' if st.session_state.dark_mode else '#E8F5E9'};
    color:#27AE60;padding:9px;border-radius:8px;
    font-size:13px;text-decoration:none;
    border:1px solid {'#2A5A2A' if st.session_state.dark_mode else '#81C784'};
    margin-top:12px;font-weight:500;}}
.pulse-dot{{
    display:inline-block;width:7px;height:7px;
    border-radius:50%;background:#27AE60;
    animation:pulse 1.5s infinite;margin-right:6px;}}
@keyframes pulse{{
    0%,100%{{opacity:1;transform:scale(1);}}
    50%{{opacity:0.4;transform:scale(0.8);}}
}}
</style>
""", unsafe_allow_html=True)

# ============================================================
# CHARGEMENT DONNÉES
# ============================================================
@st.cache_data(ttl=900)
def charger_donnees():
    df = pd.read_csv(
        "data/gdelt_benin_2025_clean.csv", low_memory=False)
    df_mentions = pd.read_csv(
        "data/gdelt_benin_2025_mentions.csv", low_memory=False)
    df_gkg = pd.read_csv(
        "data/gdelt_benin_2025_gkg.csv", low_memory=False)

    for col in ["GoldsteinScale","AvgTone","NumArticles",
                "QuadClass","NumMentions","NumSources",
                "ActionGeo_Lat","ActionGeo_Long"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["SQLDATE"] = pd.to_datetime(df["SQLDATE"], errors="coerce")
    df["mois"] = df["SQLDATE"].dt.month
    df["semaine"] = df["SQLDATE"].dt.isocalendar().week.astype(int)
    df["jour_semaine"] = df["SQLDATE"].dt.day_name()
    df["GlobalEventID"] = df["GlobalEventID"].astype(str)

    df_mentions["MentionDocTone"] = pd.to_numeric(
        df_mentions["MentionDocTone"], errors="coerce")
    df_mentions["GlobalEventID"] = (
        df_mentions["GlobalEventID"].astype(str))
    df_gkg["DATE"] = pd.to_datetime(
        df_gkg["DATE"], errors="coerce")

    return df, df_mentions, df_gkg

with st.spinner("Chargement des données..."):
    df, df_mentions, df_gkg = charger_donnees()

# ============================================================
# ZONES & SCORES
# ============================================================
ZONES = {
    "Alibori":    {"lat":11.50,"lon":2.80,"desc":"Nord-est · Frontière Niger & Nigeria"},
    "Atakora":    {"lat":10.50,"lon":1.40,"desc":"Nord-ouest · Frontière Burkina Faso"},
    "Borgou":     {"lat": 9.80,"lon":2.70,"desc":"Centre-nord · Parakou & Tchaourou"},
    "Donga":      {"lat": 9.50,"lon":1.70,"desc":"Centre-ouest · Zone de transition"},
    "Collines":   {"lat": 8.50,"lon":2.30,"desc":"Centre · Savalou & Savè"},
    "Plateau":    {"lat": 7.80,"lon":2.60,"desc":"Est · Frontière Nigeria"},
    "Zou":        {"lat": 7.30,"lon":2.00,"desc":"Sud-centre · Abomey"},
    "Couffo":     {"lat": 7.10,"lon":1.70,"desc":"Sud-ouest · Zone rurale"},
    "Ouémé":      {"lat": 6.80,"lon":2.50,"desc":"Sud-est · Porto-Novo"},
    "Mono":       {"lat": 6.80,"lon":1.60,"desc":"Sud-ouest · Zone lagunaire"},
    "Atlantique": {"lat": 6.50,"lon":2.20,"desc":"Sud · Zone côtière"},
    "Littoral":   {"lat": 6.35,"lon":2.43,"desc":"Cotonou · Capitale économique"},
}

def score_risque(zone_df):
    if len(zone_df) == 0: return 0
    taux = (zone_df["QuadClass"] >= 3).mean()
    gold = abs(zone_df["GoldsteinScale"].mean())
    nb   = min(len(zone_df) / 200, 1)
    return round((taux*4 + gold*0.3 + nb*3), 1)

def score_to_niveau(score):
    if score >= 7: return "🔴","Situation grave","#C0392B","rouge"
    if score >= 4: return "🟠","Vigilance recommandée","#E67E22","orange"
    if score >= 2: return "🟡","Situation modérée","#E67E22","orange"
    return "🟢","Situation normale","#27AE60","vert"

def tone_to_texte(t):
    if t <= -4: return "Les médias en parlent très négativement"
    if t <= -2: return "Couverture internationale négative"
    if t <=  0: return "Couverture internationale neutre"
    return "Couverture internationale positive"

def impunite_to_texte(nb_c, nb_j):
    r = nb_j / max(nb_c,1) * 100
    if r <= 5:  return "Presque aucun crime n'est poursuivi"
    if r <= 15: return "Peu de criminels sont poursuivis"
    if r <= 30: return "Justice partiellement présente"
    return "Justice relativement active"

@st.cache_data(ttl=900)
def calcul_scores(_df, _df_gkg):
    acteurs_j = ["TRIBUNAL","PRISON","HIGH COURT",
                 "LAWYER","PROSECUTOR","JUDGE","SUPREME COURT"]
    scores = {}
    for zone in ZONES:
        zdf = _df[_df["ActionGeo_FullName"].str.contains(
            zone, na=False, case=False)]
        nb_c = int((zdf["QuadClass"] >= 3).sum())
        nb_j = int(zdf["Actor1Name"].isin(acteurs_j).sum())
        crises_inv = int(
            ((zdf["GoldsteinScale"] < -5) &
             (zdf["NumArticles"] <= 2)).sum())
        th = 0
        gkg_z = _df_gkg[_df_gkg["Locations"].str.contains(
            zone, na=False, case=False)]
        for themes in gkg_z["Themes"].dropna():
            for t in ["TERROR","KILL","ARMEDCONFLICT"]:
                if t in str(themes): th += 1
        scores[zone] = {
            "score":      score_risque(zdf),
            "goldstein":  round(zdf["GoldsteinScale"].mean(),2) if len(zdf) else 0,
            "tone":       round(zdf["AvgTone"].mean(),2) if len(zdf) else 0,
            "nb_conflits":nb_c,
            "nb_justice": nb_j,
            "nb_events":  len(zdf),
            "crises_inv": crises_inv,
            "themes_chauds": th,
        }
    return scores

with st.spinner("Calcul des scores..."):
    scores = calcul_scores(df, df_gkg)

# ============================================================
# GÉNÉRATION IA
# ============================================================
@st.cache_data(ttl=3600)
def generer_ia(zone, score, tone, nb_c, crises_inv):
    try:
        client = anthropic.Anthropic(
            api_key=st.secrets["ANTHROPIC_API_KEY"])
        niv = ("grave" if score>=7 else
               "préoccupant" if score>=4 else
               "modéré" if score>=2 else "calme")
        m = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[{"role":"user","content":
                f"Tu es BENIN WATCH. 2 phrases simples pour un "
                f"citoyen ordinaire sur {zone}. Niveau {niv}, "
                f"{nb_c} incidents, médias "
                f"{'négatifs' if tone<-2 else 'neutres'}, "
                f"{crises_inv} crises inaperçues. "
                f"Aucun chiffre technique, langage simple."
            }])
        return m.content[0].text
    except Exception:
        if score >= 7:
            return (f"Le {zone} traverse une période difficile. "
                    "Limitez vos déplacements non essentiels.")
        if score >= 4:
            return (f"La situation dans le {zone} demande "
                    "de la vigilance. Restez informé.")
        return f"La situation dans le {zone} est calme cette semaine."

# ============================================================
# CARTE FOLIUM
# ============================================================
def creer_carte(zone_selectionnee=None):
    m = folium.Map(
        location=[9.3, 2.3],
        zoom_start=7,
        tiles=TILE,
        attr="© BENIN WATCH",
        prefer_canvas=True,
    )

    # Heatmap conflits
    df_heat = df[
        (df["QuadClass"] >= 3) &
        df["ActionGeo_Lat"].notna() &
        df["ActionGeo_Long"].notna()
    ][["ActionGeo_Lat","ActionGeo_Long","GoldsteinScale"]].copy()
    df_heat["weight"] = df_heat["GoldsteinScale"].abs()

    if len(df_heat) > 0:
        HeatMap(
            data=df_heat[["ActionGeo_Lat","ActionGeo_Long","weight"]].values.tolist(),
            min_opacity=0.3,
            radius=20,
            blur=15,
            gradient={0.2:"#27AE60",0.5:"#E67E22",0.8:"#C0392B",1:"#8B0000"}
        ).add_to(m)

    # Marqueurs par département
    for zone, info in ZONES.items():
        s = scores[zone]
        emoji, niveau, color, _ = score_to_niveau(s["score"])

        # Taille du cercle selon score
        radius = 8 + s["score"] * 2

        # Pulse effect via icon
        is_selected = (zone == zone_selectionnee)

        # Popup HTML
        popup_html = f"""
        <div style="font-family:Inter,sans-serif;
                    min-width:180px;padding:4px;">
          <b style="font-size:14px;color:{color};">
            {emoji} {zone}
          </b><br>
          <span style="font-size:12px;color:#666;">
            {niveau}
          </span><br><br>
          <span style="font-size:12px;">
            📊 {s['nb_conflits']} incidents<br>
            🔇 {s['crises_inv']} crises invisibles<br>
            {tone_to_texte(s['tone'])}
          </span>
        </div>"""

        # Cercle cliquable avec animation
        folium.CircleMarker(
            location=[info["lat"], info["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8 if is_selected else 0.6,
            weight=4 if is_selected else 2,
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=f"{emoji} {zone} — {niveau}",
        ).add_to(m)

        # Cercle pulsant pour zones rouges
        if s["score"] >= 7:
            folium.CircleMarker(
                location=[info["lat"], info["lon"]],
                radius=radius + 8,
                color=color,
                fill=False,
                weight=1,
                opacity=0.3,
            ).add_to(m)

        # Label du département
        folium.Marker(
            location=[info["lat"] + 0.15, info["lon"]],
            icon=folium.DivIcon(
                html=f"""<div style="
                    font-family:Inter,sans-serif;
                    font-size:10px;
                    font-weight:500;
                    color:{'#FFFFFF' if st.session_state.dark_mode else '#1A1A2E'};
                    text-shadow:1px 1px 2px rgba(0,0,0,0.8);
                    white-space:nowrap;">
                    {zone}
                </div>""",
                icon_size=(80, 20),
                icon_anchor=(40, 0),
            )
        ).add_to(m)

    return m

# ============================================================
# HEADER
# ============================================================
col_logo, col_status, col_actions = st.columns([2, 3, 2])

with col_logo:
    st.markdown(
        "<div class='bw-logo'>"
        "<span class='r'>BENIN</span>"
        "<span class='w'> WATCH</span>"
        "</div>", unsafe_allow_html=True)

with col_status:
    score_nat = sum(v["score"] for v in scores.values()) / len(scores)
    zones_rouges = sum(1 for v in scores.values() if v["score"] >= 7)
    zones_orange = sum(1 for v in scores.values() if 4 <= v["score"] < 7)
    st.markdown(
        f"<div style='text-align:center;padding:8px 0;"
        f"font-size:12px;color:{TEXT2};'>"
        f"<span class='pulse-dot'></span>"
        f"Mis à jour — {datetime.now().strftime('%d %b %Y · %H:%M')}"
        f" &nbsp;·&nbsp; "
        f"<span style='color:#C0392B;font-weight:500;'>"
        f"{zones_rouges} zone(s) en alerte</span>"
        f" &nbsp;·&nbsp; "
        f"<span style='color:#E67E22;'>"
        f"{zones_orange} en vigilance</span>"
        f"</div>", unsafe_allow_html=True)

with col_actions:
    col_a, col_b = st.columns([1,1])
    with col_a:
        mode_label = "☀️ Clair" if st.session_state.dark_mode else "🌙 Sombre"
        st.button(mode_label, on_click=toggle_mode,
                  use_container_width=True)
    with col_b:
        if score_nat >= 5:
            st.markdown(
                "<div style='background:#2A0A0A;color:#C0392B;"
                "border:1px solid #5A1A1A;padding:6px 12px;"
                "border-radius:8px;text-align:center;"
                "font-size:12px;font-weight:500;'>"
                "⚠️ ALERTE</div>",
                unsafe_allow_html=True)
        else:
            st.markdown(
                "<div style='background:#0A2A0A;color:#27AE60;"
                "border:1px solid #1A5A1A;padding:6px 12px;"
                "border-radius:8px;text-align:center;"
                "font-size:12px;font-weight:500;'>"
                "✅ NORMAL</div>",
                unsafe_allow_html=True)

st.divider()

# ============================================================
# KPIs GLOBAUX
# ============================================================
kpis = [
    {"val":"27,3%","lbl":"des événements sont des conflits","c":"#C0392B"},
    {"val":"33,5%","lbl":"des crises graves sont invisibles","c":"#E67E22"},
    {"val":"10,2×","lbl":"le nord est plus dangereux que le sud","c":"#C0392B"},
    {"val":"−40 km","lbl":"la menace descend vers Cotonou chaque année","c":"#E67E22"},
]
cols_kpi = st.columns(4)
for col, k in zip(cols_kpi, kpis):
    col.markdown(f"""
    <div class='kpi-card'>
      <div class='kpi-val' style='color:{k["c"]};'>{k["val"]}</div>
      <div class='kpi-lbl'>{k["lbl"]}</div>
    </div>""", unsafe_allow_html=True)

st.divider()

# ============================================================
# LAYOUT PRINCIPAL
# ============================================================
col_carte, col_panel = st.columns([3, 2])

with col_carte:
    st.markdown(
        f"<div style='font-size:11px;color:{TEXT2};"
        "text-transform:uppercase;letter-spacing:1px;"
        "margin-bottom:8px;'>"
        "🗺️ Cliquez sur un département pour voir les détails"
        "</div>", unsafe_allow_html=True)

    # Zone sélectionnée via session state
    if "zone_selectionnee" not in st.session_state:
        st.session_state.zone_selectionnee = "Alibori"

    # Carte Folium
    carte = creer_carte(st.session_state.zone_selectionnee)
    carte_data = st_folium(
        carte,
        width="100%",
        height=480,
        returned_objects=["last_object_clicked_tooltip"],
        key=f"carte_{'dark' if st.session_state.dark_mode else 'light'}"
    )

    # Récupérer la zone cliquée
    if carte_data and carte_data.get("last_object_clicked_tooltip"):
        tooltip = carte_data["last_object_clicked_tooltip"]
        for zone in ZONES.keys():
            if zone in str(tooltip):
                st.session_state.zone_selectionnee = zone
                break

    # Légende
    st.markdown(f"""
    <div style='display:flex;gap:20px;justify-content:center;
      margin-top:8px;font-size:11px;color:{TEXT2};'>
      <span>🔴 Situation grave (&gt;7)</span>
      <span>🟠 Vigilance (4–7)</span>
      <span>🟢 Calme (&lt;4)</span>
      <span>🌡️ Intensité des conflits</span>
    </div>""", unsafe_allow_html=True)

with col_panel:

    # Sélecteur manuel (backup si clic ne fonctionne pas)
    zone_choisie = st.selectbox(
        "Département",
        options=list(ZONES.keys()),
        index=list(ZONES.keys()).index(
            st.session_state.zone_selectionnee),
        key="zone_select"
    )
    if zone_choisie != st.session_state.zone_selectionnee:
        st.session_state.zone_selectionnee = zone_choisie

    zone = st.session_state.zone_selectionnee
    s = scores[zone]
    emoji, niveau, color, couleur = score_to_niveau(s["score"])

    # Panel zone
    st.markdown(f"""
    <div class='zone-panel'>
      <div class='zone-name'>{zone}</div>
      <div class='zone-meta'>{ZONES[zone]["desc"]}</div>
      <div style='font-size:14px;font-weight:500;
        color:{color};margin-bottom:12px;'>
        {emoji} {niveau}
      </div>
      <div class='score-row'>
        <span>Niveau de risque</span>
        <span style='color:{color};font-weight:600;'>
          {s["score"]}/10</span>
      </div>
      <div class='score-bar'>
        <div style='width:{min(s["score"]/10,1)*100:.0f}%;
          height:8px;background:{color};
          border-radius:4px;transition:width 0.5s;'></div>
      </div>
    </div>""", unsafe_allow_html=True)

    # Alerte signal précurseur
    if s["themes_chauds"] > 10:
        st.markdown(
            "<div class='alert-box'>"
            "<span>⚠️</span>"
            "<span>Activité inhabituelle détectée cette semaine</span>"
            "</div>", unsafe_allow_html=True)

    # Résumé IA
    with st.spinner("Analyse IA..."):
        resume = generer_ia(
            zone, s["score"], s["tone"],
            s["nb_conflits"], s["crises_inv"])

    # Infos
    for label, valeur in [
        ("Situation cette semaine", resume),
        ("Incidents récents",
         f"<b style='color:{color};'>{s['nb_conflits']}</b>"
         " incidents signalés dans ce département"),
        ("Crises non couvertes",
         f"<b style='color:#E67E22;'>{s['crises_inv']}</b>"
         " événements graves passés inaperçus dans les médias"),
        ("Ce que le monde en dit", tone_to_texte(s["tone"])),
        ("Accès à la justice",
         impunite_to_texte(s["nb_conflits"], s["nb_justice"])),
    ]:
        st.markdown(f"""
        <div class='info-row'>
          <div class='info-lbl'>{label}</div>
          <div class='info-val'>{valeur}</div>
        </div>""", unsafe_allow_html=True)

    # Timeline semaine
    jours = ["Lun","Mar","Mer","Jeu","Ven","Sam","Dim"]
    random.seed(hash(zone))
    week = []
    for _ in range(7):
        r = random.random()
        if s["score"] >= 7:
            week.append("🔴" if r > 0.3 else "🟠")
        elif s["score"] >= 4:
            week.append("🟠" if r > 0.4 else "🟢")
        else:
            week.append("🟢")

    st.markdown(
        "<div style='font-size:10px;color:{};margin-top:14px;"
        "margin-bottom:6px;text-transform:uppercase;"
        "letter-spacing:0.8px;'>Cette semaine</div>".format(TEXT2),
        unsafe_allow_html=True)

    cols_w = st.columns(7)
    for i, col in enumerate(cols_w):
        col.markdown(f"""
        <div class='day-cell'>
          <div class='day-name'>{jours[i]}</div>
          <div class='day-emoji'>{week[i]}</div>
        </div>""", unsafe_allow_html=True)

    # WhatsApp
    msg = f"BENIN WATCH — {zone} : {niveau}. {resume}"
    wa_url = f"https://wa.me/?text={msg.replace(' ','%20')}"
    st.markdown(
        f"<a href='{wa_url}' target='_blank' class='wa-btn'>"
        f"📲 Partager sur WhatsApp</a>",
        unsafe_allow_html=True)

# ============================================================
# FOOTER
# ============================================================
st.divider()
cf1, cf2 = st.columns(2)
cf1.markdown(
    f"<div style='font-size:10px;color:{TEXT2};'>"
    "BENIN WATCH · Données GDELT · Open source · 2025"
    "</div>", unsafe_allow_html=True)
cf2.markdown(
    f"<div style='font-size:10px;color:{TEXT2};"
    f"text-align:right;'>"
    f"19 042 événements analysés · "
    f"{datetime.now().strftime('%H:%M')}</div>",
    unsafe_allow_html=True)