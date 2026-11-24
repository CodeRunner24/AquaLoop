from pathlib import Path
import csv
from itertools import groupby
import json
from statistics import mean

from src.process_diagnostics import TEST_START, build_diagnostics, write_diagnostics

root = Path(__file__).resolve().parent
res = json.loads((root / 'outputs/results.json').read_text(encoding='utf-8'))
with (root / 'data/synthetic_building_90d_hourly.csv').open(newline='', encoding='utf-8') as file:
    records = [{field: float(value) for field, value in row.items()} for row in csv.DictReader(file)]

diagnostics, telemetry = build_diagnostics(records)
write_diagnostics(diagnostics, telemetry)
dashboard_fields = ('hour_of_day', 'total_water_m3', 'greywater_in_m3', 'nonpotable_demand_m3',
                    'wastewater_temp_c', 'cold_inlet_temp_c', 'forecast_nonpotable_m3')
dashboard_rows = [{field: round(row[field], 8) for field in dashboard_fields} for row in records[TEST_START:]]

# The existing whole-building detector covers one meter. Use only training-period
# readings of the same clock hour to estimate excess use during an alert episode.
hourly_reference = [mean(row['total_water_m3'] for row in records[:TEST_START] if row['hour_of_day'] == h)
                    for h in range(24)]
with (root / 'outputs/prediction_and_anomalies.csv').open(newline='', encoding='utf-8') as file:
    building_rows = list(csv.DictReader(file))
flagged_groups = (list(group) for flagged, group in
                  groupby(building_rows, key=lambda row: int(row['anomaly_flag']) == 1) if flagged)
longest_alert = max(flagged_groups, key=len, default=[])
building_alarm = None
if longest_alert:
    excess = sum(max(0, float(row['meter_with_injected_leak_m3']) - hourly_reference[int(row['hour']) % 24])
                 for row in longest_alert)
    building_alarm = {'first_hour': int(longest_alert[0]['hour']) + 1, 'duration_h': len(longest_alert),
                      'estimated_excess_l': round(1000 * excess)}
