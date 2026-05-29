# ============================================================
# BENIN WATCH — app.py — Version HTML/JS Pure
# ============================================================

import streamlit as st
import pandas as pd
from datetime import datetime
from collections import Counter
import json

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

D = st.session_state.dark_mode

# ============================================================
# DONNÉES
# ============================================================
@st.cache_data(ttl=900)
def charger_donnees():
    df = pd.read_csv("data/gdelt_benin_2025_clean.csv", low_memory=False)
    df_m = pd.read_csv("data/gdelt_benin_2025_mentions.csv", low_memory=False)
    df_g = pd.read_csv("data/gdelt_benin_2025_gkg.csv", low_memory=False)
    for col in ["GoldsteinScale","AvgTone","NumArticles",
                "QuadClass","ActionGeo_Lat","ActionGeo_Long"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["SQLDATE"] = pd.to_datetime(df["SQLDATE"], errors="coerce")
    df["GlobalEventID"] = df["GlobalEventID"].astype(str)
    df_m["MentionDocTone"] = pd.to_numeric(df_m["MentionDocTone"], errors="coerce")
    df_m["GlobalEventID"] = df_m["GlobalEventID"].astype(str)
    df_g["DATE"] = pd.to_datetime(df_g["DATE"], errors="coerce")
    return df, df_m, df_g

df, df_m, df_g = charger_donnees()

CAMEO = {
    "1": ("📢","Annonce officielle","Le gouvernement ou une organisation a fait une annonce."),
    "2": ("🕊️","Appel au dialogue","Des acteurs appellent à la discussion ou à la paix."),
    "3": ("🤝","Accord signé","Un accord ou un partenariat a été conclu."),
    "4": ("🗣️","Réunion officielle","Des responsables se sont rencontrés."),
    "5": ("✅","Accord finalisé","Un accord important a été signé."),
    "6": ("🎁","Aide annoncée","Une aide matérielle ou financière a été annoncée."),
    "7": ("🏥","Aide humanitaire","Une aide humanitaire a été mobilisée."),
    "8": ("⚖️","Action judiciaire","Une décision ou action judiciaire a eu lieu."),
    "9": ("🔍","Enquête ouverte","Une enquête a été lancée."),
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

PAYS_FLAGS = {
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
    if t <= -4: return "Très négatif","#C0392B"
    if t <= -2: return "Négatif","#E67E22"
    if t <=  0: return "Neutre","#8888AA"
    return "Positif","#27AE60"

def score_zone(zdf):
    if len(zdf) == 0: return 0
    t = (zdf["QuadClass"] >= 3).mean()
    g = abs(zdf["GoldsteinScale"].mean())
    n = min(len(zdf)/200, 1)
    return round(t*4 + g*0.3 + n*3, 1)

def niveau(s):
    if s >= 7: return "🔴","#C0392B","Situation tendue","rouge"
    if s >= 4: return "🟠","#E67E22","Vigilance","orange"
    if s >= 2: return "🟡","#F1C40F","Activité normale","jaune"
    return "🟢","#27AE60","Situation calme","vert"

@st.cache_data(ttl=900)
def tous_scores(_df):
    return {z: score_zone(
        _df[_df["ActionGeo_FullName"].str.contains(z,na=False,case=False)]
    ) for z in ZONES_DEF}

ZONES_DEF = {
    "Alibori":    {"lat":11.50,"lon":2.80,"desc":"Nord-est"},
    "Atakora":    {"lat":10.50,"lon":1.40,"desc":"Nord-ouest"},
    "Borgou":     {"lat": 9.80,"lon":2.70,"desc":"Centre-nord · Parakou"},
    "Donga":      {"lat": 9.50,"lon":1.70,"desc":"Centre-ouest"},
    "Collines":   {"lat": 8.50,"lon":2.30,"desc":"Centre"},
    "Plateau":    {"lat": 7.80,"lon":2.60,"desc":"Est"},
    "Zou":        {"lat": 7.30,"lon":2.00,"desc":"Sud-centre · Abomey"},
    "Couffo":     {"lat": 7.10,"lon":1.70,"desc":"Sud-ouest"},
    "Ouémé":      {"lat": 6.80,"lon":2.50,"desc":"Sud-est · Porto-Novo"},
    "Mono":       {"lat": 6.80,"lon":1.60,"desc":"Sud"},
    "Atlantique": {"lat": 6.50,"lon":2.20,"desc":"Sud · Côte"},
    "Littoral":   {"lat": 6.35,"lon":2.43,"desc":"Cotonou"},
}

scores = tous_scores(df)

@st.cache_data(ttl=900)
def get_zone(_df, _dfm, _dfg, zone):
    zdf = _df[_df["ActionGeo_FullName"].str.contains(
        zone,na=False,case=False)].copy()
    s = score_zone(zdf)

    evts = []
    for _, r in zdf[zdf["SOURCEURL"].notna()].nlargest(5,"NumArticles").iterrows():
        code = str(r.get("EventRootCode","")).strip()
        em, tp, desc = CAMEO.get(code,("📌","Événement","Un événement a été signalé."))
        g = float(r.get("GoldsteinScale",0) or 0)
        url = str(r.get("SOURCEURL",""))
        src = url.split("/")[2].replace("www.","") if url.startswith("http") else ""
        try: date = pd.to_datetime(r["SQLDATE"]).strftime("%d %b")
        except: date = ""
        evts.append({
            "em":em,"tp":tp,"desc":desc,"g":g,"url":url,
            "src":src,"date":date,
            "color":"#C0392B" if g<-2 else "#E67E22" if g<1 else "#27AE60"
        })

    ids = zdf["GlobalEventID"].tolist()
    mz = _dfm[_dfm["GlobalEventID"].isin(ids)].copy()
    medias = []
    if len(mz):
        mz["pays"] = mz["MentionIdentifier"].apply(classifier_pays)
        tp_pays = mz.groupby("pays").agg(
            nb=("MentionDocTone","count"),
            ton=("MentionDocTone","mean")
        ).sort_values("nb",ascending=False).head(5)
        mx = tp_pays["nb"].max()
        for pays, row in tp_pays.iterrows():
            txt, col = ton_court(row["ton"])
            fl, nm = PAYS_FLAGS.get(pays,("🌐",pays))
            medias.append({"fl":fl,"nm":nm,
                "pct":row["nb"]/mx*100,"txt":txt,"col":col})

    gz = _dfg[_dfg["Locations"].str.contains(zone,na=False,case=False)]
    th = []
    for t in gz["Themes"].dropna():
        for x in str(t).split(";"):
            if x.strip() in THEMES: th.append(THEMES[x.strip()])
    themes = [t for t,_ in Counter(th).most_common(5)]

    pers = []
    for p in gz["Persons"].dropna():
        for x in str(p).split(";"):
            x = x.strip().title()
            if x and len(x)>3: pers.append(x)
    top_pers = [p for p,_ in Counter(pers).most_common(4)]

    return {"s":s,"evts":evts,"medias":medias,"themes":themes,"pers":top_pers}

# ============================================================
# CONSTRUCTION DU JSON POUR LA CARTE
# ============================================================
zones_json = {}
for zone in ZONES_DEF:
    s = scores.get(zone, 0)
    em, col, lbl, _ = niveau(s)
    d = get_zone(df, df_m, df_g, zone)

    evts_data = []
    for e in d["evts"]:
        evts_data.append({
            "em": e["em"], "tp": e["tp"], "desc": e["desc"],
            "date": e["date"], "src": e["src"],
            "url": e["url"], "color": e["color"]
        })

    medias_data = []
    for m in d["medias"]:
        medias_data.append({
            "fl": m["fl"], "nm": m["nm"],
            "pct": m["pct"], "txt": m["txt"], "col": m["col"]
        })

    zones_json[zone] = {
        "score": s,
        "emoji": em,
        "color": col,
        "label": lbl,
        "desc": ZONES_DEF[zone]["desc"],
        "lat": ZONES_DEF[zone]["lat"],
        "lon": ZONES_DEF[zone]["lon"],
        "themes": d["themes"],
        "evts": evts_data,
        "medias": medias_data,
        "pers": d["pers"],
    }

zones_json_str = json.dumps(zones_json, ensure_ascii=False)

nb_a = sum(1 for s in scores.values() if s >= 7)
date_str = datetime.now().strftime('%d %B %Y · %H:%M')
mode_icon = "☀️" if D else "🌙"
bg = "#080810" if D else "#F0F0F8"
card = "#0F0F1Aee" if D else "#FFFFFFee"
c2 = "#13131A" if D else "#F0F0F5"
brd = "#1A1A30" if D else "#DDDDEE"
txt = "#CCCCDD" if D else "#1A1A2E"
txt2 = "#7777AA" if D else "#666688"
tile = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" if D else "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"

# ============================================================
# HTML/JS COMPLET
# ============================================================
html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
*{{margin:0;padding:0;box-sizing:border-box;font-family:'Inter',sans-serif;}}
html,body{{width:100%;height:100%;background:{bg};overflow:hidden;}}

/* Header */
#header{{
    position:fixed;top:0;left:0;right:0;height:50px;
    background:{card};
    backdrop-filter:blur(16px);
    border-bottom:1px solid {brd};
    display:flex;align-items:center;
    justify-content:space-between;
    padding:0 18px;z-index:1000;
}}
.logo{{font-size:15px;font-weight:700;letter-spacing:3px;}}
.logo .r{{color:#C0392B;}}
.logo .w{{color:{txt};}}
.live{{font-size:11px;color:{txt2};display:flex;align-items:center;gap:6px;}}
.dot{{width:6px;height:6px;border-radius:50%;background:#27AE60;
    animation:bl 1.5s infinite;}}
@keyframes bl{{0%,100%{{opacity:1}}50%{{opacity:.2}}}}
.alert-badge{{
    background:#2A0505;color:#C0392B;
    padding:3px 10px;border-radius:20px;
    font-size:11px;font-weight:500;
    border:1px solid #5A1A1A;
}}
.mode-btn{{
    background:{c2};border:1px solid {brd};
    color:{txt};padding:5px 12px;
    border-radius:20px;font-size:12px;
    cursor:pointer;
}}
.mode-btn:hover{{background:{brd};}}

/* Carte */
#map{{
    position:fixed;
    top:50px;left:0;right:0;bottom:0;
    z-index:1;
}}

/* Panneau météo latéral */
#panel{{
    position:fixed;
    top:60px;right:10px;
    width:320px;
    max-height:calc(100vh - 70px);
    background:{card};
    backdrop-filter:blur(20px);
    border:1px solid {brd};
    border-radius:14px;
    overflow-y:auto;
    z-index:900;
    box-shadow:0 8px 40px rgba(0,0,0,.5);
    display:none;
    scrollbar-width:thin;
    scrollbar-color:{brd} transparent;
}}
#panel::-webkit-scrollbar{{width:3px;}}
#panel::-webkit-scrollbar-thumb{{background:{brd};border-radius:2px;}}

