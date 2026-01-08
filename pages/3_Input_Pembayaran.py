import streamlit as st
import pandas as pd
from datetime import datetime
from utils.database import get_connection, add_pembayaran, update_pembayaran_status

# Konfigurasi Halaman
st.set_page_config(page_title="Sistem Pembayaran", layout="wide")

# CSS Minimalis
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    div[data-testid="stForm"] { border: 1px solid #e6e9ef; border-radius: 8px; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 5px; border: 1px solid #f0f2f6; }
    </style>
""", unsafe_allow_html=True)

# Data Fetcher dengan Cache
@st.cache_data(ttl=60)
def fetch_data(query_type):
    conn = get_connection()
    try:
        if query_type == "warga":
            return pd.read_sql_query("SELECT id, no_rumah, nama_kepala_keluarga FROM warga WHERE status='aktif' ORDER BY no_rumah", conn)
        elif query_type == "pembayaran":
            return pd.read_sql_query('''
                SELECT p.*, w.no_rumah, w.nama_kepala_keluarga 
                FROM pembayaran p LEFT JOIN warga w ON p.warga_id = w.id 
                ORDER BY p.tanggal_bayar DESC''', conn)
    finally:
        conn.close()

# --- FUNGSI TAB ---

@st.fragment
def tab_input():
    df_warga = fetch_data("warga")
    if df_warga.empty:
        st.info("Data warga tidak ditemukan.")
        return

    with st.form("form_bayar", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            warga_options = df_warga.apply(lambda x: f"{x['no_rumah']} - {x['nama_kepala_keluarga']}", axis=1).tolist()
            sel_warga = st.selectbox("Warga", warga_options)
            
            cb1, cb2 = st.columns(2)
            bulan = cb1.selectbox("Bulan", list(range(1, 13)), index=datetime.now().month-1)
            tahun = cb2.selectbox("Tahun", [2026, 2027, 2028], index=0)
            
        with c2:
            jumlah = st.number_input("Nominal (Rp)", min_value=0, value=100000, step=5000)
            tanggal = st.date_input("Tanggal Transaksi", value=datetime.now())
            bukti = st.text_input("Referensi / No. Bukti")
        
        catatan = st.text_input("Keterangan")
        
        if st.form_submit_button("Simpan Data", type="primary", use_container_width=True):
            if not bukti:
                st.error("Referensi wajib diisi")
            else:
                no_rumah = sel_warga.split(" - ")[0]
                w_id = int(df_warga[df_warga['no_rumah'] == no_rumah]['id'].values[0])
                status = "verified" if st.session_state.get('is_admin') else "pending"
                
                data = (w_id, bulan, tahun, jumlah, tanggal.strftime('%Y-%m-%d'), 
                        "Transfer", bukti, status, catatan)
                
                if add_pembayaran(data):
                    st.toast("Data disimpan")
                    st.cache_data.clear()

@st.fragment
def tab_riwayat():
    c1, c2, c3 = st.columns([2, 1, 1])
    search = c1.text_input("Cari", placeholder="No. Rumah / Nama")
    status_f = c2.selectbox("Filter Status", ["Semua", "verified", "pending", "rejected"])
    
    if c3.button("Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun(scope="fragment")

    df = fetch_data("pembayaran")
    if not df.empty:
        if search:
            mask = df['nama_kepala_keluarga'].str.contains(search, case=False, na=False) | \
                   df['no_rumah'].str.contains(search, case=False, na=False)
            df = df[mask]
        if status_f != "Semua":
            df = df[df['status'] == status_f]

        st.dataframe(
            df[['no_rumah', 'nama_kepala_keluarga', 'bulan', 'tahun', 'jumlah', 'status', 'tanggal_bayar']],
            use_container_width=True,
            hide_index=True,
            column_config={
                "jumlah": st.column_config.NumberColumn("Total", format="Rp %d"),
                "status": "Status",
                "tanggal_bayar": "Tanggal"
            }
        )

@st.fragment
def tab_verifikasi():
    if not st.session_state.get('is_admin', False):
        st.error("Akses Ditolak")
        return

    df = fetch_data("pembayaran")
    pending = df[df['status'] == 'pending']

    if pending.empty:
        st.info("Tidak ada antrean verifikasi.")
        return

    for _, row in pending.iterrows():
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                st.write(f"**{row['nama_kepala_keluarga']}** ({row['no_rumah']})")
                st.caption(f"Periode: {row['bulan']}/{row['tahun']} | Rp {row['jumlah']:,} | Ref: {row['bukti_bayar']}")
            
            if c2.button("Setujui", key=f"v_{row['id']}", type="primary", use_container_width=True):
                update_pembayaran_status(row['id'], 'verified', 1)
                st.cache_data.clear()
                st.rerun(scope="fragment")
                
            if c3.button("Tolak", key=f"r_{row['id']}", use_container_width=True):
                update_pembayaran_status(row['id'], 'rejected', 1)
                st.cache_data.clear()
                st.rerun(scope="fragment")

# --- MAIN ---
st.title("Manajemen Pembayaran")

t1, t2, t3 = st.tabs(["Form Input", "Riwayat Transaksi", "Verifikasi Admin"])

with t1: tab_input()
with t2: tab_riwayat()
with t3: tab_verifikasi()