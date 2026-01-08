import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from utils.database import get_connection
from utils.helpers import format_currency

# Konfigurasi Halaman
st.set_page_config(page_title="Laporan Keuangan", layout="wide")
st.title("Laporan Keuangan")

conn = get_connection()

# Pengaturan Tab
tab1, tab2, tab3, tab4 = st.tabs([
    "Laporan Bulanan", 
    "Laporan Tahunan", 
    "Analisis Tunggakan", 
    "Export Data"
])

# --- TAB 1: LAPORAN BULANAN ---
with tab1:
    col_header, col_select = st.columns([3, 1])
    with col_select:
        tahun_bulanan = st.selectbox(
            "Tahun", 
            list(range(2026, 2031)), 
            index=datetime.now().year - 2026,
            key="sb_thn_bln"
        )

    query = f"""
        SELECT 
            p.bulan,
            SUM(p.jumlah) as total_pembayaran,
            COUNT(p.id) as jumlah_transaksi,
            SUM(CASE WHEN p.status='verified' THEN p.jumlah ELSE 0 END) as verified_payment,
            SUM(CASE WHEN p.status='pending' THEN p.jumlah ELSE 0 END) as pending_payment
        FROM pembayaran p
        WHERE p.tahun={tahun_bulanan}
        GROUP BY p.bulan ORDER BY p.bulan
    """
    df_bulanan = pd.read_sql_query(query, conn)

    if not df_bulanan.empty:
        df_bulanan['bulan_nama'] = df_bulanan['bulan'].apply(lambda x: datetime(2000, x, 1).strftime('%B'))
        
        # Visualisasi
        fig_bar = px.bar(
            df_bulanan, x='bulan_nama', y='total_pembayaran',
            title=f'Distribusi Pembayaran {tahun_bulanan}',
            labels={'bulan_nama': 'Bulan', 'total_pembayaran': 'Jumlah (Rp)'},
            template="plotly_white"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        # Tabel Data
        df_display = df_bulanan.copy()
        for col in ['total_pembayaran', 'verified_payment', 'pending_payment']:
            df_display[col] = df_display[col].apply(format_currency)

        st.dataframe(
            df_display[['bulan_nama', 'total_pembayaran', 'verified_payment', 'pending_payment', 'jumlah_transaksi']],
            use_container_width=True, hide_index=True
        )

        # Metrik Utama
        st.divider()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Penerimaan", format_currency(df_bulanan['total_pembayaran'].sum()))
        m2.metric("Rata-rata Bulanan", format_currency(df_bulanan['total_pembayaran'].mean()))
        m3.metric("Puncak (Bulan)", df_bulanan.loc[df_bulanan['total_pembayaran'].idxmax(), 'bulan_nama'])
        m4.metric("Total Transaksi", df_bulanan['jumlah_transaksi'].sum())
    else:
        st.info(f"Tidak ada data untuk tahun {tahun_bulanan}")

# --- TAB 2: LAPORAN TAHUNAN ---
with tab2:
    query = "SELECT tahun, SUM(jumlah) as total, COUNT(id) as transaksi FROM pembayaran WHERE status='verified' GROUP BY tahun ORDER BY tahun DESC"
    df_tahunan = pd.read_sql_query(query, conn)

    if not df_tahunan.empty:
        fig_line = px.line(
            df_tahunan, x='tahun', y='total', markers=True,
            title='Pertumbuhan Pendapatan Tahunan',
            template="plotly_white"
        )
        st.plotly_chart(fig_line, use_container_width=True)
        
        st.dataframe(df_tahunan, use_container_width=True, hide_index=True)
    else:
        st.info("Data tahunan tidak tersedia")

# --- TAB 3: ANALISIS TUNGGAKAN ---
with tab3:
    col_t1, col_t2 = st.columns([3, 1])
    with col_t2:
        tahun_analisis = st.selectbox("Tahun Analisis", list(range(2026, 2031)), index=0)

    query_tunggakan = f"""
        SELECT 
            w.no_rumah, w.nama_kepala_keluarga,
            (SELECT COUNT(*) FROM pembayaran p2 WHERE p2.warga_id = w.id AND p2.tahun={tahun_analisis} AND p2.status='verified') as lunas,
            (12 - (SELECT COUNT(*) FROM pembayaran p2 WHERE p2.warga_id = w.id AND p2.tahun={tahun_analisis} AND p2.status='verified')) as tunggak
        FROM warga w WHERE w.status='aktif'
    """
    df_tunggakan = pd.read_sql_query(query_tunggakan, conn)
    df_tunggakan['nominal_tunggakan'] = df_tunggakan['tunggak'] * 100000 # Asumsi 100rb/bulan

    if not df_tunggakan.empty:
        # Filter hanya yang menunggak
        df_active_tunggak = df_tunggakan[df_tunggakan['tunggak'] > 0].sort_values('tunggak', ascending=False)
        
        c1, c2 = st.columns([2, 1])
        with c1:
            st.dataframe(df_active_tunggak, use_container_width=True, hide_index=True)
        with c2:
            fig_pie = px.pie(
                values=[len(df_tunggakan)-len(df_active_tunggak), len(df_active_tunggak)], 
                names=['Lunas', 'Menunggak'],
                hole=0.4, title="Rasio Kepatuhan"
            )
            st.plotly_chart(fig_pie, use_container_width=True)

# --- TAB 4: EXPORT DATA ---
with tab4:
    st.subheader("Unduh Laporan")
    report_type = st.selectbox("Format Laporan", ["Ringkasan Bulanan", "Data Tunggakan", "Database Lengkap"])
    
    # Logic export disederhanakan
    if st.button("Generate File"):
        # Placeholder untuk fungsi export asli Anda
        st.success(f"File {report_type} siap diunduh.")
        # button download asli diletakkan di sini sesuai report_type

conn.close()