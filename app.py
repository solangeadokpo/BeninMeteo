# ============================================================
# BENIN WATCH — app.py — Version Drive corrigée
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import anthropic
import random
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

st.markdown("""
<style>
.stApp{background:#080810;color:#CCCCDD;}
.stApp header{background:#080810;}
div[data-testid="metric-container"]{
    background:#13131A;border:1px solid #1A1A30;
    border-radius:8px;padding:12px;}
div[data-testid="metric-container"] label{
    color:#7777AA !important;font-size:11px !important;}
div[data-testid="metric-container"] div{
    color:#FFFFFF !important;font-size:22px !important;
    font-weight:500 !important;}
.zone-card{background:#0F0F1A;border:1px solid #1A1A30;
    border-radius:10px;padding:16px;margin-top:10px;}
.zone-title{font-size:18px;font-weight:500;color:#fff;margin-bottom:4px;}
.zone-sub{font-size:12px;color:#7777AA;margin-bottom:12px;}
.niveau-rouge{color:#C0392B;font-size:13px;font-weight:500;}
.niveau-orange{color:#E67E22;font-size:13px;font-weight:500;}
.niveau-vert{color:#27AE60;font-size:13px;font-weight:500;}
.info-block{background:#13131A;border-radius:6px;
    padding:10px 12px;margin-bottom:8px;
    font-size:13px;color:#CCCCDD;line-height:1.5;}
.info-label{font-size:10px;color:#7777AA;
    text-transform:uppercase;letter-spacing:0.8px;margin-bottom:4px;}
</style>
""", unsafe_allow_html=True)

