# -*- coding: utf-8 -*-
"""
========================================================================
ELEKTRİKLİ ARAÇ MENZİL / TÜKETİM ANALİZİ - Veri Madenciliği Ödevi
========================================================================
Makine Öğrenmesi ile Sıcaklığa ve Sürüş Koşullarına Göre
Elektrikli Araç Tüketiminin (kWh/100km) ve Menzilinin (km) Tahmini

Bu bir REGRESYON problemidir (sayı tahmini) - önceki sınıflandırma
projelerinden farklı olarak burada "kaç km gider?" sorusuna cevap ararız.

Ödevin tüm adımlarını içerir:
  1. Veri Keşfi ve Ön İşleme
  2. Betimsel İstatistikler
  3. Modelleme (Doğrusal Regresyon + Random Forest Regresyon)
  4. Değerlendirme (R², MAE, RMSE)
  5. Görselleştirme (sıcaklık-menzil eğrisi, özellik önemi...)
  6. Özet Bulgular + "Erzurum senaryosu"

NOT: Demo, dışarıdan dosya indirmeden çalışsın diye GERÇEKÇİ SENTETİK veri
     üretir. Üretim, elektrikli araçların bilinen fiziğine dayanır:
     menzil ~20°C'de en yüksektir, soğukta (ısıtma + batarya verimi) ve
     sıcakta (klima) düşer; otoyolda şehir içine göre daha çok tüketilir.

     Gerçek veri için ev-database.org'dan model + farklı koşullardaki
     menzil değerleri çekilip kullanılabilir.
========================================================================
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

RASTGELE_TOHUM = 42
np.random.seed(RASTGELE_TOHUM)
GRAFIK = os.path.join(os.path.dirname(__file__), "grafikler")
os.makedirs(GRAFIK, exist_ok=True)
sns.set_theme(style="whitegrid")


def baslik(m):
    print("\n" + "=" * 70); print(m); print("=" * 70)


# ==================================================================
# 0) VERİ OLUŞTURMA
# ==================================================================
def veri_olustur(n=6000):
    rng = np.random.default_rng(RASTGELE_TOHUM)

    # Dış sıcaklık (°C): Türkiye kışından yazına -20 ... +40
    sicaklik = rng.uniform(-20, 40, n)
    # Sürüş tipi: 1 = otoyol (yüksek hız), 0 = şehir içi
    otoyol = rng.integers(0, 2, n)
    # Batarya kapasitesi (kWh) - popüler modeller
    batarya = rng.choice([40, 52, 58, 64, 77, 82, 100], n)
    # Isıtma/klima açık mı (soğuk/sıcakta genelde açık)
    iklimlendirme = ((sicaklik < 8) | (sicaklik > 28)).astype(int)
    iklimlendirme = np.where(rng.random(n) < 0.15, 1 - iklimlendirme, iklimlendirme)  # biraz gürültü

    # --- Tüketim (kWh/100km) fiziğe dayalı ---
    base = 15.0
    sapma = sicaklik - 20.0                       # 20°C en verimli
    u_sekli = 0.004 * sapma**2                     # hem soğuk hem sıcak artırır
    soguk_ek = np.where(sicaklik < 20, 0.09 * (20 - sicaklik), 0)  # soğuk daha kötü
    otoyol_ek = 3.2 * otoyol                        # aerodinamik
    iklim_ek = 1.8 * iklimlendirme
    gurultu = rng.normal(0, 0.8, n)

    tuketim = base + u_sekli + soguk_ek + otoyol_ek + iklim_ek + gurultu
    tuketim = tuketim.clip(10, 40)

    menzil = (batarya / tuketim) * 100            # km

    df = pd.DataFrame({
        "Sicaklik_C": sicaklik.round(1),
        "Otoyol": otoyol,
        "Batarya_kWh": batarya,
        "Iklimlendirme": iklimlendirme,
        "Tuketim_kWh_100km": tuketim.round(2),
        "Menzil_km": menzil.round(1),
    })

    # Gerçek hayattaki kirlilik: birkaç eksik sıcaklık + hatalı giriş
    df.loc[df.sample(frac=0.01, random_state=1).index, "Sicaklik_C"] = np.nan
    df.loc[df.sample(n=4, random_state=2).index, "Sicaklik_C"] = 999   # sensör hatası
    return df


# ==================================================================
# 1) VERİ KEŞFİ ve ÖN İŞLEME
# ==================================================================
def kesif_ve_onisleme(df):
    baslik("1) VERİ KEŞFİ ve ÖN İŞLEME")
    print(f"Veri boyutu: {df.shape[0]} satır, {df.shape[1]} sütun\n")
    print(df.head().to_string(index=False))

    print(f"\nEksik veri:")
    print(df.isnull().sum()[df.isnull().sum() > 0])

    # Hatalı sıcaklık (999) -> NaN
    df.loc[df["Sicaklik_C"] > 60, "Sicaklik_C"] = np.nan
    # Eksik sıcaklıkları medyan ile doldur
    med = df["Sicaklik_C"].median()
    df["Sicaklik_C"] = df["Sicaklik_C"].fillna(med)
    print(f"\n-> Hatalı (999) ve eksik sıcaklık değerleri medyan ({med:.1f}°C) ile düzeltildi.")
    return df


# ==================================================================
# 2) BETİMSEL İSTATİSTİKLER
# ==================================================================
def betimsel(df):
    baslik("2) BETİMSEL İSTATİSTİKLER")
    print(df[["Sicaklik_C", "Tuketim_kWh_100km", "Menzil_km"]].describe().round(1))

    print("\nSıcaklık aralığına göre ortalama menzil:")
    df2 = df.copy()
    df2["Aralik"] = pd.cut(df2["Sicaklik_C"], [-20, 0, 10, 20, 30, 40],
                           labels=["Çok soğuk\n(-20..0)", "Soğuk\n(0..10)",
                                   "Ilık\n(10..20)", "Sıcak\n(20..30)", "Çok sıcak\n(30..40)"])
    print(df2.groupby("Aralik", observed=True)["Menzil_km"].mean().round(0))


# ==================================================================
# GÖRSELLEŞTİRME
# ==================================================================
def grafikler(df):
    baslik("GÖRSELLEŞTİRME")

    # a) Sıcaklık - Menzil ilişkisi (en önemli grafik!)
    plt.figure(figsize=(7.5, 5))
    sns.scatterplot(data=df.sample(1500, random_state=1), x="Sicaklik_C", y="Menzil_km",
                    hue="Otoyol", palette={0: "#4C72B0", 1: "#DD8452"}, alpha=0.5, s=18)
    plt.axvline(20, color="green", ls="--", alpha=0.6, label="En verimli (~20°C)")
    plt.title("Dış Sıcaklığa Göre Menzil\n(Soğukta ve çok sıcakta menzil düşüyor)")
    plt.xlabel("Dış Sıcaklık (°C)"); plt.ylabel("Menzil (km)")
    h, l = plt.gca().get_legend_handles_labels()
    plt.legend(h, ["Şehir içi", "Otoyol", "En verimli (~20°C)"], title="")
    plt.tight_layout(); plt.savefig(f"{GRAFIK}/01_sicaklik_menzil.png", dpi=120); plt.close()

    # b) Sürüş tipine göre ortalama tüketim
    plt.figure(figsize=(6, 4))
    ort = df.groupby("Otoyol")["Tuketim_kWh_100km"].mean()
    ax = sns.barplot(x=["Şehir içi", "Otoyol"], y=ort.values, hue=["Şehir içi", "Otoyol"],
                     palette=["#4C72B0", "#DD8452"], legend=False)
    ax.set_title("Sürüş Tipine Göre Ortalama Tüketim"); ax.set_ylabel("kWh / 100 km")
    for i, v in enumerate(ort.values):
        ax.text(i, v, f"{v:.1f}", ha="center", va="bottom")
    plt.tight_layout(); plt.savefig(f"{GRAFIK}/02_surus_tipi.png", dpi=120); plt.close()

    # c) Korelasyon
    plt.figure(figsize=(6.5, 5.5))
    sns.heatmap(df.corr(numeric_only=True), cmap="coolwarm", center=0, annot=True,
                fmt=".2f", linewidths=0.3)
    plt.title("Korelasyon Isı Haritası"); plt.tight_layout()
    plt.savefig(f"{GRAFIK}/03_korelasyon.png", dpi=120); plt.close()
    print("-> 01_sicaklik_menzil.png, 02_surus_tipi.png, 03_korelasyon.png kaydedildi")


# ==================================================================
# 3-4) MODELLEME ve DEĞERLENDİRME (REGRESYON)
# ==================================================================
def modelle(df):
    baslik("3) MODELLEME SÜRECİ (Regresyon)")

    # Özellik mühendisliği: U-şeklini yakalamak için sıcaklık sapma terimleri
    d = df.copy()
    d["Sapma"] = d["Sicaklik_C"] - 20
    d["Sapma2"] = d["Sapma"] ** 2
    d["Soguk_ek"] = (20 - d["Sicaklik_C"]).clip(lower=0)

    ozellikler = ["Sapma", "Sapma2", "Soguk_ek", "Otoyol", "Iklimlendirme", "Batarya_kWh"]
    X = d[ozellikler]
    y = d["Tuketim_kWh_100km"]   # önce tüketimi tahmin ediyoruz

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.30, random_state=RASTGELE_TOHUM)
    print(f"Eğitim: {X_train.shape[0]} | Test: {X_test.shape[0]}  (%70-30)")

    modeller = {
        "Doğrusal Regresyon": LinearRegression(),
        "Random Forest": RandomForestRegressor(n_estimators=200, random_state=RASTGELE_TOHUM, n_jobs=-1),
    }

    baslik("4) DEĞERLENDİRME METRİKLERİ")
    sonuclar = {}
    for ad, model in modeller.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        sonuclar[ad] = dict(r2=r2, mae=mae, rmse=rmse, y_pred=y_pred, model=model)
        print(f"\n----- {ad} -----")
        print(f"R² (açıklama gücü) : {r2:.3f}   (1'e ne kadar yakınsa o kadar iyi)")
        print(f"MAE (ort. hata)    : {mae:.2f} kWh/100km")
        print(f"RMSE               : {rmse:.2f} kWh/100km")

    # Doğrusal modelin katsayıları (panel için)
    lr = sonuclar["Doğrusal Regresyon"]["model"]
    print("\nDoğrusal Regresyon katsayıları (tüketim tahmini için):")
    for ad, k in zip(ozellikler, lr.coef_):
        print(f"  {ad:15s}: {k:+.4f}")
    print(f"  {'sabit':15s}: {lr.intercept_:+.4f}")
    import json
    panel = {"ozellikler": ozellikler, "coef": lr.coef_.tolist(), "intercept": float(lr.intercept_)}
    print("\nPANEL_JSON=" + json.dumps(panel))

    gorsel_sonuc(y_test, sonuclar, ozellikler)
    return y_test, sonuclar


def gorsel_sonuc(y_test, sonuclar, ozellikler):
    # Gerçek vs Tahmin (en iyi model)
    en_iyi = max(sonuclar, key=lambda k: sonuclar[k]["r2"])
    yp = sonuclar[en_iyi]["y_pred"]
    plt.figure(figsize=(6, 5.5))
    plt.scatter(y_test, yp, alpha=0.35, s=14, color="#4C72B0")
    lims = [min(y_test.min(), yp.min()), max(y_test.max(), yp.max())]
    plt.plot(lims, lims, "r--", label="Mükemmel tahmin")
    plt.title(f"Gerçek vs Tahmin - {en_iyi}")
    plt.xlabel("Gerçek Tüketim (kWh/100km)"); plt.ylabel("Tahmin")
    plt.legend(); plt.tight_layout()
    plt.savefig(f"{GRAFIK}/04_gercek_vs_tahmin.png", dpi=120); plt.close()

    # Özellik önemi (RF)
    rf = sonuclar["Random Forest"]["model"]
    onem = pd.Series(rf.feature_importances_, index=ozellikler).sort_values(ascending=False)
    plt.figure(figsize=(7.5, 4.5))
    sns.barplot(x=onem.values, y=onem.index, hue=onem.index, palette="viridis", legend=False)
    plt.title("Tüketimi En Çok Etkileyen Faktörler (Random Forest)")
    plt.xlabel("Önem Derecesi"); plt.tight_layout()
    plt.savefig(f"{GRAFIK}/05_ozellik_onemi.png", dpi=120); plt.close()
    print(f"\n-> 04_gercek_vs_tahmin.png ({en_iyi}), 05_ozellik_onemi.png kaydedildi")


# ==================================================================
# 6) ÖZET + ERZURUM SENARYOSU
# ==================================================================
def ozet(df, sonuclar):
    baslik("6) EN ÖNEMLİ BULGULAR")
    en_iyi = max(sonuclar, key=lambda k: sonuclar[k]["r2"])
    s = sonuclar[en_iyi]

    # Erzurum kışı senaryosu: 64 kWh batarya, -15°C, şehir içi vs otoyol
    def menzil_hesapla(sicaklik, otoyol, batarya=64, iklim=1):
        sapma = sicaklik - 20
        tuketim = 15 + 0.004*sapma**2 + max(0, 0.09*(20-sicaklik)) + 3.2*otoyol + 1.8*iklim
        return batarya / tuketim * 100

    yaz = menzil_hesapla(25, 0, iklim=0)
    kis_sehir = menzil_hesapla(-15, 0)
    kis_otoyol = menzil_hesapla(-15, 1)

    print(f"""
