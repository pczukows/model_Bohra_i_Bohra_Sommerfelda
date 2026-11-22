import json
import math

import numpy as np
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Atom Bohra i Bohra-Sommerfelda", page_icon="⚛️", layout="wide")

RY = 13.605693
HC = 1239.841984
A0_PM = 52.9177
IONS = {"H — wodór": 1, "He⁺ — jon helowy": 2, "Li²⁺ — jon litowy": 3}

HELP = {
    "model": "Model Bohra dopuszcza kołowe orbity. Historyczne rozszerzenie Bohra-Sommerfelda dopuszcza elipsy. Oba modele są etapami historycznymi, a nie współczesnym obrazem orbitalu.",
    "ion": "Model ilościowo stosujemy do układów jednoelektronowych: H, He⁺ oraz Li²⁺. Z oznacza ładunek jądra +Ze.",
    "n": "Główna liczba kwantowa. W modelu wodoropodobnym wyznacza energię Eₙ oraz skalę promienia rₙ. Dozwolone wartości: 1, 2, 3, ...",
    "l": "W aplikacji używamy zakresu l=0,1,...,n−1. W trybie historycznym l steruje rodziną elips. W mechanice kwantowej l opisuje orbitalny moment pędu, nie klasyczną trajektorię.",
    "speed": "Zmienia wyłącznie szybkość prezentacji. Nie jest rzeczywistą prędkością elektronu ani czasem przejścia kwantowego.",
    "ni": "Główna liczba kwantowa stanu przed przejściem.",
    "nf": "Główna liczba kwantowa stanu po przejściu.",
    "energy": "Energia stanu związanego jest ujemna względem granicy jonizacji E=0. Im bliżej zera, tym słabiej związany elektron.",
    "radius": "Promień historycznej orbity Bohra. Współczesny orbital nie ma ostrej granicy o takim promieniu.",
    "wavelength": "Długość fali fotonu wynikająca z |ΔE|=hc/λ. Barwa poza zakresem widzialnym jest w aplikacji umowna.",
}


def energy(n, z):
    return -RY * z * z / n**2


def radius_pm(n, z):
    return A0_PM * n * n / z


def wavelength_nm(ni, nf, z):
    return HC / abs(energy(nf, z) - energy(ni, z))


def photon_color(wavelength):
    if wavelength < 380:
        return "#a78bfa"
    if wavelength > 750:
        return "#ef4444"
    stops = [(380, "#6d28d9"), (440, "#2563eb"), (490, "#06b6d4"),
             (510, "#22c55e"), (580, "#facc15"), (645, "#f97316"), (750, "#ef4444")]
    return min(stops, key=lambda item: abs(item[0] - wavelength))[1]


def spectral_region(wavelength):
    if wavelength < 10:
        return "promieniowanie rentgenowskie — kolor umowny"
    if wavelength < 380:
        return "ultrafiolet — niewidzialny dla oka"
    if wavelength <= 750:
        return "zakres widzialny"
    return "podczerwień — niewidzialna dla oka"


def set_orbit_mode():
    st.session_state.view_mode = "orbit"
    st.session_state.transition = None


def run_transition(ni, nf, z):
    wave = wavelength_nm(ni, nf, z)
    st.session_state.run_id += 1
    st.session_state.view_mode = "transition"
    st.session_state.transition = {
        "ni": ni, "nf": nf, "lambda": wave, "emission": ni > nf,
        "color": photon_color(wave), "run_id": st.session_state.run_id,
    }


def learning_intro(title, text, goals):
    st.header(title)
    st.info(text)
    st.markdown("**Po pracy z aplikacją student powinien:**")
    st.markdown("\n".join(f"- {goal}" for goal in goals))


