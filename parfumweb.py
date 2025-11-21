import streamlit as st
import pandas as pd
from datetime import datetime
import io

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Parfüm Hesaplayıcı", page_icon="⚗️", layout="mobile")

# --- SABİTLER ---
DEFAULT_CONFIG = {
    "ALCOHOL_DENSITY": 0.789,
    "WATER_DENSITY": 1.0,
    "ALCOHOL_DEGREE": 96.6,
    "PRICE_ALCOHOL_LITER": 250.0,
    "PRICE_WATER_LITER": 100.0,
    "PRICE_BOTTLE": 50.0
}

# --- BAŞLIK ---
st.title("⚗️ Parfüm Hesaplayıcı")
st.markdown("Excel dosyası ile otomatik hesaplama veya serbest mod.")

# --- SEKME YAPISI ---
tab1, tab2 = st.tabs(["📂 Excel Modu", "📝 Serbest Mod"])

# ==========================================
# SEKME 1: EXCEL MODU
# ==========================================
with tab1:
    st.header("Excel Veri İşleme")
    
    # 1. Dosya Yükleme
    uploaded_file = st.file_uploader("Excel Dosyasını Yükle", type=["xlsx"])
    
    if uploaded_file is not None:
        try:
            # Excel'i Oku
            xls = pd.ExcelFile(uploaded_file)
            df_oranlar = pd.read_excel(xls, 'Oranlar')
            
            # VERİ Sayfasından Fiyatları Çekme Denemesi
            alc_price = DEFAULT_CONFIG["PRICE_ALCOHOL_LITER"]
            water_price = DEFAULT_CONFIG["PRICE_WATER_LITER"]
            bottle_price = DEFAULT_CONFIG["PRICE_BOTTLE"]
            
            try:
                df_veri = pd.read_excel(xls, 'VERİ', header=None)
                veri_dict = dict(zip(df_veri[0], df_veri[1]))
                alc_price = veri_dict.get("1 LİTRE ETİL ALKOL FİYATINIZ NEDİR?", alc_price)
                water_price = veri_dict.get("1 LİTRE DİSTİLE SU FİYATINIZ NEDİR?", water_price)
                bottle_price = veri_dict.get("ŞİŞE MALİYETİNİZ NEDİR?", bottle_price)
                st.success("✅ Maliyet verileri Excel'den çekildi.")
            except:
                st.warning("⚠️ VERİ sayfası okunamadı, varsayılan fiyatlar kullanılıyor.")

            # 2. Maliyet Ayarları (Excel'den geldi ama değiştirilebilir)
            with st.expander("💰 Maliyet Ayarları (Düzenle)", expanded=False):
                col_m1, col_m2 = st.columns(2)
                p_alc = col_m1.number_input("Alkol (TL/L)", value=float(alc_price))
                p_water = col_m2.number_input("Su (TL/L)", value=float(water_price))
                col_m3, col_m4 = st.columns(2)
                p_bottle = col_m3.number_input("Şişe (TL/Adet)", value=float(bottle_price))
                p_ess_manual = col_m4.number_input("Esans (TL/gr - Manuel)", value=5.0)

            # 3. Parfüm Seçimi
            if "name" in df_oranlar.columns:
                perfume_list = df_oranlar["name"].tolist()
            else:
                perfume_list = df_oranlar["Parfüm"].tolist()
                
            selected_perfume_name = st.selectbox("Parfüm Seçiniz:", perfume_list)
            
            # Seçilen Satırı Bul
            col_name = "name" if "name" in df_oranlar.columns else "Parfüm"
            row = df_oranlar[df_oranlar[col_name] == selected_perfume_name].iloc[0]

            # Esans Fiyatını Excel'den Almaya Çalış
            current_ess_price = p_ess_manual
            if "Esans Fiyat" in row and pd.notna(row["Esans Fiyat"]):
                current_ess_price = float(row["Esans Fiyat"])
                st.info(f"ℹ️ Esans fiyatı tablodan alındı: {current_ess_price} TL")

            # 4. Üretim Parametreleri
            col_p1, col_p2 = st.columns(2)
            vol = col_p1.selectbox("Şişe Hacmi (ml)", [30, 50, 100, 200], index=1)
            dens = col_p2.number_input("Esans Yoğunluğu (g/ml)", value=1.0, step=0.01)

            # --- HESAPLAMA BUTONU ---
            if st.button("Hesapla (Excel)", type="primary"):
                # Verileri Hazırla
                type_p = row.get("Esans Tipi", row.get("type", "-"))
                e_val = row.get("Esans", row.get("essencePercent", 0))
                w_val = row.get("Su", row.get("waterPercent", 0))
                
                # Yüzde düzeltme (0.20 vs 20)
                e_pct = e_val * 100 if e_val < 1 else e_val
                w_pct = w_val * 100 if w_val < 1 else w_val
                a_pct = 100 - (e_pct + w_pct)

                # Matematik
                ess_ml = vol * (e_pct / 100)
                water_ml = vol * (w_pct / 100)
                alc_ml = vol * (a_pct / 100)
                
                ess_g = ess_ml * dens
                water_g = water_ml * DEFAULT_CONFIG["WATER_DENSITY"]
                alc_g = alc_ml * DEFAULT_CONFIG["ALCOHOL_DENSITY"]
                total_g = ess_g + water_g + alc_g
                
                # Maliyet
                cost_alc = (alc_ml / 1000) * p_alc
                cost_water = (water_ml / 1000) * p_water
                cost_ess = ess_g * current_ess_price
                total_cost = cost_alc + cost_water + cost_ess + p_bottle

                # --- SONUÇLARI GÖSTER ---
                st.markdown("---")
                st.subheader(f"🧪 {selected_perfume_name}")
                st.caption(f"Tip: {type_p} | Hacim: {vol} ml")

                # Kartlar halinde gösterim (Mobil için uygun)
                c1, c2, c3 = st.columns(3)
                c1.metric("Esans (gr)", f"{ess_g:.2f}", f"{ess_ml:.2f} ml")
                c2.metric("Su (gr)", f"{water_g:.2f}", f"{water_ml:.2f} ml")
                c3.metric("Alkol (gr)", f"{alc_g:.2f}", f"{alc_ml:.2f} ml")
                
                st.info(f"⚖️ **Toplam Ağırlık:** {total_g:.2f} gr")
                
                # Maliyet Tablosu
                st.markdown("### 💸 Maliyet Analizi")
                cost_data = {
                    "Kalem": ["Esans", "Alkol", "Su", "Şişe", "TOPLAM"],
                    "Tutar (TL)": [cost_ess, cost_alc, cost_water, p_bottle, total_cost]
                }
                df_cost = pd.DataFrame(cost_data)
                st.dataframe(df_cost, hide_index=True, use_container_width=True)
                
                st.success(f"✅ Ürün Başı Maliyet: **{total_cost:.2f} TL**")

        except Exception as e:
            st.error(f"Bir hata oluştu: {e}")
    else:
        st.info("Lütfen hesaplama yapmak için Excel dosyasını yükleyin.")