/* En-tête zone */
.p-head{{padding:14px 16px 12px;border-bottom:1px solid {brd};}}
.p-name{{font-size:18px;font-weight:600;color:{txt};margin-bottom:2px;}}
.p-desc{{font-size:11px;color:{txt2};margin-bottom:10px;}}
.p-badge{{
    display:inline-flex;align-items:center;gap:5px;
    padding:4px 10px;border-radius:20px;
    font-size:12px;font-weight:500;
}}
.close-btn{{
    float:right;background:none;border:none;
    color:{txt2};font-size:16px;cursor:pointer;
    margin-top:-2px;
}}

/* Sections */
.p-sec{{padding:12px 16px;border-bottom:1px solid {brd};}}
.p-lbl{{
    font-size:10px;color:{txt2};
    text-transform:uppercase;letter-spacing:1px;
    font-weight:600;margin-bottom:8px;
}}

/* Événements style météo — avec flèches */
.evt-item{{
    display:flex;align-items:flex-start;gap:10px;
    padding:9px 0;border-bottom:1px solid {brd}22;
    cursor:pointer;
    transition:background .15s;
}}
.evt-item:last-child{{border-bottom:none;}}
.evt-item:hover{{background:{c2};border-radius:6px;padding:9px 6px;}}
.evt-icon{{
    font-size:18px;min-width:26px;
    text-align:center;margin-top:1px;
}}
.evt-body{{flex:1;}}
.evt-type{{
    font-size:11px;font-weight:600;
    margin-bottom:3px;
}}
.evt-desc{{
    font-size:12px;color:{txt};
    line-height:1.4;margin-bottom:4px;
}}
.evt-meta{{
    font-size:10px;color:{txt2};
    display:flex;justify-content:space-between;
}}
.evt-arrow{{
    font-size:14px;color:{txt2};
    margin-top:4px;transition:transform .2s;
    min-width:16px;
}}
.evt-item:hover .evt-arrow{{
    color:#4A9EFF;transform:translateX(3px);
}}
.evt-link{{color:#4A9EFF;text-decoration:none;font-size:10px;}}

/* Tags */
.tag{{
    display:inline-block;
    background:{c2};border:1px solid {brd};
    border-radius:12px;padding:3px 9px;
    font-size:11px;color:{txt};margin:2px;
}}

/* Barres médias */
.media-row{{
    display:flex;align-items:center;gap:7px;
    margin-bottom:8px;
}}
.media-bar-bg{{
    flex:1;background:{brd};
    border-radius:3px;height:5px;
}}
.media-bar-fill{{height:5px;border-radius:3px;}}

/* WhatsApp */
.wa-btn{{
    display:block;margin:12px 16px 14px;
    text-align:center;
    background:{"#1A3A1A" if D else "#E8F5E9"};
    color:#27AE60;padding:9px;border-radius:10px;
    font-size:12px;text-decoration:none;font-weight:500;
    border:1px solid {"#2A5A2A" if D else "#A5D6A7"};
}}

/* Alerte */
.alerte{{
    background:#1A0505;border:1px solid #C0392B;
    border-radius:8px;padding:9px 12px;
    font-size:12px;color:#E24B4A;
    margin-bottom:8px;display:flex;gap:7px;
}}

/* Hint */
#hint{{
    position:fixed;bottom:14px;left:50%;
    transform:translateX(-50%);
    background:{card};
    border:1px solid {brd};border-radius:20px;
    padding:7px 18px;font-size:11px;color:{txt2};
    z-index:500;pointer-events:none;white-space:nowrap;
    box-shadow:0 4px 16px rgba(0,0,0,.3);
}}

