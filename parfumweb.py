import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os

# --- 1. KONFİGÜRASYON ---
st.set_page_config(
    page_title="Pro Lab",
    page_icon="🧪",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. SESSION STATE (HAFIZA) ---
defaults = {
    "perfume_name": "",
    "target_vol": 100,
    "essence_dens": 0.98,
    "essence_pct": 20.0,
    "water_pct": 0.0,
    "cost_ess_gr": 0.0,
    "cost_wat_ml": 0.0,
    "cost_alc_ml": 0.0,
    "price_ess": 0.0,
    "price_wat": 0.0,
    "price_alc": 0.0
}

for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# --- 3. SABİT DEĞERLER ---
FIXED_DENSITY_ALCOHOL = 0.80
FIXED_DENSITY_WATER = 1.00
SOURCE_ALCOHOL_DEGREE = 96.6
DB_FILE = "parfum_veritabani.xlsx" # Veritabanı dosya adı

# --- 4. CSS VE TASARIM ---
st.markdown("""
    <style>
    .block-container {padding-top: 1.5rem; padding-bottom: 5rem;}
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    
    .main-title {
        font-family: 'Helvetica Neue', sans-serif;
        font-size: 2rem;
        font-weight: 300;
        letter-spacing: 2px;
        text-align: center;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 0.9rem;
        opacity: 0.6;
        text-align: center;
        margin-bottom: 2.5rem;
        letter-spacing: 1px;
    }

    /* Giriş Kutusu */
    div[data-testid="stTextInput"] input {
        font-weight: bold;
        font-size: 1.1rem;
        text-align: center;
        color: var(--text-color) !important;
        background-color: rgba(128, 128, 128, 0.1) !important;
        border: 1px solid rgba(128, 128, 128, 0.2) !important;
        border-radius: 8px;
    }
    
    /* Tablo Stili */
    div[data-testid="stDataFrame"] {
        font-size: 0.9rem;
    }

    /* Şişe */
    .bottle-wrapper {
        display: flex;
        justify-content: center;
        margin: 20px 0;
    }
    .bottle {
        width: 130px;
        height: 200px;
        border: 2px solid var(--text-color);
        border-radius: 15px 15px 5px 5px;
        position: relative;
        overflow: hidden;
        background: rgba(128, 128, 128, 0.05);
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    .bottle::after {
        content: '';
        position: absolute;
        top: -25px; left: 40px;
        width: 50px; height: 20px;
        background: #333;
        border-radius: 2px;
    }
    .layer { width: 100%; transition: height 0.6s cubic-bezier(0.25, 0.8, 0.25, 1); }
    .l-alc { background: #BDBDBD; }
    .l-wat { background: #81D4FA; }
    .l-ess { background: #FFD700; }

    .legend {
        display: flex; justify-content: center; gap: 15px;
        font-size: 0.8rem; opacity: 0.8; margin-bottom: 20px;
    }
    .dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-right: 5px; }

    div[data-testid="stMetric"] {
        background-color: rgba(128, 128, 128, 0.05);
        border: 1px solid rgba(128, 128, 128, 0.1);
        border-radius: 8px;
        padding: 10px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# --- 5. YARDIMCI FONKSİYONLAR ---
def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_excel(DB_FILE)
            return df
        except Exception as e:
            st.error(f"Veritabanı okunurken hata oluştu: {e}")
            return None
    return None

def create_pdf(vol, mass, data, degree, name_tag):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 15, "PRO LAB RECETESI", 0, 1, 'C')
    
    if name_tag:
        pdf.set_font("Arial", 'I', 14)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 10, f"{name_tag}", 0, 1, 'C')
        pdf.set_text_color(0, 0, 0)
    
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 10, f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}", 0, 1, 'C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"HEDEF: {vol} ML | KUTLE: {mass:.2f} GR | ALKOL: {degree:.1f} Derece", 0, 1, 'C')
    pdf.ln(10)
    
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(60, 10, "BILESEN", 1, 0, 'L', 1)
    pdf.cell(40, 10, "MIKTAR", 1, 0, 'C', 1)
    pdf.cell(40, 10, "ORAN", 1, 1, 'C', 1)
    
    pdf.set_font("Arial", '', 10)
    for item in data:
        unit = "Gr" if item['name'] == "ESANS" else "Ml"
        val = item['mass'] if unit == "Gr" else item['vol']
        pdf.cell(60, 10, item['name'], 1)
        pdf.cell(40, 10, f"{val:.2f} {unit}", 1, 0, 'C')
        pdf.cell(40, 10, f"%{item['pct']:.1f}", 1, 1, 'C')
        pdf.ln()
        
    if name_tag:
        pdf.set_y(-30)
        pdf.set_font("Arial", 'I', 8)
        pdf.cell(0, 10, f"Proje: {name_tag}", 0, 0, 'C')
        
    return pdf.output(dest='S').encode('latin-1', 'replace')

def render_bottle(e, w, a):
    total = e + w + a
    empty = 100 - total if total < 100 else 0
    html = f"""
    <div class="bottle-wrapper">
        <div class="bottle">
            <div class="layer" style="height: {empty}%;"></div>
            <div class="layer l-alc" style="height: {a}%;"></div>
            <div class="layer l-wat" style="height: {w}%;"></div>
            <div class="layer l-ess" style="height: {e}%;"></div>
        </div>
    </div>
    <div class="legend">
        <span><span class="dot" style="background:#FFD700;"></span>Esans</span>
        <span><span class="dot" style="background:#81D4FA;"></span>Su</span>
        <span><span class="dot" style="background:#BDBDBD;"></span>Alkol</span>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# --- 6. UYGULAMA AKIŞI ---

st.markdown('<div class="main-title">PRO LAB</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">KÜTLESEL HESAPLAYICI</div>', unsafe_allow_html=True)

# 3 Sekmeli Yapı
tab1, tab2, tab3 = st.tabs(["REÇETE & ORANLAR", "MALİYET HESABI", "📂 VERİTABANI"])

# --- SEKME 1: REÇETE ---
with tab1:
    st.text_input("PROJE / PARFÜM ADI", 
                  placeholder="Örn: Louis Vuitton Imagination Muadili", 
                  key="perfume_name")
    
    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        t_vol = st.number_input("Şişe Hacmi (ML)", step=10, key="target_vol")
        e_dens = st.number_input("Esans Yoğunluğu", step=0.01, format="%.2f", key="essence_dens")
    with c2:
        e_pct = st.number_input("Esans Oranı (%)", step=0.5, format="%.1f", key="essence_pct")
        w_pct = st.number_input("Su Oranı (%)", step=0.5, format="%.1f", key="water_pct")

    a_pct = 100 - (e_pct + w_pct)
    
    if a_pct < 0:
        st.error("⚠️ HATA: Oranlar toplamı %100'ü geçiyor!")
    else:
        v_e = t_vol * (e_pct / 100)
        v_w = t_vol * (w_pct / 100)
        v_a = t_vol * (a_pct / 100)
        
        m_e = v_e * e_dens
        m_w = v_w * FIXED_DENSITY_WATER
        m_a = v_a * FIXED_DENSITY_ALCOHOL
        total_mass = m_e + m_w + m_a
        
        final_degree = (v_a / t_vol) * SOURCE_ALCOHOL_DEGREE if t_vol > 0 else 0

        render_bottle(e_pct, w_pct, a_pct)
        
        st.markdown("### 📋 Reçete Detayı")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("ESANS", f"{m_e:.2f} gr")
        k2.metric("SU", f"{v_w:.1f} ml")
        k3.metric("ALKOL", f"{v_a:.1f} ml")
        k4.metric("DERECE", f"{final_degree:.1f}°")
        
        st.info(f"⚖️ **TOPLAM KÜTLE:** {total_mass:.2f} Gram")
        
        export_data = [
            {'name': 'ESANS', 'mass': m_e, 'vol': v_e, 'pct': e_pct},
            {'name': 'SAF SU', 'mass': m_w, 'vol': v_w, 'pct': w_pct},
            {'name': 'ALKOL', 'mass': m_a, 'vol': v_a, 'pct': a_pct}
        ]
        p_name_val = st.session_state.perfume_name
        
        pdf_val = create_pdf(t_vol, total_mass, export_data, final_degree, p_name_val)
        
        btn_label = f"📥 Reçeteyi İndir ({p_name_val})" if p_name_val else "📥 Reçeteyi İndir"
        
        st.download_button(btn_label, pdf_val, file_name="prolab_recete.pdf", mime="application/pdf", use_container_width=True)

# --- SEKME 2: MALİYET ---
with tab2:
    st.caption("Birim fiyat analizi yapın.")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Miktarlar**")
        ue = st.number_input("Esans (Gr)", step=1.0, key="cost_ess_gr")
        uw = st.number_input("Su (Ml)", step=1.0, key="cost_wat_ml")
        ua = st.number_input("Alkol (Ml)", step=1.0, key="cost_alc_ml")
    
    with col_b:
        st.markdown("**Birim Fiyatlar**")
        pe = st.number_input("Esans (TL/Gr)", step=0.5, key="price_ess")
        pw = st.number_input("Su (TL/Lt)", step=1.0, key="price_wat")
        pa = st.number_input("Alkol (TL/Lt)", step=10.0, key="price_alc")
        
    total_c = (ue * pe) + ((uw/1000)*pw) + ((ua/1000)*pa)
    st.divider()
    st.metric("TOPLAM SIVI MALİYETİ", f"{total_c:.2f} TL")

# --- SEKME 3: VERİTABANI (YENİ) ---
with tab3:
    st.markdown("### 📂 Parfüm Veritabanı")
    df = load_data()
    
    if df is not None:
        # Arama Çubuğu
        search_term = st.text_input("🔍 Parfüm Ara", placeholder="Örn: Dior, Chanel, Invictus...")
        
        # Filtreleme
        if search_term:
            filtered_df = df[df['name'].astype(str).str.contains(search_term, case=False, na=False)]
        else:
            filtered_df = df
            
        # Tabloyu Göster (Sütun adlarını Türkçeleştirerek)
        display_df = filtered_df[['name', 'essence_pct', 'water_pct', 'type']].copy()
        display_df.columns = ['Parfüm Adı', 'Esans %', 'Su %', 'Tip']
        
        st.dataframe(
            display_df, 
            use_container_width=True,
            hide_index=True,
            height=400
        )
        
        st.caption(f"Toplam {len(filtered_df)} kayıt gösteriliyor.")
        
        # Seçilen Parfümü Aktarma Özelliği
        if not filtered_df.empty:
            st.markdown("---")
            selected_p = st.selectbox("Reçeteye Aktarılacak Parfümü Seç:", filtered_df['name'].tolist())
            
            if st.button("👉 Bu Oranları Kullan"):
                # Seçilen satırı bul
                row = filtered_df[filtered_df['name'] == selected_p].iloc[0]
                
                # Session State güncelle
                st.session_state.perfume_name = row['name']
                st.session_state.essence_pct = float(row['essence_pct'])
                st.session_state.water_pct = float(row['water_pct'])
                
                st.success(f"✅ '{row['name']}' oranları yüklendi! 'REÇETE' sekmesine geçebilirsiniz.")
                
    else:
        st.info("Veritabanı dosyası (parfum_veritabani.xlsx) henüz yüklenmemiş.")
        st.markdown("Lütfen Excel dosyanızı projeye dahil edin.")