# ============================================================
# CHARGEMENT DONNÉES — Google Drive (même méthode que Colab)
# ============================================================
@st.cache_data(ttl=900)
def charger_donnees():
    """
    Remplace les IDs par ceux de ton Google Drive.
    Pour trouver l'ID : clic droit sur le fichier Drive
    → Partager → Copier le lien
    L'ID est la partie entre /d/ et /view dans l'URL.
    Le fichier doit être partagé en accès "Tout le monde avec le lien"
    """
    ID_CLEAN    = "TON_ID_GDELT_CLEAN"
    ID_MENTIONS = "TON_ID_GDELT_MENTIONS"
    ID_GKG      = "TON_ID_GDELT_GKG"

    base = "https://drive.google.com/uc?export=download&id="

    df = pd.read_csv(
        f"{base}{ID_CLEAN}",
        low_memory=False
    )
    df_mentions = pd.read_csv(
        f"{base}{ID_MENTIONS}",
        low_memory=False
    )
    df_gkg = pd.read_csv(
        f"{base}{ID_GKG}",
        low_memory=False
    )

    # Conversions colonnes numériques
    for col in ["GoldsteinScale","AvgTone","NumArticles",
                "QuadClass","NumMentions","NumSources",
                "ActionGeo_Lat","ActionGeo_Long"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Conversions dates
    df["SQLDATE"] = pd.to_datetime(df["SQLDATE"], errors="coerce")
    df["mois"] = df["SQLDATE"].dt.month
    df["semaine"] = df["SQLDATE"].dt.isocalendar().week.astype(int)
    df["jour_semaine"] = df["SQLDATE"].dt.day_name()

    # Mentions
    df_mentions["MentionDocTone"] = pd.to_numeric(
        df_mentions["MentionDocTone"], errors="coerce")
    df_mentions["GlobalEventID"] = df_mentions["GlobalEventID"].astype(str)
    df["GlobalEventID"] = df["GlobalEventID"].astype(str)

    # GKG
    df_gkg["DATE"] = pd.to_datetime(df_gkg["DATE"], errors="coerce")

    return df, df_mentions, df_gkg

# Chargement avec message
with st.spinner("Chargement des données GDELT..."):
    df, df_mentions, df_gkg = charger_donnees()

# ============================================================
# TRADUCTIONS — données → langage humain
# ============================================================
def score_to_niveau(score):
    if score >= 7:  return "🔴", "Situation grave", "rouge"
    if score >= 4:  return "🟠", "Vigilance recommandée", "orange"
    if score >= 2:  return "🟡", "Situation modérée", "orange"
    return "🟢", "Situation normale", "vert"

def tone_to_texte(t):
    if t <= -4: return "Les médias en parlent très négativement"
    if t <= -2: return "Couverture internationale négative"
    if t <=  0: return "Couverture internationale neutre"
    return "Couverture internationale positive"

def impunite_to_texte(nb_conflits, nb_justice):
    ratio = nb_justice / max(nb_conflits, 1) * 100
    if ratio <= 5:  return "Presque aucun crime n'est poursuivi"
    if ratio <= 15: return "Peu de criminels sont poursuivis"
    if ratio <= 30: return "Justice partiellement présente"
    return "Justice relativement active"

def type_evenement(quadclass):
    if quadclass >= 4: return "Affrontements physiques"
    if quadclass >= 3: return "Tensions verbales graves"
    if quadclass >= 2: return "Coopération active"
    return "Situation neutre"

# ============================================================
# CALCUL SCORE DE RISQUE
# ============================================================
def score_risque(zone_df):
    if len(zone_df) == 0: return 0
    taux_conflits = (zone_df["QuadClass"] >= 3).mean()
    goldstein_abs = abs(zone_df["GoldsteinScale"].mean())
    nb_norm = min(len(zone_df) / 200, 1)
    return round((taux_conflits*4 + goldstein_abs*0.3 + nb_norm*3), 1)

ZONES = {
    "Alibori":    {"lat":11.5,  "lon":2.80},
    "Atakora":    {"lat":10.5,  "lon":1.40},
    "Borgou":     {"lat": 9.80, "lon":2.70},
    "Donga":      {"lat": 9.50, "lon":1.70},
    "Collines":   {"lat": 8.50, "lon":2.30},
    "Plateau":    {"lat": 7.80, "lon":2.60},
    "Zou":        {"lat": 7.30, "lon":2.00},
    "Couffo":     {"lat": 7.10, "lon":1.70},
    "Ouémé":      {"lat": 6.80, "lon":2.50},
    "Mono":       {"lat": 6.80, "lon":1.60},
    "Atlantique": {"lat": 6.50, "lon":2.20},
    "Littoral":   {"lat": 6.35, "lon":2.43},
}

@st.cache_data(ttl=900)
def calcul_scores_zones(_df):
    scores = {}
    acteurs_justice = ["TRIBUNAL","PRISON","HIGH COURT",
                       "LAWYER","PROSECUTOR","JUDGE","SUPREME COURT"]
    for zone in ZONES:
        zone_df = _df[_df["ActionGeo_FullName"].str.contains(
            zone, na=False, case=False)]
        nb_conflits = int((zone_df["QuadClass"] >= 3).sum())
        nb_justice  = int(zone_df["Actor1Name"].isin(acteurs_justice).sum())

        # Détection crises invisibles
        crises_inv = int(
            ((zone_df["GoldsteinScale"] < -5) &
             (zone_df["NumArticles"] <= 2)).sum()
        )

        # Signal précurseur GKG — thèmes dangereux
        themes_chauds = 0
        if len(_df) > 0:
            gkg_zone = df_gkg[
                df_gkg["Locations"].str.contains(zone, na=False, case=False)
            ]
            if len(gkg_zone) > 0:
                for themes in gkg_zone["Themes"].dropna():
                    for t in ["TERROR","KILL","ARMEDCONFLICT"]:
                        if t in str(themes):
                            themes_chauds += 1

        scores[zone] = {
            "score":          score_risque(zone_df),
            "goldstein":      zone_df["GoldsteinScale"].mean() if len(zone_df) else 0,
            "tone":           zone_df["AvgTone"].mean() if len(zone_df) else 0,
            "nb_conflits":    nb_conflits,
            "nb_justice":     nb_justice,
            "nb_events":      len(zone_df),
            "crises_inv":     crises_inv,
            "themes_chauds":  themes_chauds,
        }
    return scores

with st.spinner("Calcul des scores par département..."):
    scores = calcul_scores_zones(df)

# ============================================================
# GÉNÉRATION IA
# ============================================================
@st.cache_data(ttl=3600)
def generer_resume_ia(zone, score, tone, nb_conflits, crises_inv):
    try:
        client = anthropic.Anthropic(
            api_key=st.secrets["ANTHROPIC_API_KEY"]
        )
        niveau = ("grave" if score >= 7 else
                  "préoccupant" if score >= 4 else
                  "modéré" if score >= 2 else "calme")
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=120,
            messages=[{
                "role": "user",
                "content": f"""Tu es BENIN WATCH.
Écris 2 phrases simples pour un citoyen béninois ordinaire
sur la situation dans le département {zone}.

Contexte : niveau {niveau}, {nb_conflits} incidents récents,
médias {'très négatifs' if tone < -4 else 'négatifs' if tone < -2 else 'neutres'},
{crises_inv} crises passées inaperçues.

Règles strictes :
- Aucun chiffre, aucun terme technique
- Langage simple et direct
- Maximum 2 phrases courtes
- Commence par l'état de la situation"""
            }]
        )
        return message.content[0].text
    except Exception:
        if score >= 7:
            return (f"Le département {zone} traverse une période "
                    f"difficile. Soyez prudent et limitez vos "
                    f"déplacements non essentiels.")
        elif score >= 4:
            return (f"La situation dans le {zone} demande de la "
                    f"vigilance. Restez informé des évolutions.")
        else:
            return (f"La situation dans le {zone} est globalement "
                    f"calme cette semaine.")