/* Marqueurs personnalisés — style météo */
.marker-wrap{{
    display:flex;flex-direction:column;
    align-items:center;cursor:pointer;
}}
.marker-circle{{
    border-radius:50%;
    display:flex;align-items:center;justify-content:center;
    font-size:11px;font-weight:700;color:#fff;
    box-shadow:0 2px 8px rgba(0,0,0,.4);
    transition:transform .2s;
    border:2px solid rgba(255,255,255,.3);
}}
.marker-circle:hover{{transform:scale(1.15);}}
.marker-arrow{{
    width:0;height:0;
    border-left:6px solid transparent;
    border-right:6px solid transparent;
    margin-top:-1px;
}}
.marker-label{{
    font-size:10px;font-weight:600;
    color:{"#EEE" if D else "#111"};
    margin-top:3px;
    text-shadow:0 1px 3px rgba(0,0,0,.9);
    white-space:nowrap;
    pointer-events:none;
}}
</style>
</head>
<body>

<!-- Header -->
<div id="header">
  <div class="logo"><span class="r">BENIN</span><span class="w"> WATCH</span></div>
  <div class="live">
    <div class="dot"></div>
    {date_str}
    {f'&nbsp;·&nbsp;<span class="alert-badge">⚠️ {nb_a} zone(s) à surveiller</span>' if nb_a else ''}
  </div>
  <button class="mode-btn" onclick="window.parent.postMessage('toggle_mode','*')">
    {mode_icon}
  </button>