def atom_canvas(model, z, n, l, speed, view_mode, transition, run_id):
    cfg = json.dumps({
        "model": model, "z": z, "n": n, "l": l, "speed": speed,
        "mode": view_mode, "transition": transition, "runId": run_id,
    })
    html = r'''
<div id="root"><canvas id="canvas"></canvas><div id="mode"></div><div id="family"></div><div id="note"></div></div>
<style>
html,body{margin:0;background:#06101d;color:#e5e7eb;font-family:system-ui;overflow:hidden}
#root{height:660px;position:relative}canvas{width:100%;height:100%;display:block}
#mode,#family{position:absolute;top:12px;padding:8px 11px;background:#07111fee;border:1px solid #334155;border-radius:8px;font-weight:700}
#mode{left:16px}#family{right:16px;color:#facc15;max-width:48%;text-align:right}
#note{position:absolute;bottom:8px;left:16px;right:16px;text-align:center;background:#07111fee;padding:8px;border-radius:8px;font-size:13px}
</style>
<script>
const q=__CFG__,cv=document.getElementById('canvas'),g=cv.getContext('2d');let W,H,D,start=performance.now();
function resize(){D=Math.min(devicePixelRatio||1,2);W=cv.clientWidth;H=cv.clientHeight;cv.width=W*D;cv.height=H*D;g.setTransform(D,0,0,D,0,0)}addEventListener('resize',resize);resize();
function axes(n,l,s){let a=s*n*n/q.z;let b=q.model==='bs'?a*(l+1)/n:a;return[a,b]}
function arrow(x,y,vx,vy,col){let a=Math.atan2(vy,vx),ex=x+vx,ey=y+vy;g.strokeStyle=col;g.fillStyle=col;g.lineWidth=2;g.beginPath();g.moveTo(x,y);g.lineTo(ex,ey);g.stroke();g.beginPath();g.moveTo(ex,ey);g.lineTo(ex-7*Math.cos(a-.45),ey-7*Math.sin(a-.45));g.lineTo(ex-7*Math.cos(a+.45),ey-7*Math.sin(a+.45));g.fill()}
function photon(x,y,dir,col,label){g.strokeStyle=col;g.lineWidth=3;g.beginPath();for(let k=0;k<38;k++){let xx=x+dir*k*3,yy=y+Math.sin(k*.7)*6;k?g.lineTo(xx,yy):g.moveTo(xx,yy)}g.stroke();g.fillStyle='#fff';g.font='14px system-ui';g.textAlign='center';g.fillText(label,x+dir*50,y-16)}
function electron(x,y,vx,vy){g.fillStyle='#38bdf8';g.shadowColor='#38bdf8';g.shadowBlur=14;g.beginPath();g.arc(x,y,7,0,7);g.fill();g.shadowBlur=0;let vn=Math.hypot(vx,vy)||1;arrow(x,y,vx/vn*24,vy/vn*24,'#bae6fd')}
function orbit(n,l,cx,cy,s,active){let[a,b]=axes(n,l,s);g.strokeStyle=active?'#60a5fa':'#334155';g.lineWidth=active?3:1.4;g.beginPath();g.ellipse(cx,cy,a,b,0,0,7);g.stroke();g.fillStyle=active?'#bfdbfe':'#64748b';g.font='13px system-ui';g.textAlign='left';g.fillText('n='+n+(q.model==='bs'?', l='+l:''),cx+a+4,cy);return[a,b]}
function frame(now){g.clearRect(0,0,W,H);let cx=W/2,cy=H*.51,s=(Math.min(W,H)*.5-55)/36,t=(now-start)/1000*q.speed,minN=q.model==='bs'?q.l+1:1;
for(let k=minN;k<=6;k++)orbit(k,q.model==='bs'?q.l:k,cx,cy,s,q.mode==='orbit'&&k===q.n);
g.fillStyle='#f59e0b';g.beginPath();g.arc(cx,cy,1.2+.2*q.z,0,7);g.fill();g.fillStyle='#fbbf24';g.font='bold 13px system-ui';g.textAlign='left';g.fillText('jądro +'+q.z,cx+8,cy-7);
if(q.mode==='orbit'){let L=q.model==='bs'?q.l:q.n,[a,b]=axes(q.n,L,s),th=t*1.8/q.n**3,x=cx+a*Math.cos(th),y=cy+b*Math.sin(th),vx=-a*Math.sin(th),vy=b*Math.cos(th);electron(x,y,vx,vy);document.getElementById('mode').textContent='WIDOK ORBITY: n='+q.n+(q.model==='bs'?', l='+q.l:'');document.getElementById('note').textContent='Historyczna ilustracja trajektorii. Współczesna mechanika kwantowa opisuje orbital, nie klasyczną orbitę.'}
else if(q.transition){let T=q.transition,duration=1800,e=now-start,p=Math.min(1,e/duration),Li=q.model==='bs'?q.l:T.ni,Lf=q.model==='bs'?q.l:T.nf,[ai,bi]=axes(T.ni,Li,s),[af,bf]=axes(T.nf,Lf,s),a=ai+(af-ai)*p,b=bi+(bf-bi)*p,th=t*1.8/Math.max(1,T.ni)**3,x=cx+a*Math.cos(th),y=cy+b*Math.sin(th),vx=-a*Math.sin(th),vy=b*Math.cos(th);electron(x,y,vx,vy);g.strokeStyle=T.color;g.lineWidth=4;g.beginPath();g.ellipse(cx,cy,a,b,0,0,7);g.stroke();if(T.emission){if(e>500)photon(cx+(e-500)*.20,cy-120,1,T.color,'emisja '+T.lambda.toFixed(1)+' nm')}else{let tr=Math.min(1,e/1200),px=W-35-(W-35-cx)*tr;if(tr<1)photon(px,cy-120,-1,T.color,'absorpcja '+T.lambda.toFixed(1)+' nm')}document.getElementById('mode').textContent='PRZEJŚCIE: n='+T.ni+' → '+T.nf;document.getElementById('note').textContent=p<1?'Trwa umowna animacja przejścia. Nie przedstawia rzeczywistej trajektorii podczas skoku kwantowego.':'Przejście zakończone. Kliknij ponownie, aby je powtórzyć, albo zmień n/l, aby wrócić do orbity.'}
document.getElementById('family').textContent=q.model==='bs'?'Rodzina o stałym l='+q.l+'; dozwolone n ≥ '+(q.l+1):'Model Bohra — orbity kołowe';requestAnimationFrame(frame)}requestAnimationFrame(frame)
</script>'''.replace("__CFG__", cfg)
    components.html(html, height=670, scrolling=False)