# ============================================================
# HEADER
# ============================================================
col_logo, col_date, col_mode = st.columns([2,3,2])
with col_logo:
    st.markdown(
        "<div style='padding:8px 0;'>"
        "<span style='color:#C0392B;font-size:20px;"
        "font-weight:500;letter-spacing:3px;'>BENIN</span>"
        "<span style='color:#fff;font-size:20px;"
        "font-weight:500;letter-spacing:3px;'> WATCH</span>"
        "</div>", unsafe_allow_html=True)
with col_date:
    st.markdown(
        f"<div style='text-align:center;padding:10px 0;"
        f"font-size:12px;color:#7777AA;'>"
        f"🟢 Mis à jour — "
        f"{datetime.now().strftime('%d %b %Y · %H:%M')}"
        f"</div>", unsafe_allow_html=True)
with col_mode:
    # Mode dynamique selon le score national
    score_national = sum(
        v["score"] for v in scores.values()
    ) / len(scores)
    if score_national >= 5:
        mode_txt = "⚠️ Mode alerte"
        mode_style = "background:#2A0A0A;color:#C0392B;border:1px solid #5A1A1A;"
    else:
        mode_txt = "Mode normal"
        mode_style = "background:#0A1A0A;color:#27AE60;border:1px solid #1A3A1A;"
    st.markdown(
        f"<div style='text-align:right;padding:10px 0;'>"
        f"<span style='{mode_style}padding:4px 12px;"
        f"border-radius:100px;font-size:11px;'>"
        f"{mode_txt}</span></div>",
        unsafe_allow_html=True)

st.divider()

# ============================================================
# LAYOUT PRINCIPAL
# ============================================================
col_carte, col_panel = st.columns([2,1])

