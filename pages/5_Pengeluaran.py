import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
# Tambahkan delete_pengeluaran di import
from utils.database import add_pengeluaran, get_all_pengeluaran, delete_pengeluaran 
from utils.helpers import format_currency

# Konfigurasi Halaman
st.set_page_config(page_title="Laporan Pengeluaran", layout="wide")

# CSS Minimalis
st.markdown("""
    <style>
    div[data-testid="stForm"] { border: 1px solid #e6e9ef; border-radius: 8px; padding: 20px; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    </style>
""", unsafe_allow_html=True)

st.title("Pengelolaan Pengeluaran")

if not st.session_state.get('is_admin', False):
    st.error("Akses ditolak.")
    st.stop()

# --- NAVIGASI TAB ---
tab1, tab2, tab3 = st.tabs(["Input Data", "Daftar Transaksi", "Analisis"])

# ==================== TAB 1: INPUT ====================
with tab1:
    with st.form("form_pengeluaran", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            kategori = st.selectbox("Kategori", 
                                   ["Kebersihan", "Keamanan", "Pemeliharaan", 
                                    "Administrasi", "Listrik", "Air", "ATK", "Lainnya"])
            jumlah = st.number_input("Nominal (Rp)", min_value=0, step=50000)
            tanggal = st.date_input("Tanggal", datetime.now())
        
        with c2:
            deskripsi = st.text_area("Deskripsi", placeholder="Keterangan pengeluaran")
            bukti = st.text_input("No. Referensi / Bukti", placeholder="Contoh: KW-001")
            disetujui = st.text_input("Otoritas", value=st.session_state.get('username', ''))
        
        if st.form_submit_button("Simpan Pengeluaran", type="primary", use_container_width=True):
            if not deskripsi or jumlah <= 0:
                st.error("Lengkapi deskripsi dan nominal.")
            else:
                data = (kategori, deskripsi, jumlah, tanggal.strftime('%Y-%m-%d'), bukti, disetujui)
                try:
                    add_pengeluaran(data)
                    st.toast("Data berhasil disimpan")
                    st.cache_data.clear() # Penting agar tabel langsung update
                    st.rerun()
                except Exception as e:
                    st.error(f"Kegagalan sistem: {e}")

# ==================== TAB 2: DAFTAR & HAPUS ====================
with tab2:
    f1, f2, f3 = st.columns([1, 1, 2])
    with f1:
        tahun_f = st.selectbox("Tahun", ["Semua"] + [str(i) for i in range(2026, 2031)], key="filter_thn")
    with f2:
        kat_f = st.selectbox("Kategori", ["Semua", "Kebersihan", "Keamanan", "Pemeliharaan", "Administrasi", "Lainnya"], key="filter_kat")
    
    df_raw = get_all_pengeluaran()
    
    if not df_raw.empty:
        df_f = df_raw.copy()
        df_f['tanggal'] = pd.to_datetime(df_f['tanggal'])
        
        if tahun_f != "Semua":
            df_f = df_f[df_f['tanggal'].dt.year == int(tahun_f)]
        if kat_f != "Semua":
            df_f = df_f[df_f['kategori'] == kat_f]
            
        st.write("### Riwayat Transaksi")
        st.caption("Centang kolom 'Pilih' untuk menghapus data, lalu klik tombol konfirmasi di bawah.")

        # Menyiapkan kolom Hapus di depan
        df_f['Pilih'] = False
        cols = ['Pilih'] + [c for c in df_f.columns if c != 'Pilih']
        df_display = df_f[cols]

        # Menggunakan data_editor agar bisa dicentang
        edited_df = st.data_editor(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Pilih": st.column_config.CheckboxColumn(help="Pilih data yang akan dihapus"),
                "id": st.column_config.TextColumn("ID", disabled=True),
                "jumlah": st.column_config.NumberColumn("Jumlah", format="Rp %d", disabled=True),
                "tanggal": st.column_config.DateColumn("Tanggal", disabled=True),
                "kategori": st.column_config.TextColumn("Kategori", disabled=True),
                "deskripsi": st.column_config.TextColumn("Deskripsi", disabled=True),
                "bukti": st.column_config.TextColumn("Bukti", disabled=True),
                "disetujui_oleh": st.column_config.TextColumn("Otoritas", disabled=True),
                "created_at": None # Sembunyikan kolom created_at jika tidak perlu
            }
        )
        
        # Logika Penghapusan
        items_to_delete = edited_df[edited_df['Pilih'] == True]
        
        if not items_to_delete.empty:
            if st.button(f"Hapus {len(items_to_delete)} Data Terpilih", type="primary"):
                for idx, row in items_to_delete.iterrows():
                    delete_pengeluaran(row['id'])
                st.success("Data berhasil dihapus!")
                st.cache_data.clear()
                st.rerun()

        st.divider()
        # Ringkasan Angka
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Terfilter", format_currency(df_f['jumlah'].sum()))
        m2.metric("Volume Transaksi", len(df_f))
        m3.metric("Rata-rata Nilai", format_currency(df_f['jumlah'].mean() if not df_f.empty else 0))
    else:
        st.info("Tidak ada data pengeluaran.")

# ==================== TAB 3: ANALISIS ====================
with tab3:
    if not df_raw.empty:
        col_sel, _ = st.columns([1, 3])
        with col_sel:
            thn_ana = st.selectbox("Tahun Analisis", range(2026, 2031), key="ana_y")
        
        df_ana = df_raw.copy()
        df_ana['tanggal'] = pd.to_datetime(df_ana['tanggal'])
        df_ana = df_ana[df_ana['tanggal'].dt.year == thn_ana]
        
        if not df_ana.empty:
            c1, c2 = st.columns(2)
            
            with c1:
                df_pie = df_ana.groupby('kategori')['jumlah'].sum().reset_index()
                fig_pie = px.pie(df_pie, values='jumlah', names='kategori', 
                               hole=0.4, template="plotly_white")
                fig_pie.update_layout(title="Distribusi per Kategori")
                st.plotly_chart(fig_pie, use_container_width=True)
                
            with c2:
                df_ana['bulan'] = df_ana['tanggal'].dt.month
                df_trend = df_ana.groupby('bulan')['jumlah'].sum().reset_index()
                df_trend = df_trend.sort_values('bulan')
                df_trend['bulan'] = df_trend['bulan'].apply(lambda x: datetime(2000, x, 1).strftime('%b'))
                
                fig_line = px.line(df_trend, x='bulan', y='jumlah', 
                                  markers=True, template="plotly_white")
                fig_line.update_layout(title="Trend Pengeluaran Bulanan")
                st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info(f"Data tahun {thn_ana} tidak tersedia.")
    else:
        st.info("Database kosong.")