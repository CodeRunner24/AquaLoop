# AquaLoop AI — Baştan sona hackathon proje dosyası

**Alt başlık** Yurt ve otellerde gri suyun yeniden kullanılması ve arıtma performansının erken izlenmesi.

**Güncel odak** Gri su altyapısı bulunan veya altyapısı tasarım aşamasındaki bir tesiste, çalışan arıtma hattının verim kaybını erken göstermek. Arıtma Alarmı ve Eşanjör Yatırımı, çevrimdışı demodaki yeni bölümlerdir.

### İlk uzman görüşmesi ve karşılığı

Kasım 2026'da alınan yazılı uzman görüşünde sonradan tesisat eklemenin maliyeti, personel ve ekipman sorunları, elektrik maliyeti nedeniyle tesisin devre dışı bırakılabilmesi ve erken ölçüm/uyarı ihtiyacı öne çıktı. Isı kaynağıyla kullanım ihtiyacının örtüşmesi de vurgulandı. Bu görüşme problem seçimini yönlendirir. Sorunların yaygınlığını saptamak ve alarmı doğrulamak için ek saha verisi gerekir.

| Tasarım kararı | Demoda gösterilen |
|---|---|
| Mevcut veya planlanan gri su altyapısı olan tesise odaklan | Gri suyunun toplanması, arıtılması ve rezervuara geri verilmesi |
| Erken bakım incelemesi | Beklenen debi ve elektrikten sapma, kWh/m³ ve arıza uyarısı |
| Eşanjör yatırımını binaya göre değerlendir | Saatlik ısı-talep eşleşmesi, kurulum ve yıllık işletme maliyeti, değiştirilebilir basit geri ödeme |

Arıtma alarmı 45 gün normal eğitim, 15 gün eşik ayarı, 30 gün sentetik testle değerlendirilir. Dört olayın tamamı iki yöntemle de tespit edildi. Öğrenen model ve sabit eşikte ortalama gecikme sırasıyla **4,75** ve **11,75 saat**, arıza dışındaki alarm süreleri **1** ve **6 saat**. Ölçüm ve alarmlar `outputs/process_diagnostics.csv` dosyasında, olay kıyası `outputs/process_benchmark.json` dosyasındadır. Saha pilotunda sayaç ve bakım kayıtlarıyla aynı kıyas tekrarlanacaktır.

**Kullanıcı problemi:** Bir otel veya yurtta günlük büyük su tüketimi gerçekleşir. Duş ve lavabo gibi kaynaklardan uygun biçimde toplanabilecek gri su kanalizasyona karışabilir; içindeki sıcaklık farkı da boşa gidebilir. Aynı tesiste tuvalet rezervuarı gibi içilemez kullanımlar için şebeke suyu harcanır. İşletmeci çoğu zaman hangi saatte ne kadar su toplanacağı, ne kadar yeniden kullanılabileceği ve bunun enerji değerini tek bir ekranda görmez. Gerçek tesislerde bu gözlemlerin ne ölçüde doğru olduğu görüşmelerle test edilecektir.

## 1 — Tasarım odaklı düşünme

| Aşama | Yapılacak iş | Kanıt/çıktı |
|---|---|---|
| Keşfet | Bina yöneticisi, mekanik tesisat uzmanı, çevre mühendisi görüşmeleri | Yazılı cevaplar, alıntı izni, problem günlüğü |
| Tanımla | En fazla 1 ana kullanıcı ve onun en yüksek maliyetli su sorunu | İhtiyaç cümlesi ve en az 3 görüşme bulgusu |
| Fikir üret | Su, ısı, anomali, pompa alt sistemlerini değerlendir | Etki/uygulanabilirlik matrisi |
| Prototiple | 90 günlük sentetik verili karar ekranı, model baz kıyasları | Çalışan çevrimdışı HTML ve Python kaynak kodu |
| Test et | İki kontrol senaryosu, arıza enjeksiyonu, görüşme geri bildirimi | Nicel değerlendirme + sınırlılık raporu |

**Problem cümlesi:** “Sıcak su kullanımının yoğun olduğu bir binanın tesis yöneticisi, güvenli şekilde geri kazanılabilecek su ve ısının miktarını önceden bilip işletmeyi planlayamaz; çünkü veri ve karar mekanizmaları ayrı çalışır.” Bu bir test edilecek hipotezdir, doğrulanmış sektör görüşü değildir.

## 2 — Hedef kullanıcı ve kullanım alanı