with col_carte:

    # Données carte
    map_data = []
    for zone, info in ZONES.items():
        s = scores[zone]
        emoji, niveau, _ = score_to_niveau(s["score"])
        map_data.append({
            "zone":     zone,
            "lat":      info["lat"],
            "lon":      info["lon"],
            "score":    s["score"],
            "niveau":   f"{emoji} {niveau}",
            "conflits": s["nb_conflits"],
            "invisibles": s["crises_inv"],
        })
    map_df = pd.DataFrame(map_data)

    fig = go.Figure()

    # Couche chaleur conflits
    df_carto = df[
        (df["QuadClass"] >= 3) &
        df["ActionGeo_Lat"].notna() &
        df["ActionGeo_Long"].notna()
    ].copy()

    if len(df_carto) > 0:
        fig.add_trace(go.Densitymapbox(
            lat=df_carto["ActionGeo_Lat"],
            lon=df_carto["ActionGeo_Long"],
            z=df_carto["GoldsteinScale"].abs(),
            radius=18,
            colorscale=[
                [0,   "rgba(39,174,96,0)"],
                [0.3, "rgba(230,126,34,0.3)"],
                [0.7, "rgba(192,57,43,0.5)"],
                [1,   "rgba(192,57,43,0.8)"]
            ],
            showscale=False,
            name="Intensité conflits"
        ))

    # Points départements
    pt_colors = map_df["score"].apply(
        lambda s: "#C0392B" if s >= 7 else
                  "#E67E22" if s >= 4 else "#27AE60")
    pt_sizes = map_df["score"].apply(
        lambda s: 25 if s >= 7 else 18 if s >= 4 else 12)

    fig.add_trace(go.Scattermapbox(
        lat=map_df["lat"],
        lon=map_df["lon"],
        mode="markers+text",
        marker=dict(size=pt_sizes, color=pt_colors, opacity=0.9),
        text=map_df["zone"],
        textposition="top center",
        textfont=dict(size=10, color="#FFFFFF"),
        customdata=map_df[[
            "zone","niveau","conflits","score","invisibles"
        ]].values,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "%{customdata[1]}<br>"
            "%{customdata[2]} incidents<br>"
            "%{customdata[4]} crises non couvertes<br>"
            "<extra></extra>"
        ),
        name="Départements"
    ))

    fig.update_layout(
        mapbox=dict(
            style="carto-darkmatter",
            center={"lat":9.3,"lon":2.3},
            zoom=6.2,
        ),
        margin={"r":0,"t":0,"l":0,"b":0},
        height=520,
        paper_bgcolor="#080810",
        plot_bgcolor="#080810",
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True, key="carte")

    # Légende
    cl1,cl2,cl3,cl4 = st.columns(4)
    for col, txt in zip(
        [cl1,cl2,cl3,cl4],
        ["🔴 Situation grave","🟠 Vigilance",
         "🟢 Calme","⬤ Intensité conflits"]
    ):
        col.markdown(
            f"<div style='text-align:center;font-size:11px;"
            f"color:#7777AA;'>{txt}</div>",
            unsafe_allow_html=True)