</div>

<!-- Carte -->
<div id="map"></div>

<!-- Panneau latéral -->
<div id="panel">
  <div class="p-head">
    <button class="close-btn" onclick="closePanel()">✕</button>
    <div class="p-name" id="p-name">—</div>
    <div class="p-desc" id="p-desc">—</div>
    <span class="p-badge" id="p-badge">—</span>
  </div>
  <div id="p-content"></div>
</div>

<!-- Hint -->
<div id="hint">🗺️ Cliquez sur un département pour voir ce qui s'y passe</div>

<script>
// Données zones
const ZONES = {zones_json_str};

// Initialiser carte Leaflet
const map = L.map('map', {{
    center: [9.0, 2.3],
    zoom: 7,
    zoomControl: true,
}});

L.tileLayer('{tile}', {{
    attribution: '© CartoDB',
    subdomains: 'abcd',
    maxZoom: 19
}}).addTo(map);

// Ajouter marqueurs style météo
Object.entries(ZONES).forEach(([nom, z]) => {{
    const size = 32 + z.score * 3;
    const icon = L.divIcon({{
        className: '',
        html: `
        <div class="marker-wrap">
          <div class="marker-circle"
            style="width:${{size}}px;height:${{size}}px;
                   background:${{z.color}};
                   box-shadow:0 0 ${{z.score>=6?'14':'6'}}px ${{z.color}}66;">
            ${{z.emoji}}
          </div>
          <div class="marker-arrow"
            style="border-top:8px solid ${{z.color}};"></div>
          <div class="marker-label">${{nom}}</div>
        </div>`,
        iconSize: [size+40, size+30],
        iconAnchor: [(size+40)/2, size/2],
    }});

    L.marker([z.lat, z.lon], {{icon}})
     .addTo(map)
     .on('click', () => openPanel(nom));
}});

