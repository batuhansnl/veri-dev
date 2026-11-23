# -*- coding: utf-8 -*-
"""Haritalı EV menzil panelini üretir: harita SVG + il sıcaklıkları + EV modelleri."""
import json, os

BASE = os.path.dirname(__file__)
group = open(os.path.join(BASE, "_harita", "turkiye_group.svg"), encoding="utf-8").read()

# 81 il için KASIM ayı yaklaşık ortalama sıcaklığı (°C) - iklim normalleri (yaklaşık)
NOV = {
 "01":17,"02":11,"03":6,"04":-1,"05":9,"06":6,"07":16,"08":8,"09":15,"10":11,
 "11":8,"12":5,"13":2,"14":7,"15":9,"16":11,"17":13,"18":6,"19":7,"20":12,
 "21":11,"22":10,"23":9,"24":5,"25":-1,"26":6,"27":11,"28":13,"29":6,"30":3,
 "31":17,"32":8,"33":17,"34":13,"35":15,"36":-2,"37":7,"38":5,"39":10,"40":6,
 "41":12,"42":6,"43":6,"44":8,"45":13,"46":12,"47":11,"48":13,"49":2,"50":5,
 "51":6,"52":13,"53":13,"54":12,"55":13,"56":9,"57":12,"58":3,"59":12,"60":8,
 "61":13,"62":6,"63":13,"64":8,"65":3,"66":4,"67":11,"68":6,"69":2,"70":7,
 "71":7,"72":10,"73":9,"74":10,"75":-3,"76":2,"77":13,"78":8,"79":12,"80":15,"81":11,
 "00":18,  # KKTC
}

# Gerçek elektrikli araç modelleri: kullanılabilir batarya (kWh), WLTP menzil (km) - yaklaşık
EV = [
 ["Togg T10X Standart", 52.4, 314],
 ["Togg T10X Uzun Menzil", 88.5, 523],
 ["Togg T10F Uzun Menzil", 88.5, 600],
 ["Tesla Model 3 RWD", 57.5, 513],
 ["Tesla Model 3 Long Range", 75, 629],
 ["Tesla Model Y RWD", 57.5, 455],
 ["Tesla Model Y Long Range", 75, 533],
 ["Tesla Model S", 95, 634],
 ["Tesla Model X", 95, 576],
 ["Volkswagen ID.3", 58, 426],
 ["Volkswagen ID.4", 77, 522],
 ["Volkswagen ID.5", 77, 520],
 ["Hyundai Ioniq 5", 77.4, 507],
 ["Hyundai Ioniq 6", 77.4, 614],
 ["Hyundai Kona Electric", 65.4, 514],
 ["Kia EV6", 77.4, 528],
 ["Kia Niro EV", 64.8, 460],
 ["Kia EV9", 99.8, 563],
 ["BMW i4", 80.7, 590],
 ["BMW iX3", 74, 460],
 ["BMW iX xDrive40", 71, 425],
 ["Mercedes EQA", 66.5, 426],
 ["Mercedes EQB", 66.5, 423],
 ["Mercedes EQE", 90, 639],
 ["Audi Q4 e-tron", 76.6, 528],
 ["Audi e-tron GT", 93.4, 488],
 ["Renault Megane E-Tech", 60, 470],
 ["Renault Scenic E-Tech", 87, 625],
 ["Renault Zoe", 52, 395],
 ["Dacia Spring", 26.8, 230],
 ["Fiat 500e", 42, 320],
 ["Peugeot e-208", 51, 400],
 ["Opel Corsa Electric", 51, 405],
 ["MG4 Electric", 64, 450],
 ["MG ZS EV", 72, 440],
 ["BYD Atto 3", 60.5, 420],
 ["BYD Dolphin", 60.4, 427],
 ["BYD Seal", 82.5, 570],
 ["Volvo EX30", 69, 480],
 ["Volvo XC40 Recharge", 78, 460],
 ["Skoda Enyaq", 77, 544],
 ["Nissan Leaf e+", 59, 385],
 ["Cupra Born", 58, 425],
 ["Ford Mustang Mach-E", 91, 600],
 ["Citroen e-C4", 50, 357],
]

