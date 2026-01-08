import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from utils.database import get_connection, get_pending_changes, update_pending_change_status
import plotly.express as px

st.set_page_config(page_title="Admin Panel", layout="wide")
st.title("Admin Panel")

if not st.session_state.get('is_admin', False):
    st.error("Akses ditolak.")
    st.stop()

conn = get_connection()
tab1, tab2, tab3 = st.tabs(["Pending Changes", "Log Aktivitas", "Statistik"])

# ==================== TAB 1: PENDING CHANGES ====================
with tab1:
    df_pending = get_pending_changes()
    
    if not df_pending.empty:
        # Aksi Massal di bagian atas
        c_mass1, c_mass2 = st.columns([1, 5])
        with c_mass1:
            if st.button("Setujui Semua", type="primary", use_container_width=True):
                for _, r in df_pending.iterrows():
                    update_pending_change_status(r['id'], 'approved', st.session_state.user_id)
                st.rerun()

        for _, row in df_pending.iterrows():
            with st.expander(f"{row['action'].upper()} - {row['table_name']} (ID: {row['record_id'] or 'Baru'})"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.caption(f"Diajukan oleh: {row['requested_by_name']} | {pd.to_datetime(row['created_at']).strftime('%d/%m/%y %H:%M')}")
                    
                    try:
                        c_data1, c_data2 = st.columns(2)
                        if row['old_data']:
                            with c_data1:
                                st.write("**Data Lama**")
                                st.json(json.loads(row['old_data']), expanded=True)
                        
                        if row['new_data']:
                            with c_data2:
                                st.write("**Data Baru**")
                                st.json(json.loads(row['new_data']), expanded=True)
                    except:
                        st.text(row['new_data'])
                
                with col2:
                    if st.button("Setujui", key=f"app_{row['id']}", use_container_width=True, type="primary"):
                        update_pending_change_status(row['id'], 'approved', st.session_state.user_id)
                        st.rerun()
                    if st.button("Tolak", key=f"rej_{row['id']}", use_container_width=True):
                        update_pending_change_status(row['id'], 'rejected', st.session_state.user_id)
                        st.rerun()
    else:
        st.info("Tidak ada antrean perubahan.")

# ==================== TAB 2: LOG AKTIVITAS ====================
with tab2:
    c1, c2, c3 = st.columns(3)
    with c1:
        date_from = st.date_input("Mulai", value=datetime.now().replace(day=1))
    with c2:
        date_to = st.date_input("Selesai", value=datetime.now())
    with c3:
        filter_action = st.selectbox("Aksi", ["Semua", "insert", "update", "delete", "approve", "reject"])

    query = '''
        SELECT pc.table_name, pc.action, pc.status, u1.username as pemohon, 
               u2.username as reviewer, pc.created_at, pc.review_date
        FROM pending_changes pc
        LEFT JOIN users u1 ON pc.requested_by = u1.id
        LEFT JOIN users u2 ON pc.reviewed_by = u2.id
        WHERE DATE(pc.created_at) BETWEEN ? AND ?
    '''
    df_logs = pd.read_sql_query(query, conn, params=[date_from.strftime('%Y-%m-%d'), date_to.strftime('%Y-%m-%d')])
    
    st.dataframe(df_logs, use_container_width=True, hide_index=True)
    
    csv = df_logs.to_csv(index=False)
    st.download_button("Download CSV", data=csv, file_name="log_system.csv", mime="text/csv")

# ==================== TAB 3: STATISTIK ====================
with tab3:
    cursor = conn.cursor()
    
    # Row 1: Key Metrics
    m1, m2, m3, m4 = st.columns(4)
    cursor.execute("SELECT COUNT(*) FROM warga WHERE status='aktif'")
    m1.metric("Warga Aktif", cursor.fetchone()[0])
    
    cursor.execute("SELECT SUM(jumlah) FROM pembayaran WHERE status='verified'")
    total = cursor.fetchone()[0] or 0
    m2.metric("Total Kas", f"Rp {total:,}")
    
    cursor.execute("SELECT COUNT(*) FROM pembayaran WHERE status='pending'")
    m3.metric("Pmt Pending", cursor.fetchone()[0])
    
    cursor.execute("SELECT COUNT(*) FROM users")
    m4.metric("Total User", cursor.fetchone()[0])

    st.divider()

    # Row 2: Visualisasi
    q_act = "SELECT DATE(created_at) as tgl, COUNT(*) as jml FROM pending_changes GROUP BY tgl LIMIT 30"
    df_act = pd.read_sql_query(q_act, conn)
    if not df_act.empty:
        fig = px.line(df_act, x='tgl', y='jml', title='Tren Aktivitas (30 Hari)')
        st.plotly_chart(fig, use_container_width=True)

    # Row 3: Info Sistem & Maintenance
    st.divider()
    s1, s2, s3 = st.columns(3)
    with s1:
        if os.path.exists('data/database.db'):
            size = os.path.getsize('data/database.db') / (1024*1024)
            st.write(f"**DB Size:** {size:.2f} MB")
    with s2:
        if st.button("Optimize DB", use_container_width=True):
            conn.execute("VACUUM")
            st.toast("Optimasi selesai")
    with s3:
        if st.button("Clear Cache", use_container_width=True):
            st.session_state.clear()
            st.rerun()

conn.close()