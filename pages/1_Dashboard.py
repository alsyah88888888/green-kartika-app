import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from utils.database import get_connection

# ============================================
# 1. FUNGSI DATA (DENGAN CACHE)
# ============================================
@st.cache_data(ttl=300) # Data disimpan di cache selama 5 menit
def load_dashboard_data():
    conn = get_connection()
    try:
        # Ambil ringkasan pembayaran per bulan
        query = """
            SELECT bulan, tahun, SUM(jumlah) as total, COUNT(id) as transaksi
            FROM pembayaran 
            WHERE status = 'verified'
            GROUP BY tahun, bulan
            ORDER BY tahun DESC, bulan DESC
            LIMIT 12
        """
        df_monthly = pd.read_sql_query(query, conn)
        
        # Ambil status pembayaran saat ini
        query_status = "SELECT status, COUNT(*) as jumlah FROM pembayaran GROUP BY status"
        df_status = pd.read_sql_query(query_status, conn)
        
        return df_monthly, df_status
    finally:
        conn.close()

# ============================================
# 2. TAMPILAN DASHBOARD (ANTI-FLICKER)
# ============================================
@st.fragment
def render_dashboard():
    st.header("📊 Ringkasan Keuangan")
    
    # Load data
    df_monthly, df_status = load_dashboard_data()
    
    # --- BAGIAN METRIC (ATAS) ---
    col1, col2, col3 = st.columns(3)
    
    if not df_monthly.empty:
        total_pemasukan = df_monthly['total'].sum()
        latest_income = df_monthly.iloc[0]['total']
        
        col1.metric("Total Pemasukan (12 Bln)", f"Rp {total_pemasukan:,.0f}")
        col2.metric("Pemasukan Bulan Ini", f"Rp {latest_income:,.0f}")
    
    # Hitung pending dari df_status
    pending_count = df_status[df_status['status'] == 'pending']['jumlah'].sum()
    col3.metric("Menunggu Verifikasi", f"{pending_count} Data", delta_color="inverse")

    st.markdown("---")

    # --- BAGIAN GRAFIK ---
    c1, c2 = st.columns([2, 1])

    with c1:
        st.subheader("Tren Pemasukan Bulanan")
        if not df_monthly.empty:
            # Format nama bulan untuk grafik
            df_monthly['periode'] = df_monthly.apply(
                lambda x: f"{datetime(2000, int(x['bulan']), 1).strftime('%b')} {int(x['tahun'])}", axis=1
            )
            fig = px.line(df_monthly, x='periode', y='total', 
                          markers=True, template="plotly_white",
                          labels={'total': 'Pemasukan (Rp)', 'periode': 'Bulan'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Belum ada data keuangan yang terverifikasi.")

    with c2:
        st.subheader("Komposisi Status")
        if not df_status.empty:
            fig_pie = px.pie(df_status, values='jumlah', names='status',
                             color='status',
                             color_discrete_map={'verified':'#2E8B57', 'pending':'#FFA500', 'rejected':'#FF4B4B'})
            st.plotly_chart(fig_pie, use_container_width=True)

# ============================================
# 3. FUNGSI UNTUK USER BIASA (NON-ADMIN)
# ============================================
def render_user_info():
    st.info("💡 Anda masuk sebagai warga. Silakan hubungi admin jika ingin melakukan verifikasi pembayaran.")
    
    # Menampilkan riwayat milik warga itu sendiri (Jika ada session_state warga_id)
    if 'warga_id' in st.session_state:
        st.subheader("Riwayat Pembayaran Anda")
        # Logika filter riwayat pribadi...

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    render_dashboard()
    
    if not st.session_state.get('is_admin', False):
        render_user_info()