1) En iyi model: {en_iyi} (R² = {s['r2']:.3f}) — tüketimin neredeyse tamamını açıklıyor.

2) Sıcaklık menzili ÇOK etkiliyor: en verimli nokta ~20°C. Hem soğuk hem
   aşırı sıcak menzili düşürür ("U" şekli).

3) Otoyol sürüşü, şehir içine göre belirgin biçimde daha çok tüketir (aerodinamik).

4) ERZURUM KIŞ SENARYOSU (64 kWh'lik bir araç):
   - Ilık yazda (25°C, şehir içi)      : ~{yaz:.0f} km
   - Erzurum kışı (-15°C, şehir içi)   : ~{kis_sehir:.0f} km   (≈ %{(1-kis_sehir/yaz)*100:.0f} kayıp)
   - Erzurum kışı (-15°C, otoyol)      : ~{kis_otoyol:.0f} km   (≈ %{(1-kis_otoyol/yaz)*100:.0f} kayıp)
   => Soğuk + otoyol birleşince menzil neredeyse yarıya iner!
""")


def main():
    df = veri_olustur()
    df = kesif_ve_onisleme(df)
    betimsel(df)
    grafikler(df)
    y_test, sonuclar = modelle(df)
    ozet(df, sonuclar)
    baslik("BİTTİ")
    print(f"Tüm grafikler: {GRAFIK}")


if __name__ == "__main__":
    main()