- İlk pazar: 100–500 yataklı öğrenci yurdu / otel; büyük ölçekte hastane ve kampüs ikinci aşama.
- Satın alma kararı: tesis/enerji yöneticisi, işletme müdürü, mal sahibi.
- Teknik etkileyenler: makine mühendisi, çevre mühendisi, yüklenici firma, su idaresi ve regülatör.
- Kullanıcı işi: günlük hedefleri ve su kalitesi durumunu izlemek, maliyetli sapmaları bulmak, bakım uyarıları almak ve yatırım fizibilitesini şeffaf hesaplamak.

## 3 — Modüller

### WaterLoop: Yeniden kullanım

Duş/lavabo gibi uygun gri su kaynakları siyah sudan ayrı toplanır. İlk ham tank, sertifikalı arıtma prosesi, kalite kapısı, arıtılmış su tankı ve içilemez dağıtım şebekesi vardır. Kalite geçmezse güvenli yönlendirme ve şebeke yedeği sağlanır. Çıkış önceliği: klozet rezervuarı; diğer kullanım alanları ancak özel mühendislik ve izin şartlarına göre.

**Demo hesabı:** Saatlik ham tank: `R[t+1] = min(Rmax, R[t] + giren − arıtılan)`; temiz tank: `C[t+1] = min(Cmax, C[t] + arıtılan − kullanılan)`; `kullanılan <= ihtiyaç`, `arıtılan <= kapasite`. Taşma kanalizasyona yönlendirilir. Gerçek arıtma teknolojisi ve kalite testi simüle edilmez.

### HeatLoop: Atık ısı geri kazanımı

Isı eşanjörü, atık su hattından soğuk besleme hattına ısı aktarır. Teorik ısı `Q(kWh) = V(m³) × 1000 kg/m³ × 4.186 kJ/(kg·°C) × ΔT(°C) × η / 3600` ile hesaplanır. Eşanjör Yatırımı sekmesi aktarılabilecek ısıyı aynı saatin atık su ve eşzamanlı besleme suyu akışlarından küçük olanıyla, ayrıca sıcak su ihtiyacıyla sınırlar. Yıllık bakım ile yardımcı elektrik düşülür. Net fayda pozitifse kurulum dahil yatırım net yıllık faydaya bölünür. Isı akışı, ekipman seçimi ve maliyetler pilot binada ölçülüp doğrulanacaktır.

### AI Control: Tahmin ve karar

- RandomForestRegressor: saat, hafta günü ve doluluğa göre önümüzdeki saat içilemez su talebi.
- IsolationForest: debi/çalışma profili sapmalarını alarm adayı olarak işaretler.
- İki işletme stratejisi: sabit saat kurallı kontrol ve kısa vadeli tahmine göre çalışan sezgisel kontrol. Aynı sentetik talep ve su akışı kullanılır.
- Bir sonraki faz: elektrik tarifesi, dinamik pompa eğrisi ve sıcak su talebi ile fiziksel kısıtlı MPC. **Mevcut sürüm MPC veya RL içermez.**
- Karar hiçbir zaman sertifikalı su kalitesi önlemlerini, mekanik bypass veya operatörün manuel kumandasını geçersiz kılamaz.

### CityLoop (gelecek faz)

Birden fazla binanın agregat su tasarrufu potansiyeli, arz-talep etkisi ve bakım önceliklerini ilçe/şehir düzeyinde görünür kılacak karşılaştırmalı gösterge paneli. Bina-level prototipte şehir altyapısına veri bağlantısı veya şehir bazlı optimizasyon **yoktur**.

## 4 — Çalışan prototip

- **Dosya:** `AquaLoop_AI_Demo.html` — tarayıcıda çevrimdışı açılır.
- **Veri:** 90 günlük saatlik sentetik bina; ilk 60 gün eğitim, son 30 gün test.
- **Model dosyası:** `src/run_project.py`; sonuçlar `outputs/results.json`.
- **Dashboard:** su ve ısı kartları; 7 günlük tahmin grafiği; senaryo parametreleri; su ve pompaya ilişkin iki strateji kıyası; AI ve güvenlik açıklamaları.
- **Etkileşim:** tank hacmini, saatlik arıtma kapasitesini, ısı verimi varsayımını ve varsayımsal su fiyatını değiştirip 30 günlük saatlik su modelini yeniden çalıştırma.

### İlk kontrollü sentetik test sonucu

