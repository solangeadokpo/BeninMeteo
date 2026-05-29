# ============================================================
# BENIN WATCH — app.py — Version Mobile + Corrections
# ============================================================

import streamlit as st
import pandas as pd
from datetime import datetime
from collections import Counter
from gtts import gTTS
import io
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
if "rumeur_input" not in st.session_state:
    st.session_state.rumeur_input = ""
if "audio_lang" not in st.session_state:
    st.session_state.audio_lang = "fr"

D = st.session_state.dark_mode
bg   = "#080810" if D else "#F0F0F8"
card = "#0F0F1A" if D else "#FFFFFF"
c2   = "#13131A" if D else "#F0F0F5"
brd  = "#1A1A30" if D else "#DDDDEE"
txt  = "#CCCCDD" if D else "#1A1A2E"
txt2 = "#7777AA" if D else "#666688"
tile = ("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        if D else
        "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png")

# ============================================================
# DONNÉES
# ============================================================
@st.cache_data(ttl=900)
def charger_donnees():
    df  = pd.read_csv("data/gdelt_benin_2025_clean.csv", low_memory=False)
    dfm = pd.read_csv("data/gdelt_benin_2025_mentions.csv", low_memory=False)
    dfg = pd.read_csv("data/gdelt_benin_2025_gkg.csv", low_memory=False)
    for col in ["GoldsteinScale","AvgTone","NumArticles",
                "QuadClass","ActionGeo_Lat","ActionGeo_Long"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["SQLDATE"]  = pd.to_datetime(df["SQLDATE"], errors="coerce")
    df["GlobalEventID"] = df["GlobalEventID"].astype(str)
    dfm["MentionDocTone"] = pd.to_numeric(dfm["MentionDocTone"], errors="coerce")
    dfm["GlobalEventID"]  = dfm["GlobalEventID"].astype(str)
    dfg["DATE"] = pd.to_datetime(dfg["DATE"], errors="coerce")
    return df, dfm, dfg

df, dfm, dfg = charger_donnees()

CAMEO = {
    "1":("📢","Annonce officielle","Le gouvernement ou une organisation a fait une annonce."),
    "2":("🕊️","Appel au dialogue","Des acteurs appellent à la discussion ou à la paix."),
    "3":("🤝","Accord signé","Un accord ou un partenariat a été conclu."),
    "4":("🗣️","Réunion officielle","Des responsables se sont rencontrés."),
    "5":("✅","Accord finalisé","Un accord important a été signé."),
    "6":("🎁","Aide annoncée","Une aide matérielle ou financière a été annoncée."),
    "7":("🏥","Aide humanitaire","Une aide humanitaire a été mobilisée."),
    "8":("⚖️","Action judiciaire","Une décision ou action judiciaire a eu lieu."),
    "9":("🔍","Enquête ouverte","Une enquête a été lancée."),
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
    if s >= 7: return "🔴","#C0392B","Situation tendue"
    if s >= 4: return "🟠","#E67E22","Vigilance"
    if s >= 2: return "🟡","#F1C40F","Activité normale"
    return "🟢","#27AE60","Situation calme"

@st.cache_data(ttl=900)
def tous_scores(_df):
    return {z: score_zone(
        _df[_df["ActionGeo_FullName"].str.contains(z,na=False,case=False)]
    ) for z in ZONES_DEF}

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
        evts.append({"em":em,"tp":tp,"desc":desc,"g":g,"url":url,"src":src,
            "date":date,"color":"#C0392B" if g<-2 else "#E67E22" if g<1 else "#27AE60"})
    ids = zdf["GlobalEventID"].tolist()
    mz = _dfm[_dfm["GlobalEventID"].isin(ids)].copy()
    medias = []
    if len(mz):
        mz["pays"] = mz["MentionIdentifier"].apply(classifier_pays)
        tp_p = mz.groupby("pays").agg(
            nb=("MentionDocTone","count"),
            ton=("MentionDocTone","mean")
        ).sort_values("nb",ascending=False).head(5)
        mx = tp_p["nb"].max()
        for pays, row in tp_p.iterrows():
            txt_t, col = ton_court(row["ton"])
            fl, nm = PAYS_FLAGS.get(pays,("🌐",pays))
            medias.append({"fl":fl,"nm":nm,"pct":row["nb"]/mx*100,"txt":txt_t,"col":col})
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

@st.cache_data(ttl=3600)
def generer_resume(_df):
    zones_act = []
    for zone in ZONES_DEF:
        zdf = _df[_df["ActionGeo_FullName"].str.contains(zone,na=False,case=False)]
        s = score_zone(zdf)
        if s >= 4:
            em, _, lbl = niveau(s)
            zones_act.append(f"{zone} ({lbl.lower()})")
    top_evts = _df.nlargest(3,"NumArticles")
    evts_txt = []
    for _, row in top_evts.iterrows():
        code = str(row.get("EventRootCode","")).strip()
        _, tp, desc = CAMEO.get(code,("","Événement","Un événement a été signalé."))
        zone_e = str(row.get("ActionGeo_FullName","le Bénin"))
        evts_txt.append(f"{tp} à {zone_e}. {desc}")
    zones_str = ", ".join(zones_act) if zones_act else "aucune zone particulière"
    evts_str  = " ".join(evts_txt[:2]) if evts_txt else ""
    return (f"Bonjour. Voici le rapport BENIN WATCH "
            f"du {datetime.now().strftime('%d %B %Y')}. "
            f"Zones à surveiller : {zones_str}. "
            f"Événements de la semaine : {evts_str} "
            f"Pour plus d'informations, consultez BENIN WATCH. "
            f"Restez informé, restez en sécurité.")

@st.cache_data(ttl=3600)
def texte_vers_audio(texte, langue="fr"):
    try:
        tts = gTTS(text=texte, lang=langue, slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.read()
    except:
        return None

# ============================================================
# JSON ZONES
# ============================================================
zones_json = {}
for zone in ZONES_DEF:
    s = scores.get(zone, 0)
    em, col, lbl = niveau(s)
    d = get_zone(df, dfm, dfg, zone)
    zones_json[zone] = {
        "score": s, "emoji": em, "color": col, "label": lbl,
        "desc": ZONES_DEF[zone]["desc"],
        "lat": ZONES_DEF[zone]["lat"],
        "lon": ZONES_DEF[zone]["lon"],
        "themes": d["themes"],
        "evts": [{"em":e["em"],"tp":e["tp"],"desc":e["desc"],
                  "date":e["date"],"src":e["src"],
                  "url":e["url"],"color":e["color"]}
                 for e in d["evts"]],
        "medias": [{"fl":m["fl"],"nm":m["nm"],"pct":m["pct"],
                    "txt":m["txt"],"col":m["col"]}
                   for m in d["medias"]],
        "pers": d["pers"],
    }

zones_json_str = json.dumps(zones_json, ensure_ascii=False)
nb_a     = sum(1 for s in scores.values() if s >= 7)
date_str = datetime.now().strftime('%d %B %Y · %H:%M')
mode_icon = "☀️" if D else "🌙"

# ============================================================
# HTML COMPLET — MOBILE FIRST
# ============================================================
html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1"/>
<title>BENIN WATCH</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
*{{margin:0;padding:0;box-sizing:border-box;font-family:'Inter',sans-serif;-webkit-tap-highlight-color:transparent;}}
html,body{{width:100%;height:100%;background:{bg};overflow:hidden;}}

/* ── Header ── */
#hdr{{
    position:fixed;top:0;left:0;right:0;
    height:50px;
    background:{card};
    backdrop-filter:blur(16px);
    -webkit-backdrop-filter:blur(16px);
    border-bottom:1px solid {brd};
    display:flex;align-items:center;
    justify-content:space-between;
    padding:0 14px;
    z-index:1000;
}}
.logo{{font-size:14px;font-weight:700;letter-spacing:3px;}}
.logo .r{{color:#C0392B;}}
.logo .w{{color:{txt};}}
.live{{font-size:10px;color:{txt2};
    display:flex;align-items:center;gap:5px;}}
.dot{{width:5px;height:5px;border-radius:50%;
    background:#27AE60;animation:bl 1.5s infinite;}}
@keyframes bl{{0%,100%{{opacity:1}}50%{{opacity:.2}}}}
.hdr-right{{display:flex;align-items:center;gap:8px;}}
.alert-pill{{
    background:#2A0505;color:#C0392B;
    padding:2px 8px;border-radius:12px;
    font-size:10px;font-weight:600;
    border:1px solid #5A1A1A;
}}
.mode-btn{{
    background:{c2};border:1px solid {brd};
    color:{txt};padding:4px 10px;
    border-radius:16px;font-size:11px;cursor:pointer;
    -webkit-appearance:none;
}}

/* ── Carte ── */
#map{{
    position:fixed;
    top:50px;left:0;right:0;bottom:0;
    z-index:1;
}}

/* ── Panel — bottom sheet sur mobile, sidebar sur desktop ── */
#panel{{
    position:fixed;
    z-index:900;
    background:{card};
    backdrop-filter:blur(20px);
    -webkit-backdrop-filter:blur(20px);
    border:1px solid {brd};
    overflow-y:auto;
    display:none;
    box-shadow:0 -4px 40px rgba(0,0,0,.5);
    scrollbar-width:thin;
    scrollbar-color:{brd} transparent;
}}
#panel::-webkit-scrollbar{{width:3px;height:3px;}}
#panel::-webkit-scrollbar-thumb{{background:{brd};border-radius:2px;}}

/* Mobile — bottom sheet */
@media (max-width:768px) {{
    #panel{{
        left:0;right:0;bottom:0;
        width:100%;
        max-height:72vh;
        border-radius:18px 18px 0 0;
        border-bottom:none;
    }}
    .drag-handle{{
        width:40px;height:4px;
        background:{brd};border-radius:2px;
        margin:10px auto 4px;
    }}
}}

