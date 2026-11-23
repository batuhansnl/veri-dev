# Elektrikli Araçlarda Sıcaklığın Menzile Etkisi

**Veri Madenciliği ve Bilgi Keşfi** dersi dönem ödevi — makine öğrenmesi ile elektrikli araç tüketiminin ve menzilinin tahmini.

Bu bir **regresyon** projesidir: dış sıcaklık, sürüş tipi (şehir içi/otoyol), batarya kapasitesi ve iklimlendirme bilgisinden aracın **tüketimi (kWh/100km)** ve **menzili (km)** tahmin edilir.

## İçerik

| Dosya | Açıklama |
|---|---|
| `ev_menzil.py` | Uçtan uca analiz: ön işleme, betimsel istatistik, modelleme (Doğrusal Regresyon + Random Forest), değerlendirme ve grafikler |
| `panel_harita.html` | İnteraktif araç — Türkiye haritasından il seç, 45 gerçek EV modelinden birini seç, bugünkü tahmini menzili gör |
| `panel.html` | Sade interaktif menzil hesaplayıcı (harita olmadan) |
| `build_panel.py` | `panel_harita.html` dosyasını harita SVG'si + il sıcaklıkları + EV listesinden üreten betik |
| `grafikler/` | Analiz çıktısı grafikler (PNG) |
| `deck/` | Sunum destesi kaynak dosyaları |
| `_harita/` | Harita kaynak dosyaları (dnomak/svg-turkiye-haritasi, MIT) |

## Çalıştırma

Gerekli kütüphaneler: `pandas`, `numpy`, `scikit-learn`, `matplotlib`, `seaborn`

```bash
pip install pandas numpy scikit-learn matplotlib seaborn
python ev_menzil.py
```

Grafikler `grafikler/` klasörüne kaydedilir.

## Yöntem ve Sonuçlar

- **Veri:** 6.000 sürüş kaydı, 6 değişken (fiziğe dayalı üretilmiş demo veri; gerçek veri için [ev-database.org](https://ev-database.org)).
- **Model:** Doğrusal Regresyon ve Random Forest Regresyon, %70-30 eğitim-test ayrımı.
- **Metrikler:** En iyi model Doğrusal Regresyon — **R² = 0,95**, MAE = 0,66 kWh/100km.

### En önemli bulgular
1. Sıcaklık en belirleyici faktör; en verimli nokta ~20 °C ("U" biçimli ilişki).
2. Otoyol sürüşü, aerodinamik direnç nedeniyle tüketimi belirgin artırır.
3. Kış menzil kaybı büyük: −15 °C'de ~%40, soğuk + otoyolda ~%46.

> Not: Rakamlar fiziğe dayalı demo veriye aittir; yaklaşık değerlerdir.

## Kaynaklar

- [ev-database.org](https://ev-database.org)
- [Geotab — EV range vs temperature](https://www.geotab.com/ie/blog/ev-range/)
- Harita: [dnomak/svg-turkiye-haritasi](https://github.com/dnomak/svg-turkiye-haritasi) (MIT)
