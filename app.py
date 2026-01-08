import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import sqlite3
import os
from utils.database import (
    init_db, 
    get_connection, 
    get_all_warga, 
    get_pembayaran_report,
    add_warga,
    update_warga,  
    delete_warga,
    authenticate_user,
    get_all_users,
    add_user
)

# Konfigurasi halaman
st.set_page_config(
    page_title="Green Kartika Residence - Admin System",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inisialisasi database
init_db()

# CSS Kustom
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E8B57;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #3CB371;
        margin-bottom: 1rem;
    }
    .card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .stat-card {
        text-align: center;
        padding: 15px;
        border-radius: 8px;
        background: linear-gradient(135deg, #2E8B57, #3CB371);
        color: white;
    }
    .admin-card {
        background: linear-gradient(135deg, #4169E1, #6495ED);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .stButton button {
        background-color: #2E8B57;
        color: white;
        border: none;
    }
    .stButton button:hover {
        background-color: #3CB371;
        color: white;
    }
    .danger-button button {
        background-color: #DC143C;
        color: white;
    }
    .danger-button button:hover {
        background-color: #B22222;
        color: white;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .info-message {
        background-color: #d1ecf1;
        color: #0c5460;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .admin-badge {
        background-color: #4169E1;
        color: white;
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Session State Management
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False
if 'username' not in st.session_state:
    st.session_state.username = ''
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'page' not in st.session_state:
    st.session_state.page = 'Login'
if 'current_page_key' not in st.session_state:
    st.session_state.current_page_key = ''

# Sidebar Navigation
with st.sidebar:
    st.markdown('<div class="admin-card"><h2>🔒 Admin System</h2><p>Green Kartika Residence</p></div>', unsafe_allow_html=True)
    
    # Menu berdasarkan status login
    if st.session_state.logged_in and st.session_state.is_admin:
        menu_options = ["Dashboard", "Data Warga", "Pembayaran", "Laporan", 
                      "Pengeluaran", "Kelola User", "Pengaturan"]
    elif st.session_state.logged_in:
        # Non-admin hanya bisa melihat dashboard
        menu_options = ["Dashboard"]
    else:
        menu_options = ["Login"]
    
    # Tampilkan menu navigasi hanya jika sudah login
    if st.session_state.logged_in:
        selected_page = st.selectbox("Menu", menu_options, 
                                    index=menu_options.index(st.session_state.page) 
                                    if st.session_state.page in menu_options else 0,
                                    key="main_menu_select")
        st.session_state.page = selected_page
    
    st.markdown("---")
    
    # Login/Logout Section
    if st.session_state.logged_in:
        st.markdown(f"**User ID:** #{st.session_state.user_id}")
        st.markdown(f"**Nama:** {st.session_state.username}")
        
        if st.session_state.is_admin:
            st.markdown('<span class="admin-badge">Administrator</span>', unsafe_allow_html=True)
            st.markdown("**Hak Akses:** Full Access")
        else:
            st.markdown('<span style="color: #666; background: #f0f0f0; padding: 5px 10px; border-radius: 15px; font-size: 0.8rem;">Regular User</span>', unsafe_allow_html=True)
            st.markdown("**Hak Akses:** Read Only")
        
        if st.button("Logout", key="sidebar_logout_button", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.is_admin = False
            st.session_state.username = ''
            st.session_state.user_id = None
            st.session_state.page = 'Login'
            st.success("Logout berhasil!")
            st.rerun()
    else:
        st.subheader("Admin Login")
        
        # Form login
        with st.form("login_form", clear_on_submit=True):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            
            col1, col2 = st.columns(2)
            with col1:
                login_submitted = st.form_submit_button("Login", use_container_width=True, type="primary")
            with col2:
                reset_submitted = st.form_submit_button("Reset", use_container_width=True, type="secondary")
            
            if login_submitted:
                if username and password:
                    # Autentikasi user
                    user = authenticate_user(username, password)
                    
                    if user:
                        user_id, db_username, _, nama_lengkap, role, status, _ = user
                        
                        if status != 'active':
                            st.error("Akun dinonaktifkan. Hubungi administrator.")
                        elif role == 'admin':
                            # Admin login berhasil
                            st.session_state.logged_in = True
                            st.session_state.is_admin = True
                            st.session_state.username = nama_lengkap
                            st.session_state.user_id = user_id
                            st.session_state.page = 'Dashboard'
                            st.success(f"Login berhasil! Selamat datang {nama_lengkap}")
                            st.rerun()
                        else:
                            # User biasa login
                            st.session_state.logged_in = True
                            st.session_state.is_admin = False
                            st.session_state.username = nama_lengkap
                            st.session_state.user_id = user_id
                            st.session_state.page = 'Dashboard'
                            st.success(f"Login berhasil! Selamat datang {nama_lengkap}")
                            st.rerun()
                    else:
                        st.error("Username atau password salah!")
                else:
                    st.error("Username dan password harus diisi!")
    
    st.markdown("---")
    st.markdown("**System Info**")
    st.caption(f"Waktu Server: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.caption("© 2026 Green Kartika Residence by Riansyah")

# ==================== PAGE ROUTING ====================

# Hanya tampilkan konten jika sudah login
if not st.session_state.logged_in:
    # Judul utama dan sub-header dengan perataan tengah
    st.markdown('<h1 style="text-align: center;" class="main-header">Green Kartika Residence</h1>', unsafe_allow_html=True)
    st.markdown('<h3 style="text-align: center;" class="sub-header">Sistem Administrasi Iuran Lingkungan</h3>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("""
        ### 🔒 Sistem Khusus Administrator
        
        **Fitur Admin:**
        - Kelola data warga lengkap
        - Verifikasi pembayaran iuran
        - Laporan keuangan lengkap
        - Kelola pengguna sistem
        - Pengaturan aplikasi
        
        **Persyaratan:**
        - Akun dengan role 'admin'
        - Status akun 'active'
        - Kredensial valid dari administrator
        
        Silakan login menggunakan kredensial yang diberikan.
        """)
    
    # Statistik public (bisa dilihat tanpa login)
    st.markdown("---")
    st.subheader("Statistik Publik")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        conn = get_connection()
        total_warga = pd.read_sql_query("SELECT COUNT(*) as total FROM warga WHERE status='aktif'", conn)['total'][0]
        conn.close()
        st.metric("Total Warga Aktif", total_warga)
    
    with col2:
        current_month = datetime.now().month
        current_year = datetime.now().year
        conn = get_connection()
        query = f"""
            SELECT COUNT(DISTINCT warga_id) as jumlah 
            FROM pembayaran 
            WHERE bulan={current_month} AND tahun={current_year} AND status='verified'
        """
        lunas_count = pd.read_sql_query(query, conn)['jumlah'][0]
        conn.close()
        st.metric(f"Pembayaran Lunas {current_month}/{current_year}", lunas_count)
    
    with col3:
        st.metric("Bulan Berjalan", datetime.now().strftime("%B %Y"))

else:
    # User sudah login, tampilkan konten sesuai role
    if st.session_state.is_admin:
        # =========== ADMIN PAGES ===========
        
        if st.session_state.page == "Dashboard":
            st.markdown('<h1 class="main-header">Dashboard Admin</h1>', unsafe_allow_html=True)
            st.markdown('<h3 class="sub-header">Green Kartika Residence - Administrator Panel</h3>', unsafe_allow_html=True)
            
            # Info admin
            st.markdown('<div class="info-message">👋 Selamat datang, Administrator! Anda memiliki akses penuh ke semua fitur sistem.</div>', unsafe_allow_html=True)
            
            # Statistik Cepat untuk Admin
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                conn = get_connection()
                total_warga = pd.read_sql_query("SELECT COUNT(*) as total FROM warga", conn)['total'][0]
                conn.close()
                st.markdown(f'<div class="stat-card"><h4>Total Warga</h4><h2>{total_warga}</h2></div>', unsafe_allow_html=True)
            
            with col2:
                conn = get_connection()
                total_users = pd.read_sql_query("SELECT COUNT(*) as total FROM users", conn)['total'][0]
                conn.close()
                st.markdown(f'<div class="stat-card"><h4>Total User</h4><h2>{total_users}</h2></div>', unsafe_allow_html=True)
            
            with col3:
                conn = get_connection()
                current_month = datetime.now().month
                current_year = datetime.now().year
                query = f"""
                    SELECT SUM(jumlah) as total 
                    FROM pembayaran 
                    WHERE bulan={current_month} AND tahun={current_year} AND status='verified'
                """
                total_pembayaran = pd.read_sql_query(query, conn)['total'][0]
                total_pembayaran = total_pembayaran if total_pembayaran else 0
                conn.close()
                st.markdown(f'<div class="stat-card"><h4>Pembayaran Bulan Ini</h4><h2>Rp {total_pembayaran:,}</h2></div>', unsafe_allow_html=True)
            
            with col4:
                conn = get_connection()
                query = """
                    SELECT COUNT(*) as total 
                    FROM pembayaran 
                    WHERE status='pending'
                """
                pending_count = pd.read_sql_query(query, conn)['total'][0]
                conn.close()
                st.markdown(f'<div class="stat-card"><h4>Verifikasi Pending</h4><h2>{pending_count}</h2></div>', unsafe_allow_html=True)
            
          
            
            # Grafik untuk Admin
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="card"><h4>Status Pembayaran Bulan Ini</h4></div>', unsafe_allow_html=True)
                
                conn = get_connection()
                current_month = datetime.now().month
                current_year = datetime.now().year
                query = f"""
                    SELECT 
                        status,
                        COUNT(*) as jumlah
                    FROM pembayaran 
                    WHERE bulan={current_month} AND tahun={current_year}
                    GROUP BY status
                """
                df_status = pd.read_sql_query(query, conn)
                conn.close()
                
                if not df_status.empty:
                    fig = px.pie(df_status, values='jumlah', names='status', 
                                title='Distribusi Status Pembayaran',
                                color_discrete_map={'verified': '#2E8B57', 'pending': '#FFA500', 'rejected': '#DC143C'})
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Belum ada data pembayaran bulan ini")
            
            with col2:
                st.markdown('<div class="card"><h4>Pembayaran 6 Bulan Terakhir</h4></div>', unsafe_allow_html=True)
                
                conn = get_connection()
                query = """
                    SELECT 
                        bulan,
                        tahun,
                        SUM(jumlah) as total_pembayaran
                    FROM pembayaran 
                    WHERE status='verified'
                    GROUP BY tahun, bulan
                    ORDER BY tahun DESC, bulan DESC
                    LIMIT 6
                """
                df_pembayaran = pd.read_sql_query(query, conn)
                conn.close()
                
                if not df_pembayaran.empty:
                    df_pembayaran['periode'] = df_pembayaran['bulan'].astype(str) + '/' + df_pembayaran['tahun'].astype(str)
                    df_pembayaran = df_pembayaran.sort_values('periode')
                    
                    fig = px.bar(df_pembayaran, x='periode', y='total_pembayaran',
                                title='Pembayaran Iuran 6 Bulan Terakhir',
                                color='total_pembayaran',
                                labels={'total_pembayaran': 'Total Pembayaran (Rp)', 'periode': 'Periode'})
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Belum ada data pembayaran terverifikasi")
            
            # Aktivitas Terbaru yang Perlu Perhatian Admin
            st.markdown("---")
            st.subheader("Aktivitas yang Perlu Verifikasi")
            
            conn = get_connection()
            query = """
                SELECT 
                    p.id,
                    w.no_rumah,
                    w.nama_kepala_keluarga,
                    p.bulan || '/' || p.tahun as periode,
                    p.jumlah,
                    p.tanggal_bayar,
                    p.status
                FROM pembayaran p
                JOIN warga w ON p.warga_id = w.id
                WHERE p.status = 'pending'
                ORDER BY p.tanggal_bayar DESC
                LIMIT 10
            """
            df_pending = pd.read_sql_query(query, conn)
            conn.close()
            
            if not df_pending.empty:
                st.dataframe(df_pending, use_container_width=True, hide_index=True)
            else:
                st.info("Tidak ada pembayaran yang perlu diverifikasi")
        
        elif st.session_state.page == "Data Warga":
            st.markdown('<h1 class="main-header">Data Warga</h1>', unsafe_allow_html=True)
            
            # Tab untuk berbagai fungsi data warga
            tab1, tab2, tab3 = st.tabs(["Daftar Warga", "Tambah Warga", "Import Data"])
            
            with tab1:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader("Daftar Semua Warga")
                with col2:
                    if st.button("Refresh Data", key="refresh_warga"):
                        st.rerun()
                
                conn = get_connection()
                df_warga = pd.read_sql_query("SELECT * FROM warga ORDER BY no_rumah", conn)
                conn.close()
                
                if not df_warga.empty:
                    # Filter
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        filter_status = st.selectbox("Filter Status", ["Semua", "aktif", "non-aktif"])
                    
                    with col2:
                        search_term = st.text_input("Cari", placeholder="Nama / No Rumah")
                    
                    # Apply filters
                    filtered_df = df_warga.copy()
                    if filter_status != "Semua":
                        filtered_df = filtered_df[filtered_df['status'] == filter_status]
                    
                    if search_term:
                        mask = filtered_df['nama_kepala_keluarga'].str.contains(search_term, case=False) | \
                               filtered_df['no_rumah'].str.contains(search_term, case=False)
                        filtered_df = filtered_df[mask]
                    
                    # Tampilkan data
                    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
                    
                    # Action buttons untuk setiap warga
                    st.subheader("Kelola Warga")
                    selected_warga = st.selectbox(
                        "Pilih warga untuk dikelola",
                        options=["Pilih warga..."] + filtered_df.apply(
                            lambda x: f"{x['no_rumah']} - {x['nama_kepala_keluarga']}", axis=1
                        ).tolist()
                    )
                    
                    if selected_warga != "Pilih warga...":
                        no_rumah = selected_warga.split(" - ")[0]
                        warga_data = filtered_df[filtered_df['no_rumah'] == no_rumah].iloc[0]
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.button("Edit Data", use_container_width=True):
                                st.session_state.edit_warga_id = int(warga_data['id'])
                                st.session_state.page = "Edit Warga"
                                st.rerun()
                        
                        with col2:
                            if st.button("Nonaktifkan", use_container_width=True):
                                if update_warga(int(warga_data['id']), (
                                    warga_data['no_rumah'],
                                    warga_data['nama_kepala_keluarga'],
                                    int(warga_data['anggota_keluarga']),
                                    warga_data['telepon'],
                                    warga_data['email'],
                                    warga_data['tanggal_masuk'],
                                    'non-aktif'
                                )):
                                    st.success(f"Warga {warga_data['nama_kepala_keluarga']} dinonaktifkan")
                                    st.rerun()
                        
                        with col3:
                            if st.button("Hapus Data", use_container_width=True, type="secondary"):
                                if st.checkbox(f"Konfirmasi hapus {warga_data['nama_kepala_keluarga']}?"):
                                    if delete_warga(int(warga_data['id'])):
                                        st.success("Data berhasil dihapus")
                                        st.rerun()
                
                else:
                    st.info("Belum ada data warga")
            
            with tab2:
                st.subheader("Tambah Warga Baru")
                with st.form("tambah_warga_form", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        no_rumah = st.text_input("No Rumah*", placeholder="A-01")
                        nama = st.text_input("Nama Kepala Keluarga*")
                        anggota = st.number_input("Jumlah Anggota", min_value=1, value=1)
                    
                    with col2:
                        telepon = st.text_input("Telepon", placeholder="081234567890")
                        email = st.text_input("Email", placeholder="nama@email.com")
                        tanggal_masuk = st.date_input("Tanggal Masuk", value=datetime.now())
                        status = st.selectbox("Status", ["aktif", "non-aktif"])
                    
                    submitted = st.form_submit_button("Simpan", type="primary", use_container_width=True)
                    
                    if submitted:
                        if no_rumah and nama:
                            try:
                                data = (
                                    no_rumah.strip(),
                                    nama.strip(),
                                    int(anggota),
                                    telepon.strip(),
                                    email.strip(),
                                    tanggal_masuk.strftime('%Y-%m-%d'),
                                    status
                                )
                                warga_id = add_warga(data)
                                st.success(f"Data warga berhasil ditambahkan (ID: {warga_id})")
                            except Exception as e:
                                st.error(f"Gagal menambahkan data: {str(e)}")
                        else:
                            st.error("No Rumah dan Nama harus diisi")
            
            with tab3:
                st.subheader("Import Data Warga")
                uploaded_file = st.file_uploader("Upload file CSV", type=['csv'])
                
                if uploaded_file:
                    try:
                        df_import = pd.read_csv(uploaded_file)
                        st.dataframe(df_import.head(), use_container_width=True)
                        
                        if st.button("Import Data", type="primary"):
                            success_count = 0
                            error_count = 0
                            
                            for _, row in df_import.iterrows():
                                try:
                                    if pd.notna(row.get('no_rumah')) and pd.notna(row.get('nama_kepala_keluarga')):
                                        data = (
                                            str(row['no_rumah']).strip(),
                                            str(row['nama_kepala_keluarga']).strip(),
                                            int(row.get('anggota_keluarga', 1)),
                                            str(row.get('telepon', '')).strip(),
                                            str(row.get('email', '')).strip(),
                                            pd.to_datetime(row.get('tanggal_masuk', datetime.now())).strftime('%Y-%m-%d'),
                                            str(row.get('status', 'aktif')).lower()
                                        )
                                        add_warga(data)
                                        success_count += 1
                                    else:
                                        error_count += 1
                                except:
                                    error_count += 1
                            
                            st.success(f"Import selesai: {success_count} berhasil, {error_count} gagal")
                    except Exception as e:
                        st.error(f"Error membaca file: {str(e)}")
        
        elif st.session_state.page == "Pembayaran":
            st.markdown('<h1 class="main-header">Kelola Pembayaran</h1>', unsafe_allow_html=True)
            
            tab1, tab2, tab3 = st.tabs(["Verifikasi Pembayaran", "Input Pembayaran", "Riwayat"])
            
            with tab1:
                st.subheader("Pembayaran yang Perlu Verifikasi")
                
                conn = get_connection()
                query = """
                    SELECT 
                        p.id,
                        w.no_rumah,
                        w.nama_kepala_keluarga,
                        p.bulan || '/' || p.tahun as periode,
                        p.jumlah,
                        p.tanggal_bayar,
                        p.metode_bayar,
                        p.bukti_bayar,
                        p.catatan
                    FROM pembayaran p
                    JOIN warga w ON p.warga_id = w.id
                    WHERE p.status = 'pending'
                    ORDER BY p.tanggal_bayar DESC
                """
                df_pending = pd.read_sql_query(query, conn)
                conn.close()
                
                if not df_pending.empty:
                    for _, row in df_pending.iterrows():
                        with st.container():
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown(f"**{row['no_rumah']} - {row['nama_kepala_keluarga']}**")
                                st.markdown(f"Periode: {row['periode']} | Jumlah: Rp {row['jumlah']:,}")
                                st.markdown(f"Metode: {row['metode_bayar']} | Tanggal: {row['tanggal_bayar']}")
                                if row['bukti_bayar']:
                                    st.markdown(f"Bukti: {row['bukti_bayar']}")
                                if row['catatan']:
                                    st.markdown(f"Catatan: {row['catatan']}")
                            
                            with col2:
                                col_ver, col_rej = st.columns(2)
                                with col_ver:
                                    if st.button("✓ Verifikasi", key=f"ver_{row['id']}", use_container_width=True):
                                        from utils.database import update_pembayaran_status
                                        update_pembayaran_status(row['id'], 'verified', st.session_state.user_id)
                                        st.success("Pembayaran diverifikasi")
                                        st.rerun()
                                with col_rej:
                                    if st.button("✗ Tolak", key=f"rej_{row['id']}", use_container_width=True, type="secondary"):
                                        from utils.database import update_pembayaran_status
                                        update_pembayaran_status(row['id'], 'rejected', st.session_state.user_id)
                                        st.warning("Pembayaran ditolak")
                                        st.rerun()
                            
                            st.divider()
                else:
                    st.info("Tidak ada pembayaran yang perlu diverifikasi")
            
            with tab2:
                st.subheader("Input Pembayaran Manual")
                
                with st.form("input_pembayaran_form"):
                    # Pilih warga
                    conn = get_connection()
                    df_warga = pd.read_sql_query("SELECT id, no_rumah, nama_kepala_keluarga FROM warga WHERE status='aktif' ORDER BY no_rumah", conn)
                    conn.close()
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        warga_options = df_warga.apply(lambda x: f"{x['no_rumah']} - {x['nama_kepala_keluarga']}", axis=1).tolist()
                        selected_warga = st.selectbox("Pilih Warga", ["Pilih warga..."] + warga_options)
                        
                        bulan = st.number_input("Bulan", min_value=1, max_value=12, value=datetime.now().month)
                        tahun = st.number_input("Tahun", min_value=2020, max_value=2100, value=datetime.now().year)
                    
                    with col2:
                        jumlah = st.number_input("Jumlah (Rp)", min_value=0, value=100000)
                        tanggal_bayar = st.date_input("Tanggal Bayar", value=datetime.now())
                        metode_bayar = st.selectbox("Metode Bayar", ["Transfer", "Tunai", "QRIS"])
                        status = st.selectbox("Status", ["verified", "pending"])
                        bukti_bayar = st.text_input("No. Bukti/Referensi")
                        catatan = st.text_area("Catatan")
                    
                    submitted = st.form_submit_button("Simpan Pembayaran", type="primary", use_container_width=True)
                    
                    if submitted and selected_warga != "Pilih warga...":
                        # Extract warga_id
                        no_rumah = selected_warga.split(" - ")[0]
                        warga_id = int(df_warga[df_warga['no_rumah'] == no_rumah]['id'].iloc[0])
                        
                        from utils.database import add_pembayaran
                        try:
                            data = (
                                warga_id, bulan, tahun, jumlah,
                                tanggal_bayar.strftime('%Y-%m-%d'),
                                metode_bayar, bukti_bayar, status, catatan
                            )
                            pembayaran_id = add_pembayaran(data)
                            st.success(f"Pembayaran berhasil disimpan (ID: {pembayaran_id})")
                        except Exception as e:
                            st.error(f"Gagal menyimpan: {str(e)}")
            
            with tab3:
                st.subheader("Riwayat Pembayaran")
                
                conn = get_connection()
                df_pembayaran = pd.read_sql_query("""
                    SELECT 
                        p.*,
                        w.no_rumah,
                        w.nama_kepala_keluarga
                    FROM pembayaran p
                    JOIN warga w ON p.warga_id = w.id
                    ORDER BY p.tahun DESC, p.bulan DESC, p.tanggal_bayar DESC
                    LIMIT 100
                """, conn)
                conn.close()
                
                if not df_pembayaran.empty:
                    st.dataframe(df_pembayaran, use_container_width=True, hide_index=True)
                else:
                    st.info("Belum ada riwayat pembayaran")
        
        elif st.session_state.page == "Pengeluaran":
            st.markdown('<h1 class="main-header">Kelola Pengeluaran</h1>', unsafe_allow_html=True)
            
            tab1, tab2 = st.tabs(["Daftar Pengeluaran", "Tambah Pengeluaran"])
            
            with tab1:
                st.subheader("Riwayat Pengeluaran Kas")
                
                conn = get_connection()
                # Mengambil data pengeluaran dari database
                df_pengeluaran = pd.read_sql_query("SELECT * FROM pengeluaran ORDER BY tanggal DESC", conn)
                conn.close()
                
                if not df_pengeluaran.empty:
                    # Filter sederhana
                    search_pengeluaran = st.text_input("Cari deskripsi pengeluaran...")
                    if search_pengeluaran:
                        df_pengeluaran = df_pengeluaran[df_pengeluaran['keterangan'].str.contains(search_pengeluaran, case=False)]
                    
                    st.dataframe(df_pengeluaran, use_container_width=True, hide_index=True)
                    
                    # Statistik Pengeluaran
                    total_keluar = df_pengeluaran['jumlah'].sum()
                    st.info(f"**Total Pengeluaran Tercatat:** Rp {total_keluar:,}")
                else:
                    st.info("Belum ada data pengeluaran.")
            
            with tab2:
                st.subheader("Input Pengeluaran Baru")
                with st.form("form_pengeluaran", clear_on_submit=True):
                    tanggal = st.date_input("Tanggal Pengeluaran", value=datetime.now())
                    keterangan = st.text_input("Keterangan / Keperluan*", placeholder="Contoh: Perbaikan lampu jalan")
                    jumlah = st.number_input("Jumlah (Rp)*", min_value=0, step=1000)
                    kategori = st.selectbox("Kategori", ["Kebersihan", "Keamanan", "Perbaikan", "Administrasi", "Lain-lain"])
                    pj = st.text_input("Penanggung Jawab", value=st.session_state.username)
                    
                    submitted = st.form_submit_button("Simpan Pengeluaran", type="primary")
                    
                    if submitted:
                        if keterangan and jumlah > 0:
                            try:
                                conn = get_connection()
                                cursor = conn.cursor()
                                cursor.execute("""
                                    INSERT INTO pengeluaran (tanggal, keterangan, jumlah, kategori, penanggung_jawab)
                                    VALUES (?, ?, ?, ?, ?)
                                """, (tanggal.strftime('%Y-%m-%d'), keterangan, jumlah, kategori, pj))
                                conn.commit()
                                conn.close()
                                st.success("Data pengeluaran berhasil disimpan!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Gagal menyimpan data: {e}")
                        else:
                            st.warning("Mohon isi keterangan dan jumlah dengan benar.")
        
        elif st.session_state.page == "Kelola User":
            st.markdown('<h1 class="main-header">Kelola Pengguna</h1>', unsafe_allow_html=True)
            
            tab1, tab2 = st.tabs(["Daftar User", "Tambah User"])
            
            with tab1:
                st.subheader("Daftar Semua Pengguna")
                
                users = get_all_users()
                if not users.empty:
                    st.dataframe(users, use_container_width=True, hide_index=True)
                    
                    # Action untuk user
                    selected_user = st.selectbox(
                        "Pilih user untuk dikelola",
                        options=["Pilih user..."] + users.apply(
                            lambda x: f"{x['username']} - {x['nama_lengkap']} ({x['role']})", axis=1
                        ).tolist()
                    )
                    
                    if selected_user != "Pilih user...":
                        username = selected_user.split(" - ")[0]
                        user_data = users[users['username'] == username].iloc[0]
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.button("Edit Role", use_container_width=True):
                                st.session_state.edit_user_id = int(user_data['id'])
                                st.session_state.edit_user_role = user_data['role']
                                st.rerun()
                        
                        with col2:
                            new_status = "inactive" if user_data['status'] == 'active' else 'active'
                            status_text = "Nonaktifkan" if user_data['status'] == 'active' else 'Aktifkan'
                            if st.button(status_text, use_container_width=True):
                                conn = get_connection()
                                cursor = conn.cursor()
                                cursor.execute("UPDATE users SET status=? WHERE id=?", (new_status, int(user_data['id'])))
                                conn.commit()
                                conn.close()
                                st.success(f"Status user diubah menjadi {new_status}")
                                st.rerun()
                        
                        with col3:
                            if st.button("Reset Password", use_container_width=True, type="secondary"):
                                conn = get_connection()
                                cursor = conn.cursor()
                                cursor.execute("UPDATE users SET password='user123' WHERE id=?", (int(user_data['id']),))
                                conn.commit()
                                conn.close()
                                st.success("Password direset ke 'user123'")
                else:
                    st.info("Belum ada data user")
            
            with tab2:
                st.subheader("Tambah User Baru")
                with st.form("tambah_user_form", clear_on_submit=True):
                    username = st.text_input("Username*")
                    nama_lengkap = st.text_input("Nama Lengkap*")
                    password = st.text_input("Password*", type="password")
                    role = st.selectbox("Role", ["user", "admin"])
                    
                    submitted = st.form_submit_button("Tambah User", type="primary", use_container_width=True)
                    
                    if submitted:
                        if username and nama_lengkap and password:
                            try:
                                user_id = add_user(username, password, nama_lengkap, role)
                                st.success(f"User berhasil ditambahkan (ID: {user_id})")
                            except Exception as e:
                                st.error(f"Gagal menambahkan user: {str(e)}")
                        else:
                            st.error("Semua field harus diisi")
        
        elif st.session_state.page == "Pengaturan":
            st.markdown('<h1 class="main-header">Pengaturan Sistem</h1>', unsafe_allow_html=True)
            
            tab1, tab2 = st.tabs(["Database", "Aplikasi"])
            
            with tab1:
                st.subheader("Manajemen Database")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Backup Database", use_container_width=True):
                        import shutil
                        backup_file = f"backup/database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                        os.makedirs("backup", exist_ok=True)
                        shutil.copy2("data/database.db", backup_file)
                        st.success(f"Database berhasil di-backup ke {backup_file}")
                
                with col2:
                    if st.button("Reset Auto-increment", use_container_width=True, type="secondary"):
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM sqlite_sequence")
                        conn.commit()
                        conn.close()
                        st.success("Auto-increment direset")
                
                # Database Info
                st.subheader("Info Database")
                conn = get_connection()
                tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
                
                for table in tables['name']:
                    count = pd.read_sql_query(f"SELECT COUNT(*) as count FROM {table}", conn)['count'][0]
                    st.write(f"**{table}**: {count} records")
                
                conn.close()
            
            with tab2:
                st.subheader("Pengaturan Aplikasi")
                
                # Default settings
                default_iuran = st.number_input("Default Iuran per Bulan (Rp)", min_value=0, value=100000)
                batas_waktu = st.number_input("Batas Waktu Pembayaran (hari)", min_value=1, value=15)
                notifikasi_email = st.checkbox("Aktifkan Notifikasi Email", value=False)
                
                if st.button("Simpan Pengaturan", type="primary"):
                    # Save settings (simplified)
                    settings = {
                        'default_iuran': default_iuran,
                        'batas_waktu': batas_waktu,
                        'notifikasi_email': notifikasi_email,
                        'updated_by': st.session_state.username,
                        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    st.success("Pengaturan disimpan")
        
        else:
            st.error("Halaman tidak ditemukan")
    
    else:
        # =========== USER BIASA PAGES ===========
        if st.session_state.page == "Dashboard":
            st.markdown('<h1 class="main-header">Dashboard User</h1>', unsafe_allow_html=True)
            st.markdown('<div class="info-message">👋 Selamat datang! Anda login sebagai user biasa dengan akses terbatas.</div>', unsafe_allow_html=True)
            
            # Statistik untuk user biasa
            col1, col2 = st.columns(2)
            
            with col1:
                conn = get_connection()
                total_warga = pd.read_sql_query("SELECT COUNT(*) as total FROM warga WHERE status='aktif'", conn)['total'][0]
                conn.close()
                st.metric("Total Warga Aktif", total_warga)
            
            with col2:
                current_month = datetime.now().month
                current_year = datetime.now().year
                conn = get_connection()
                query = f"""
                    SELECT COUNT(DISTINCT warga_id) as jumlah 
                    FROM pembayaran 
                    WHERE bulan={current_month} AND tahun={current_year} AND status='verified'
                """
                lunas_count = pd.read_sql_query(query, conn)['jumlah'][0]
                conn.close()
                st.metric(f"Sudah Bayar ({current_month}/{current_year})", lunas_count)
            
            # Info untuk user biasa
            st.info("""
            **Hak Akses Anda:**
            - Melihat statistik umum
            - Tidak dapat mengubah data
            - Tidak dapat verifikasi pembayaran
            - Tidak dapat mengelola user
            
            **Jika memerlukan akses lebih:**
            Hubungi administrator untuk mendapatkan hak akses admin.
            """)