if "view_mode" not in st.session_state:
    st.session_state.view_mode = "orbit"
if "transition" not in st.session_state:
    st.session_state.transition = None
if "run_id" not in st.session_state:
    st.session_state.run_id = 0

st.title("⚛️ Budowa atomu: model Bohra i Bohra-Sommerfelda")
st.caption("Interaktywny historyczny model układów jednoelektronowych: dozwolone energie, promienie, rodziny orbit oraz emisja i absorpcja fotonów.")
st.warning("Model jest ważnym etapem historii nauki i dobrym narzędziem do poziomów energii, ale elektron nie porusza się współcześnie po dokładnie określonej klasycznej orbicie.")

with st.sidebar:
    st.header("Ustawienia modelu", help="Zmiana modelu, jonu, n lub l automatycznie przełącza aplikację do widoku orbity.")
    model_label = st.radio("Model", ["Bohr — orbity kołowe", "Bohr-Sommerfelda — orbity eliptyczne"], key="model_widget", on_change=set_orbit_mode, help=HELP["model"])
    model = "bs" if "Sommerfelda" in model_label else "bohr"
    z = IONS[st.selectbox("Atom lub jon jednoelektronowy", list(IONS), key="ion_widget", on_change=set_orbit_mode, help=HELP["ion"])]
    n = st.slider("Główna liczba kwantowa n", 1, 6, 2, key="n_widget", on_change=set_orbit_mode, help=HELP["n"])
    if model == "bs":
        if st.session_state.get("l_widget", 0) >= n:
            st.session_state.l_widget = n - 1
        l = st.selectbox("Poboczna liczba kwantowa l", options=list(range(n)), key="l_widget", on_change=set_orbit_mode, help=HELP["l"])
        st.info(f"Wybrano rodzinę l={l}. Dozwolone są tylko stany n≥{l+1}; stany n≤{l} nie są rysowane.")
    else:
        l = n - 1
        st.caption("W modelu Bohra orbity są kołowe; kontrolka l nie jest potrzebna.")
    speed = st.slider("Szybkość animacji", .25, 2., 1., .25, help=HELP["speed"])

    st.header("Przejście elektronowe", help="Wybierz stan początkowy i końcowy. ni>nf oznacza emisję, ni<nf absorpcję.")
    allowed = list(range(l + 1, 7)) if model == "bs" else list(range(1, 7))
    ni = st.selectbox("Poziom początkowy nᵢ", allowed, index=min(2, len(allowed)-1), help=HELP["ni"])
    nf = st.selectbox("Poziom końcowy n_f", allowed, index=min(1, len(allowed)-1), help=HELP["nf"])
    if ni == nf:
        st.caption("Wybierz różne poziomy. Dla nᵢ=n_f energia fotonu wynosiłaby zero.")
    if st.button("▶ Animuj wybrane przejście", type="primary", use_container_width=True, disabled=ni == nf, help="Uruchamia pojedynczą animację. Ponowne kliknięcie powtarza to samo przejście."):
        run_transition(ni, nf, z)
    if st.button("◎ Pokaż ponownie wybraną orbitę", use_container_width=True, help="Kończy tryb przejścia i wraca do orbity wskazanej przez n oraz l."):
        set_orbit_mode()