/* Desktop — sidebar */
@media (min-width:769px) {{
    #panel{{
        top:60px;right:10px;
        width:330px;
        max-height:calc(100vh - 70px);
        border-radius:14px;
    }}
    .drag-handle{{display:none;}}
}}

/* ── Onglets panel ── */
.tabs{{
    display:flex;
    border-bottom:1px solid {brd};
    background:{c2};
}}
.tab{{
    flex:1;padding:10px 6px;
    font-size:11px;font-weight:500;
    color:{txt2};text-align:center;
    cursor:pointer;border-bottom:2px solid transparent;
    transition:all .2s;
}}
.tab.active{{color:#4A9EFF;border-bottom-color:#4A9EFF;}}

/* ── En-tête zone ── */
.p-head{{
    padding:12px 14px 10px;
    border-bottom:1px solid {brd};
    position:relative;
}}
.p-name{{font-size:17px;font-weight:600;color:{txt};margin-bottom:2px;}}
.p-desc{{font-size:11px;color:{txt2};margin-bottom:8px;}}
.p-badge{{
    display:inline-flex;align-items:center;gap:4px;
    padding:3px 10px;border-radius:20px;
    font-size:12px;font-weight:500;
}}
.close-btn{{
    position:absolute;top:12px;right:12px;
    background:{c2};border:1px solid {brd};
    color:{txt2};width:26px;height:26px;
    border-radius:50%;cursor:pointer;
    font-size:14px;display:flex;
    align-items:center;justify-content:center;
    -webkit-appearance:none;
}}

/* ── Tab content ── */
.tab-content{{display:none;padding:12px 14px;}}
.tab-content.active{{display:block;}}
.sec-label{{
    font-size:10px;color:{txt2};
    text-transform:uppercase;letter-spacing:1px;
    font-weight:600;margin-bottom:8px;
}}

/* ── Événements ── */
.evt{{
    display:flex;align-items:flex-start;gap:9px;
    padding:9px 10px;border-radius:8px;
    margin-bottom:6px;cursor:pointer;
    background:{c2};
    transition:opacity .15s;
    text-decoration:none;
}}
.evt:hover,.evt:active{{opacity:.8;}}
.evt-em{{font-size:18px;min-width:24px;margin-top:1px;}}
.evt-body{{flex:1;}}
.evt-type{{font-size:11px;font-weight:600;margin-bottom:3px;}}
.evt-desc{{font-size:12px;color:{txt};line-height:1.4;margin-bottom:3px;}}
.evt-meta{{font-size:10px;color:{txt2};
    display:flex;justify-content:space-between;}}
.evt-arrow{{color:{txt2};font-size:14px;margin-top:3px;}}

/* ── Tags ── */
.tag{{
    display:inline-block;
    background:{c2};border:1px solid {brd};
    border-radius:12px;padding:3px 9px;
    font-size:11px;color:{txt};margin:2px;
}}

/* ── Médias ── */
.med-row{{
    display:flex;align-items:center;gap:7px;margin-bottom:8px;
}}
.med-bar-bg{{flex:1;background:{brd};border-radius:3px;height:5px;}}
.med-bar{{height:5px;border-radius:3px;}}

/* ── Vérification ── */
.verif-form{{padding:12px 14px;}}
.verif-input{{
    width:100%;padding:10px 12px;
    background:{c2};border:1px solid {brd};
    border-radius:10px;color:{txt};
    font-size:13px;outline:none;
    -webkit-appearance:none;
    font-family:'Inter',sans-serif;
    resize:none;
}}
.verif-input:focus{{border-color:#4A9EFF;}}
.verif-btn{{
    width:100%;margin-top:8px;
    padding:10px;border-radius:10px;
    background:#1A2A3A;color:#4A9EFF;
    border:1px solid #2A3A5A;
    font-size:13px;font-weight:600;cursor:pointer;
    -webkit-appearance:none;
    font-family:'Inter',sans-serif;
}}
.verif-btn:active{{opacity:.8;}}
.verif-result{{
    padding:10px 12px;border-radius:10px;
    margin-top:10px;font-size:12px;
    line-height:1.5;
}}
.verif-ok{{background:#0A2A0A;border:1px solid #27AE60;color:#4AE64A;}}
.verif-warn{{background:#1A1A05;border:1px solid #E67E22;color:#E67E22;}}
.verif-no{{background:#1A0505;border:1px solid #C0392B;color:#E24B4A;}}
.verif-title{{font-weight:600;font-size:13px;margin-bottom:4px;}}
.src-item{{
    background:{c2};border-radius:6px;
    padding:7px 10px;margin-top:6px;
    display:flex;justify-content:space-between;align-items:center;
}}
.src-name{{font-size:11px;color:{txt};font-weight:500;}}
.src-link{{font-size:11px;color:#4A9EFF;text-decoration:none;}}

/* ── Audio ── */
.audio-section{{padding:12px 14px;}}
.lang-grid{{
    display:grid;grid-template-columns:1fr 1fr 1fr;
    gap:6px;margin-bottom:10px;
}}
.lang-btn{{
    padding:8px 4px;border-radius:8px;
    background:{c2};border:1px solid {brd};
    color:{txt2};font-size:12px;cursor:pointer;
    text-align:center;-webkit-appearance:none;
    font-family:'Inter',sans-serif;
}}
.lang-btn.active{{
    background:#1A2A1A;border-color:#27AE60;color:#27AE60;
}}
.gen-btn{{
    width:100%;padding:11px;border-radius:10px;
    background:#1A2A1A;color:#27AE60;
    border:1px solid #2A5A2A;
    font-size:13px;font-weight:600;cursor:pointer;
    -webkit-appearance:none;font-family:'Inter',sans-serif;
}}
.gen-btn:active{{opacity:.8;}}
.audio-info{{
    font-size:11px;color:{txt2};
    margin-top:10px;text-align:center;line-height:1.5;
}}

/* ── WhatsApp ── */
.wa-btn{{
    display:block;margin:10px 0 4px;
    text-align:center;
    background:{"#1A3A1A" if D else "#E8F5E9"};
    color:#27AE60;padding:10px;border-radius:10px;
    font-size:13px;text-decoration:none;font-weight:600;
    border:1px solid {"#2A5A2A" if D else "#A5D6A7"};
    -webkit-tap-highlight-color:transparent;
}}

/* ── Alerte ── */
.alerte{{
    background:#1A0505;border:1px solid #C0392B;
    border-radius:8px;padding:9px 12px;
    font-size:12px;color:#E24B4A;
    margin-bottom:10px;display:flex;gap:7px;
    align-items:flex-start;
}}

/* ── Hint ── */
#hint{{
    position:fixed;bottom:16px;left:50%;
    transform:translateX(-50%);
    background:{card};
    border:1px solid {brd};border-radius:20px;
    padding:8px 18px;font-size:11px;color:{txt2};
    z-index:500;pointer-events:none;white-space:nowrap;
    box-shadow:0 4px 16px rgba(0,0,0,.3);
    max-width:90vw;text-align:center;
}}

/* ── Marqueurs météo ── */
.mk-wrap{{
    display:flex;flex-direction:column;
    align-items:center;cursor:pointer;
}}
.mk-circle{{
    border-radius:50%;
    display:flex;align-items:center;justify-content:center;
    font-size:12px;font-weight:700;
    border:2px solid rgba(255,255,255,.3);
    transition:transform .15s;
}}
.mk-circle:active{{transform:scale(.9);}}
.mk-arrow{{
    width:0;height:0;
    border-left:6px solid transparent;
    border-right:6px solid transparent;
    margin-top:-1px;
}}
.mk-lbl{{
    font-size:9px;font-weight:600;
    color:{"#EEE" if D else "#111"};
    margin-top:3px;
    text-shadow:0 1px 3px rgba(0,0,0,.9);
    white-space:nowrap;pointer-events:none;
}}
</style>
</head>
<body>

<!-- Header -->
<div id="hdr">
  <div class="logo">
    <span class="r">BENIN</span><span class="w"> WATCH</span>
  </div>
  <div class="live">
    <div class="dot"></div>
    <span>{date_str}</span>
  </div>
  <div class="hdr-right">
    {f'<span class="alert-pill">⚠️ {nb_a}</span>' if nb_a else ''}
    <button class="mode-btn" onclick="toggleMode()">{mode_icon}</button>
  </div>
</div>

<!-- Carte -->
<div id="map"></div>

<!-- Hint -->
<div id="hint">🗺️ Appuyez sur un département</div>

<!-- Panel -->
<div id="panel">
  <div class="drag-handle"></div>

  <!-- En-tête zone -->
  <div class="p-head">
    <button class="close-btn" onclick="closePanel()">✕</button>
    <div class="p-name" id="p-name">—</div>
    <div class="p-desc" id="p-desc">—</div>
    <span class="p-badge" id="p-badge">—</span>
  </div>

  <!-- Onglets -->
  <div class="tabs">
    <div class="tab active" onclick="showTab('actu')">📰 Actualité</div>
    <div class="tab" onclick="showTab('medias')">🌍 Médias</div>
    <div class="tab" onclick="showTab('verif')">🔍 Vérifier</div>
    <div class="tab" onclick="showTab('audio')">🎙️ Audio</div>
  </div>

  <!-- Tab Actualité -->
  <div id="tab-actu" class="tab-content active">
    <div id="t-alerte"></div>
    <div class="sec-label" id="t-themes-label"></div>
    <div id="t-themes"></div>
    <div class="sec-label" style="margin-top:10px;">Ce qui s'est passé</div>
    <div id="t-evts"></div>
    <div id="t-pers-wrap">
      <div class="sec-label" style="margin-top:10px;">Personnes citées</div>
      <div id="t-pers"></div>
    </div>
    <a id="t-wa" href="#" target="_blank" class="wa-btn">📲 Partager sur WhatsApp</a>
  </div>

  <!-- Tab Médias -->
  <div id="tab-medias" class="tab-content">
    <div class="sec-label">Comment les médias couvrent cette zone</div>
    <div id="t-medias"></div>
  </div>

  <!-- Tab Vérifier -->
  <div id="tab-verif" class="tab-content" style="padding:0;">
    <div class="verif-form">
      <div class="sec-label">Vous avez entendu quelque chose ?</div>
      <textarea class="verif-input" id="verif-input" rows="3"
        placeholder="Décrivez l'information que vous voulez vérifier..."></textarea>
      <button class="verif-btn" onclick="verifierInfo()">
        🔍 Vérifier dans les données
      </button>
      <div id="verif-result" style="display:none;"></div>
    </div>
  </div>

  <!-- Tab Audio -->
  <div id="tab-audio" class="tab-content" style="padding:0;">
    <div class="audio-section">
      <div class="sec-label">Rapport audio de la semaine</div>
      <div class="lang-grid">
        <button class="lang-btn active" onclick="setLang('fr',this)">🇫🇷 Français</button>
        <button class="lang-btn" onclick="setLang('yo',this)">🇳🇬 Yoruba</button>
        <button class="lang-btn" onclick="setLang('ha',this)">🌍 Hausa</button>
      </div>
      <button class="gen-btn" onclick="genererAudio()">
        🎙️ Générer le rapport audio
      </button>
      <div id="audio-result" style="margin-top:12px;display:none;">
        <audio id="audio-player" controls style="width:100%;border-radius:8px;"></audio>
        <a id="audio-dl" href="#" download="benin_watch.mp3" class="wa-btn" style="margin-top:8px;color:#4A9EFF;background:{"#0A1A2A" if D else "#E8F0FA"};border-color:{"#1A3A5A" if D else "#90CAF9"};">
          ⬇️ Télécharger le rapport MP3
        </a>
        <div class="audio-info">
          💡 Partagez ce fichier audio directement sur WhatsApp
          pour informer vos proches.
        </div>
      </div>
      <div id="audio-loading" style="display:none;text-align:center;
        padding:16px;font-size:12px;color:{txt2};">
        ⏳ Génération en cours...
      </div>
    </div>
  </div>

</div>

<script>
const ZONES = {zones_json_str};
const STOP_WORDS = new Set(['dans','cette','semaine','il','ya',
  'une','des','les','que','est','pas','sur','avec','pour',
  'qui','ont','été','plus','mais','par','au','du','en']);

let currentZone = null;
let selectedLang = 'fr';

// ── Carte ──
const map = L.map('map',{{center:[9.0,2.3],zoom:7,zoomControl:true}});
L.tileLayer('{tile}',{{
    attribution:'© CartoDB',subdomains:'abcd',maxZoom:19
}}).addTo(map);

// Marqueurs météo
Object.entries(ZONES).forEach(([nom, z]) => {{
    const sz = 30 + z.score * 3;
    const icon = L.divIcon({{
        className:'',
        html:`<div class="mk-wrap">
          <div class="mk-circle"
            style="width:${{sz}}px;height:${{sz}}px;
              background:${{z.color}};
              box-shadow:0 0 ${{z.score>=6?16:8}}px ${{z.color}}55;">
            ${{z.emoji}}
          </div>
          <div class="mk-arrow"
            style="border-top:8px solid ${{z.color}};"></div>
          <div class="mk-lbl">${{nom}}</div>
        </div>`,
        iconSize:[sz+40,sz+32],
        iconAnchor:[(sz+40)/2, sz/2+2],
    }});
    L.marker([z.lat,z.lon],{{icon}})
     .addTo(map)
     .on('click',()=>openPanel(nom));
}});

// ── Ouvrir panel ──
function openPanel(nom) {{
    currentZone = nom;
    const z = ZONES[nom];
    document.getElementById('hint').style.display = 'none';
    document.getElementById('panel').style.display = 'block';
    document.getElementById('p-name').textContent = nom;
    document.getElementById('p-desc').textContent = z.desc;
    const badge = document.getElementById('p-badge');
    badge.textContent = z.emoji + ' ' + z.label;
    badge.style.cssText =
        `background:${{z.color}}18;color:${{z.color}};
         border:1px solid ${{z.color}}44;`;

    // Alerte
    const aEl = document.getElementById('t-alerte');
    if (z.score >= 4) {{
        aEl.innerHTML = `<div class="alerte">
          <span>⚠️</span>
          <span>${{z.score>=6
            ? 'Des incidents ont été signalés. Soyez prudent.'
            : 'Situation à surveiller. Restez informé.'}}</span>
        </div>`;
    }} else aEl.innerHTML = '';

    // Thèmes
    const thEl = document.getElementById('t-themes');
    const thLbl = document.getElementById('t-themes-label');
    if (z.themes && z.themes.length) {{
        thLbl.textContent = 'De quoi parle-t-on ici ?';
        thEl.innerHTML = z.themes.map(t=>`<span class="tag">${{t}}</span>`).join('');
    }} else {{
        thLbl.textContent = '';
        thEl.innerHTML = '';
    }}

    // Événements
    const evEl = document.getElementById('t-evts');
    if (z.evts && z.evts.length) {{
        evEl.innerHTML = z.evts.map(e => {{
            const href = e.url.startsWith('http') ? e.url : '#';
            const target = e.url.startsWith('http') ? '_blank' : '_self';
            return `<a href="${{href}}" target="${{target}}" class="evt">
              <div class="evt-em">${{e.em}}</div>
              <div class="evt-body">
                <div class="evt-type" style="color:${{e.color}};">${{e.tp}}</div>
                <div class="evt-desc">${{e.desc}}</div>
                <div class="evt-meta">
                  <span>${{e.date}} · ${{e.src}}</span>
                  ${{e.url.startsWith('http') ? '<span style="color:#4A9EFF;">Lire →</span>' : ''}}
                </div>
              </div>
              <div class="evt-arrow">›</div>
            </a>`;
        }}).join('');
    }} else {{
        evEl.innerHTML = `<div style="color:{txt2};font-size:12px;padding:8px 0;">
          Aucun événement disponible.</div>`;
    }}

    // Personnes
    const pEl = document.getElementById('t-pers');
    const pWrap = document.getElementById('t-pers-wrap');
    if (z.pers && z.pers.length) {{
        pWrap.style.display = 'block';
        pEl.innerHTML = z.pers.map(p=>`<span class="tag">${{p}}</span>`).join('');
    }} else pWrap.style.display = 'none';

    // WhatsApp
    const msg = encodeURIComponent(
        `BENIN WATCH · ${{nom}} — ${{z.label}}.\nInfos sur beninwatch.streamlit.app`);
    document.getElementById('t-wa').href =
        `https://wa.me/?text=${{msg}}`;

    // Médias
    const mEl = document.getElementById('t-medias');
    if (z.medias && z.medias.length) {{
        mEl.innerHTML = z.medias.map(m => `
        <div class="med-row">
          <span style="font-size:14px;">${{m.fl}}</span>
          <span style="font-size:12px;min-width:85px;color:{txt};">${{m.nm}}</span>
          <div class="med-bar-bg">
            <div class="med-bar"
              style="width:${{m.pct.toFixed(0)}}%;background:${{m.col}};"></div>
          </div>
          <span style="font-size:10px;color:${{m.col}};
            min-width:80px;text-align:right;font-weight:500;">
            ${{m.txt}}
          </span>
        </div>`).join('');
    }} else {{
        mEl.innerHTML = `<div style="color:{txt2};font-size:12px;">
          Pas de données médias disponibles.</div>`;
    }}

    // Reset tabs
    showTab('actu');
}}

function closePanel() {{
    document.getElementById('panel').style.display = 'none';
    document.getElementById('hint').style.display = 'block';
    currentZone = null;
}}

function showTab(id) {{
    document.querySelectorAll('.tab-content').forEach(el=>el.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(el=>el.classList.remove('active'));
    document.getElementById('tab-'+id).classList.add('active');
    const idx = {{'actu':0,'medias':1,'verif':2,'audio':3}}[id];
    document.querySelectorAll('.tab')[idx].classList.add('active');
}}

// ── Vérification ──
function verifierInfo() {{
    const input = document.getElementById('verif-input').value.trim();
    if (!input || input.length < 5) return;
    const mots = input.toLowerCase().split(/\s+/)
        .filter(m => m.length > 3 && !STOP_WORDS.has(m));
    if (!mots.length) return;

    // Chercher dans les données de toutes les zones
    let matches = [];
    Object.entries(ZONES).forEach(([nom, z]) => {{
        z.evts.forEach(e => {{
            const texte = (e.desc + ' ' + e.tp + ' ' + nom).toLowerCase();
            if (mots.some(m => texte.includes(m))) {{
                matches.push({{zone:nom, evt:e}});
            }}
        }});
    }});

    // Dédupliquer par src
    const seen = new Set();
    matches = matches.filter(m => {{
        if (seen.has(m.evt.src)) return false;
        seen.add(m.evt.src);
        return true;
    }});

    const resEl = document.getElementById('verif-result');
    resEl.style.display = 'block';

    if (matches.length >= 2) {{
        let srcs = matches.slice(0,3).map(m => {{
            const lien = m.evt.url.startsWith('http')
                ? `<a href="${{m.evt.url}}" target="_blank" class="src-link">Lire →</a>`
                : '';
            return `<div class="src-item">
              <span class="src-name">${{m.evt.em}} ${{m.evt.tp}} · ${{m.zone}} · ${{m.evt.date}}</span>
              ${{lien}}
            </div>`;
        }}).join('');
        resEl.innerHTML = `<div class="verif-result verif-ok">
          <div class="verif-title">✅ Confirmé dans les données</div>
          <div>Des médias ont rapporté des événements liés à cette information.</div>
          ${{srcs}}
        </div>`;
    }} else if (matches.length === 1) {{
        const m = matches[0];
        const lien = m.evt.url.startsWith('http')
            ? `<a href="${{m.evt.url}}" target="_blank" class="src-link">Lire l'article →</a>`
            : '';
        resEl.innerHTML = `<div class="verif-result verif-warn">
          <div class="verif-title">⚠️ Partiellement confirmé</div>
          <div>Une seule source a rapporté quelque chose de similaire.
            Vérifiez avant de partager.</div>
          <div class="src-item">
            <span class="src-name">${{m.evt.em}} ${{m.evt.tp}} · ${{m.zone}}</span>
            ${{lien}}
          </div>
        </div>`;
    }} else {{
        resEl.innerHTML = `<div class="verif-result verif-no">
          <div class="verif-title">❌ Non confirmé</div>
          <div>Aucun média n'a rapporté cet événement dans nos données.
            Soyez prudent avant de partager cette information.</div>
        </div>`;
    }}
}}

// ── Audio ──
function setLang(lang, btn) {{
    selectedLang = lang;
    document.querySelectorAll('.lang-btn').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
}}

function genererAudio() {{
    document.getElementById('audio-loading').style.display = 'block';
    document.getElementById('audio-result').style.display = 'none';
    // Signal Streamlit via postMessage
    window.parent.postMessage(
        JSON.stringify({{type:'generate_audio', lang:selectedLang}}),
        '*'
    );
}}

// ── Mode sombre/clair ──
function toggleMode() {{
    window.parent.postMessage(
        JSON.stringify({{type:'toggle_mode'}}), '*');
}}

// ── Swipe pour fermer sur mobile ──
let startY = 0;
document.getElementById('panel').addEventListener('touchstart', e => {{
    startY = e.touches[0].clientY;
}}, {{passive:true}});
document.getElementById('panel').addEventListener('touchmove', e => {{
    const dy = e.touches[0].clientY - startY;
    if (dy > 80) closePanel();
}}, {{passive:true}});
</script>
</body>
</html>"""

# ============================================================
# RENDER + INTERACTIVITÉ
# ============================================================
st.components.v1.html(html, height=800, scrolling=False)

# Gestion messages JS → Streamlit
st.markdown("""
<script>
window.addEventListener('message', function(e) {
    if (!e.data) return;
    try {
        const d = typeof e.data === 'string' ? JSON.parse(e.data) : e.data;
        if (d.type === 'toggle_mode') {
            window.location.reload();
        }
        if (d.type === 'generate_audio') {
            // Handled below
        }
    } catch(err) {}
});
</script>
""", unsafe_allow_html=True)

# Section audio séparée (hors HTML — gérée par Streamlit)
st.markdown("---")
st.markdown(
    f"<div style='font-size:12px;color:{txt2};margin-bottom:8px;'>"
    f"🎙️ Rapport audio — sélectionnez la langue et cliquez Générer "
    f"dans l'onglet Audio du panel</div>",
    unsafe_allow_html=True)

col1, col2, col3 = st.columns([2,1,1])
with col1:
    lang_sel = st.selectbox(
        "Langue",
        ["Français","Yoruba","Hausa"],
        label_visibility="collapsed"
    )
with col2:
    gen_audio = st.button("🎙️ Générer", use_container_width=True)
with col3:
    pass

lang_map = {"Français":"fr","Yoruba":"yo","Hausa":"ha"}

if gen_audio:
    with st.spinner("Génération du rapport audio..."):
        texte = generer_resume(df)
        audio = texte_vers_audio(texte, lang_map[lang_sel])
    if audio:
        st.audio(audio, format="audio/mp3")
        st.download_button(
            "⬇️ Télécharger le rapport MP3",
            data=audio,
            file_name=f"benin_watch_{datetime.now().strftime('%Y%m%d')}.mp3",
            mime="audio/mp3",
            use_container_width=True
        )
    else:
        st.error("Génération audio indisponible. Vérifiez votre connexion.")