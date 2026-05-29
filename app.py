# ============================================================
# BENIN WATCH — app.py — Carte plein écran vraie
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

D    = st.session_state.dark_mode
BG   = "#080810" if D else "#F0F0F8"
CARD = "#0F0F1A" if D else "#FFFFFF"
C2   = "#13131A" if D else "#F5F5FA"
BRD  = "#1A1A30" if D else "#DDDDEE"
TXT  = "#CCCCDD" if D else "#1A1A2E"
TXT2 = "#7777AA" if D else "#666688"
TILE = "CartoDB dark_matter" if D else "CartoDB positron"

# CSS — tout en fixed, zéro padding Streamlit
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
*, *::before, *::after {{
    font-family: 'Inter', sans-serif;
    box-sizing: border-box;
}}

/* ── Supprime TOUT l'habillage Streamlit ── */
.stApp {{ background: {BG}; overflow: hidden; }}
.stApp > header {{ display: none !important; }}
#MainMenu, footer, .stDeployButton {{ display: none !important; }}
.block-container {{
    padding: 0 !important;
    margin: 0 !important;
    max-width: 100vw !important;
}}
section[data-testid="stSidebar"] {{ display: none !important; }}
div[data-testid="stVerticalBlock"] {{ gap: 0 !important; }}
div[data-testid="stHorizontalBlock"] {{ gap: 0 !important; }}
.element-container {{ margin: 0 !important; padding: 0 !important; }}
div[data-testid="stToolbar"] {{ display: none !important; }}

/* ── Header fixe ── */
#bw-header {{
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 48px;
    background: {CARD}EE;
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border-bottom: 1px solid {BRD};
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 16px;
    z-index: 9999;
}}
.bw-logo {{
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 3px;
}}
.bw-logo .r {{ color: #C0392B; }}
.bw-logo .w {{ color: {TXT}; }}
.bw-live {{
    font-size: 11px;
    color: {TXT2};
    display: flex;
    align-items: center;
    gap: 6px;
}}
.dot {{
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #27AE60;
    animation: bl 1.5s infinite;
    flex-shrink: 0;
}}
@keyframes bl {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.2; }}
}}

/* ── Carte couvre tout sauf le header ── */
#bw-map {{
    position: fixed;
    top: 48px; left: 0; right: 0; bottom: 0;
    z-index: 1;
}}
#bw-map iframe {{
    width: 100% !important;
    height: 100% !important;
    border: none !important;
    display: block;
}}

/* Force streamlit_folium à remplir l'espace */
.stfolium-container {{
    position: fixed !important;
    top: 48px !important;
    left: 0 !important;
    right: 0 !important;
    bottom: 0 !important;
    width: 100vw !important;
    height: calc(100vh - 48px) !important;
}}

/* ── Panel latéral flottant ── */
#bw-panel {{
    position: fixed;
    top: 58px;
    right: 10px;
    width: 330px;
    max-height: calc(100vh - 68px);
    background: {CARD}F2;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid {BRD};
    border-radius: 14px;
    overflow-y: auto;
    z-index: 9998;
    box-shadow: 0 8px 40px rgba(0,0,0,0.5);
    scrollbar-width: thin;
    scrollbar-color: {BRD} transparent;
}}
#bw-panel::-webkit-scrollbar {{
    width: 3px;
}}
#bw-panel::-webkit-scrollbar-thumb {{
    background: {BRD};
    border-radius: 2px;
}}

/* ── Hint bas de page ── */
#bw-hint {{
    position: fixed;
    bottom: 14px;
    left: 50%;
    transform: translateX(-50%);
    background: {CARD}EE;
    backdrop-filter: blur(10px);
    border: 1px solid {BRD};
    border-radius: 20px;
    padding: 7px 18px;
    font-size: 11px;
    color: {TXT2};
    z-index: 9997;
    pointer-events: none;
    white-space: nowrap;
}}