transition = st.session_state.transition if st.session_state.view_mode == "transition" else None
if transition and model == "bs" and (transition["ni"] <= l or transition["nf"] <= l):
    set_orbit_mode()
    transition = None

learning_intro("Jak pracować z aplikacją?",
               "Najpierw przewidź wynik, potem zmień parametr i porównaj przewidywanie z wykresem. W aplikacji istnieją dwa rozłączne tryby: widok wybranej orbity oraz animacja jednego przejścia.",
               ["obliczać zależność energii i promienia od n oraz Z", "rozpoznawać emisję i absorpcję", "odróżniać historyczną orbitę od współczesnego orbitalu", "interpretować diagram poziomów energii"])

metrics = st.columns(5)
metrics[0].metric("Tryb wizualizacji", "Przejście" if st.session_state.view_mode == "transition" else "Orbita", help="Tryb zmienia się po kliknięciu przycisku przejścia albo zmianie n/l.")
metrics[1].metric("Energia Eₙ", f"{energy(n,z):.4f} eV", help=HELP["energy"])
metrics[2].metric("Promień rₙ", f"{radius_pm(n,z):.2f} pm", help=HELP["radius"])
metrics[3].metric("n", n, help=HELP["n"])
metrics[4].metric("l", l if model == "bs" else "—", help=HELP["l"] if model == "bs" else "Model Bohra nie używa tutaj l do rozróżnienia kołowych orbit.")

left, right = st.columns([4, 1], gap="large")
with left:
    atom_canvas(model, z, n, l, speed, st.session_state.view_mode, transition, st.session_state.run_id)
with right:
    st.subheader("Uwagi")
    st.markdown("- Zmiana **n**, **l**, modelu lub jonu pokazuje ponownie **orbitę**.\n- Przycisk przejścia pokazuje tylko jeden elektron zmieniający poziom.\n- Przy **absorpcji** foton biegnie ku atomowi; przy **emisji** oddala się.\n- Rozmiar jądra i elektronu jest silnie powiększony.\n- Animacja przejścia jest symbolem zmiany stanu, a nie rejestracją klasycznej drogi elektronu.")
    if transition:
        delta = abs(energy(transition["nf"], z) - energy(transition["ni"], z))
        st.metric("Różnica energii |ΔE|", f"{delta:.4f} eV", help="Energia emitowanego lub absorbowanego fotonu.")
        st.metric("Długość fali λ", f"{transition['lambda']:.2f} nm", help=HELP["wavelength"])
        st.write("**Emisja fotonu**" if transition["emission"] else "**Absorpcja fotonu**")
        st.caption(spectral_region(transition["lambda"]))
    else:
        st.info("Aktualnie obserwujesz stan o wybranych n i l. Użyj przycisku, aby przejść do animacji emisji lub absorpcji.")