html = f"""<title>EV Menzil Haritası</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
  /* Layout: üstte araç seçimi, sonra tıklanabilir Türkiye haritası, altta canlı menzil sonucu */
  :root {{
    --bg:#f3f7f5; --surface:#fff; --surface-2:#eaf1ee; --ink:#142019; --muted:#55675e;
    --line:#d8e3dd; --brand:#159a6a; --brand-soft:#dcf2e8; --cold:#2f7fd6; --cold-soft:#e0edfb;
    --hot:#e0803a; --warn:#c6881c;
    --font-head:"Space Grotesk",ui-sans-serif,system-ui,sans-serif;
    --font-body:"Inter",ui-sans-serif,system-ui,sans-serif;
    --font-num:"Space Grotesk",ui-monospace,monospace;
    --radius:18px; --shadow:0 1px 2px rgba(20,32,25,.05),0 10px 30px rgba(20,32,25,.07);
    --mapfill:#cdd9d3; --mapstroke:#fff;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      --bg:#0b1310; --surface:#13201a; --surface-2:#1a2a22; --ink:#e9f3ee; --muted:#96a89f;
      --line:#253830; --brand:#3fc48c; --brand-soft:#123524; --cold:#5aa0ea; --cold-soft:#112a44;
      --hot:#eb9a5c; --warn:#e0ad51; --mapfill:#24352c; --mapstroke:#0b1310; color-scheme:dark;
    }}
  }}
  :root[data-theme="dark"] {{
    --bg:#0b1310; --surface:#13201a; --surface-2:#1a2a22; --ink:#e9f3ee; --muted:#96a89f;
    --line:#253830; --brand:#3fc48c; --brand-soft:#123524; --cold:#5aa0ea; --cold-soft:#112a44;
    --hot:#eb9a5c; --warn:#e0ad51; --mapfill:#24352c; --mapstroke:#0b1310; color-scheme:dark;
  }}
  * {{ box-sizing:border-box; }}
  body {{ background:var(--bg); color:var(--ink); font-family:var(--font-body); line-height:1.6; -webkit-font-smoothing:antialiased; }}
  .wrap {{ max-width:860px; margin:0 auto; padding-left:max(16px,env(safe-area-inset-left,0px)); padding-right:max(16px,env(safe-area-inset-right,0px)); padding-block:28px 56px; }}
  h1,h2,h3 {{ font-family:var(--font-head); text-wrap:balance; margin:0; }}
  h1 {{ font-size:clamp(1.6rem,4.5vw,2.3rem); letter-spacing:-.02em; }}
  h2 {{ font-size:1.2rem; margin-bottom:4px; }}
  p {{ margin:0; }}
  .num {{ font-family:var(--font-num); font-variant-numeric:tabular-nums; }}
  header {{ text-align:center; margin-bottom:6px; }}
  .eyebrow {{ text-transform:uppercase; letter-spacing:.14em; font-size:.72rem; font-weight:600; color:var(--brand); }}
  .lead {{ color:var(--muted); font-size:1.05rem; margin:12px auto 0; max-width:56ch; }}
  .theme-btn {{ border:1px solid var(--line); background:var(--surface); color:var(--muted); border-radius:999px; padding:7px 14px; font-size:.8rem; cursor:pointer; font-family:var(--font-body); margin-top:16px; }}
  .theme-btn:hover {{ color:var(--ink); }}
  section {{ margin-top:24px; }}
  .card {{ background:var(--surface); border:1px solid var(--line); border-radius:var(--radius); padding:22px; box-shadow:var(--shadow); }}
  .stepnum {{ display:inline-flex; align-items:center; justify-content:center; width:26px; height:26px; border-radius:8px; background:var(--brand-soft); color:var(--brand); font-family:var(--font-num); font-weight:700; font-size:.85rem; margin-right:8px; }}

  select {{ width:100%; margin-top:12px; padding:13px 14px; font-size:1rem; font-family:var(--font-body); border:1.5px solid var(--line); border-radius:12px; background:var(--surface); color:var(--ink); -webkit-appearance:none; appearance:none; cursor:pointer; }}
  select:focus {{ outline:2px solid var(--brand); }}
  .carinfo {{ display:flex; gap:20px; margin-top:12px; flex-wrap:wrap; color:var(--muted); font-size:.9rem; }}
  .carinfo b {{ color:var(--ink); font-family:var(--font-num); font-size:1.05rem; }}

  .road {{ display:flex; gap:8px; margin-top:14px; }}
  .opt {{ flex:1; border:1.5px solid var(--line); background:var(--surface); color:var(--muted); border-radius:12px; padding:10px; font-family:var(--font-body); font-weight:600; font-size:.92rem; cursor:pointer; }}
  .opt small {{ display:block; font-weight:400; font-size:.72rem; opacity:.8; }}
  .opt[aria-pressed="true"] {{ border-color:var(--brand); background:var(--brand-soft); color:var(--brand); }}

  .maphead {{ display:flex; justify-content:space-between; align-items:baseline; flex-wrap:wrap; gap:8px; }}
  .citypick {{ font-size:.9rem; color:var(--muted); }}
  .citypick b {{ color:var(--brand); font-family:var(--font-head); font-size:1.05rem; }}
  .mapbox {{ margin-top:12px; width:100%; overflow:hidden; }}
  #svg-turkiye-haritasi {{ width:100%; height:auto; display:block; }}
  #svg-turkiye-haritasi path {{ fill:var(--mapfill); stroke:var(--mapstroke); stroke-width:.6; cursor:pointer; transition:fill .12s, opacity .12s; }}
  #svg-turkiye-haritasi g:hover path {{ opacity:.78; }}
  #svg-turkiye-haritasi g.sec path {{ stroke:var(--ink); stroke-width:1.4; }}
  .legend {{ display:flex; align-items:center; gap:10px; margin-top:10px; font-size:.75rem; color:var(--muted); flex-wrap:wrap; }}
  .legbar {{ height:12px; width:160px; border-radius:6px; background:linear-gradient(90deg,#2f7fd6,#67b36a,#f0c24a,#e0803a,#d8503a); }}

  .result {{ margin-top:16px; border-radius:var(--radius); padding:24px; text-align:center; background:var(--brand-soft); transition:background .25s; }}
  .result .menzil {{ font-family:var(--font-num); font-size:3rem; font-weight:700; line-height:1; color:var(--brand); }}
  .result .menzil small {{ font-size:1rem; font-weight:600; }}
  .result .sub {{ color:var(--muted); margin-top:6px; font-size:.95rem; }}
  .result .bar {{ height:15px; border-radius:999px; background:var(--line); overflow:hidden; margin:16px auto 6px; max-width:460px; }}
  .result .bar>span {{ display:block; height:100%; border-radius:999px; background:var(--brand); transition:width .35s,background .35s; }}
  .result .loss {{ font-size:.9rem; margin-top:8px; }}
  .result .loss b {{ color:var(--hot); font-family:var(--font-num); }}
  .mini {{ display:flex; justify-content:center; gap:22px; margin-top:16px; flex-wrap:wrap; }}
  .mini div {{ font-size:.8rem; color:var(--muted); }}
  .mini b {{ display:block; font-family:var(--font-num); font-size:1.1rem; color:var(--ink); }}
  .hintbox {{ background:var(--surface-2); border-radius:12px; padding:12px 16px; color:var(--muted); font-size:.82rem; margin-top:14px; }}
  footer {{ margin-top:36px; color:var(--muted); font-size:.78rem; text-align:center; line-height:1.7; }}
</style>

<div class="wrap">
  <header>
    <div class="eyebrow">Veri Madenciliği Ödevi · İnteraktif Araç</div>
    <h1>Elektrikli Araç Menzil Haritası</h1>
    <p class="lead">Aracını seç, haritadan yaşadığın ili tıkla. O ilin bu mevsimki (Kasım) ortalama sıcaklığına göre bugün kaç km gidebileceğini hesaplar.</p>
    <button class="theme-btn" id="themeBtn">◐ Tema</button>
  </header>

  <section class="card">
    <h2><span class="stepnum">1</span>Aracını seç</h2>
    <select id="car"></select>
    <div class="carinfo">
      <span>Batarya: <b id="battInfo">–</b> kWh</span>
      <span>WLTP menzil: <b id="wltpInfo">–</b> km</span>
    </div>
    <div class="road" id="roadGroup">
      <button class="opt" data-road="0" aria-pressed="true">🏙️ Şehir içi<small>düşük hız</small></button>
      <button class="opt" data-road="1" aria-pressed="false">🛣️ Otoyol<small>yüksek hız</small></button>
    </div>
  </section>

  <section class="card">
    <div class="maphead">
      <h2 style="margin:0"><span class="stepnum">2</span>Haritadan ilini seç</h2>
      <div class="citypick">Seçilen: <b id="cityName">—</b> <span id="cityTemp"></span></div>
    </div>
    <div class="mapbox">
      <svg id="svg-turkiye-haritasi" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1007.478 527.323" role="img" aria-label="Türkiye il haritası">
      {group}
      </svg>
    </div>
    <div class="legend">
      <span>Soğuk</span><div class="legbar"></div><span>Sıcak</span>
      <span style="margin-left:auto">İller Kasım ortalama sıcaklığına göre renklendirildi</span>
    </div>
  </section>

  <section>
    <div class="result" id="result">
      <div class="menzil"><span id="menzilVal">—</span> <small>km</small></div>
      <div class="sub" id="sub">Önce araç ve il seç</div>
      <div class="bar"><span id="bar"></span></div>
      <div class="loss" id="loss"></div>
      <div class="mini">
        <div>Bugünkü tüketim<b id="tuketim">–</b><span style="font-size:.7rem">kWh/100km</span></div>
        <div>İdeal menzil<b id="ideal">–</b><span style="font-size:.7rem">km (~20°C)</span></div>
        <div>Tarih<b id="tarih">–</b><span style="font-size:.7rem">bugün</span></div>
      </div>
    </div>
    <div class="hintbox" id="hint">💡 İpucu: Soğuk illerde (Erzurum, Kars, Ardahan) menzilin ne kadar düştüğünü dene. Sonra sıcak bir ili (Antalya, Mersin) seçip farkı gör.</div>
  </section>

  <footer>
    Veri Madenciliği ve Bilgi Keşfi dönem ödevi · Harita: dnomak/svg-turkiye-haritasi (MIT)<br>
    Not: Sıcaklıklar Kasım ayı yaklaşık iklim ortalamalarıdır; menzil, araçların WLTP değerine fiziksel soğuk/otoyol etkisi uygulanarak tahmin edilir. Gerçek değerler sürüşe göre değişir.
  </footer>
</div>

<script>
  const NOV = {json.dumps(NOV)};
  const EV = {json.dumps(EV, ensure_ascii=False)};

  // Tema
  document.getElementById('themeBtn').addEventListener('click', ()=>{{
    const c=document.documentElement.getAttribute('data-theme');
    const n=c==='dark'?'light':(c==='light'?'dark':(matchMedia('(prefers-color-scheme: dark)').matches?'light':'dark'));
    document.documentElement.setAttribute('data-theme', n);
  }});

  // Araç dropdown doldur
  const carSel=document.getElementById('car');
  EV.forEach((m,i)=>{{ const o=document.createElement('option'); o.value=i; o.textContent=m[0]+' — '+m[1]+' kWh'; carSel.appendChild(o); }});

  // Sıcaklığa göre renk (mavi->yeşil->sarı->turuncu->kırmızı)
  function tempColor(t){{
    const stops=[[-5,[47,127,214]],[5,[90,170,120]],[12,[103,179,106]],[18,[240,194,74]],[25,[224,128,58]],[35,[216,80,58]]];
    if(t<=stops[0][0]) return rgb(stops[0][1]);
    for(let i=1;i<stops.length;i++){{
      if(t<=stops[i][0]){{
        const [t0,c0]=stops[i-1],[t1,c1]=stops[i]; const f=(t-t0)/(t1-t0);
        return rgb(c0.map((v,k)=>Math.round(v+(c1[k]-v)*f)));
      }}
    }}
    return rgb(stops[stops.length-1][1]);
  }}
  const rgb=a=>`rgb(${{a[0]}},${{a[1]}},${{a[2]}})`;

  // Haritayı renklendir + tıklama bağla
  const svg=document.getElementById('svg-turkiye-haritasi');
  const state={{ car:0, road:0, plate:null }};
  let secili=null;
  svg.querySelectorAll('g[data-plakakodu]').forEach(g=>{{
    const pk=g.getAttribute('data-plakakodu');
    const t=NOV[pk];
    if(t!==undefined){{ g.querySelectorAll('path').forEach(p=>p.style.fill=tempColor(t)); }}
    const name=g.getAttribute('data-iladi');
    g.querySelectorAll('path').forEach(p=>{{ p.style.pointerEvents='all'; }});
    g.addEventListener('click', ()=>{{
      if(secili) secili.classList.remove('sec');
      g.classList.add('sec'); secili=g;
      state.plate=pk; run();
    }});
    const tt=document.createElementNS('http://www.w3.org/2000/svg','title');
    tt.textContent = name + (t!==undefined?(' · ~'+t+'°C'):'');
    g.appendChild(tt);
  }});

  // Sürüş tipi
  document.querySelectorAll('#roadGroup .opt').forEach(b=>b.addEventListener('click',()=>{{
    state.road=Number(b.dataset.road);
    document.querySelectorAll('#roadGroup .opt').forEach(x=>x.setAttribute('aria-pressed', x===b?'true':'false'));
    run();
  }}));
  carSel.addEventListener('change', ()=>{{ state.car=Number(carSel.value); run(); }});

  // Tüketim (fiziksel model): WLTP temel + sıcaklık/otoyol cezası
  function tuketimHesapla(base, t, road){{
    const iklim=(t<8||t>28)?1:0;
    const ek = 0.004*Math.pow(t-20,2) + Math.max(0,0.09*(20-t)) + 1.8*iklim + 3.2*road;
    return base + ek;
  }}
  const trN=(x,d=0)=>Number(x).toLocaleString('tr-TR',{{minimumFractionDigits:d,maximumFractionDigits:d}});

  const el=id=>document.getElementById(id);
  // tarih
  const bugun=new Date();
  const aylar=['Oca','Şub','Mar','Nis','May','Haz','Tem','Ağu','Eyl','Eki','Kas','Ara'];
  el('tarih').textContent = bugun.getDate()+' '+aylar[bugun.getMonth()];

  function updateCarInfo(){{ const m=EV[state.car]; el('battInfo').textContent=trN(m[1],m[1]%1?1:0); el('wltpInfo').textContent=m[2]; }}

  function run(){{
    updateCarInfo();
    const m=EV[state.car]; const batt=m[1], wltp=m[2];
    const base = batt/wltp*100;   // aracın WLTP verimi (kWh/100km)

    if(state.plate===null){{ return; }}
    const t=NOV[state.plate];
    const g=svg.querySelector(`g[data-plakakodu="${{state.plate}}"]`);
    const name=g.getAttribute('data-iladi');
    el('cityName').textContent=name;
    el('cityTemp').textContent='· ~'+t+'°C';

    const tuketim=tuketimHesapla(base, t, state.road);
    const menzil=batt/tuketim*100;
    const idealTuk=tuketimHesapla(base, 20, state.road);
    const idealMenzil=batt/idealTuk*100;
    const kayip=Math.max(0,(1-menzil/idealMenzil)*100);

    el('menzilVal').textContent=trN(menzil);
    el('tuketim').textContent=trN(tuketim,1);
    el('ideal').textContent=trN(idealMenzil);
    el('bar').style.width=Math.max(4,(menzil/idealMenzil)*100)+'%';

    const col=t<=5?'var(--cold)':(t>=30?'var(--hot)':'var(--brand)');
    el('bar').style.background=col;
    el('result').style.background=t<=5?'var(--cold-soft)':'var(--brand-soft)';
    document.querySelector('.menzil').style.color=col;

    el('sub').textContent=name+' · '+el('tarih').textContent+' · ~'+t+'°C ('+(state.road?'otoyol':'şehir içi')+')';
    if(kayip<3){{ el('loss').innerHTML='Hava ideale yakın — menzil en iyi hâlinde. 👍'; }}
    else {{
      const neden=t<=5?(state.road?'soğuk + otoyol':'soğuk hava'):(state.road?'otoyol':'ideal dışı sıcaklık');
      el('loss').innerHTML='İdeale göre menzil kaybı: <b>%'+trN(kayip)+'</b> ('+neden+')';
    }}
  }}
  updateCarInfo();
</script>
"""

out = os.path.join(BASE, "panel_harita.html")
open(out, "w", encoding="utf-8").write(html)
print("yazıldı:", out, "boyut:", len(html))
