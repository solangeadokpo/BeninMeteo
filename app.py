# ============================================================
# BENIN WATCH — app.py — Version Citoyenne
# ============================================================

import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from datetime import datetime
from collections import Counter
import random

st.set_page_config(
    page_title="BENIN WATCH",
    page_icon="🇧🇯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True
if "zone_active" not in st.session_state:
    st.session_state.zone_active = None

def toggle_mode():
    st.session_state.dark_mode = not st.session_state.dark_mode

D = st.session_state.dark_mode
BG   = "#080810" if D else "#F0F0F8"
CARD = "#0F0F1A" if D else "#FFFFFF"
C2   = "#13131A" if D else "#F5F5FA"
BRD  = "#1A1A30" if D else "#DDDDEE"
TXT  = "#CCCCDD" if D else "#1A1A2E"
TXT2 = "#7777AA" if D else "#666688"
TILE = "CartoDB dark_matter" if D else "CartoDB positron"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
*{{font-family:'Inter',sans-serif;box-sizing:border-box;margin:0;padding:0;}}
.stApp{{background:{BG};}}
.stApp header,.stDecoration{{display:none !important;}}
#MainMenu,footer{{display:none;}}
.block-container{{padding:0 !important;max-width:100% !important;}}
section[data-testid="stSidebar"]{{display:none;}}
div[data-testid="stVerticalBlock"]{{gap:0 !important;}}
.element-container{{margin:0 !important;padding:0 !important;}}

.bw-header{{
    position:fixed;top:0;left:0;right:0;height:50px;
    background:{CARD}DD;backdrop-filter:blur(12px);
    border-bottom:1px solid {BRD};
    display:flex;align-items:center;justify-content:space-between;
    padding:0 18px;z-index:1000;
}}
.bw-logo{{font-size:15px;font-weight:600;letter-spacing:3px;}}
.bw-logo .r{{color:#C0392B;}}
.bw-logo .w{{color:{TXT};}}
.bw-live{{font-size:11px;color:{TXT2};display:flex;align-items:center;gap:6px;}}
.dot{{width:6px;height:6px;border-radius:50%;background:#27AE60;
    animation:bl 1.5s infinite;}}
@keyframes bl{{0%,100%{{opacity:1}}50%{{opacity:.2}}}}

.panel{{
    position:fixed;top:62px;right:10px;
    width:340px;max-height:calc(100vh - 74px);
    background:{CARD}F0;backdrop-filter:blur(20px);
    border:1px solid {BRD};border-radius:14px;
    overflow-y:auto;z-index:500;
    box-shadow:0 8px 40px rgba(0,0,0,.5);
}}
.panel::-webkit-scrollbar{{width:3px;}}
.panel::-webkit-scrollbar-thumb{{background:{BRD};border-radius:2px;}}

.p-zone-header{{padding:14px 16px;border-bottom:1px solid {BRD};}}
.p-zone-name{{font-size:17px;font-weight:600;color:{TXT};margin-bottom:2px;}}
.p-zone-sub{{font-size:11px;color:{TXT2};}}

.p-section{{padding:10px 16px;border-bottom:1px solid {BRD};}}
.p-section-title{{
    font-size:10px;color:{TXT2};
    text-transform:uppercase;letter-spacing:1px;
    margin-bottom:8px;font-weight:500;
}}

.article-card{{
    background:{C2};border-radius:8px;
    padding:10px 12px;margin-bottom:7px;
    border-left:3px solid {BRD};
}}
.article-card.negatif{{border-left-color:#C0392B;}}
.article-card.neutre{{border-left-color:#E67E22;}}
.article-card.positif{{border-left-color:#27AE60;}}
.art-type{{
    font-size:10px;font-weight:600;
    text-transform:uppercase;letter-spacing:0.5px;
    margin-bottom:4px;
}}
.art-desc{{font-size:12px;color:{TXT};line-height:1.5;margin-bottom:5px;}}
.art-source{{
    font-size:10px;color:{TXT2};
    display:flex;justify-content:space-between;
}}
.art-link{{
    font-size:10px;color:#4A9EFF;text-decoration:none;
}}
.art-link:hover{{text-decoration:underline;}}

.media-item{{
    display:flex;align-items:center;gap:8px;margin-bottom:8px;
}}
.media-flag{{font-size:14px;min-width:20px;}}
.media-name{{font-size:12px;color:{TXT};min-width:80px;}}
.media-bar-bg{{flex:1;background:{BRD};border-radius:3px;height:5px;}}
.media-bar-fill{{height:5px;border-radius:3px;}}
.media-ton{{font-size:11px;font-weight:500;min-width:70px;text-align:right;}}

.theme-tag{{
    display:inline-block;
    background:{C2};border:1px solid {BRD};
    border-radius:12px;padding:3px 9px;
    font-size:11px;color:{TXT};margin:2px;
}}
.theme-tag.actif{{
    background:#1A1A30;border-color:#4444AA;color:#9999FF;
}}

.alerte-box{{
    background:#1A0505;border:1px solid #C0392B;
    border-radius:8px;padding:10px 12px;
    font-size:12px;color:#E24B4A;margin-bottom:8px;
    display:flex;gap:8px;align-items:flex-start;
}}

.wa-btn{{
    display:block;margin:12px 16px 14px;text-align:center;
    background:{'#1A3A1A' if D else '#E8F5E9'};
    color:#27AE60;padding:9px;border-radius:10px;
    font-size:12px;text-decoration:none;font-weight:500;
    border:1px solid {'#2A5A2A' if D else '#A5D6A7'};
}}

.hint{{
    position:fixed;bottom:16px;left:50%;
    transform:translateX(-50%);
    background:{CARD}EE;backdrop-filter:blur(10px);
    border:1px solid {BRD};border-radius:20px;
    padding:7px 18px;font-size:11px;color:{TXT2};
    z-index:100;pointer-events:none;
    white-space:nowrap;
}}
</style>
""", unsafe_allow_html=True)

# ============================================================
# DONNÉES
# ============================================================
@st.cache_data(ttl=900)
def charger_donnees():
    df = pd.read_csv("data/gdelt_benin_2025_clean.csv", low_memory=False)
    df_mentions = pd.read_csv("data/gdelt_benin_2025_mentions.csv", low_memory=False)
    df_gkg = pd.read_csv("data/gdelt_benin_2025_gkg.csv", low_memory=False)

    for col in ["GoldsteinScale","AvgTone","NumArticles",
                "QuadClass","ActionGeo_Lat","ActionGeo_Long"]:
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
# ZONES
# ============================================================
ZONES = {
    "Alibori":    {"lat":11.50,"lon":2.80,"desc":"Nord-est"},
    "Atakora":    {"lat":10.50,"lon":1.40,"desc":"Nord-ouest"},
    "Borgou":     {"lat": 9.80,"lon":2.70,"desc":"Centre-nord · Parakou"},
    "Donga":      {"lat": 9.50,"lon":1.70,"desc":"Centre-ouest"},
    "Collines":   {"lat": 8.50,"lon":2.30,"desc":"Centre · Savalou"},
    "Plateau":    {"lat": 7.80,"lon":2.60,"desc":"Est"},
    "Zou":        {"lat": 7.30,"lon":2.00,"desc":"Sud-centre · Abomey"},
    "Couffo":     {"lat": 7.10,"lon":1.70,"desc":"Sud-ouest"},
    "Ouémé":      {"lat": 6.80,"lon":2.50,"desc":"Sud-est · Porto-Novo"},
    "Mono":       {"lat": 6.80,"lon":1.60,"desc":"Sud · Frontière Togo"},
    "Atlantique": {"lat": 6.50,"lon":2.20,"desc":"Sud · Côte"},
    "Littoral":   {"lat": 6.35,"lon":2.43,"desc":"Cotonou"},
}

# ============================================================
# TRADUCTIONS — le cœur du système
# ============================================================

# Types d'événements en français CITOYEN
CAMEO_CITOYEN = {
    "1":  ("📢","Déclaration publique","Le gouvernement ou une organisation a fait une annonce officielle."),
    "2":  ("🕊️","Appel au dialogue","Des acteurs appellent à la paix ou à la discussion."),
    "3":  ("🤝","Accord de coopération","Un accord ou un partenariat a été signé."),
    "4":  ("🗣️","Consultation diplomatique","Des responsables se sont rencontrés pour discuter."),
    "5":  ("✅","Accord conclu","Un accord important a été finalisé."),
    "6":  ("🎁","Aide accordée","Une aide matérielle ou financière a été annoncée."),
    "7":  ("🏥","Aide humanitaire","Une aide humanitaire a été mobilisée."),
    "8":  ("⚖️","Action judiciaire","Une décision ou action judiciaire a eu lieu."),
    "9":  ("🔍","Enquête ouverte","Une enquête a été lancée."),
    "10": ("📣","Revendication","Un groupe exprime une demande ou une revendication."),
    "11": ("🗳️","Désaccord politique","Un désaccord entre acteurs politiques a été signalé."),
    "12": ("🚫","Rejet","Une proposition ou demande a été rejetée."),
    "13": ("⚠️","Avertissement","Un avertissement ou une mise en garde a été émis."),
    "14": ("✊","Manifestation","Une manifestation ou protestation a eu lieu."),
    "15": ("📵","Pression exercée","Une pression politique ou économique est signalée."),
    "16": ("🪖","Opération militaire","Une opération ou action militaire a été menée."),
    "17": ("🔒","Arrestation","Une arrestation ou détention a eu lieu."),
    "18": ("💥","Incident violent","Un incident violent a été signalé."),
    "19": ("⚔️","Affrontement","Des affrontements ont eu lieu."),
    "20": ("🚨","Violence grave","Un acte de violence grave a été signalé."),
}

# Thèmes GKG → français citoyen
THEMES_CITOYEN = {
    "EDUCATION":              "Éducation",
    "HEALTH":                 "Santé",
    "WB_840_JUSTICE":         "Justice",
    "ECONOMY":                "Économie",
    "EPU_ECONOMY":            "Économie",
    "TOURISM":                "Tourisme",
    "AGRICULTURE":            "Agriculture",
    "ENVIRONMENT":            "Environnement",
    "GENERAL_GOVERNMENT":     "Gouvernement",
    "LEADER":                 "Politique",
    "MILITARY":               "Armée",
    "ARMEDCONFLICT":          "Conflit armé",
    "TERROR":                 "Terrorisme",
    "KILL":                   "Violence",
    "CRISISLEX_C07_SAFETY":   "Sécurité",
    "CRISISLEX_CRISISLEXREC": "Crise",
    "MEDIA_MSM":              "Médias",
    "ELECTION":               "Élections",
    "CORRUPTION":             "Corruption",
    "HUMAN_RIGHTS":           "Droits humains",
    "WB_696_PUBLIC_SECTOR":   "Service public",
    "INFRASTRUCTURE":         "Infrastructures",
    "EPU_POLICY_GOVERNMENT":  "Politique publique",
    "WB_2432_FRAGILITY_CONFLICT_AND_VIOLENCE": "Instabilité",
}

# Pays sources → drapeau + nom
PAYS_SOURCES = {
    "Nigeria":    ("🇳🇬","Nigeria"),
    "Bénin":      ("🇧🇯","Bénin"),
    "France":     ("🇫🇷","France"),
    "UK":         ("🇬🇧","Royaume-Uni"),
    "Reuters":    ("📡","Reuters"),
    "Al Jazeera": ("📺","Al Jazeera"),
    "USA":        ("🇺🇸","États-Unis"),
    "Afrique":    ("🌍","Afrique"),
    "Autre":      ("🌐","International"),
}

def classifier_pays(url):
    if not isinstance(url, str): return "Autre"
    u = url.lower()
    if any(x in u for x in [".ng","naija","nigerian"]): return "Nigeria"
    if any(x in u for x in [".bj","benin24","beninwebtv","matinlibre"]): return "Bénin"
    if any(x in u for x in [".fr","rfi","lemonde","france24"]): return "France"
    if any(x in u for x in ["bbc",".co.uk","theguardian"]): return "UK"
    if any(x in u for x in ["reuters"]): return "Reuters"
    if any(x in u for x in ["aljazeera"]): return "Al Jazeera"
    if any(x in u for x in ["allafrica","africannews"]): return "Afrique"
    if any(x in u for x in ["yahoo","cnn","washington","nytimes"]): return "USA"
    return "Autre"

def ton_texte_court(tone):
    if tone <= -4: return ("En parle très négativement","#C0392B")
    if tone <= -2: return ("Couverture négative","#E67E22")
    if tone <=  0: return ("Couverture neutre","#8888AA")
    return ("Couverture positive","#27AE60")

def score_zone(zdf):
    if len(zdf) == 0: return 0
    taux = (zdf["QuadClass"] >= 3).mean()
    gold = abs(zdf["GoldsteinScale"].mean())
    nb   = min(len(zdf) / 200, 1)
    return round((taux*4 + gold*0.3 + nb*3), 1)

def niveau_zone(score):
    if score >= 7: return "🔴","#C0392B"
    if score >= 4: return "🟠","#E67E22"
    if score >= 2: return "🟡","#E6A817"
    return "🟢","#27AE60"

# ============================================================
# CALCUL SCORES GLOBAUX
# ============================================================
@st.cache_data(ttl=900)
def tous_scores(_df):
    s = {}
    for zone in ZONES:
        zdf = _df[_df["ActionGeo_FullName"].str.contains(
            zone, na=False, case=False)]
        s[zone] = score_zone(zdf)
    return s

scores_all = tous_scores(df)

# ============================================================
# DONNÉES PAR ZONE — version citoyenne
# ============================================================
@st.cache_data(ttl=900)
def donnees_zone(_df, _df_mentions, _df_gkg, zone):

    zdf = _df[_df["ActionGeo_FullName"].str.contains(
        zone, na=False, case=False)].copy()

    # Score et stats de base
    score = score_zone(zdf)
    nb_events = len(zdf)

    # ---- ÉVÉNEMENTS TRADUITS EN FRANÇAIS CITOYEN ----
    # On prend les plus significatifs (les plus couverts)
    evenements = []
    if len(zdf) > 0:
        top = zdf[zdf["SOURCEURL"].notna()].nlargest(8, "NumArticles")
        for _, row in top.iterrows():
            code = str(row.get("EventRootCode","")).strip()
            emoji, type_evt, description = CAMEO_CITOYEN.get(
                code, ("📌","Événement","Un événement a été signalé dans cette zone."))
            g = row.get("GoldsteinScale", 0)
            tone_class = "negatif" if g < -2 else "neutre" if g < 1 else "positif"
            url = row.get("SOURCEURL","")
            source = url.split("/")[2].replace("www.","") if url.startswith("http") else ""
            date = ""
            try:
                date = pd.to_datetime(row["SQLDATE"]).strftime("%d %b")
            except: pass
            pays = classifier_pays(url)

            evenements.append({
                "emoji":       emoji,
                "type":        type_evt,
                "description": description,
                "tone_class":  tone_class,
                "url":         url,
                "source":      source,
                "date":        date,
                "pays":        pays,
            })

    # ---- COMMENT LES MÉDIAS COUVRENT CETTE ZONE ----
    ids_zone = zdf["GlobalEventID"].tolist()
    mentions_zone = _df_mentions[
        _df_mentions["GlobalEventID"].isin(ids_zone)].copy()

    medias = []
    if len(mentions_zone) > 0:
        mentions_zone["pays"] = mentions_zone["MentionIdentifier"].apply(
            classifier_pays)
        ton_pays = mentions_zone.groupby("pays").agg(
            nb=("MentionDocTone","count"),
            ton=("MentionDocTone","mean")
        ).sort_values("nb", ascending=False).head(5)
        max_nb = ton_pays["nb"].max()
        for pays, row in ton_pays.iterrows():
            txt, color = ton_texte_court(row["ton"])
            flag, nom = PAYS_SOURCES.get(pays, ("🌐", pays))
            medias.append({
                "flag":  flag,
                "nom":   nom,
                "pct":   row["nb"] / max_nb * 100,
                "txt":   txt,
                "color": color,
                "nb":    int(row["nb"]),
            })

    # ---- THÈMES DE LA ZONE ----
    gkg_zone = _df_gkg[_df_gkg["Locations"].str.contains(
        zone, na=False, case=False)]
    themes_bruts = []
    for themes in gkg_zone["Themes"].dropna():
        for t in str(themes).split(";"):
            t = t.strip()
            if t in THEMES_CITOYEN:
                themes_bruts.append(THEMES_CITOYEN[t])
    themes_comptes = Counter(themes_bruts).most_common(6)

    # ---- PERSONNES CITÉES ----
    personnes = []
    for persons in gkg_zone["Persons"].dropna():
        for p in str(persons).split(";"):
            p = p.strip().title()
            if p and len(p) > 3:
                personnes.append(p)
    top_personnes = [p for p,_ in Counter(personnes).most_common(4)]

    # ---- ALERTE SI ZONE À RISQUE ----
    alerte = None
    if score >= 6:
        alerte = "Des incidents sécuritaires ont été signalés dans cette zone. Soyez prudent dans vos déplacements."
    elif score >= 4:
        alerte = "La situation dans cette zone mérite attention. Restez informé via les sources officielles."

    return {
        "score":      score,
        "nb_events":  nb_events,
        "evenements": evenements,
        "medias":     medias,
        "themes":     themes_comptes,
        "personnes":  top_personnes,
        "alerte":     alerte,
    }

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
    )

    # Heatmap activité générale
    df_heat = df[
        df["ActionGeo_Lat"].notna() &
        df["ActionGeo_Long"].notna()
    ][["ActionGeo_Lat","ActionGeo_Long","NumArticles"]].copy()
    df_heat["NumArticles"] = pd.to_numeric(
        df_heat["NumArticles"], errors="coerce").fillna(1)

    if len(df_heat) > 0:
        HeatMap(
            data=df_heat[["ActionGeo_Lat","ActionGeo_Long","NumArticles"]
                         ].values.tolist(),
            min_opacity=0.2, radius=20, blur=16,
            gradient={
                0.2:"#27AE60", 0.5:"#E67E22",
                0.8:"#C0392B", 1.0:"#7B0000"
            }
        ).add_to(m)

    # Marqueurs
    for zone, info in ZONES.items():
        score = scores_all.get(zone, 0)
        emoji, color = niveau_zone(score)
        radius = 9 + score * 2

        popup_html = (
            f'<div style="font-family:Inter,sans-serif;'
            f'padding:6px;min-width:140px;">'
            f'<b style="color:{color};font-size:13px;">'
            f'{emoji} {zone}</b><br>'
            f'<span style="font-size:11px;color:#666;">'
            f'{info["desc"]}</span></div>'
        )

        folium.CircleMarker(
            location=[info["lat"], info["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            weight=2,
            popup=folium.Popup(popup_html, max_width=200),
            tooltip=f"{emoji} {zone}",
        ).add_to(m)

        # Anneau pour zones actives
        if score >= 5:
            folium.CircleMarker(
                location=[info["lat"], info["lon"]],
                radius=radius + 9,
                color=color,
                fill=False,
                weight=1,
                opacity=0.2,
            ).add_to(m)

        # Label
        folium.Marker(
            location=[info["lat"]+0.17, info["lon"]],
            icon=folium.DivIcon(
                html=(
                    f'<div style="font-family:Inter,sans-serif;'
                    f'font-size:10px;font-weight:600;'
                    f'color:{"#EEE" if D else "#111"};'
                    f'text-shadow:0 1px 3px rgba(0,0,0,.9);'
                    f'white-space:nowrap;pointer-events:none;">'
                    f'{zone}</div>'
                ),
                icon_size=(90,18),
                icon_anchor=(45,0),
            )
        ).add_to(m)

    return m

# ============================================================
# HEADER
# ============================================================
nb_alertes = sum(1 for s in scores_all.values() if s >= 7)
nb_vigil   = sum(1 for s in scores_all.values() if 4 <= s < 7)

col_h1, col_h2, col_h3 = st.columns([2,4,2])
with col_h1:
    st.markdown(
        f'<div class="bw-logo" style="padding:14px 18px;">'
        f'<span class="r">BENIN</span>'
        f'<span class="w"> WATCH</span></div>',
        unsafe_allow_html=True)
with col_h2:
    statut = ""
    if nb_alertes > 0:
        statut = (f'&nbsp;·&nbsp;'
                  f'<span style="color:#C0392B;font-weight:500;">'
                  f'⚠️ {nb_alertes} zone(s) à surveiller</span>')
    st.markdown(
        f'<div class="bw-live" style="padding:16px 0;">'
        f'<div class="dot"></div>'
        f'Bénin · {datetime.now().strftime("%d %B %Y")}'
        f'{statut}</div>',
        unsafe_allow_html=True)
with col_h3:
    mode_lbl = "☀️ Mode clair" if D else "🌙 Mode sombre"
    st.button(mode_lbl, on_click=toggle_mode)

st.divider()

# ============================================================
# CARTE + PANEL
# ============================================================
col_carte, col_panel = st.columns([3, 2])

with col_carte:
    carte = creer_carte()
    carte_data = st_folium(
        carte,
        width="100%",
        height=600,
        returned_objects=["last_object_clicked_tooltip"],
        key=f"map_{'d' if D else 'l'}"
    )
    if carte_data:
        tt = carte_data.get("last_object_clicked_tooltip","")
        for zone in ZONES:
            if zone in str(tt):
                st.session_state.zone_active = zone
                break

with col_panel:

    if not st.session_state.zone_active:
        st.markdown(
            f'<div style="height:400px;display:flex;'
            f'align-items:center;justify-content:center;'
            f'flex-direction:column;gap:12px;color:{TXT2};">'
            f'<div style="font-size:32px;">🗺️</div>'
            f'<div style="font-size:14px;">Cliquez sur un département</div>'
            f'<div style="font-size:12px;">pour voir les informations</div>'
            f'</div>',
            unsafe_allow_html=True)
    else:
        zone = st.session_state.zone_active
        with st.spinner(f"Chargement — {zone}..."):
            data = donnees_zone(df, df_mentions, df_gkg, zone)

        score = data["score"]
        emoji_niv, color = niveau_zone(score)

        # ---- EN-TÊTE ZONE ----
        st.markdown(
            f'<div style="background:{CARD};border:1px solid {BRD};'
            f'border-radius:12px;padding:14px 16px;margin-bottom:10px;">'
            f'<div style="font-size:18px;font-weight:600;'
            f'color:{TXT};margin-bottom:2px;">{zone}</div>'
            f'<div style="font-size:11px;color:{TXT2};margin-bottom:8px;">'
            f'{ZONES[zone]["desc"]}</div>'
            f'<span style="background:{color}22;color:{color};'
            f'border:1px solid {color}44;border-radius:20px;'
            f'padding:3px 10px;font-size:12px;font-weight:500;">'
            f'{emoji_niv} Activité {"élevée" if score>=7 else "modérée" if score>=4 else "normale"}'
            f'</span>'
            f'</div>',
            unsafe_allow_html=True)

        # ---- ALERTE SI NÉCESSAIRE ----
        if data["alerte"]:
            st.markdown(
                f'<div class="alerte-box">'
                f'<span>⚠️</span>'
                f'<span>{data["alerte"]}</span>'
                f'</div>',
                unsafe_allow_html=True)

        # ---- THÈMES DE LA SEMAINE ----
        if data["themes"]:
            st.markdown(
                f'<div style="font-size:10px;color:{TXT2};'
                f'text-transform:uppercase;letter-spacing:1px;'
                f'margin-bottom:6px;font-weight:500;">'
                f'De quoi parle-t-on dans cette zone ?</div>',
                unsafe_allow_html=True)
            tags = ""
            for theme, _ in data["themes"]:
                tags += (f'<span class="theme-tag">{theme}</span>')
            st.markdown(
                f'<div style="margin-bottom:12px;">{tags}</div>',
                unsafe_allow_html=True)

        # ---- CE QUI S'EST PASSÉ ----
        st.markdown(
            f'<div style="font-size:10px;color:{TXT2};'
            f'text-transform:uppercase;letter-spacing:1px;'
            f'margin-bottom:8px;font-weight:500;">'
            f'Ce qui s\'est passé dans cette zone</div>',
            unsafe_allow_html=True)

        if data["evenements"]:
            for evt in data["evenements"][:5]:
                tone_color = (
                    "#C0392B" if evt["tone_class"]=="negatif" else
                    "#E67E22" if evt["tone_class"]=="neutre" else
                    "#27AE60")

                # Utiliser les composants Streamlit natifs
                with st.container():
                    st.markdown(
                        f'<div style="background:{C2};'
                        f'border-left:3px solid {tone_color};'
                        f'border-radius:0 8px 8px 0;'
                        f'padding:10px 12px;margin-bottom:7px;">'
                        f'<div style="font-size:11px;font-weight:600;'
                        f'color:{tone_color};margin-bottom:4px;">'
                        f'{evt["emoji"]} {evt["type"]}</div>'
                        f'<div style="font-size:12px;color:{TXT};'
                        f'line-height:1.5;margin-bottom:5px;">'
                        f'{evt["description"]}</div>'
                        f'<div style="display:flex;justify-content:space-between;'
                        f'align-items:center;">'
                        f'<span style="font-size:10px;color:{TXT2};">'
                        f'{evt["date"]} · {evt["source"]}</span>'
                        f'{"<a href=" + repr(evt["url"]) + " target=_blank style=font-size:10px;color:#4A9EFF;text-decoration:none;>Lire l\'article →</a>" if evt["url"].startswith("http") else ""}'
                        f'</div></div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div style="color:{TXT2};font-size:12px;'
                f'padding:10px 0;">Aucun événement disponible.</div>',
                unsafe_allow_html=True)

        # ---- CE QUE LES MÉDIAS DISENT ----
        if data["medias"]:
            st.markdown(
                f'<div style="font-size:10px;color:{TXT2};'
                f'text-transform:uppercase;letter-spacing:1px;'
                f'margin:12px 0 8px;font-weight:500;">'
                f'Ce que les médias disent de cette zone</div>',
                unsafe_allow_html=True)

            for m in data["medias"]:
                st.markdown(
                    f'<div style="display:flex;align-items:center;'
                    f'gap:8px;margin-bottom:8px;">'
                    f'<span style="font-size:14px;">{m["flag"]}</span>'
                    f'<span style="font-size:12px;color:{TXT};'
                    f'min-width:90px;">{m["nom"]}</span>'
                    f'<div style="flex:1;background:{BRD};'
                    f'border-radius:3px;height:5px;overflow:hidden;">'
                    f'<div style="width:{m["pct"]:.0f}%;height:5px;'
                    f'background:{m["color"]};border-radius:3px;"></div>'
                    f'</div>'
                    f'<span style="font-size:10px;color:{m["color"]};'
                    f'min-width:90px;text-align:right;font-weight:500;">'
                    f'{m["txt"]}</span>'
                    f'</div>',
                    unsafe_allow_html=True)

        # ---- PERSONNES CITÉES ----
        if data["personnes"]:
            st.markdown(
                f'<div style="font-size:10px;color:{TXT2};'
                f'text-transform:uppercase;letter-spacing:1px;'
                f'margin:12px 0 6px;font-weight:500;">'
                f'Personnes citées dans les articles</div>',
                unsafe_allow_html=True)
            personnes_html = " ".join([
                f'<span style="background:{C2};border:1px solid {BRD};'
                f'border-radius:12px;padding:3px 9px;'
                f'font-size:11px;color:{TXT};">{p}</span>'
                for p in data["personnes"]
            ])
            st.markdown(
                f'<div style="margin-bottom:12px;">{personnes_html}</div>',
                unsafe_allow_html=True)

        # ---- WHATSAPP ----
        msg = (f"BENIN WATCH · {zone} — "
               f'{"⚠️ Situation à surveiller" if score>=4 else "✅ Situation normale"}. '
               f"Ce qui se passe : beninwatch.streamlit.app")
        wa_url = f"https://wa.me/?text={msg.replace(' ','%20')}"
        st.markdown(
            f'<a href="{wa_url}" target="_blank" '
            f'style="display:block;margin-top:14px;'
            f'text-align:center;'
            f'background:{"#1A3A1A" if D else "#E8F5E9"};'
            f'color:#27AE60;padding:9px;border-radius:10px;'
            f'font-size:12px;text-decoration:none;font-weight:500;'
            f'border:1px solid {"#2A5A2A" if D else "#A5D6A7"};">'
            f'📲 Partager sur WhatsApp</a>',
            unsafe_allow_html=True)

# Hint
if not st.session_state.zone_active:
    st.markdown(
        f'<div class="hint">'
        f'🗺️ Cliquez sur un département pour voir ce qui s\'y passe'
        f'</div>',
        unsafe_allow_html=True)