st.subheader("Poziomy energii dostępne w aktualnej rodzinie", help="Poziome linie są dozwolonymi energiami. Odstępy maleją wraz ze wzrostem n; poziomy zbliżają się do granicy jonizacji E=0.")
fig = go.Figure()
for level in allowed:
    e = energy(level, z)
    active = st.session_state.view_mode == "orbit" and level == n
    fig.add_trace(go.Scatter(x=[0,1], y=[e,e], mode="lines+text",
                             line=dict(color="#60a5fa" if active else "#64748b", width=4 if active else 2),
                             text=[f"n={level}" + (f", l={l}" if model=="bs" else ""), ""], textposition="top left", showlegend=False))
if transition:
    fig.add_annotation(x=.65, y=energy(transition["nf"],z), ax=.65, ay=energy(transition["ni"],z), xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=3, arrowwidth=3, arrowcolor=transition["color"], text=f"{transition['lambda']:.1f} nm")
fig.add_hline(y=0, line_dash="dot", line_color="#facc15", annotation_text="granica jonizacji E=0")
fig.update_layout(height=440, xaxis_visible=False, yaxis_title="Energia [eV]", paper_bgcolor="#07111f", plot_bgcolor="#07111f", font=dict(color="#e5e7eb"), margin=dict(l=20,r=20,t=30,b=10))
st.plotly_chart(fig, use_container_width=True, config={"displaylogo":False})

st.markdown("### Wzory użyte w aplikacji")
formula_cols = st.columns(3)
formula_cols[0].info("**Energia poziomu**\n\nEₙ = −13,6057·Z²/n² eV\n\nZwiększenie Z wzmacnia związanie; zwiększenie n zbliża energię do zera.")
formula_cols[1].info("**Promień Bohra**\n\nrₙ = a₀·n²/Z\n\na₀≈52,9177 pm. Promień rośnie jak n² i maleje ze wzrostem Z.")
formula_cols[2].info("**Foton przejścia**\n\n|ΔE| = hν = hc/λ\n\nni>nf: emisja; ni<nf: absorpcja.")

st.markdown("### Sprawdź rozumienie")
q1 = st.radio("Co stanie się z |Eₙ| dla tego samego n, gdy Z wzrośnie?", ["zmniejszy się", "wzrośnie jak Z²", "nie zmieni się"], index=None, key="quiz_energy")
if q1:
    st.success("Poprawnie: energia staje się bardziej ujemna, a |Eₙ| rośnie jak Z²." if q1=="wzrośnie jak Z²" else "Sprawdź wzór Eₙ=−13,6057·Z²/n².")
q2 = st.radio("Przejście n=2 → n=4 oznacza:", ["emisję", "absorpcję", "jonizację"], index=None, key="quiz_transition")
if q2:
    st.success("Poprawnie: elektron musi pobrać energię fotonu." if q2=="absorpcję" else "Poziom końcowy ma wyższą energię, więc potrzebna jest absorpcja.")

st.markdown("### Granice modeli historycznych")
st.warning("Model Bohra dobrze odtwarza podstawowe energie atomu wodoru i jonów jednoelektronowych, lecz nie opisuje poprawnie atomów wieloelektronowych, intensywności linii, spinu ani probabilistycznych orbitali. Model Bohra-Sommerfelda częściowo rozszerza opis o elipsy, ale nadal należy do starej teorii kwantowej.")
st.info("Następny krok w nauce: funkcja falowa, gęstość prawdopodobieństwa |ψ|², orbitale s/p/d, liczby kwantowe oraz równanie Schrödingera.")

st.markdown("### Proponowana ścieżka samodzielnej pracy")
st.markdown("1. Dla H ustaw n=1, 2, 3 i porównaj Eₙ oraz rₙ.\n2. Dla n=2 porównaj H, He⁺ i Li²⁺.\n3. Włącz model Bohra-Sommerfelda i zmieniaj l.\n4. Wykonaj emisję 3→2 oraz absorpcję 2→3.\n5. Porównaj długość fali przejścia dla Z=1, 2 i 3.\n6. Wyjaśnij, które elementy wizualizacji są historyczne i umowne.")