html=r'''<!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AquaLoop AI — Building Water Intelligence</title><style>
:root{--bg:#f4f8fc;--navy:#102c4c;--teal:#008c91;--sky:#27a1ce;--muted:#63798e;--border:#e0e9f0;--white:#fff;--green:#07886c}*{box-sizing:border-box}body{margin:0;background:var(--bg);font-family:Inter,'Segoe UI',Arial,sans-serif;color:#18334c}.shell{max-width:1320px;margin:auto;padding:28px 32px}.top{background:#102c4c;color:white;padding:25px 0 36px}.top .shell{display:flex;justify-content:space-between;align-items:center;gap:15px;flex-wrap:wrap}.logo{font-weight:850;font-size:28px;letter-spacing:-1px}.logo b{color:#67dfce}.tag{font-size:11px;color:#9dd9e6;letter-spacing:2px;text-transform:uppercase;margin-bottom:7px}h1{margin:8px 0;font-size:35px;letter-spacing:-1.2px}.sub{color:#bcd1df;font-size:15px;line-height:1.5;max-width:710px}.pill{border:1px solid #5a7b8d;color:#e8fbff;padding:9px 14px;border-radius:30px;font-size:12px}.notice{background:#fff7dd;border:1px solid #f1d997;color:#74541e;border-radius:12px;padding:12px 16px;margin-top:22px;font-size:13px}.tabs{display:flex;gap:9px;margin:22px 0 20px;flex-wrap:wrap}.tabs button{border:1px solid #dbe8f0;background:white;color:#284963;padding:12px 19px;border-radius:9px;cursor:pointer;font-weight:700}.tabs button.active{background:var(--navy);color:white}.tab{display:none}.tab.active{display:block}.cards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:15px}.card,.panel{background:white;border-radius:15px;border:1px solid var(--border);box-shadow:0 3px 9px #13314b08}.card{padding:21px}.card .small{font-size:12px;color:var(--muted);font-weight:700}.value{font-size:30px;font-weight:850;margin:9px 0 4px;color:#103555}.hint{font-size:12px;color:#668194;line-height:1.5}.panels{display:grid;grid-template-columns:1.5fr 1fr;gap:16px;margin-top:17px}.panel{padding:22px}h2{font-size:19px;margin:0 0 9px}h3{font-size:15px}.eyebrow{font-size:11px;letter-spacing:1.7px;color:#078d90;font-weight:850;text-transform:uppercase;margin-bottom:8px}.chart{width:100%;height:260px}canvas{width:100%;height:100%}.control{margin:18px 0}.control label{display:flex;justify-content:space-between;font-size:13px;font-weight:750}.control input{width:100%;accent-color:#008c91;margin-top:12px}.btn{border:0;background:#008b91;color:#fff;font-weight:750;padding:12px 17px;border-radius:9px;cursor:pointer}.metric{display:flex;justify-content:space-between;gap:12px;border-bottom:1px solid #edf1f5;padding:11px 0;font-size:13px}.metric strong{color:#0b516c}.flow{display:grid;grid-template-columns:repeat(5,1fr);gap:7px;margin:20px 0}.node{background:#e9f7f7;border:1px solid #c5e6e2;text-align:center;padding:18px 8px;border-radius:12px;font-weight:750;font-size:13px}.node span{display:block;color:#567984;font-size:11px;font-weight:500;margin-top:7px;line-height:1.45}.node:nth-child(3){background:#eef3fc;border-color:#d5e4f4}.two{display:grid;grid-template-columns:1fr 1fr;gap:18px}.badge{background:#eaf8f0;color:#08764f;display:inline-block;padding:7px 12px;border-radius:20px;font-size:12px;font-weight:800}.step{display:flex;gap:13px;margin:14px 0}.number{background:#102c4c;color:#fff;width:28px;height:28px;flex:0 0 28px;border-radius:50%;display:grid;place-items:center;font-size:13px;font-weight:700}.step p{margin:3px 0;color:#60798b;font-size:13px;line-height:1.6}.note{color:#6c8392;font-size:12px;line-height:1.7}ul{font-size:13px;line-height:1.9;color:#456476}.stat{display:flex;gap:18px;margin-top:16px}.stat strong{font-size:26px;color:#0c7480}.stat div{font-size:12px;color:#6c8091}.footer{text-align:center;color:#70859a;font-size:12px;padding:35px}.chartbar{font-size:12px;color:#678091;margin:10px 0}.chip{display:inline-block;background:#eff7fa;border-radius:6px;padding:6px 9px;font-size:11px;color:#43768e}.comparison{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.comparison .card{background:#f7fbfe}input:focus,button:focus{outline:3px solid #7ad8d4}@media(max-width:900px){.cards{grid-template-columns:1fr 1fr}.panels,.two{grid-template-columns:1fr}.flow{grid-template-columns:1fr 1fr}.shell{padding:20px}.comparison{grid-template-columns:1fr}h1{font-size:28px}}@media(max-width:520px){.cards{grid-template-columns:1fr}.flow{grid-template-columns:1fr}}
/* Tahmin grafiği: açıklayıcı lejant, okunabilir eksenler ve çevrimdışı tooltip */
.forecast-panel h2{line-height:1.3;margin-bottom:7px}
.forecast-subtitle{font-size:12px;color:#5b7386;line-height:1.6;margin:0 0 13px}
.forecast-legend{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:14px}
.forecast-legend-item{display:flex;align-items:center;gap:8px;padding:8px 11px;border:1px solid #dce8ef;border-radius:9px;background:#f8fbfd;font-size:12px;color:#183a55}
.forecast-legend-item strong{font-size:12px;white-space:nowrap}
.forecast-legend-item small{font-size:10px;color:#648093;white-space:nowrap}
.forecast-line{display:inline-block;width:26px;flex:0 0 26px;height:0;border-top:3px solid #2877a9}
.forecast-line.predicted{border-top:3px dashed #008b83}
.forecast-unit{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;font-size:11px;font-weight:650;color:#527084;margin-bottom:4px}
.forecast-hover-hint{font-weight:500;color:#00837f}
.forecast-chart{height:268px;position:relative;touch-action:pan-y}
.forecast-chart canvas{display:block;cursor:crosshair}
.forecast-chart canvas:focus-visible{outline:2px solid #028b86;outline-offset:2px}
.forecast-tooltip{position:absolute;z-index:5;width:225px;max-width:calc(100% - 12px);padding:11px 13px;background:#102e47;color:#fff;border:1px solid #365b72;border-radius:11px;box-shadow:0 8px 25px #082e4950;pointer-events:none;font-size:12px;line-height:1.5}
.forecast-tooltip[hidden]{display:none}
.forecast-tooltip-title{font-weight:800;margin-bottom:7px;color:#fff}
.forecast-tooltip-row{display:flex;justify-content:space-between;align-items:center;gap:10px;margin:3px 0}
.forecast-tooltip-row strong{font-variant-numeric:tabular-nums;white-space:nowrap;color:#fff}
.forecast-tooltip-dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:#5ab3e0;margin-right:6px}
.forecast-tooltip-dot.predicted{background:#44d5c5}
.forecast-tooltip-diff{border-top:1px solid #446275;margin-top:7px;padding-top:7px;color:#d4e6ec}
.forecast-bottom{display:flex;justify-content:space-between;gap:9px;align-items:center;flex-wrap:wrap;color:#657f8e;font-size:11px;margin-top:8px}
.forecast-bottom strong{font-size:11px;color:#075c68}
.forecast-explain{font-size:12px;line-height:1.6;color:#5b7486;margin:13px 0 0}
@media(max-width:600px){.forecast-legend{gap:7px}.forecast-legend-item{padding:7px 8px}.forecast-legend-item small{display:none}.forecast-hover-hint{font-size:10px}.forecast-chart{height:250px}}

__OPERATIONS_CSS__
</style></head><body>
<header class="top"><div class="shell"><div><div class="tag">Wilo Water AI Hackathon 2026</div><div class="logo">Aqua<b>Loop</b> AI</div><h1>Binalarda gri suyun geri kazanımı ve işletimi</h1><div class="sub">Arıtma performansını izleyin, olağandışı çalışmayı erken fark edin ve eşanjör yatırımını binanın ısı talebine göre değerlendirin.</div></div><div class="pill">Sentetik demo</div></div></header>
<main class="shell"><div class="notice"><b>Önemli:</b> Bu bir konsept doğrulama simülasyonudur. Veriler sentetiktir, fiyatlar varsayımsaldır. Canlı su kalitesi kontrolü, gerçek bina bağlantısı, ekipman verimi ve izinli fiziksel uygulama dahil değildir. Buradaki sayılar saha tasarrufu iddiası değildir.</div><nav class="tabs"><button class="active" data-tab="overview">Genel Bakış</button><button data-tab="sim">Senaryo Laboratuvarı</button><button data-tab="operations">Arıtma Alarmı</button><button data-tab="payback">Eşanjör Yatırımı</button><button data-tab="ai">AI & Analitik</button><button data-tab="research">Saha Araştırması</button><button data-tab="roadmap">Uygulama Planı</button></nav>
<section class="tab active" id="overview"><div class="eyebrow">30 Günlük Sentetik Test • Referans Senaryo</div><div class="cards"><div class="card"><div class="small">Şebeke suyu tasarrufu</div><div class="value" id="waterSave">—</div><div class="hint">Geri kullanılan gri su miktarı</div></div><div class="card"><div class="small">Isı geri kazanım potansiyeli</div><div class="value" id="heatValue">—</div><div class="hint">Fiziksel üst sınır hesabı; ihtiyaçla eşleştirilmemiş</div></div><div class="card"><div class="small">Pompa enerjisindeki fark</div><div class="value" id="pumpValue">—</div><div class="hint">Klasik kontrol karşısında AI destekli kontrol</div></div><div class="card"><div class="small">Su tasarruf oranı</div><div class="value" id="savePct">—</div><div class="hint">Toplam şebeke tüketimine göre</div></div></div>
<div class="panels"><div class="panel"><div class="eyebrow">Su akışı</div><h2>Sistem nasıl çalışıyor?</h2><div class="flow"><div class="node">🚿 Gri su<span>Duş + lavabo; siyah sudan ayrı</span></div><div class="node">♨️ Isı eşanjörü<span>Suya karışmadan ısı transferi</span></div><div class="node">🧪 Arıtma + kalite<span>Filtrasyon / dezenfeksiyon / ölçüm</span></div><div class="node">🤖 AI desteği<span>Talep tahmini ve arıtma alarmı</span></div><div class="node">🚽 Yeniden kullanım<span>Yalnızca uygun içilemez kullanım</span></div></div><div class="note">Su ve ısı akışları aynı kaynakta başlar; ısı eşanjörü fiziksel olarak suyun arıtılmış su devresinden ayrıdır. Kalite koşulları sağlanmazsa otomatik bypass ve şebeke yedeği gerekir.</div></div><div class="panel"><div class="eyebrow">Fark yaratan nokta</div><h2>Arıtma kontrolü karşılaştırması</h2><div class="metric"><span>Geri kazanılan su (klasik)</span><strong id="baseReuse">—</strong></div><div class="metric"><span>Geri kazanılan su (AI)</span><strong id="aiReuse">—</strong></div><div class="metric"><span>Pompa enerjisi (klasik)</span><strong id="basePump">—</strong></div><div class="metric"><span>Pompa enerjisi (AI)</span><strong id="aiPump">—</strong></div><p class="note">Aynı girdilerle farklı kontrol kuralları karşılaştırılıyor. Bu denemede iki kontrol stratejisi benzer su ve elektrik sonucu veriyor; AI kontrolünün operasyonel üstünlüğü henüz gösterilmiş değil. Arıtma hattındaki erken uyarı ayrı bir deney olarak test edilir.</p></div></div>
<div class="panels"><div class="panel forecast-panel"><div class="eyebrow">Tahmin modeli · 7 günlük sentetik test kesiti</div><h2>Saatlik yeniden kullanım suyu ihtiyacı: gerçek ve AI tahmini</h2><p class="forecast-subtitle">Binada içme suyu gerektirmeyen kullanım için gereken miktar. 30 günlük test döneminin ilk 168 saati gösteriliyor.</p><div class="forecast-legend" aria-label="Grafik çizgilerinin açıklaması"><span class="forecast-legend-item"><span class="forecast-line actual" aria-hidden="true"></span><strong>Gerçekleşen talep</strong><small>Sentetik test verisi</small></span><span class="forecast-legend-item"><span class="forecast-line predicted" aria-hidden="true"></span><strong>AI tahmini</strong><small>Random Forest</small></span></div><div class="forecast-unit"><span>Dikey eksen: Saatlik su talebi (m³/saat)</span><span class="forecast-hover-hint">Fareyle üzerine gelin veya dokunun</span></div><div class="chart forecast-chart" id="forecastChartWrap"><canvas id="forecastChart" tabindex="0" aria-label="İlk yedi gündeki saatlik gerçek ve AI tahmini su talebi. Değerleri görmek için fareyle üzerine gelin; klavyede sağ ve sol okları da kullanabilirsiniz." role="img"></canvas><div class="forecast-tooltip" id="forecastTooltip" hidden></div></div><div class="forecast-bottom"><span>Yatay eksen: Test dönemindeki günler (her nokta 1 saat)</span><strong id="forecastMae">—</strong></div><p class="forecast-explain">Çizgiler birbirine ne kadar yakınsa tahmin o kadar isabetli. Bu grafik iki kontrol stratejisinin su tasarrufunu değil, <b>tahmin modelinin doğruluğunu</b> gösterir.</p></div><div class="panel"><div class="eyebrow">Sistem değeri</div><h2>Hangi sorun çözülüyor?</h2><ul><li>Sıcak gri suyun kanalizasyona gitmesiyle kaybedilen ısı</li><li>Yeniden kullanılabilecek suyun şebekeden karşılanması</li><li>Sabit zamanlı sistemlerde gereksiz pompa/arıtma operasyonu</li><li>Anormal tüketim ve olası kaçakların geç fark edilmesi</li><li>İşletmecinin su–enerji etkisini birlikte görememesi</li></ul></div></div></section>
<section class="tab" id="sim"><div class="eyebrow">Etkileşimli Prototip</div><h2>Senaryoyu değiştir, 30 günü yeniden simüle et</h2><div class="two"><div class="panel"><div class="control"><label>Gri su depolama kapasitesi <strong id="tankLabel">20 m³</strong></label><input type="range" id="tank" min="4" max="60" step="2" value="20"></div><div class="control"><label>Arıtma kapasitesi <strong id="treatLabel">2.2 m³/saat</strong></label><input type="range" id="treat" min="0.4" max="5" step="0.2" value="2.2"></div><div class="control"><label>Isı eşanjörü verim varsayımı <strong id="effLabel">45%</strong></label><input type="range" id="eff" min="0" max="100" step="1" value="45"></div><div class="control"><label>Su birim fiyatı (varsayımsal) <strong id="priceLabel">65 TL/m³</strong></label><input type="range" id="price" min="20" max="160" step="5" value="65"></div><button class="btn" id="calc">30 günü yeniden hesapla</button><p class="note">Hesaplama tarayıcınızda, saatlik su dengesi modeliyle gerçekleşir. Isı hesabı gerçek sıcak su talebine göre sınırlandırılmadığı için potansiyel olarak gösterilir.</p></div><div class="panel"><div class="eyebrow">Model Karşılaştırması</div><div class="comparison"><div class="card"><div class="small">Geri kazanımsız</div><div class="value" id="s0">—</div><div class="hint">Şebeke suyu</div></div><div class="card"><div class="small">Klasik kontrol</div><div class="value" id="s1">—</div><div class="hint">Şebeke suyu</div></div><div class="card"><div class="small">AI destekli</div><div class="value" id="s2">—</div><div class="hint">Şebeke suyu</div></div></div><div class="metric"><span>AI ile tekrar kullanılan su</span><strong id="s3">—</strong></div><div class="metric"><span>AI pompa elektriği</span><strong id="s4">—</strong></div><div class="metric"><span>Geri kazanılabilir ısı potansiyeli</span><strong id="s5">—</strong></div><div class="metric"><span>İndirgenmemiş su maliyeti farkı</span><strong id="s6">—</strong></div><p class="note">Su bedeli farkı brüt bir senaryo sonucudur. Yatırım ve işletme giderleri dahil değildir. Eşanjörün geri ödeme hesabı için Eşanjör Yatırımı sekmesini kullanın.</p></div></div><div class="panel" style="margin-top:17px"><div class="eyebrow">Saatlik operasyon</div><h2>Tahminli arıtma kuralıyla tank seviyesi</h2><div class="chart"><canvas id="tankChart"></canvas></div></div></section>
__OPERATIONS_HTML__
<section class="tab" id="ai"><div class="two"><div class="panel"><div class="eyebrow">Tahmin Modeli</div><h2>Random Forest — 60 gün eğitim / 30 gün test</h2><div class="stat"><div><strong id="mae">—</strong><div>MAE (m³/saat)</div></div><div><strong id="naive">—</strong><div>Ortalama tahmin MAE</div></div></div><p class="note">Zaman, haftanın günü ve doluluk üzerinden saatlik içilemez kullanım ihtiyacı tahmin edilir. Sentetik veri üretimi ile model girdileri ilişkili olduğundan gerçek dünyada genelleşme iddiası yapılamaz.</p><div class="chip">Özellikler: saat, hafta günü, doluluk</div></div><div class="panel"><div class="eyebrow">Anomali Tespiti</div><h2>Isolation Forest — ana sayaçta kaçak denemesi</h2><div class="stat"><div><strong id="leak">—</strong><div>Kaçak saatlerinde alarm</div></div><div><strong id="falseAlarm">—</strong><div>Kaçak dışı test alarmı</div></div></div><p class="note">13 saat süren 2.8 m³/saat ölçüm artışı enjekte edildi. Anomali bayrakları gerçek bir kaçak doğrulaması değil, bakım incelemesi için işarettir.</p></div></div><div class="panel" style="margin-top:16px"><h2>Karar sistemi — güvenlik önce</h2><div class="flow"><div class="node">Sensör verisi<span>Debi, sıcaklık, seviye, kalite</span></div><div class="node">RF tahmin<span>Gelecek saat talebi</span></div><div class="node">Kurallı optimizasyon<span>İşletim hedefi ve kapasite</span></div><div class="node">Emniyet kilitleri<span>Kalite kapısı, bypass, manuel kontrol</span></div><div class="node">Bina yönetimi<span>Öneri / alarm / rapor</span></div></div><p class="note">Prototipin optimizasyonu güvenlik kısıtlı bir sezgisel politikadır; MPC, RL veya fiziksel ekipman kumandası olduğuna dair iddia yoktur.</p></div></section>
<section class="tab" id="research"><div class="eyebrow">Design Thinking • Keşfet</div><h2>Gerçek kullanıcının problemi önce doğrulanmalı</h2><div class="two"><div class="panel"><h3>Hedef görüşmeler</h3><div class="step"><div class="number">1</div><div><b>Tesis işletmecileri</b><p>Günlük su/enerji maliyetleri, veri erişimi, bakım süreçleri ve öncelikler.</p></div></div><div class="step"><div class="number">2</div><div><b>Mekanik tesisat uzmanları</b><p>Mevcut bina retrofit zorlukları, ekipman, hidrolik gereksinimler ve yatırım geri dönüşü.</p></div></div><div class="step"><div class="number">3</div><div><b>Su yönetimi araştırmacıları</b><p>Su güvenliği, arıtma, uygun kullanım alanı, teknik sınırlar ve test metrikleri.</p></div></div></div><div class="panel"><h3>İlk yazılı uzman görüşmesinden</h3><ul><li>Ayrı hat ve depolama geç planlandığında tadilat maliyeti büyüyebiliyor.</li><li>Personel, ekipman seçimi ve elektrik maliyeti tesisin sürekli kullanımını zorlaştırabiliyor.</li><li>Ölçüm ve erken uyarı, performans kaybı büyümeden incelemeyi başlatabilir.</li><li>Isı yatırımı için kaynakla sıcak su ihtiyacı örtüşmeli.</li></ul><p class="note">Tek uzman görüşünün özeti. Bir sonraki saha adımı, gerçek bir olayın ölçüm kayıtlarıyla alarmı sınamak.</p></div></div></section>
<section class="tab" id="roadmap"><div class="eyebrow">Proof of Concept → Pilot</div><h2>Projeyi gerçek ürüne dönüştürme yol haritası</h2><div class="two"><div class="panel"><div class="step"><div class="number">1</div><div><b>Keşfet ve doğrula</b><p>Kurumsal görüşmeler, tek bina tipi seçimi, kullanım senaryosu, su kalitesi ve izin gereklilikleri.</p></div></div><div class="step"><div class="number">2</div><div><b>Ölçüm ve fizibilite</b><p>Ayrı gri su hattı, iki tank, hijyen bariyerleri, debi ve sıcaklık sensörleri, pompa eğrisi, ısı talepleri.</p></div></div><div class="step"><div class="number">3</div><div><b>Veri toplama ve model eğitimi</b><p>Zaman sıralı eğitim/test, mevsimsellik, anomali etiketleri, eksik veri analizi.</p></div></div><div class="step"><div class="number">4</div><div><b>Shadow mode / güvenlik</b><p>AI sadece öneri verir; sertifikalı kontrolör, bağımsız kalite sensörleri ve fail-safe kuralları işletimi yönetir.</p></div></div><div class="step"><div class="number">5</div><div><b>A/B kontrollü pilot</b><p>Aynı bina koşullarında su ve elektrik tüketimini normalleştir, bakım ve arıtma maliyetlerini dahil et.</p></div></div></div><div class="panel"><h3>Gerçek pilotta zorunlu donanım</h3><ul><li>Ayrı gri su toplama tesisatı ve uygun arıtma üniteleri</li><li>Kirli/temiz tampon tankları ve seviyeler</li><li>Su kalitesi sensörleri, laboratuvar doğrulaması, alarm</li><li>Bağımsız içilemez su dağıtımı ve şebeke güvenliği</li><li>Atık su hattına uygun ısı eşanjörü + sıcaklık ölçümü</li><li>Debimetre, elektrik sayacı, uygun pompa/sürücü</li><li>Yetkili mühendislik, yerel izin ve işletme protokolü</li></ul><div class="notice">İçilemez su hiçbir koşulda içme suyu olarak önerilmez. Su kalitesi ve fiziksel ayrım kontrolü AI tahminine bırakılmaz.</div></div></div></section>
</main><div class="footer">AquaLoop AI • Hackathon konsept prototipi • Tek HTML, internet bağlantısı gerektirmez • v2.1</div>
<script>
const DATA=__DATA__;const RESULT=__RESULT__;const fmt=(v,dec=1)=>Number(v).toLocaleString('tr-TR',{maximumFractionDigits:dec,minimumFractionDigits:dec});
function simulate(mode,tank,cap,eff){let raw=tank*.35*.6,clean=tank*.35*.4,rawCap=tank*.6,cleanCap=tank*.4,save=0,pump=0,heat=0,series=[];for(let i=0;i<DATA.length;i++){let r=DATA[i],need=r.nonpotable_demand_m3,inf=r.greywater_in_m3;raw=Math.min(rawCap,raw+inf);let future=DATA[Math.min(i+1,DATA.length-1)].forecast_nonpotable_m3,target=mode==='conventional'?cap*((r.hour_of_day>=6&&r.hour_of_day<=22)?.8:.3):Math.min(cap,Math.max(.05,r.forecast_nonpotable_m3*1.12+Math.max(0,future-r.forecast_nonpotable_m3)*.15));let treated=Math.min(cap,raw,Math.max(0,cleanCap-clean),target);raw-=treated;clean+=treated;let reuse=Math.min(need,clean);clean-=reuse;save+=reuse;pump+=treated*.48+(treated>.02?.14:0);heat+=Math.max(0,inf*1000*4.186*(r.wastewater_temp_c-r.cold_inlet_temp_c)*eff/3600);series.push(raw+clean)}return{save,pump,heat,series}}
function canvasChart(id, datasets, colors, maxPoints = 168, markers = []) {
  const canvas = document.getElementById(id);
  if (!canvas || canvas.clientWidth === 0 || canvas.clientHeight === 0) return;
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  const density = window.devicePixelRatio || 1;
  canvas.width = Math.round(width * density);
  canvas.height = Math.round(height * density);
  const ctx = canvas.getContext('2d');
  ctx.scale(density, density);
  const left = 46, top = 19, right = 18, bottom = 31;
  const plotW = width - left - right;
  const plotH = height - top - bottom;
  const series = datasets.map((set) => set.slice(0, maxPoints));
  const maximum = Math.max(...series.flat()) * 1.15 || 1;
  const points = series[0].length;
  const xAt = (i) => left + i / Math.max(1, points - 1) * plotW;
  const yAt = (v) => top + (1 - v / maximum) * plotH;
  ctx.font = '11px Segoe UI, Arial, sans-serif';
  for (let i = 0; i <= 4; i++) {
    const value = maximum * (1 - i / 4);
    const y = yAt(value);
    ctx.strokeStyle = '#dfe7ed';
    ctx.beginPath();
    ctx.moveTo(left, y);
    ctx.lineTo(width - right, y);
    ctx.stroke();
    ctx.fillStyle = '#476477';
    ctx.fillText(fmt(value, maximum < 2 ? 2 : 1), 4, y + 4);
  }
  series.forEach((set, k) => {
    ctx.strokeStyle = colors[k];
    ctx.lineWidth = k === 0 ? 2 : 1.5;
    ctx.setLineDash(k === 0 ? [] : [4, 3]);
    ctx.beginPath();
    set.forEach((value, i) => i ? ctx.lineTo(xAt(i), yAt(value)) : ctx.moveTo(xAt(i), yAt(value)));
    ctx.stroke();
  });
  markers.forEach((marker, i) => {
    const x = xAt(marker.index);
    ctx.strokeStyle = marker.color;
    ctx.fillStyle = marker.color;
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 3]);
    ctx.beginPath();
    ctx.moveTo(x, top);
    ctx.lineTo(x, height - bottom);
    ctx.stroke();
    ctx.fillText(marker.label, Math.min(x + 3, width - 42), top + 12 + i * 12);
  });
  ctx.fillStyle = '#476477';
  ctx.fillText('0', left, height - 9);
  ctx.fillText(points + ' saatlik kesit', width - 99, height - 9);
}
// 7 günlük tahmin grafiği: ölçülen ve modelin çıktısı aynı saatte karşılaştırılır.
const FORECAST_HOURS = Math.min(168, DATA.length);
const FORECAST_ACTUAL = DATA.slice(0, FORECAST_HOURS).map(row => row.nonpotable_demand_m3);
const FORECAST_PREDICTED = DATA.slice(0, FORECAST_HOURS).map(row => row.forecast_nonpotable_m3);
let forecastHover = -1;
let forecastGeom = null;
const forecastActualColor = '#2877a9';
const forecastPredictedColor = '#008b83';

function drawForecastChart() {
  const canvas = document.getElementById('forecastChart');
  const tooltip = document.getElementById('forecastTooltip');
  if (!canvas || canvas.clientWidth === 0 || canvas.clientHeight === 0) return;
  const w = canvas.clientWidth, h = canvas.clientHeight;
  const density = Math.min(window.devicePixelRatio || 1, 3);
  canvas.width = Math.round(w * density);
  canvas.height = Math.round(h * density);
  const ctx = canvas.getContext('2d');
  ctx.scale(density, density);
  const left = 49, right = 14, top = 13, bottom = 34;
  const plotW = Math.max(1, w - left - right), plotH = Math.max(1, h - top - bottom);
  const n = FORECAST_HOURS;
  if (!n) return;
  const maxSample = Math.max(...FORECAST_ACTUAL, ...FORECAST_PREDICTED, 0.1);
  const scaleStep = Math.ceil(maxSample * 1.08 / 4 * 10) / 10;
  const ceiling = scaleStep * 4;
  const xAt = i => left + i / Math.max(1, n - 1) * plotW;
  const yAt = v => top + (1 - v / ceiling) * plotH;
  forecastGeom = {left, right, top, bottom, plotW, plotH, w, h, xAt, yAt};

  ctx.font = '11px Segoe UI, Arial, sans-serif';
  ctx.textBaseline = 'middle';
  for (let i = 0; i <= 4; i++) {
    const v = scaleStep * i, y = yAt(v);
    ctx.beginPath(); ctx.moveTo(left, y); ctx.lineTo(w-right, y);
    ctx.strokeStyle = '#e3eaf0'; ctx.lineWidth = 1; ctx.setLineDash([]); ctx.stroke();
    ctx.fillStyle = '#567083'; ctx.textAlign = 'right';
    ctx.fillText(fmt(v, 1), left-9, y);
  }
  // Her günün orta noktasına gün adı; sınırlarına soluk kılavuz çizgisi.
  const days = Math.ceil(n / 24);
  ctx.textAlign = 'center';
  for (let day = 0; day < days; day++) {
    const start = day*24, end = Math.min(n-1, start+23);
    if (day > 0) {
      const boundary = xAt(start)-plotW/(n-1)/2;
      ctx.setLineDash([2,5]); ctx.strokeStyle = '#e5edf1';
      ctx.beginPath(); ctx.moveTo(boundary, top); ctx.lineTo(boundary, h-bottom); ctx.stroke();
      ctx.setLineDash([]);
    }
    ctx.fillStyle = '#567083';
    ctx.fillText((day+1)+'. gün', (xAt(start)+xAt(end))/2, h-13);
  }
  const plot = (values,color,dashed,lineWidth) => {
    ctx.strokeStyle = color; ctx.lineWidth = lineWidth;
    ctx.lineJoin='round'; ctx.lineCap='round'; ctx.setLineDash(dashed ? [6,4] : []);
    ctx.beginPath();
    values.forEach((v,i)=> i ? ctx.lineTo(xAt(i),yAt(v)) : ctx.moveTo(xAt(i),yAt(v)));
    ctx.stroke(); ctx.setLineDash([]);
  };
  plot(FORECAST_ACTUAL,forecastActualColor,false,2.3);
  plot(FORECAST_PREDICTED,forecastPredictedColor,true,2.2);
  if (forecastHover >= 0 && forecastHover < n) {
    const x=xAt(forecastHover);
    ctx.strokeStyle='#8aa9b7'; ctx.lineWidth=1; ctx.setLineDash([3,3]);
    ctx.beginPath(); ctx.moveTo(x,top); ctx.lineTo(x,h-bottom); ctx.stroke(); ctx.setLineDash([]);
    [[FORECAST_ACTUAL[forecastHover],forecastActualColor], [FORECAST_PREDICTED[forecastHover],forecastPredictedColor]].forEach(([v,c])=>{
      ctx.beginPath();ctx.arc(x,yAt(v),4.5,0,2*Math.PI);
      ctx.fillStyle='#fff'; ctx.fill(); ctx.strokeStyle=c; ctx.lineWidth=2.5; ctx.stroke();
    });
  }
  if (tooltip && !tooltip.hidden && forecastHover >= 0) {
    positionForecastTooltip(forecastHover);
  }
}
function positionForecastTooltip(index) {
  const tip = document.getElementById('forecastTooltip');
  if (!tip || !forecastGeom || tip.hidden) return;
  const {w,h,xAt,yAt} = forecastGeom;
  const x=xAt(index), y=yAt(Math.max(FORECAST_ACTUAL[index],FORECAST_PREDICTED[index]));
  const tipW=tip.offsetWidth,tipH=tip.offsetHeight;
  let px = x+13;
  if (px + tipW > w-5) px = x - tipW - 13;
  px=Math.max(5,Math.min(px,w-tipW-5));
  let py = y-tipH-13;
  if(py < 5) py=y+15;
  py=Math.max(5,Math.min(py,h-tipH-5));
  tip.style.left=px+'px'; tip.style.top=py+'px';
}
function showForecastHour(index) {
  const tip = document.getElementById('forecastTooltip');
  const n=FORECAST_HOURS;
  if(index<0 || index>=n || !tip) return;
  forecastHover=index;
  const actual=FORECAST_ACTUAL[index],pred=FORECAST_PREDICTED[index],diff=pred-actual;
  const day=Math.floor(index/24)+1,hour=index%24;
  const clock=String(hour).padStart(2,'0');
  const nextClock=String((hour+1)%24).padStart(2,'0');
  const direction=Math.abs(diff)<0.0005?'Tahmin aynı':diff>0?'Model daha yüksek tahmin etti':'Model daha düşük tahmin etti';
  tip.innerHTML=`<div class="forecast-tooltip-title">${day}. gün · ${clock}:00–${nextClock}:00</div>
    <div class="forecast-tooltip-row"><span><i class="forecast-tooltip-dot"></i>Gerçekleşen</span><strong>${fmt(actual,3)} m³/saat</strong></div>
    <div class="forecast-tooltip-row"><span><i class="forecast-tooltip-dot predicted"></i>AI tahmini</span><strong>${fmt(pred,3)} m³/saat</strong></div>
    <div class="forecast-tooltip-diff">${direction}: <strong>${fmt(Math.abs(diff),3)} m³/saat</strong></div>`;
  tip.hidden=false;
  drawForecastChart();
}
function hideForecastTooltip(){
  forecastHover=-1;
  document.getElementById('forecastTooltip').hidden=true;
  drawForecastChart();
}
function setupForecastChart(){
  const canvas=document.getElementById('forecastChart');
  const mae=FORECAST_ACTUAL.reduce((s,v,i)=>s+Math.abs(v-FORECAST_PREDICTED[i]),0)/Math.max(1,FORECAST_HOURS);
  document.getElementById('forecastMae').textContent='7 günlük MAE: '+fmt(mae,3)+' m³/saat';
  const pointer=e=>{
    if(!forecastGeom)return;
    const rect=canvas.getBoundingClientRect();
    const x=e.clientX-rect.left,y=e.clientY-rect.top;
    if(x<forecastGeom.left-8 || x>forecastGeom.w-forecastGeom.right+8 || y<forecastGeom.top-8 || y>forecastGeom.h-forecastGeom.bottom+8){hideForecastTooltip();return;}
    const index=Math.max(0,Math.min(FORECAST_HOURS-1,Math.round((x-forecastGeom.left)/forecastGeom.plotW*(FORECAST_HOURS-1))));
    if(index!==forecastHover)showForecastHour(index);
  };
  canvas.addEventListener('pointermove',pointer);
  canvas.addEventListener('pointerdown',pointer);
  canvas.addEventListener('pointerleave',hideForecastTooltip);
  canvas.addEventListener('focus',()=>{if(forecastHover<0)showForecastHour(0);});
  canvas.addEventListener('blur',hideForecastTooltip);
  canvas.addEventListener('keydown',e=>{
    if(e.key==='ArrowRight'||e.key==='ArrowLeft'){
      e.preventDefault();showForecastHour(Math.max(0,Math.min(FORECAST_HOURS-1,Math.max(0,forecastHover)+(e.key==='ArrowRight'?1:-1))));
    }
    if(e.key==='Escape')hideForecastTooltip();
  });
}
let last=[];function render(){let tank=+document.getElementById('tank').value,cap=+document.getElementById('treat').value,eff=+document.getElementById('eff').value/100,price=+document.getElementById('price').value;let baseline=simulate('conventional',tank,cap,eff),smart=simulate('smart',tank,cap,eff),total=RESULT.comparison.no_recovery.freshwater_m3;let update=(id,s)=>document.getElementById(id).textContent=s;update('tankLabel',fmt(tank,0)+' m³');update('treatLabel',fmt(cap,1)+' m³/saat');update('effLabel',fmt(eff*100,0)+'%');update('priceLabel',fmt(price,0)+' TL/m³');update('waterSave',fmt(smart.save,0)+' m³');update('heatValue',fmt(smart.heat,0)+' kWh');update('pumpValue',fmt((baseline.pump-smart.pump)/baseline.pump*100,2)+'%');update('savePct',fmt(smart.save/total*100,1)+'%');update('baseReuse',fmt(baseline.save,1)+' m³');update('aiReuse',fmt(smart.save,1)+' m³');update('basePump',fmt(baseline.pump,1)+' kWh');update('aiPump',fmt(smart.pump,1)+' kWh');update('s0',fmt(total,0)+' m³');update('s1',fmt(total-baseline.save,0)+' m³');update('s2',fmt(total-smart.save,0)+' m³');update('s3',fmt(smart.save,1)+' m³');update('s4',fmt(smart.pump,1)+' kWh');update('s5',fmt(smart.heat,0)+' kWh');update('s6',fmt(smart.save*price,0)+' TL');last=smart.series;canvasChart('tankChart',[last],['#008c91'])}
function setup(){document.querySelectorAll('[data-tab]').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('[data-tab]').forEach(x=>x.classList.remove('active'));document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.getElementById(b.dataset.tab).classList.add('active');if(b.dataset.tab==='sim')canvasChart('tankChart',[last],['#008c91']);if(b.dataset.tab==='overview')drawForecastChart()}));['tank','treat','eff','price'].forEach(id=>document.getElementById(id).addEventListener('input',()=>{let t=document.getElementById(id);document.getElementById(id==='tank'?'tankLabel':id==='treat'?'treatLabel':id==='eff'?'effLabel':'priceLabel').textContent=fmt(+t.value,id==='treat'?1:0)+(id==='tank'?' m³':id==='treat'?' m³/saat':id==='eff'?'%':' TL/m³')}));document.getElementById('calc').addEventListener('click',render);document.getElementById('mae').textContent=fmt(RESULT.forecast.random_forest_test_mae_m3_h,3);document.getElementById('naive').textContent=fmt(RESULT.forecast.training_mean_test_mae_m3_h,3);document.getElementById('leak').textContent=RESULT.anomalies.flagged_leak_hours+'/'+RESULT.anomalies.injected_leak_hours;document.getElementById('falseAlarm').textContent=RESULT.anomalies.false_alarm_hours_outside_leak_test+' saat';render();setupForecastChart();drawForecastChart()}window.addEventListener('resize',()=>{drawForecastChart();canvasChart('tankChart',[last],['#008c91'])});setup();
const PROCESS = __OPERATIONS_DATA__;
__OPERATIONS_JS__
</script></body></html>'''
panel = root / 'src'
data = {'summary': diagnostics, 'rows': telemetry, 'building_alarm': building_alarm}
html = html.replace('__DATA__', json.dumps(dashboard_rows, separators=(',', ':'), allow_nan=False))
html = html.replace('__RESULT__', json.dumps(res, ensure_ascii=False, separators=(',', ':'), allow_nan=False))
html = html.replace('__OPERATIONS_CSS__', (panel / 'operations_panel.css').read_text(encoding='utf-8'))
html = html.replace('__OPERATIONS_HTML__', (panel / 'operations_panels.html').read_text(encoding='utf-8'))
html = html.replace('__OPERATIONS_DATA__', json.dumps(data, ensure_ascii=False, separators=(',', ':'), allow_nan=False))
html = html.replace('__OPERATIONS_JS__', (panel / 'operations_panel.js').read_text(encoding='utf-8'))
(root / 'AquaLoop_AI_Demo.html').write_text(html, encoding='utf-8')
print('Created', root / 'AquaLoop_AI_Demo.html')