// Ouvrir panneau
function openPanel(nom) {{
    const z = ZONES[nom];
    document.getElementById('hint').style.display = 'none';
    document.getElementById('panel').style.display = 'block';

    document.getElementById('p-name').textContent = nom;
    document.getElementById('p-desc').textContent = z.desc;
    document.getElementById('p-badge').innerHTML =
        `${{z.emoji}} ${{z.label}}`;
    document.getElementById('p-badge').style.cssText =
        `background:${{z.color}}18;color:${{z.color}};
         border:1px solid ${{z.color}}44;`;

    let html = '';

    // Alerte si nécessaire
    if (z.score >= 4) {{
        html += `<div class="p-sec">
          <div class="alerte">
            <span>⚠️</span>
            <span>${{z.score >= 6
                ? 'Des incidents ont été signalés. Soyez prudent.'
                : 'Situation à surveiller. Restez informé.'}}</span>
          </div>
        </div>`;
    }}

    // Thèmes
    if (z.themes && z.themes.length) {{
        html += `<div class="p-sec">
          <div class="p-lbl">De quoi parle-t-on ici ?</div>
          ${{z.themes.map(t => `<span class="tag">${{t}}</span>`).join('')}}
        </div>`;
    }}

    // Événements style météo avec flèches
    if (z.evts && z.evts.length) {{
        html += `<div class="p-sec">
          <div class="p-lbl">Ce qui s'est passé</div>`;
        z.evts.forEach(e => {{
            html += `
            <div class="evt-item" onclick="${{e.url ? `window.open('${{e.url}}','_blank')` : ''}}" >
              <div class="evt-icon">${{e.em}}</div>
              <div class="evt-body">
                <div class="evt-type" style="color:${{e.color}};">${{e.tp}}</div>
                <div class="evt-desc">${{e.desc}}</div>
                <div class="evt-meta">
                  <span>${{e.date}} · ${{e.src}}</span>
                  ${{e.url ? '<span style="color:#4A9EFF;">Lire →</span>' : ''}}
                </div>
              </div>
              <div class="evt-arrow">›</div>
            </div>`;
        }});
        html += `</div>`;
    }}

    // Médias
    if (z.medias && z.medias.length) {{
        html += `<div class="p-sec">
          <div class="p-lbl">Ce que les médias en disent</div>`;
        z.medias.forEach(m => {{
            html += `
            <div class="media-row">
              <span style="font-size:14px;">${{m.fl}}</span>
              <span style="font-size:12px;min-width:85px;">${{m.nm}}</span>
              <div class="media-bar-bg">
                <div class="media-bar-fill"
                  style="width:${{m.pct.toFixed(0)}}%;background:${{m.col}};"></div>
              </div>
              <span style="font-size:10px;color:${{m.col}};
                min-width:80px;text-align:right;font-weight:500;">
                ${{m.txt}}
              </span>
            </div>`;
        }});
        html += `</div>`;
    }}

    // Personnes citées
    if (z.pers && z.pers.length) {{
        html += `<div class="p-sec">
          <div class="p-lbl">Personnes citées</div>
          ${{z.pers.map(p => `<span class="tag">${{p}}</span>`).join('')}}
        </div>`;
    }}

    // WhatsApp
    const msg = encodeURIComponent(
        `BENIN WATCH · ${{nom}} — ${{z.label}}. ` +
        `Infos sur beninwatch.streamlit.app`);
    html += `<a href="https://wa.me/?text=${{msg}}"
               target="_blank" class="wa-btn">
               📲 Partager sur WhatsApp</a>`;

    document.getElementById('p-content').innerHTML = html;
}}

function closePanel() {{
    document.getElementById('panel').style.display = 'none';
    document.getElementById('hint').style.display = 'block';
}}
</script>
</body>
</html>
"""

st.components.v1.html(html, height=800, scrolling=False)