/* ── Bouton mode ── */
.stButton > button {{
    background: {C2} !important;
    border: 1px solid {BRD} !important;
    color: {TXT} !important;
    border-radius: 20px !important;
    font-size: 11px !important;
    padding: 4px 12px !important;
    height: 30px !important;
}}

/* ── Éléments du panel ── */
.p-header {{
    padding: 14px 16px 12px;
    border-bottom: 1px solid {BRD};
}}
.p-zone-name {{
    font-size: 18px;
    font-weight: 600;
    color: {TXT};
    margin-bottom: 3px;
}}
.p-zone-desc {{
    font-size: 11px;
    color: {TXT2};
    margin-bottom: 10px;
}}
.p-badge {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
}}
.p-section {{
    padding: 12px 16px;
    border-bottom: 1px solid {BRD};
}}
.p-label {{
    font-size: 10px;
    color: {TXT2};
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 500;
    margin-bottom: 8px;
}}
.evt-card {{
    background: {C2};
    border-radius: 8px;
    padding: 9px 11px;
    margin-bottom: 6px;
}}
.evt-type {{
    font-size: 11px;
    font-weight: 600;
    margin-bottom: 3px;
}}
.evt-desc {{
    font-size: 12px;
    color: {TXT};
    line-height: 1.45;
    margin-bottom: 4px;
}}
.evt-meta {{
    font-size: 10px;
    color: {TXT2};
    display: flex;
    justify-content: space-between;
    align-items: center;
}}
.evt-link {{
    color: #4A9EFF;
    text-decoration: none;
    font-size: 10px;
}}
.tag {{
    display: inline-block;
    background: {C2};
    border: 1px solid {BRD};
    border-radius: 12px;
    padding: 3px 9px;
    font-size: 11px;
    color: {TXT};
    margin: 2px;
}}
.media-row {{
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 7px;
}}
.media-bar-bg {{
    flex: 1;
    background: {BRD};
    border-radius: 3px;
    height: 5px;
    overflow: hidden;
}}
.alerte {{
    background: #1A0505;
    border: 1px solid #C0392B;
    border-radius: 8px;
    padding: 9px 12px;
    font-size: 12px;
    color: #E24B4A;
    margin-bottom: 8px;
    display: flex;
    gap: 7px;
}}
.wa-btn {{
    display: block;
    margin: 10px 16px 14px;
    text-align: center;
    background: {"#1A3A1A" if D else "#E8F5E9"};
    color: #27AE60;
    padding: 9px;
    border-radius: 10px;
    font-size: 12px;
    text-decoration: none;
    font-weight: 500;
    border: 1px solid {"#2A5A2A" if D else "#A5D6A7"};
}}
</style>
""", unsafe_allow_html=True)

# ============================================================
# DONNÉES
# ============================================================
@st.cache_data(ttl=900)
def charger_donnees():
    df = pd.read_csv(
        "data/gdelt_benin_2025_clean.csv", low_memory=False)
    df_m = pd.read_csv(
        "data/gdelt_benin_2025_mentions.csv", low_memory=False)
    df_g = pd.read_csv(
        "data/gdelt_benin_2025_gkg.csv", low_memory=False)
    for col in ["GoldsteinScale","AvgTone","NumArticles",
                "QuadClass","ActionGeo_Lat","ActionGeo_Long"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["SQLDATE"] = pd.to_datetime(df["SQLDATE"], errors="coerce")
    df["GlobalEventID"] = df["GlobalEventID"].astype(str)
    df_m["MentionDocTone"] = pd.to_numeric(
        df_m["MentionDocTone"], errors="coerce")
    df_m["GlobalEventID"] = df_m["GlobalEventID"].astype(str)
    df_g["DATE"] = pd.to_datetime(df_g["DATE"], errors="coerce")
    return df, df_m, df_g

df, df_m, df_g = charger_donnees()

ZONES = {
    "Alibori":    {"lat":11.50,"lon":2.80,"desc":"Nord-est"},
    "Atakora":    {"lat":10.50,"lon":1.40,"desc":"Nord-ouest"},
    "Borgou":     {"lat": 9.80,"lon":2.70,"desc":"Centre-nord · Parakou"},
    "Donga":      {"lat": 9.50,"lon":1.70,"desc":"Centre-ouest"},
    "Collines":   {"lat": 8.50,"lon":2.30,"desc":"Centre"},
    "Plateau":    {"lat": 7.80,"lon":2.60,"desc":"Est"},
    "Zou":        {"lat": 7.30,"lon":2.00,"desc":"Sud-centre · Abomey"},
    "Couffo":     {"lat": 7.10,"lon":1.70,"desc":"Sud-ouest"},
    "Ouémé":      {"lat": 6.80,"lon":2.50,"desc":"Sud-est · Porto-Novo"},
    "Mono":       {"lat": 6.80,"lon":1.60,"desc":"Sud · Frontière Togo"},
    "Atlantique": {"lat": 6.50,"lon":2.20,"desc":"Sud · Côte"},
    "Littoral":   {"lat": 6.35,"lon":2.43,"desc":"Cotonou"},
}

CAMEO = {
    "1": ("📢","Annonce officielle","Le gouvernement ou une organisation a fait une annonce."),
    "2": ("🕊️","Appel au dialogue","Des acteurs appellent à la discussion ou à la paix."),
    "3": ("🤝","Accord signé","Un accord ou un partenariat a été conclu."),
    "4": ("🗣️","Réunion diplomatique","Des responsables se sont rencontrés."),
    "5": ("✅","Accord finalisé","Un accord important a été signé."),
    "6": ("🎁","Aide annoncée","Une aide matérielle ou financière a été annoncée."),
    "7": ("🏥","Aide humanitaire","Une aide humanitaire a été mobilisée."),
    "8": ("⚖️","Action judiciaire","Une décision ou action judiciaire a eu lieu."),
    "9": ("🔍","Enquête","Une enquête a été ouverte."),
    "10":("📣","Revendication","Un groupe exprime une demande."),
    "11":("🗳️","Désaccord politique","Un désaccord entre acteurs politiques."),
    "12":("🚫","Rejet","Une proposition a été refusée."),
    "13":("⚠️","Avertissement","Un avertissement a été émis."),
    "14":("✊","Manifestation","Une manifestation a eu lieu."),
    "15":("📵","Pression politique","Une pression est signalée."),
    "16":("🪖","Opération militaire","Une opération militaire a été menée."),
    "17":("🔒","Arrestation","Une arrestation a eu lieu."),
    "18":("💥","Incident violent","Un incident violent a été signalé."),
    "19":("⚔️","Affrontement","Des affrontements ont eu lieu."),
    "20":("🚨","Violence grave","Un acte de violence grave a été signalé."),
}

THEMES = {
    "EDUCATION":"Éducation","HEALTH":"Santé",
    "WB_840_JUSTICE":"Justice","ECONOMY":"Économie",
    "EPU_ECONOMY":"Économie","TOURISM":"Tourisme",
    "AGRICULTURE":"Agriculture","ENVIRONMENT":"Environnement",
    "GENERAL_GOVERNMENT":"Gouvernement","LEADER":"Politique",
    "MILITARY":"Armée","ARMEDCONFLICT":"Conflit armé",
    "TERROR":"Terrorisme","KILL":"Violence",
    "CRISISLEX_C07_SAFETY":"Sécurité",
    "CRISISLEX_CRISISLEXREC":"Crise","MEDIA_MSM":"Médias",
    "ELECTION":"Élections","CORRUPTION":"Corruption",
    "HUMAN_RIGHTS":"Droits humains",
    "EPU_POLICY_GOVERNMENT":"Politique publique",
    "INFRASTRUCTURE":"Infrastructures",
}

PAYS = {
    "Nigeria":("🇳🇬","Nigeria"),
    "Bénin":("🇧🇯","Bénin"),
    "France":("🇫🇷","France"),
    "UK":("🇬🇧","Royaume-Uni"),
    "Reuters":("📡","Reuters"),
    "Al Jazeera":("📺","Al Jazeera"),
    "USA":("🇺🇸","États-Unis"),
    "Afrique":("🌍","Afrique"),
    "Autre":("🌐","International"),
}

def classifier_pays(url):
    if not isinstance(url, str): return "Autre"
    u = url.lower()
    if any(x in u for x in [".ng","naija","nigerian"]): return "Nigeria"
    if any(x in u for x in [".bj","benin24","beninwebtv"]): return "Bénin"
    if any(x in u for x in [".fr","rfi","lemonde","france24"]): return "France"
    if any(x in u for x in ["bbc",".co.uk"]): return "UK"
    if "reuters" in u: return "Reuters"
    if "aljazeera" in u: return "Al Jazeera"
    if any(x in u for x in ["allafrica","africannews"]): return "Afrique"
    if any(x in u for x in ["cnn","washington","nytimes"]): return "USA"
    return "Autre"

def ton_court(t):
    if t <= -4: return "En parle très négativement","#C0392B"
    if t <= -2: return "Couverture négative","#E67E22"
    if t <=  0: return "Couverture neutre","#8888AA"
    return "Couverture positive","#27AE60"

def score_zone(zdf):
    if len(zdf) == 0: return 0
    t = (zdf["QuadClass"] >= 3).mean()
    g = abs(zdf["GoldsteinScale"].mean())
    n = min(len(zdf)/200, 1)
    return round(t*4 + g*0.3 + n*3, 1)

def niveau(s):
    if s >= 7: return "🔴","#C0392B","Activité élevée"
    if s >= 4: return "🟠","#E67E22","Activité modérée"
    if s >= 2: return "🟡","#E6A817","Activité normale"
    return "🟢","#27AE60","Situation calme"

@st.cache_data(ttl=900)
def tous_scores(_df):
    return {z: score_zone(
        _df[_df["ActionGeo_FullName"].str.contains(z, na=False, case=False)]
    ) for z in ZONES}

scores = tous_scores(df)

@st.cache_data(ttl=900)
def zone_data(_df, _dfm, _dfg, zone):
    zdf = _df[_df["ActionGeo_FullName"].str.contains(
        zone, na=False, case=False)].copy()
    s = score_zone(zdf)

    # Événements
    evts = []
    for _, r in zdf[zdf["SOURCEURL"].notna()].nlargest(
            6,"NumArticles").iterrows():
        code = str(r.get("EventRootCode","")).strip()
        em, tp, desc = CAMEO.get(code, ("📌","Événement","Un événement a été signalé."))
        g = r.get("GoldsteinScale", 0)
        url = r.get("SOURCEURL","")
        src = url.split("/")[2].replace("www.","") if url.startswith("http") else ""
        try: date = pd.to_datetime(r["SQLDATE"]).strftime("%d %b")
        except: date = ""
        evts.append({
            "em":em,"tp":tp,"desc":desc,"g":g,
            "url":url,"src":src,"date":date,
            "color":("#C0392B" if g<-2 else "#E67E22" if g<1 else "#27AE60")
        })

    # Médias
    ids = zdf["GlobalEventID"].tolist()
    mz = _dfm[_dfm["GlobalEventID"].isin(ids)].copy()
    medias = []
    if len(mz):
        mz["pays"] = mz["MentionIdentifier"].apply(classifier_pays)
        tp = mz.groupby("pays").agg(
            nb=("MentionDocTone","count"),
            ton=("MentionDocTone","mean")
        ).sort_values("nb",ascending=False).head(5)
        mx = tp["nb"].max()
        for pays, row in tp.iterrows():
            txt, col = ton_court(row["ton"])
            fl, nm = PAYS.get(pays, ("🌐", pays))
            medias.append({
                "fl":fl,"nm":nm,"pct":row["nb"]/mx*100,
                "txt":txt,"col":col,"nb":int(row["nb"])
            })

    # Thèmes
    gz = _dfg[_dfg["Locations"].str.contains(zone, na=False, case=False)]
    th_list = []
    for t in gz["Themes"].dropna():
        for x in str(t).split(";"):
            if x.strip() in THEMES:
                th_list.append(THEMES[x.strip()])
    themes = [t for t,_ in Counter(th_list).most_common(6)]

    # Personnes
    pers = []
    for p in gz["Persons"].dropna():
        for x in str(p).split(";"):
            x = x.strip().title()
            if x and len(x)>3: pers.append(x)
    top_pers = [p for p,_ in Counter(pers).most_common(4)]

    alerte = None
    if s >= 6: alerte = "Des incidents ont été signalés. Soyez prudent."
    elif s >= 4: alerte = "Situation à surveiller. Restez informé."

    return {"s":s,"evts":evts,"medias":medias,
            "themes":themes,"pers":top_pers,"alerte":alerte}

# ============================================================
# CARTE
# ============================================================
def carte():
    m = folium.Map(
        location=[9.0, 2.3], zoom_start=7,
        tiles=TILE, attr="BENIN WATCH",
        prefer_canvas=True, zoom_control=True,
    )

    # Heatmap
    dh = df[df["ActionGeo_Lat"].notna() & df["ActionGeo_Long"].notna()][
        ["ActionGeo_Lat","ActionGeo_Long","NumArticles"]].copy()
    dh["NumArticles"] = pd.to_numeric(dh["NumArticles"],errors="coerce").fillna(1)
    if len(dh):
        HeatMap(
            dh.values.tolist(), min_opacity=0.2,
            radius=20, blur=16,
            gradient={0.2:"#27AE60",0.5:"#E67E22",
                      0.8:"#C0392B",1.0:"#7B0000"}
        ).add_to(m)

    for zone, info in ZONES.items():
        s = scores.get(zone, 0)
        em, col, _ = niveau(s)
        r = 9 + s*2

        folium.CircleMarker(
            [info["lat"], info["lon"]],
            radius=r, color=col,
            fill=True, fill_color=col,
            fill_opacity=0.75, weight=2,
            popup=folium.Popup(
                f'<div style="font-family:Inter,sans-serif;padding:4px;">'
                f'<b style="color:{col};">{em} {zone}</b><br>'
                f'<small style="color:#666;">{info["desc"]}</small></div>',
                max_width=180),
            tooltip=f"{em} {zone}",
        ).add_to(m)

        if s >= 5:
            folium.CircleMarker(
                [info["lat"], info["lon"]],
                radius=r+9, color=col,
                fill=False, weight=1, opacity=0.2,
            ).add_to(m)

        folium.Marker(
            [info["lat"]+0.17, info["lon"]],
            icon=folium.DivIcon(
                html=(f'<div style="font-family:Inter,sans-serif;'
                      f'font-size:10px;font-weight:600;'
                      f'color:{"#EEE" if D else "#111"};'
                      f'text-shadow:0 1px 3px rgba(0,0,0,.9);'
                      f'white-space:nowrap;pointer-events:none;">'
                      f'{zone}</div>'),
                icon_size=(90,18), icon_anchor=(45,0),
            )
        ).add_to(m)
    return m

# ============================================================
# RENDER
# ============================================================
nb_a = sum(1 for s in scores.values() if s >= 7)
nb_v = sum(1 for s in scores.values() if 4 <= s < 7)

# Header HTML pur
st.markdown(f"""
<div id="bw-header">
  <div class="bw-logo">
    <span class="r">BENIN</span><span class="w"> WATCH</span>
  </div>
  <div class="bw-live">
    <div class="dot"></div>
    {datetime.now().strftime('%d %B %Y')}
    {"&nbsp;·&nbsp;<span style='color:#C0392B;font-weight:500;'>⚠️ " + str(nb_a) + " zone(s) à surveiller</span>" if nb_a else ""}
    {"&nbsp;·&nbsp;<span style='color:#E67E22;'>" + str(nb_v) + " en vigilance</span>" if nb_v else ""}
  </div>
  <div></div>
