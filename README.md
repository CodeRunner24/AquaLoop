# AquaLoop AI

Wilo Water AI Hackathon 2026 için, yurt ve otellerde gri suyun yeniden kullanılması ve arıtma hattının izlenmesi üzerine geliştirilmiş çevrimdışı prototip. Eşanjör yatırımı, binanın aynı saat içinde kullanabileceği ısıya göre ayrıca değerlendirilebilir.

## Wilo Water AI Hackathon 2026 — Jüri teslim dosyaları

### [💧 İnteraktif demoyu aç / indir](https://github.com/CodeRunner24/AquaLoop/blob/main/AquaLoop_AI_Demo.html)
[HTML dosyasını doğrudan indir](https://github.com/CodeRunner24/AquaLoop/raw/refs/heads/main/AquaLoop_AI_Demo.html) · Kurulum gerektirmez; indirip tarayıcıda açın.

### [▶️ Tanıtım videosunu izle](submission/AquaLoop_AI_Tanitim.mp4)
3 dakika 40 saniye · Sessiz tanıtım · [Altyazı](submission/AquaLoop_AI_Tanitim.srt) · [MP4 indir](https://github.com/CodeRunner24/AquaLoop/raw/refs/heads/main/submission/AquaLoop_AI_Tanitim.mp4)

### [📄 A3 proje posterini görüntüle (PDF)](submission/AquaLoop_AI_Proje_Posteri.pdf)
[Tek sayfalık poster — düzenlenebilir PowerPoint](submission/AquaLoop_AI_Proje_Posteri.pptx)

### [📊 Jüri sunumunu görüntüle (PDF)](submission/AquaLoop_AI_Juri_Sunumu.pdf)
[10 slayt — düzenlenebilir PowerPoint](submission/AquaLoop_AI_Juri_Sunumu.pptx)

### [🔬 Teknik proje planı ve saha araştırması](docs/PROJECT_PLAN_TR.md)

**Sentetik deney sonuçları:** 4/4 arıza tespiti; ortalama ilk alarm gecikmesi 11,75 saatten 4,75 saate düştü. Bu bulgular gerçek saha ölçümü değildir.

---

## Demoyu açma

`AquaLoop_AI_Demo.html` dosyasını Chrome, Edge veya Firefox ile açın. Kurulum ya da internet bağlantısı gerekmez.

0. **Genel Bakış** sekmesindeki 7 günlük saatlik talep grafiğinde düz mavi çizgi sentetik testte gerçekleşen, kesikli turkuaz çizgi ise Random Forest tarafından tahmin edilen içme suyu gerektirmeyen kullanım talebini gösterir. Fare imlecini grafiğe getirdiğinizde (veya mobilde dokunduğunuzda) gün/saat, iki değer ve mutlak fark görünür. Ok tuşlarıyla da saatler arasında gezilebilir. Eksen birimi m³/saat; alt bölümde sadece gösterilen 168 saatin MAE sonucu yer alır. Bu grafik klasik/AI işletim politikalarını karşılaştırmaz.
1. **Senaryo Laboratuvarı** sekmesinde tank hacmi ve arıtma kapasitesini değiştirerek 30 günü yeniden hesaplayın.
2. **Arıtma Alarmı** sekmesinde normal işletim ile dört arıza kesitini karşılaştırın. Ölçülen ve beklenen debi/elektrik ile ilk alarm saatini görün.
3. **Eşanjör Yatırımı** sekmesinde yatırım, fiyat, bakım ve sıcak su varsayımlarını girin. Yıllık fayda ve geri ödeme anında güncellenir.

## İlk uzman görüşmesinin etkisi

Proje geliştirme sürecinde MTMD (Mekanik Tesisat Müteahhitleri Derneği) müdürü **Nilgün İlik Eren** ile e-posta üzerinden iletişim kurduk. Onun yönlendirmesiyle **Melek Yıldız** (Meta Mühendislik sahibi, kimya mühendisi ve su arıtımı alanında çalışan uzman) ile iletişime geçerek yazılı saha görüşü aldık. Görüşü üç somut tasarım kararına dönüştürdük:

- Gri suyu ayrı toplama ve dağıtma hattı sonradan eklendiğinde tadilat zorlaşıyor. İlk pilot için mevcut gri su altyapısı olan veya tesisatı tasarlanan bir yapı hedefleniyor.
- Kalifiye personel, ekipmanın çalışabilirliği ve elektrik gideri sistemin kullanımda kalmasını etkiliyor. Arıtma alarmı, beklenenden düşük debiyi veya yüksek pompa elektriğini inceleme için işaretliyor.
- Eşanjör hesabı, ısı kaynağıyla kullanılabilir sıcak su ihtiyacının aynı saat içinde örtüşmesine bağlı. Görüşme tek bir uzmanın değerlendirmesini yansıtır.

## Veriler ve yeniden üretim

`data/synthetic_building_90d_hourly.csv` dosyasında 90 günlük saatlik sentetik bina profili yer alıyor. Hazır veriyle yeni alarm çıktısı ve HTML'yi üretmek için Python ve NumPy yeterli.

```bash
python -m pip install numpy
python make_dashboard.py
```

Binanın kaynak verisini, önceki talep/kaçak modellerini ve ilk su dengesini de baştan üretmek için:

```bash
python -m pip install -r requirements.txt
python src/run_project.py
python make_dashboard.py
```

| Çıktı | İçerik |
| --- | --- |
| `outputs/results.json` | Random Forest talep tahmini, ana sayaç kaçak deneyi ve orijinal su senaryoları |
| `outputs/process_diagnostics.csv` | 30 günlük saatlik arıtma telemetrisi, beklenen debi ve elektrik, arıza etiketleri ve iki alarm |
| `outputs/process_benchmark.json` | Dört olayın ilk alarm gecikmeleri ve arıza dışı alarm saatleri |
| `docs/PROJECT_PLAN_TR.md` | Uzman görüşmesi, teknik kapsam, jüri anlatımı ve pilot planı |

## Alarm deneyi

Doğrusal regresyon, arıtma komutu ve iki tank seviyesinden beklenen arıtılan hacmi ve pompa elektriğini öğrenir. Normal ilk 45 gün model eğitimi, sonraki 15 gün eşik ayarı, son 30 gün test için kullanılır. İki yöntem de normal kalibrasyon verisindeki kendi skorunun %97 persentilini eşik alır ve ardışık iki uygun saat boyunca eşik aşımı arar. Düşük komut seviyesinde ölçüm oranı kararsız olduğu için alarm uygulanmaz. Model, düşük debi veya yüksek enerji sapmasına bakar. Klasik kontrol, sabit bir kWh/m³ eşiğini kullanır. İki yöntem de dört sentetik olayı yakalar. Modelin ortalama ilk uyarı gecikmesi **4,75 saat**, sabit eşiğin **11,75 saat**. Arıza dışında sırasıyla **1** ve **6 saat** boyunca alarm verilir. Bu sonuçlar seçilen sentetik olaylara aittir.

Ana sayaç için mevcut Isolation Forest deneyi ayrı bir bakım kartı oluşturur. En uzun kesintisiz alarmın başlangıcı, süresi, ilk 60 günün aynı saat ortalamalarına göre tahmini fazla tüketim ve sayacın kapsadığı bölge gösterilir.

## Eşanjör hesabı

Her saatte teorik kaynak ısısı, gri su hacmi × suyun hacimsel ısı kapasitesi × pozitif kaynak sıcaklık farkı × eşanjör etkinliği olarak hesaplanır. Gerçekleşebilir transfer için kaynak ve aynı anda ön ısıtılabilecek besleme suyunun hacimlerinden küçük olanı kullanılır. Bu değer, hedef sıcaklığa göre hesaplanan talebi aşamaz. 30 günlük profil yıllık işletme günlerine ölçeklenir. Isı transferi hesabının temeli için [ASHRAE Handbook, Heat Transfer](https://handbook.ashrae.org/Handbooks/F25/SI/f25_ch04/f25_ch04_si.aspx).

**Basit geri ödeme = kurulum dahil ek eşanjör yatırımı ÷ (yıllık faydalı ısı × ikame ısının birim bedeli − bakım − yardımcı elektrik).** Net fayda pozitif değilse geri ödeme gösterilmez. Varsayılan maliyetler temsili senaryo girdileridir. Hesap ısı eşanjörüne aittir ve finansman, iskonto, enflasyon, ekipman değişimi ve ayrı gri su arıtma yatırımını içermez.

Varsayılan örnekte 180.000 TL kurulum dahil yatırım, yılda 7.897 kWh faydalı ısı ve yaklaşık 10.185 TL net yıllık fayda ile **17,67 yıl** basit geri ödeme verir. Değerler tesis ve teklif bilgileriyle güncellenebilir.

Prototip sentetik su dengesi, tüketim ve arıza senaryolarını gösterir. Gerçek arıtma kalitesi ve su güvenliği için bağımsız ölçüm, kontroller ve yetkin mühendislik gerekir. Bakım uyarısının işlevi operatöre inceleme sinyali vermektir.
