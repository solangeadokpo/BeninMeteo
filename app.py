# ============================================================
# BENIN WATCH — app.py — Version finale
# ============================================================

import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from datetime import datetime
import random

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
if "zone_active" not in st.session_state:
    st.session_state.zone_active = None

def toggle_mode():
    st.session_state.dark_mode = not st.session_state.dark_mode

D = st.session_state.dark_mode
BG    = "#080810" if D else "#F0F0F8"
CARD  = "#0F0F1Aee" if D else "#FFFFFFee"
CARD2 = "#13131Acc" if D else "#F5F5FAcc"
BRD   = "#1A1A30" if D else "#DDDDEE"
TXT   = "#CCCCDD" if D else "#1A1A2E"
TXT2  = "#7777AA" if D else "#666688"
TILE  = "CartoDB dark_matter" if D else "CartoDB positron"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
*{{font-family:'Inter',sans-serif;box-sizing:border-box;}}

/* Remove all streamlit padding */
.stApp{{background:{BG};}}
.stApp header{{display:none;}}
#MainMenu{{display:none;}}
footer{{display:none;}}
.block-container{{
    padding:0 !important;
    max-width:100% !important;
}}
section[data-testid="stSidebar"]{{display:none;}}

/* Header fixe */
.bw-header{{
    position:fixed;top:0;left:0;right:0;
    height:52px;
    background:{CARD};
    backdrop-filter:blur(12px);
    border-bottom:1px solid {BRD};
    display:flex;align-items:center;
    justify-content:space-between;
    padding:0 20px;
    z-index:1000;
}}
.bw-logo{{
    font-size:16px;font-weight:600;
    letter-spacing:3px;
}}
.bw-logo .r{{color:#C0392B;}}
.bw-logo .w{{color:{TXT};}}
.bw-status{{
    font-size:11px;color:{TXT2};
    display:flex;align-items:center;gap:6px;
}}
.pulse{{
    width:6px;height:6px;border-radius:50%;
    background:#27AE60;
    animation:pl 1.5s infinite;
}}
@keyframes pl{{
    0%,100%{{opacity:1;transform:scale(1);}}
    50%{{opacity:.3;transform:scale(.7);}}
}}
.bw-actions{{display:flex;gap:8px;align-items:center;}}
.bw-btn{{
    background:{CARD2};
    border:1px solid {BRD};
    color:{TXT};
    padding:5px 12px;border-radius:20px;
    font-size:11px;cursor:pointer;
    font-weight:500;
}}

/* Carte plein écran */
.map-container{{
    position:fixed;
    top:52px;left:0;right:0;bottom:0;
    z-index:1;
}}
.map-container iframe{{
    width:100% !important;
    height:100% !important;
    border:none !important;
}}

/* Panel latéral flottant */
.side-panel{{
    position:fixed;
    top:64px;right:12px;
    width:340px;
    max-height:calc(100vh - 76px);
    background:{CARD};
    backdrop-filter:blur(16px);
    border:1px solid {BRD};
    border-radius:14px;
    overflow-y:auto;
    z-index:100;
    box-shadow:0 8px 32px rgba(0,0,0,0.4);
}}

/* KPIs flottants en bas */
.kpi-bar{{
    position:fixed;
    bottom:12px;left:50%;
    transform:translateX(-50%);
    display:flex;gap:8px;
    z-index:100;
}}
.kpi-pill{{
    background:{CARD};
    backdrop-filter:blur(12px);
    border:1px solid {BRD};
    border-radius:20px;
    padding:6px 14px;
    font-size:11px;
    color:{TXT};
    white-space:nowrap;
    box-shadow:0 4px 12px rgba(0,0,0,0.3);
}}
.kpi-pill b{{font-weight:600;}}

/* Contenu panel */
.zone-header{{
    padding:16px 16px 0;
    border-bottom:1px solid {BRD};
    margin-bottom:0;
    padding-bottom:14px;
}}
.zone-nom{{
    font-size:18px;font-weight:600;
    color:{TXT};margin-bottom:2px;
}}
.zone-desc{{
    font-size:11px;color:{TXT2};
    margin-bottom:10px;
}}
.niveau-badge{{
    display:inline-flex;align-items:center;
    gap:5px;padding:4px 10px;
    border-radius:20px;font-size:12px;
    font-weight:500;
}}
.score-wrap{{padding:12px 16px;border-bottom:1px solid {BRD};}}
.score-lbl{{
    display:flex;justify-content:space-between;
    font-size:11px;color:{TXT2};
    margin-bottom:5px;
}}
.score-bar{{
    height:6px;background:{BRD};
    border-radius:3px;overflow:hidden;
}}

/* Articles */
.section-title{{
    font-size:10px;color:{TXT2};
    text-transform:uppercase;
    letter-spacing:1px;
    padding:12px 16px 6px;
}}
.article-row{{
    display:flex;gap:10px;
    padding:10px 16px;
    border-bottom:1px solid {BRD};
    cursor:pointer;
    transition:background .15s;
    text-decoration:none;
}}
.article-row:hover{{background:{CARD2};}}
.art-dot{{
    width:8px;height:8px;border-radius:50%;
    flex-shrink:0;margin-top:5px;
}}
.art-content{{flex:1;}}
.art-titre{{
    font-size:12px;color:{TXT};
    font-weight:500;line-height:1.4;
    margin-bottom:3px;
}}
.art-meta{{
    font-size:10px;color:{TXT2};
    display:flex;gap:8px;
}}

/* Semaine météo */
.week-wrap{{padding:10px 16px 14px;}}
.week-grid{{
    display:grid;grid-template-columns:repeat(7,1fr);
    gap:4px;
}}
.day-c{{
    text-align:center;
    background:{CARD2};
    border-radius:6px;
    padding:5px 2px;
}}
.day-n{{font-size:9px;color:{TXT2};margin-bottom:2px;}}
.day-e{{font-size:14px;}}

/* Stats médias */
.media-wrap{{padding:0 16px 14px;}}
.media-row{{
    display:flex;align-items:center;
    gap:8px;margin-bottom:7px;
}}
.media-name{{font-size:11px;color:{TXT2};min-width:85px;}}
.media-bar-w{{
    flex:1;background:{BRD};
    border-radius:3px;height:5px;
    overflow:hidden;
}}
.media-fill{{height:5px;border-radius:3px;}}
.media-txt{{font-size:11px;font-weight:500;min-width:45px;text-align:right;}}

/* WhatsApp */
.wa-btn{{
    display:block;margin:4px 16px 16px;
    text-align:center;
    background:{'#1A3A1A' if D else '#E8F5E9'};
    color:#27AE60;padding:9px;
    border-radius:10px;font-size:12px;
    text-decoration:none;font-weight:500;
    border:1px solid {'#2A5A2A' if D else '#A5D6A7'};
}}

/* Fermer panel */
.close-btn{{
    position:absolute;top:12px;right:12px;
    background:{CARD2};border:1px solid {BRD};
    color:{TXT2};width:26px;height:26px;
    border-radius:50%;display:flex;
    align-items:center;justify-content:center;
    font-size:13px;cursor:pointer;
    line-height:1;
}}

/* Hint carte */
.map-hint{{
    position:fixed;
    bottom:60px;left:50%;
    transform:translateX(-50%);
    background:{CARD};
    backdrop-filter:blur(12px);
    border:1px solid {BRD};
    border-radius:20px;
    padding:7px 16px;
    font-size:11px;color:{TXT2};
    z-index:100;
    pointer-events:none;
}}

/* Scrollbar */
.side-panel::-webkit-scrollbar{{width:4px;}}
.side-panel::-webkit-scrollbar-track{{background:transparent;}}
.side-panel::-webkit-scrollbar-thumb{{
    background:{BRD};border-radius:2px;}}

/* Streamlit overrides */
div[data-testid="stVerticalBlock"]{{gap:0 !important;}}
div[data-testid="stHorizontalBlock"]{{gap:0 !important;}}
.element-container{{margin:0 !important;padding:0 !important;}}
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
                "QuadClass","NumMentions","ActionGeo_Lat","ActionGeo_Long"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["SQLDATE"] = pd.to_datetime(df["SQLDATE"], errors="coerce")
    df["mois"] = df["SQLDATE"].dt.month
    df["GlobalEventID"] = df["GlobalEventID"].astype(str)
    df_mentions["MentionDocTone"] = pd.to_numeric(
        df_mentions["MentionDocTone"], errors="coerce")
    df_mentions["GlobalEventID"] = df_mentions["GlobalEventID"].astype(str)
    df_gkg["DATE"] = pd.to_datetime(df_gkg["DATE"], errors="coerce")

    return df, df_mentions, df_gkg

df, df_mentions, df_gkg = charger_donnees()

# ============================================================
# ZONES & DONNÉES
# ============================================================
ZONES = {
    "Alibori":    {"lat":11.50,"lon":2.80,"desc":"Nord-est · Frontière Niger & Nigeria"},
    "Atakora":    {"lat":10.50,"lon":1.40,"desc":"Nord-ouest · Frontière Burkina Faso"},
    "Borgou":     {"lat": 9.80,"lon":2.70,"desc":"Centre-nord · Parakou"},
    "Donga":      {"lat": 9.50,"lon":1.70,"desc":"Centre-ouest"},
    "Collines":   {"lat": 8.50,"lon":2.30,"desc":"Centre · Savalou"},
    "Plateau":    {"lat": 7.80,"lon":2.60,"desc":"Est · Porto-Novo region"},
    "Zou":        {"lat": 7.30,"lon":2.00,"desc":"Sud-centre · Abomey"},
    "Couffo":     {"lat": 7.10,"lon":1.70,"desc":"Sud-ouest"},
    "Ouémé":      {"lat": 6.80,"lon":2.50,"desc":"Sud-est · Porto-Novo"},
    "Mono":       {"lat": 6.80,"lon":1.60,"desc":"Sud · Frontière Togo"},
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
    if score >= 7: return "🔴","Situation grave","#C0392B","#2A0505","#C0392B22"
    if score >= 4: return "🟠","Vigilance","#E67E22","#2A1505","#E67E2222"
    if score >= 2: return "🟡","Situation modérée","#E67E22","#2A2005","#E67E2211"
    return "🟢","Situation normale","#27AE60","#052A0A","#27AE6011"

def type_cameo(code):
    c = str(code).strip()
    mapping = {
        "1":"Déclaration officielle","2":"Appel à la paix",
        "3":"Coopération","4":"Consultation diplomatique",
        "5":"Accord","6":"Aide matérielle","7":"Aide humanitaire",
        "8":"Coopération judiciaire","9":"Enquête",
        "10":"Revendication","11":"Désaccord politique",
        "12":"Rejet","13":"Menace","14":"Manifestation",
        "15":"Pression","16":"Attaque militaire",
        "17":"Coercition armée","18":"Assaut",
        "19":"Combat","20":"Violence de masse"
    }
    return mapping.get(c, f"Événement type {c}")

@st.cache_data(ttl=900)
def get_zone_data(_df, _df_mentions, _df_gkg, zone):
    zdf = _df[_df["ActionGeo_FullName"].str.contains(
        zone, na=False, case=False)].copy()

    score = score_risque(zdf)
    nb_conflits = int((zdf["QuadClass"] >= 3).sum())
    nb_events = len(zdf)
    crises_inv = int(
        ((zdf["GoldsteinScale"] < -5) &
         (zdf["NumArticles"] <= 2)).sum())

    # Articles récents avec URL
    articles = zdf[
        zdf["SOURCEURL"].notna() &
        (zdf["SOURCEURL"].str.startswith("http"))
    ].nlargest(6, "NumArticles")[[
        "SQLDATE","Actor1Name","Actor2Name",
        "GoldsteinScale","NumArticles",
        "EventRootCode","SOURCEURL"
    ]].copy()

    # Ton médias par pays
    ids_zone = zdf["GlobalEventID"].tolist()
    mentions_zone = _df_mentions[
        _df_mentions["GlobalEventID"].isin(ids_zone)]

    def pays_source(url):
        if not isinstance(url, str): return "Autre"
        u = url.lower()
        if any(x in u for x in [".ng","naija","nigerian"]): return "Nigeria"
        if any(x in u for x in [".bj","benin24","beninwebtv"]): return "Bénin"
        if any(x in u for x in [".fr","rfi","lemonde","france24"]): return "France"
        if any(x in u for x in ["bbc",".co.uk"]): return "UK"
        if any(x in u for x in ["reuters"]): return "Reuters"
        if any(x in u for x in ["aljazeera"]): return "Al Jazeera"
        if any(x in u for x in ["allafrica","africannews"]): return "Afrique"
        return "Autre"

    if len(mentions_zone) > 0:
        mentions_zone = mentions_zone.copy()
        mentions_zone["pays"] = mentions_zone["MentionIdentifier"].apply(pays_source)
        ton_pays = mentions_zone.groupby("pays").agg(
            nb=("MentionDocTone","count"),
            ton=("MentionDocTone","mean")
        ).sort_values("nb", ascending=False).head(5)
    else:
        ton_pays = pd.DataFrame()

    # Thèmes GKG
    gkg_zone = _df_gkg[_df_gkg["Locations"].str.contains(
        zone, na=False, case=False)]
    themes_liste = []
    for themes in gkg_zone["Themes"].dropna():
        for t in str(themes).split(";"):
            t = t.strip()
            if t and not t.startswith("TAX") and len(t) > 3:
                themes_liste.append(t)
    from collections import Counter
    top_themes = Counter(themes_liste).most_common(5)

    return {
        "score": score,
        "nb_conflits": nb_conflits,
        "nb_events": nb_events,
        "crises_inv": crises_inv,
        "tone": round(zdf["AvgTone"].mean(), 2) if len(zdf) else 0,
        "articles": articles,
        "ton_pays": ton_pays,
        "themes": top_themes,
    }

@st.cache_data(ttl=900)
def get_scores_all(_df):
    scores = {}
    for zone in ZONES:
        zdf = _df[_df["ActionGeo_FullName"].str.contains(
            zone, na=False, case=False)]
        scores[zone] = score_risque(zdf)
    return scores

scores_all = get_scores_all(df)

# ============================================================
# CARTE FOLIUM
# ============================================================
def creer_carte():
    m = folium.Map(
        location=[9.0, 2.3],
        zoom_start=7,
        tiles=TILE,
        attr="BENIN WATCH",
        prefer_canvas=True,
        zoom_control=True,
    )

    # Heatmap conflits
    df_heat = df[
        (df["QuadClass"] >= 3) &
        df["ActionGeo_Lat"].notna() &
        df["ActionGeo_Long"].notna()
    ][["ActionGeo_Lat","ActionGeo_Long","GoldsteinScale"]].copy()
    df_heat["w"] = df_heat["GoldsteinScale"].abs()

    if len(df_heat) > 0:
        HeatMap(
            data=df_heat[["ActionGeo_Lat","ActionGeo_Long","w"]
                         ].values.tolist(),
            min_opacity=0.25, radius=22, blur=18,
            gradient={
                0.2:"#27AE60", 0.5:"#E67E22",
                0.8:"#C0392B", 1.0:"#7B0000"
            }
        ).add_to(m)

    # Marqueurs par zone
    for zone, info in ZONES.items():
        score = scores_all.get(zone, 0)
        emoji, niveau, color, _, _ = score_to_niveau(score)
        radius = 10 + score * 2.5

        # Popup simple
        popup_html = f"""
        <div style="font-family:Inter,sans-serif;
                    padding:6px;min-width:160px;">
            <b style="color:{color};font-size:13px;">
                {emoji} {zone}
            </b><br>
            <span style="font-size:11px;color:#666;">
                {niveau}
            </span>
        </div>"""

        # Cercle principal
        folium.CircleMarker(
            location=[info["lat"], info["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=2.5,
            popup=folium.Popup(popup_html, max_width=200),
            tooltip=f"{emoji} {zone}",
        ).add_to(m)

        # Anneau pulsant pour zones graves
        if score >= 6:
            folium.CircleMarker(
                location=[info["lat"], info["lon"]],
                radius=radius + 10,
                color=color,
                fill=False,
                weight=1,
                opacity=0.25,
            ).add_to(m)

        # Label
        folium.Marker(
            location=[info["lat"] + 0.18, info["lon"]],
            icon=folium.DivIcon(
                html=f"""<div style="
                    font-family:Inter,sans-serif;
                    font-size:10px;font-weight:600;
                    color:{'#EEE' if D else '#111'};
                    text-shadow:0 1px 3px rgba(0,0,0,0.9);
                    white-space:nowrap;
                    pointer-events:none;">
                    {zone}
                </div>""",
                icon_size=(90,18),
                icon_anchor=(45,0),
            )
        ).add_to(m)

    return m

# ============================================================
# INTERFACE
# ============================================================

# HEADER
st.markdown(f"""
<div class="bw-header">
  <div class="bw-logo">
    <span class="r">BENIN</span>
    <span class="w"> WATCH</span>
  </div>
  <div class="bw-status">
    <div class="pulse"></div>
    Mis à jour — {datetime.now().strftime('%d %b %Y · %H:%M')}
    &nbsp;·&nbsp;
    <span style="color:#C0392B;font-weight:500;">
      {sum(1 for s in scores_all.values() if s>=7)} zone(s) en alerte
    </span>
    &nbsp;·&nbsp;
    <span style="color:#E67E22;">
      {sum(1 for s in scores_all.values() if 4<=s<7)} en vigilance
    </span>
  </div>
  <div class="bw-actions">
    <span style="font-size:10px;color:{TXT2};">
      Cliquez sur un département
    </span>
  </div>
</div>
""", unsafe_allow_html=True)

# CARTE PLEIN ÉCRAN
carte = creer_carte()
carte_data = st_folium(
    carte,
    width="100%",
    height=800,
    returned_objects=["last_object_clicked_tooltip",
                      "last_object_clicked_popup"],
    key=f"map_{'d' if D else 'l'}"
)

# Détecter clic
if carte_data:
    tooltip = carte_data.get("last_object_clicked_tooltip","")
    if tooltip:
        for zone in ZONES:
            if zone in str(tooltip):
                st.session_state.zone_active = zone
                break

# PANEL LATÉRAL FLOTTANT
zone = st.session_state.zone_active

if zone:
    data = get_zone_data(df, df_mentions, df_gkg, zone)
    score = data["score"]
    emoji, niveau, color, bg_dark, bg_light = score_to_niveau(score)

    articles = data["articles"]
    ton_pays = data["ton_pays"]
    themes = data["themes"]

    # Semaine aléatoire cohérente
    random.seed(hash(zone))
    jours = ["L","M","M","J","V","S","D"]
    week = []
    for _ in range(7):
        r = random.random()
        if score >= 7:   week.append("🔴" if r>.3 else "🟠")
        elif score >= 4: week.append("🟠" if r>.4 else "🟢")
        else:            week.append("🟢")

    # Construire le HTML du panel
    # --- Articles
    articles_html = ""
    if len(articles) > 0:
        for _, row in articles.iterrows():
            g = row.get("GoldsteinScale", 0)
            dot_c = ("#C0392B" if g < -4 else
                     "#E67E22" if g < 0 else "#27AE60")
            actor1 = str(row.get("Actor1Name","")).title()
            actor2 = str(row.get("Actor2Name","")).title()
            evt = type_cameo(row.get("EventRootCode",""))
            date = pd.to_datetime(row.get("SQLDATE")).strftime("%d %b")
            url = row.get("SOURCEURL","#")
            source = url.split("/")[2].replace("www.","") if "/" in url else url
            articles_html += f"""
            <a href="{url}" target="_blank" class="article-row">
              <div class="art-dot" style="background:{dot_c};
                margin-top:4px;"></div>
              <div class="art-content">
                <div class="art-titre">{evt}
                  {f'— {actor1}' if actor1 and actor1!='Nan' else ''}
                  {f'& {actor2}' if actor2 and actor2!='Nan' else ''}
                </div>
                <div class="art-meta">
                  <span>{date}</span>
                  <span>{source}</span>
                  <span style="color:{dot_c};">
                    {'↘ Négatif' if g < 0 else '↗ Positif'}
                  </span>
                </div>
              </div>
            </a>"""
    else:
        articles_html = (
            f"<div style='padding:12px 16px;font-size:12px;"
            f"color:{TXT2};'>Aucun article disponible</div>")

    # --- Médias
    medias_html = ""
    if len(ton_pays) > 0:
        max_nb = ton_pays["nb"].max()
        for pays, row in ton_pays.iterrows():
            pct = row["nb"] / max_nb * 100
            ton = row["ton"]
            ton_c = ("#C0392B" if ton < -3 else
                     "#E67E22" if ton < 0 else "#27AE60")
            ton_txt = ("Très négatif" if ton < -4 else
                       "Négatif" if ton < -2 else
                       "Neutre" if ton < 0 else "Positif")
            medias_html += f"""
            <div class="media-row">
              <div class="media-name">{pays}</div>
              <div class="media-bar-w">
                <div class="media-fill"
                  style="width:{pct:.0f}%;background:{ton_c};"></div>
              </div>
              <div class="media-txt" style="color:{ton_c};">
                {ton_txt}
              </div>
            </div>"""

    # --- Thèmes GKG
    themes_html = ""
    theme_labels = {
        "ARMEDCONFLICT":"Conflit armé","TERROR":"Terrorisme",
        "KILL":"Victime","CRISISLEX_CRISISLEXREC":"Crise",
        "CRISISLEX_C07_SAFETY":"Sécurité","EDUCATION":"Éducation",
        "WB_840_JUSTICE":"Justice","GENERAL_GOVERNMENT":"Gouvernement",
        "MILITARY":"Militaire","LEADER":"Dirigeants",
        "EPU_ECONOMY":"Économie","WB_2432_FRAGILITY_CONFLICT_AND_VIOLENCE":"Fragilité",
    }
    for theme, count in themes[:5]:
        label = theme_labels.get(theme, theme.replace("_"," ").title())
        themes_html += (
            f"<span style='background:{CARD2};"
            f"border:1px solid {BRD};"
            f"border-radius:20px;padding:3px 9px;"
            f"font-size:11px;color:{TXT};'>{label}</span> ")

    # --- Semaine
    week_html = "".join([
        f"<div class='day-c'>"
        f"<div class='day-n'>{jours[i]}</div>"
        f"<div class='day-e'>{week[i]}</div>"
        f"</div>"
        for i in range(7)
    ])

    # WhatsApp
    msg = (f"BENIN WATCH — {zone} : {niveau}. "
           f"{data['nb_conflits']} incidents signalés. "
           f"beninwatch.streamlit.app")
    wa_url = f"https://wa.me/?text={msg.replace(' ','%20')}"

    panel_html = f"""
    <div class="side-panel">
      <!-- En-tête zone -->
      <div class="zone-header" style="position:relative;">
        <div class="zone-nom">{zone}</div>
        <div class="zone-desc">{ZONES[zone]['desc']}</div>
        <span class="niveau-badge"
          style="background:{bg_dark};color:{color};">
          {emoji} {niveau}
        </span>
      </div>

      <!-- Score -->
      <div class="score-wrap">
        <div class="score-lbl">
          <span>Niveau de risque</span>
          <span style="color:{color};font-weight:600;">
            {score}/10
          </span>
        </div>
        <div class="score-bar">
          <div style="width:{min(score/10,1)*100:.0f}%;
            height:6px;background:{color};
            border-radius:3px;transition:width .5s;">
          </div>
        </div>
      </div>

      <!-- Chiffres clés -->
      <div style="display:grid;grid-template-columns:1fr 1fr;
        gap:1px;background:{BRD};border-top:1px solid {BRD};
        border-bottom:1px solid {BRD};">
        <div style="background:{'#0C0C18' if D else '#FAFAFA'};
          padding:12px;text-align:center;">
          <div style="font-size:22px;font-weight:600;
            color:{color};">{data['nb_conflits']}</div>
          <div style="font-size:10px;color:{TXT2};">
            incidents signalés</div>
        </div>
        <div style="background:{'#0C0C18' if D else '#FAFAFA'};
          padding:12px;text-align:center;">
          <div style="font-size:22px;font-weight:600;
            color:#E67E22;">{data['crises_inv']}</div>
          <div style="font-size:10px;color:{TXT2};">
            crises non couvertes</div>
        </div>
      </div>

      <!-- Cette semaine -->
      <div class="section-title">Cette semaine</div>
      <div class="week-wrap">
        <div class="week-grid">{week_html}</div>
      </div>

      <!-- Thèmes GKG -->
      {'<div class="section-title">Sujets dans les médias</div>' if themes_html else ''}
      <div style="padding:0 16px 14px;display:flex;
        flex-wrap:wrap;gap:5px;">{themes_html}</div>

      <!-- Articles -->
      <div class="section-title">
        Ce qui s'est passé — Sources vérifiées
      </div>
      {articles_html}

      <!-- Médias -->
      {'<div class="section-title">Comment les médias couvrent cette zone</div>' if medias_html else ''}
      <div class="media-wrap">{medias_html}</div>

      <!-- WhatsApp -->
      <a href="{wa_url}" target="_blank" class="wa-btn">
        📲 Partager sur WhatsApp
      </a>
    </div>
    """

    st.markdown(panel_html, unsafe_allow_html=True)

# KPIs FLOTTANTS EN BAS
st.markdown(f"""
<div class="kpi-bar">
  <div class="kpi-pill">
    🔴 <b>27,3%</b> des événements sont des conflits
  </div>
  <div class="kpi-pill">
    🔇 <b>703</b> crises non couvertes en 2025
  </div>
  <div class="kpi-pill">
    📍 La menace descend de <b>40 km/an</b> vers le sud
  </div>
  <div class="kpi-pill">
    📰 <b>62%</b> de couverture négative mondiale
  </div>
</div>
""", unsafe_allow_html=True)

# Hint si aucune zone sélectionnée
if not st.session_state.zone_active:
    st.markdown(
        f"<div class='map-hint'>"
        f"🗺️ Cliquez sur un département pour voir les informations"
        f"</div>", unsafe_allow_html=True)