- RF talep tahmini test MAE: **0,0481 m³/saat**; eğitim dönemi ortalamasını tahmin eden basit referans MAE: **0,2578 m³/saat**.
- Kaçak enjeksiyonu: 13 saat; 9 saat alarm, kaçak dışında 26 yanlış/başka anomali alarm saati. Bu gerçek kaçak tespit performansı değildir.
- Test döneminde toplam şebeke kullanımı, geri kazanım öncesi **1.637,8 m³/30 gün**.
- Klasik kontrol: **441,8 m³** gri su kullanımı; **314,89 kWh** modellenmiş pompa elektriği.
- AI destekli sezgisel kontrol: **441,8 m³** gri su kullanımı; **314,92 kWh** modellenmiş pompa elektriği.
- Teorik brüt ısı geri kazanım potansiyeli: **4.941,49 kWh** (varsayımsal %45 verim, gerçek kullanım talebiyle sınırlandırılmamış).
- **Dürüst sonuç:** Bu sentetik testte AI tabanlı işletim klasik kontrolden daha başarılı değildir. Tahmin modeli ayrı bir görevde iyi performans gösterir; operasyonel katkı için gerçekçi kontrol optimizasyonu ve saha verisi gereklidir.

## 5 — Jüri kriterlerine cevap

1. **Problemi anlama:** İnterview ve sorun bazlı kullanıcı haritası; önceden çözüm dayatmak yerine hipotezleri test etme.
2. **Yenilikçilik:** Su ve ısı geri kazanımını pompa/arıtma kararlarıyla aynı veri çerçevesinde ele alan karar destek katmanı. Bunun bileşenlerinin dünyada ilk olduğu iddia edilmez.
3. **AI:** Ölçülebilir saatlik tahmin ve anomali tespiti; sabit kurala karşı kontrol benchmarkı.
4. **Uygulanabilirlik:** Mevcut standart tesisat alt sistemlerine bağlanabilecek dijital katman, sertifikalı güvenlik bariyeri, kademeli pilot planı.
5. **Etki:** Şebekeden alınmayan m³, gerçekten kullanılan kWh, karbon etkisi, kWh/m³, yanlış alarm, toplam sahip olma maliyeti. Yalnızca varsayım olanlar açık işaretlenir.
6. **Sunum:** Canlı senaryo değişimi → sonuç → önemli sınırlılık → pilot planı.

## 6 — Başlıca riskler ve güvenlik

| Risk | Önlem |
|---|---|
| Su kalitesi / patojen | Tasarımı yetkili çevre mühendisi yapar; sertifikalı arıtma, ölçüm, güvenli bypass, bağımsız kontrol |
| İçme suyu ile karışma | Fiziksel ayrım, geri akış önleyici, renk kodu, izinli bağlantı |
| Sıcaklık ve debi değişkenliği | Saha ölçümü, ısı talebi ve eşanjör doğrulama |
| Tankta biyolojik risk | Rezidans süresi ve bakım protokolü; demo bunları hesaplamıyor |
| Enerji tasarrufu abartısı | Aynı talep ve sıcaklık girdileriyle benchmark; net tüketim ölçümü |
| İşletme maliyeti | Capex, Opex, kalibrasyon, servis, analiz ve enerji birim fiyatı ile TCO |
| Veri gizliliği | Kişi bazlı tüketim değil bina/zon agregasyonu; erişim yetkisi |
| Veri yokluğu | Simülasyon yalnızca fikir doğrulama; gerçek saha kanıtı diye sunulmaz |

## 7 — Minimum veri şeması

Zaman damgası, yerel saat, haftanın günü, bina doluluk tahmini, ana su sayacı (m³/h), gri su hattı debisi (m³/h), içilemez su tüketimi (m³/h), giriş/çıkış sıcaklığı (°C), kirli/temiz tank seviyeleri (m³), pompa kWh, arıtma performansı/kalite durumu, bakım olayı, elektrik tarifesi ve sıcak su talebi. Gerçek veri mümkün olduğunca en az 15 dakikalık çözünürlükle kaydedilmeli; demo saatliktir.

## 8 — İş modeli

**Müşteri:** Oteller, üniversite kampüsleri, yurtlar, hastaneler, tesis yönetimi firmaları.

**Ürün:** Bina kontrol sistemlerine bağlanan optimizasyon/raporlama yazılımı + uygulamaya özel mühendislik danışmanlığı. Sensör/tesisat kurulumunu partner mekanik tesisat firmaları yapabilir.