# ==========================================
# SEKME 2: SERBEST MOD
# ==========================================
with tab2:
    st.header("Manuel Hesaplama")
    
    col_f1, col_f2 = st.columns(2)
    f_vol = col_f1.number_input("Hacim (ml)", 50)
    f_dens = col_f2.number_input("Esans Yoğ.", 1.0)
    
    col_f3, col_f4 = st.columns(2)
    f_epct = col_f3.number_input("Esans %", 20.0)
    f_wpct = col_f4.number_input("Su %", 5.0)
    
    st.markdown("---")
    st.markdown("**Birim Fiyatlar**")
    col_fp1, col_fp2 = st.columns(2)
    fp_ess = col_fp1.number_input("Esans TL/g", 5.0)
    fp_alc = col_fp2.number_input("Alkol TL/L", 250.0)
    fp_bot = st.number_input("Şişe TL", 50.0)
    
    if st.button("Hesapla (Serbest)", type="secondary"):
        # Basit Hesaplama
        fa_pct = 100 - (f_epct + f_wpct)
        if fa_pct < 0:
            st.error("Hata: Oranlar 100'ü geçti!")
        else:
            f_ess_ml = f_vol * (f_epct / 100)
            f_w_ml = f_vol * (f_wpct / 100)
            f_alc_ml = f_vol * (fa_pct / 100)
            
            f_ess_g = f_ess_ml * f_dens
            f_w_g = f_w_ml * 1.0
            f_alc_g = f_alc_ml * 0.789
            
            f_cost = (f_ess_g * fp_ess) + ((f_alc_ml/1000)*fp_alc) + ((f_w_ml/1000)*100) + fp_bot
            
            st.success(f"Toplam Maliyet: {f_cost:.2f} TL")
            st.text(f"Esans: {f_ess_g:.2f}g | Su: {f_w_g:.2f}g | Alkol: {f_alc_g:.2f}g")
