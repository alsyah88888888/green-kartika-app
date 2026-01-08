import streamlit as st
import pandas as pd
from utils.database import get_all_users, add_user, get_connection

# Konfigurasi Halaman
st.set_page_config(page_title="Kelola User", layout="wide")

# Fungsi pembantu untuk Update & Delete (Jika belum ada di database.py)
def update_user_db(user_id, data):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        query = "UPDATE users SET username=?, nama_lengkap=?, role=?, status=? WHERE id=?"
        cursor.execute(query, (*data, user_id))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error Update: {e}")
        return False
    finally:
        conn.close()

def delete_user_db(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error Delete: {e}")
        return False
    finally:
        conn.close()

# --- HEADER ---
st.title("👥 Manajemen User")
st.info("Halaman ini digunakan untuk mengatur akses login pengurus dan admin.")

# Inisialisasi Data
if 'df_users' not in st.session_state:
    st.session_state.df_users = get_all_users()

def refresh_users():
    st.session_state.df_users = get_all_users()
    st.rerun()

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📋 Daftar User", "➕ Tambah User", "⚙️ Edit/Hapus Access"])

# TAB 1: DAFTAR USER
with tab1:
    df = st.session_state.df_users.copy()
    if not df.empty:
        # Menghapus kolom password agar tidak tampil di tabel
        display_df = df.drop(columns=['password']) if 'password' in df.columns else df
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        if st.button("🔄 Refresh List"):
            refresh_users()
    else:
        st.warning("Belum ada data user.")

# TAB 2: TAMBAH USER
with tab2:
    with st.form("form_tambah_user", clear_on_submit=True):
        st.subheader("Buat Akun Baru")
        c1, c2 = st.columns(2)
        with c1:
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            new_nama = st.text_input("Nama Lengkap")
        with c2:
            new_role = st.selectbox("Role", ["admin", "pengurus"])
            new_status = st.selectbox("Status", ["aktif", "non-aktif"])
        
        if st.form_submit_button("Simpan User", type="primary"):
            if new_username and new_password and new_nama:
                # Membungkus data ke dalam SATU tuple (Solusi error 5 argumen)
                data_user = (new_username, new_password, new_nama, new_role, new_status)
                
                if add_user(data_user):
                    st.success(f"User {new_username} berhasil dibuat!")
                    refresh_users()
                else:
                    st.error("Gagal menambah user. Username mungkin sudah digunakan.")
            else:
                st.warning("Mohon isi semua field wajib.")

# TAB 3: EDIT / HAPUS
with tab3:
    df_manage = st.session_state.df_users
    if not df_manage.empty:
        selected_user = st.selectbox(
            "Pilih User untuk Dikelola",
            options=df_manage.index,
            format_func=lambda x: f"{df_manage.loc[x, 'username']} ({df_manage.loc[x, 'nama_lengkap']})"
        )
        
        curr = df_manage.loc[selected_user]
        
        with st.form("form_edit_user"):
            col1, col2 = st.columns(2)
            with col1:
                e_user = st.text_input("Username", value=curr['username'])
                e_nama = st.text_input("Nama Lengkap", value=curr['nama_lengkap'])
            with col2:
                e_role = st.selectbox("Role", ["admin", "pengurus"], 
                                     index=0 if curr['role'] == 'admin' else 1)
                e_stat = st.selectbox("Status", ["aktif", "non-aktif"],
                                     index=0 if curr['status'] == 'aktif' else 1)
            
            c_btn1, c_btn2 = st.columns([1, 4])
            with c_btn1:
                if st.form_submit_button("Update", type="primary"):
                    update_data = (e_user, e_nama, e_role, e_stat)
                    if update_user_db(int(curr['id']), update_data):
                        st.success("Data user diperbarui!")
                        refresh_users()
            
            with c_btn2:
                if st.form_submit_button("Hapus User"):
                    if delete_user_db(int(curr['id'])):
                        st.warning("User telah dihapus.")
                        refresh_users()
    else:
        st.info("Tidak ada data user.")