**Önerilen fiyat modeli:** Kurulum/entegrasyon bedeli + bina başına yıllık izleme lisansı; fiyat henüz doğrulanmış müşteri görüşmeleri olmadan belirlenmemeli. Yatırım geri dönüşü için yerel fiyat, CAPEX ve OPEX hesaplanmalı.

## 9 — 3 dakikalık final sunumu metni

**0:00–0:30 Problem** “Bir yurtta duş suyu kanalizasyona giderken tuvaletler için yeniden şebeke suyu kullanılıyor. İlk uzman görüşmemizde, gri su tesisi kurulduktan sonra arızaların ve elektrik giderinin sistemi kullanılır tutmayı zorlaştırabileceğini öğrendik.”

**0:30–1:10 Çözüm:** “AquaLoop AI, uygun gri suyu arıtıp içilemez amaçla yeniden kullanma, atık ısısını yakalama ve bu sistemlerin işletimine ilişkin veri odaklı karar desteğini bir araya getiriyor. Fiziksel sistemler yetkili mühendislik ve su güvenliği tedbirlerine bağlı.”

**1:10–2:00 Demo** “Önce tanktaki suyun rezervuar ihtiyacına nasıl yettiğini gösteriyoruz. Sonra bir arıza seçiyoruz. Ölçülen debi düşerken modelin beklediği değer grafikte görünüyor ve operatör inceleme uyarısı alıyor. Eşanjör yatırımı sekmesinde sıcak su ihtiyacı ve bakım giderinin geri ödeme süresini nasıl değiştirdiğini gösteriyoruz.”

**2:00–2:35 Kanıt** “Varsayılan su senaryosunda her iki arıtma kontrolü yaklaşık 442 m³ gri suyu yeniden kullandı. Arıtma alarmı deneyinde dört sentetik arızanın tamamını iki yöntem de yakaladı. Model ortalama 4,75 saatte, sabit eşik 11,75 saatte uyardı. Şimdi gerçek ölçümler ve bakım kayıtlarıyla aynı karşılaştırmayı tekrarlamak istiyoruz.”

**2:35–3:00 Pilot çağrısı:** “Aradığımız ilk ortak, su sıcaklığı ve debi ölçümlerine erişimi olan bir otel veya yurttur. Üç aylık veriyi toplayıp önce shadow mode'da, sonra mühendis onayıyla gerçek tasarrufu ölçeceğiz.”

## 10 — Uzmanlara gönderilen araştırma e-postaları ve takip

20 Kasım 2026 tarihinde beş yazılı görüş talebi gönderildi. Sonradan paylaşılan ilk yazılı uzman yanıtının bulguları belgenin başında özetlenmiştir. Diğer yanıtların durumu bilinmiyor. Takip görüşmesinde tesisin devre dışı kalmasına yol açan bir olay ve olay öncesindeki debi, seviye veya elektrik ölçümünü istemek planlanıyor.

## 11 — Sunumdan önce yapılacaklar

- Görüşme yanıtlarından problem ve kullanıcı alıntıları (izinli) ekle.
- Örnek bina türünü netleştir, uygun su kaynaklarını ve içilemez kullanım sınırını göster.
- Bölgesel su/elektrik tarifelerini ve yerel mevzuatı uzmanla doğrula.
- 1 sayfalık saha tesisat blok diyagramı hazırla.
- Metriklerde sentetik vs gerçek veriyi belirgin şekilde ayır.
- Demo parametrelerinde beklenmedik sıfır/hata senaryolarını test et.
- Fiziksel güvenlik iddialarını mühendis onayı olmadan kullanma.

## 12 — Kaynaklar

- EPA, *Onsite Non-Potable Water Reuse Resources*: https://www.epa.gov/waterreuse/onsite-non-potable-water-reuse-resources
- EPA, *Risk-Based Microbial Treatment Targets for Water Reuse*: https://www.epa.gov/waterreuse/risk-based-microbial-treatment-targets-water-reuse
- U.S. DOE, *Pump Systems*: https://www.energy.gov/cmei/ito/pump-systems
- Resmî Gazete, 01.09.2024, Planlı Alanlar İmar Yönetmeliği (gri su tanımı): https://www.resmigazete.gov.tr/eskiler/2024/09/20240901-1.htm

Kaynaklar kavramsal referans niteliğindedir. Uygulama yapılacak şehrin yürürlükteki izinleri, su kalitesi gereklilikleri ve proje teknik hesapları uzmanlar tarafından ayrıca doğrulanmalıdır.