</div>
""", unsafe_allow_html=True)

# Bouton mode sombre — dans une zone invisible au-dessus de la carte
col1, col2, col3 = st.columns([8, 1, 1])
with col3:
    st.button("☀️" if D else "🌙", on_click=toggle_mode,
              help="Changer le thème")

# Carte plein écran
cd = st_folium(
    carte(),
    width="100%",
    height=700,
    returned_objects=["last_object_clicked_tooltip"],
    key=f"map_{'d' if D else 'l'}"
)

# Détecter zone cliquée
if cd and cd.get("last_object_clicked_tooltip"):
    for z in ZONES:
        if z in str(cd["last_object_clicked_tooltip"]):
            st.session_state.zone_active = z
            break

# Panel flottant en HTML pur
zone = st.session_state.zone_active
if zone:
    d = zone_data(df, df_m, df_g, zone)
    s = d["s"]
    em, col, lbl = niveau(s)

    # Événements HTML
    evts_html = ""
    for e in d["evts"][:5]:
        lien = (f'<a href="{e["url"]}" target="_blank" class="evt-link">'
                f'Lire →</a>' if e["url"].startswith("http") else "")
        evts_html += f"""
        <div class="evt-card" style="border-left:3px solid {e['color']};">
          <div class="evt-type" style="color:{e['color']};">
            {e['em']} {e['tp']}
          </div>
          <div class="evt-desc">{e['desc']}</div>
          <div class="evt-meta">
            <span>{e['date']} · {e['src']}</span>
            {lien}
          </div>
        </div>"""

    # Médias HTML
    medias_html = ""
    for md in d["medias"]:
        medias_html += f"""
        <div class="media-row">
          <span style="font-size:14px;">{md['fl']}</span>
          <span style="font-size:12px;color:{TXT};min-width:90px;">{md['nm']}</span>
          <div class="media-bar-bg">
            <div style="width:{md['pct']:.0f}%;height:5px;
              background:{md['col']};border-radius:3px;"></div>
          </div>
          <span style="font-size:10px;color:{md['col']};
            min-width:90px;text-align:right;font-weight:500;">
            {md['txt']}
          </span>
        </div>"""

    # Thèmes HTML
    tags_html = "".join(
        f'<span class="tag">{t}</span>' for t in d["themes"])

    # Personnes HTML
    pers_html = "".join(
        f'<span class="tag">{p}</span>' for p in d["pers"])

    # Alerte HTML
    alerte_html = ""
    if d["alerte"]:
        alerte_html = f"""
        <div class="alerte">
          <span>⚠️</span><span>{d['alerte']}</span>
        </div>"""

    msg = (f"BENIN WATCH · {zone} — {lbl}. "
           f"Infos sur beninwatch.streamlit.app")
    wa = f"https://wa.me/?text={msg.replace(' ','%20')}"

    panel_html = f"""
    <div id="bw-panel">

      <div class="p-header">
        <div class="p-zone-name">{zone}</div>
        <div class="p-zone-desc">{ZONES[zone]['desc']}</div>
        <span class="p-badge"
          style="background:{col}18;color:{col};border:1px solid {col}33;">
          {em} {lbl}
        </span>
      </div>

      <div class="p-section">
        {alerte_html}
        <div class="p-label">De quoi parle-t-on ici ?</div>
        <div>{tags_html}</div>
      </div>

      <div class="p-section">
        <div class="p-label">Ce qui s'est passé</div>
        {evts_html if evts_html else
         f'<div style="color:{TXT2};font-size:12px;">Aucun événement disponible.</div>'}
      </div>

      {"<div class='p-section'><div class='p-label'>Ce que les médias en disent</div>" + medias_html + "</div>" if medias_html else ""}

      {"<div class='p-section'><div class='p-label'>Personnes citées</div>" + pers_html + "</div>" if pers_html else ""}

      <a href="{wa}" target="_blank" class="wa-btn">
        📲 Partager sur WhatsApp
      </a>

    </div>"""

    st.markdown(panel_html, unsafe_allow_html=True)

else:
    st.markdown(
        '<div id="bw-hint">'
        '🗺️ Cliquez sur un département pour voir ce qui s\'y passe'
        '</div>',
        unsafe_allow_html=True)