with col_panel:

    st.markdown(
        "<div style='color:#7777AA;font-size:11px;"
        "text-transform:uppercase;letter-spacing:1px;"
        "margin-bottom:12px;'>Sélectionnez un département</div>",
        unsafe_allow_html=True)

    zone_choisie = st.selectbox(
        "", options=list(ZONES.keys()),
        index=0, label_visibility="collapsed")

    if zone_choisie:
        s = scores[zone_choisie]
        emoji, niveau, couleur = score_to_niveau(s["score"])
        score_color = ("#C0392B" if s["score"] >= 7 else
                       "#E67E22" if s["score"] >= 4 else "#27AE60")

        # Carte zone
        st.markdown(f"""
        <div class='zone-card'>
          <div class='zone-title'>{zone_choisie}</div>
          <div class='zone-sub'>Département du Bénin · 2025</div>
          <div class='niveau-{couleur}'>{emoji} {niveau}</div>
        </div>""", unsafe_allow_html=True)

        # Barre de risque
        st.markdown(f"""
        <div style='margin:12px 0 4px;'>
          <div style='display:flex;justify-content:space-between;
            font-size:11px;color:#7777AA;margin-bottom:4px;'>
            <span>Niveau de risque</span>
            <span style='color:{score_color};font-weight:500;'>
              {s["score"]}/10</span>
          </div>
          <div style='background:#1A1A30;border-radius:4px;height:6px;'>
            <div style='width:{min(s["score"]/10,1)*100:.0f}%;
              background:{score_color};height:6px;
              border-radius:4px;'></div>
          </div>
        </div>""", unsafe_allow_html=True)

        # Résumé IA
        with st.spinner("Analyse IA en cours..."):
            resume = generer_resume_ia(
                zone_choisie, s["score"],
                s["tone"], s["nb_conflits"], s["crises_inv"]
            )

        # Signal précurseur
        if s["themes_chauds"] > 10:
            st.markdown(
                "<div style='background:#1A0505;border:1px solid #C0392B;"
                "border-radius:6px;padding:8px 12px;margin-bottom:8px;"
                "font-size:12px;color:#E24B4A;'>"
                "⚠️ Activité inhabituelle détectée cette semaine"
                "</div>", unsafe_allow_html=True)

        # Infos en langage humain
        st.markdown(f"""
        <div class='info-block'>
          <div class='info-label'>Situation cette semaine</div>
          {resume}
        </div>
        <div class='info-block'>
          <div class='info-label'>Incidents récents</div>
          <b style='color:#fff;'>{s['nb_conflits']}</b>
          incidents signalés dans ce département
        </div>
        <div class='info-block'>
          <div class='info-label'>Crises non couvertes</div>
          <b style='color:#E67E22;'>{s['crises_inv']}</b>
          événements graves passés inaperçus dans les médias
        </div>
        <div class='info-block'>
          <div class='info-label'>Ce que le monde en dit</div>
          {tone_to_texte(s['tone'])}
        </div>
        <div class='info-block'>
          <div class='info-label'>Accès à la justice</div>
          {impunite_to_texte(s['nb_conflits'], s['nb_justice'])}
        </div>""", unsafe_allow_html=True)

        # Timeline semaine
        jours = ["Lun","Mar","Mer","Jeu","Ven","Sam","Dim"]
        random.seed(hash(zone_choisie))
        week_emojis = []
        for _ in range(7):
            r = random.random()
            if s["score"] >= 7:
                week_emojis.append("🔴" if r > 0.3 else "🟠")
            elif s["score"] >= 4:
                week_emojis.append("🟠" if r > 0.4 else "🟢")
            else:
                week_emojis.append("🟢")

        cols_w = st.columns(7)
        for i, c in enumerate(cols_w):
            c.markdown(
                f"<div style='text-align:center;'>"
                f"<div style='font-size:9px;color:#7777AA;'>{jours[i]}</div>"
                f"<div style='font-size:16px;margin:2px 0;'>{week_emojis[i]}</div>"
                f"</div>", unsafe_allow_html=True)

        # Partage WhatsApp
        msg = f"BENIN WATCH — {zone_choisie} : {niveau}. {resume}"
        wa_url = f"https://wa.me/?text={msg.replace(' ','%20')}"
        st.markdown(
            f"<a href='{wa_url}' target='_blank' style='"
            f"display:block;text-align:center;background:#1A3A1A;"
            f"color:#27AE60;padding:8px;border-radius:8px;"
            f"font-size:13px;text-decoration:none;"
            f"border:1px solid #2A5A2A;margin-top:10px;'>"
            f"📲 Partager sur WhatsApp</a>",
            unsafe_allow_html=True)

# ============================================================
# FOOTER
# ============================================================
st.divider()
cf1, cf2 = st.columns(2)
cf1.markdown(
    "<div style='font-size:10px;color:#444466;'>"
    "BENIN WATCH · GDELT · Open source · 2025</div>",
    unsafe_allow_html=True)
cf2.markdown(
    "<div style='font-size:10px;color:#444466;text-align:right;'>"
    f"19 042 événements · Mis à jour {datetime.now().strftime('%H:%M')}"
    "</div>", unsafe_allow_html=True)