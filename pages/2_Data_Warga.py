import streamlit as st
import pandas as pd
from datetime import datetime
from utils.database import get_all_warga, add_warga, update_warga, delete_warga, get_connection
import io

# Konfigurasi Halaman
st.set_page_config(page_title="Data Warga", layout="wide")

# CSS kustom untuk tampilan minimalis
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        border-radius: 4px 4px 0px 0px;
    }
    </style>
""", unsafe_allow_html=True)

# State Management
if 'warga_data' not in st.session_state:
    st.session_state.warga_data = get_all_warga()

def refresh_data():
    st.session_state.warga_data = get_all_warga()
    st.rerun()

st.title("Data Warga")

tab1, tab2, tab3, tab4 = st.tabs([
    "Daftar Warga", 
    "Tambah Data", 
    "Edit / Hapus", 
    "Import"
])

# --- TAB 1: DAFTAR WARGA ---
with tab1:
    df = st.session_state.warga_data.copy()
    
    # Header & Filter
    c1, c2, c3 = st.columns([2, 3, 1])
    with c1:
        f_status = st.selectbox("Filter Status", ["Semua", "Aktif", "Non-aktif"])
    with c2:
        search = st.text_input("Pencarian", placeholder="Nama atau Nomor Rumah")
    with c3:
        st.write(" ")
        if st.button("Refresh Data", use_container_width=True):
            refresh_data()

    # Logika Filter
    if not df.empty:
        if f_status != "Semua":
            df = df[df['status'] == f_status.lower()]
        if search:
            df = df[df.apply(lambda row: search.lower() in str(row).lower(), axis=1)]

    # Tampilan Tabel
    if not df.empty:
        # Statistik Ringkas
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Warga", len(df))
        m2.metric("Aktif", len(df[df['status'] == 'aktif']))
        m3.metric("Non-aktif", len(df[df['status'] == 'non-aktif']))
        m4.metric("Total Anggota", int(df['anggota_keluarga'].sum()))

        st.dataframe(
            df[['no_rumah', 'nama_kepala_keluarga', 'anggota_keluarga', 'telepon', 'email', 'status']],
            use_container_width=True,
            hide_index=True
        )
        
        # Export
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", csv, "data_warga.csv", "text/csv")
    else:
        st.info("Data tidak ditemukan")

# --- TAB 2: TAMBAH DATA ---
with tab2:
    with st.form("form_add", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            no_rumah = st.text_input("Nomor Rumah")
            nama = st.text_input("Nama Kepala Keluarga")
            anggota = st.number_input("Jumlah Anggota", min_value=1, value=1)
        with col2:
            telepon = st.text_input("Telepon")
            email = st.text_input("Email")
            status = st.selectbox("Status", ["Aktif", "Non-aktif"])
        
        if st.form_submit_button("Simpan Data Baru", type="primary"):
            if no_rumah and nama:
                data = (no_rumah, nama, anggota, telepon, email, 
                        datetime.now().strftime('%Y-%m-%d'), status.lower())
                if add_warga(data):
                    st.success("Data berhasil disimpan")
                    refresh_data()
                else:
                    st.error("Gagal menyimpan. Cek apakah nomor rumah sudah ada.")
            else:
                st.warning("Nomor rumah dan Nama wajib diisi")

# --- TAB 3: EDIT / HAPUS ---
if not st.session_state.get('is_admin', False):
    st.error("Akses ditolak.")
    st.stop()

with tab3:
    df_edit = st.session_state.warga_data
    if not df_edit.empty:
        option = st.selectbox("Pilih Warga", 
                            options=df_edit.index,
                            format_func=lambda x: f"{df_edit.loc[x, 'no_rumah']} - {df_edit.loc[x, 'nama_kepala_keluarga']}")
        
        curr = df_edit.loc[option]
        
        with st.form("form_edit"):
            c1, c2 = st.columns(2)
            with c1:
                e_no = st.text_input("Nomor Rumah", value=curr['no_rumah'])
                e_nama = st.text_input("Nama Kepala Keluarga", value=curr['nama_kepala_keluarga'])
                e_anggota = st.number_input("Jumlah Anggota", value=int(curr['anggota_keluarga']))
            with c2:
                e_telp = st.text_input("Telepon", value=curr['telepon'])
                e_mail = st.text_input("Email", value=curr['email'])
                e_stat = st.selectbox("Status", ["Aktif", "Non-aktif"], 
                                    index=0 if curr['status'] == 'aktif' else 1)
            
            col_btn1, col_btn2 = st.columns([1, 4])
            with col_btn1:
                if st.form_submit_button("Update", type="primary"):
                    update_data = (e_no, e_nama, e_anggota, e_telp, e_mail, curr['tanggal_masuk'], e_stat.lower())
                    if update_warga(int(curr['id']), update_data):
                        st.success("Data diperbarui")
                        refresh_data()
            with col_btn2:
                if st.form_submit_button("Hapus Data"):
                    if delete_warga(int(curr['id'])):
                        st.success("Data dihapus")
                        refresh_data()
    else:
        st.info("Tidak ada data untuk diedit")

        

with tab4:
    st.info("Pastikan kolom di file sesuai: no_rumah, nama_kepala_keluarga, anggota_keluarga, telepon, email, status")
    uploaded_file = st.file_uploader("Upload CSV/Excel", type=['csv', 'xlsx'])
    
    if uploaded_file:
        try:
            # Membaca file
            if uploaded_file.name.endswith('.csv'):
                df_imp = pd.read_csv(uploaded_file)
            else:
                df_imp = pd.read_excel(uploaded_file)
            
            # Tampilkan pratinjau data
            st.write("Pratinjau Data (5 baris pertama):")
            st.dataframe(df_imp.head(), use_container_width=True)
            
            if st.button("Proses Import Data", type="primary"):
                conn = get_connection()
                success_count = 0
                fail_count = 0
                error_details = []

                # Kolom yang wajib ada di database (sesuaikan dengan tabel warga Anda)
                db_columns = ['no_rumah', 'nama_kepala_keluarga', 'anggota_keluarga', 'telepon', 'email', 'status']
                
                # Filter hanya kolom yang ada di database agar tidak error
                # Jika Excel punya kolom tambahan, kolom itu akan diabaikan
                available_columns = [col for col in db_columns if col in df_imp.columns]
                df_to_save = df_imp[available_columns].copy()

                # Tambahkan tanggal_masuk otomatis jika tidak ada di Excel
                if 'tanggal_masuk' not in df_to_save.columns:
                    df_to_save['tanggal_masuk'] = datetime.now().strftime('%Y-%m-%d')

                # Proses baris demi baris agar jika 1 gagal, yang lain tetap masuk
                for index, row in df_to_save.iterrows():
                    try:
                        # Convert ke DataFrame satu baris
                        single_row_df = pd.DataFrame([row])
                        single_row_df.to_sql('warga', conn, if_exists='append', index=False)
                        success_count += 1
                    except Exception as e:
                        fail_count += 1
                        error_details.append(f"Baris {index+1}: {str(e)}")

                conn.close()

                # Hasil Akhir
                if success_count > 0:
                    st.success(f"✅ {success_count} data berhasil diimport.")
                    refresh_data()
                
                if fail_count > 0:
                    st.error(f"❌ {fail_count} data gagal diimport.")
                    with st.expander("Lihat Detail Error"):
                        for err in error_details[:10]: # Tampilkan 10 error pertama
                            st.write(err)
                        if len(error_details) > 10:
                            st.write("...dan error lainnya.")

        except Exception as e:
            st.error(f"File tidak valid atau rusak: {e}")