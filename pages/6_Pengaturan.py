import streamlit as st
import pandas as pd
from utils.database import get_all_users, update_user

st.set_page_config(page_title="Pengaturan Pengguna", layout="wide")

st.title("Pengaturan Pengguna")

if not st.session_state.get('is_admin', False):
    st.error("Akses ditolak.")
    st.stop()

# 1. Sinkronisasi Data
df_users = get_all_users()

if df_users.empty:
    st.info("Tidak ada data pengguna.")
else:
    # 2. Area Seleksi
    user_list = df_users.apply(lambda x: f"{x['id']} - {x['username']}", axis=1).tolist()
    
    col_selector, _ = st.columns([1, 2])
    with col_selector:
        selected_option = st.selectbox("Pilih pengguna", ["-- Pilih --"] + user_list)

    if selected_option != "-- Pilih --":
        # 3. Parsing Data Terpilih
        user_id = int(selected_option.split(" - ")[0])
        user_data = df_users[df_users['id'] == user_id].iloc[0]

        st.divider()
        
        # 4. Form Edit Minimalis
        with st.form(key=f"edit_form_{user_id}"):
            st.write(f"**Update Profil: {user_data['username']}**")
            
            c1, c2 = st.columns(2)
            with c1:
                new_username = st.text_input("Username", value=user_data['username'])
                new_nama = st.text_input("Nama Lengkap", value=user_data['nama_lengkap'])
            
            with c2:
                new_role = st.selectbox("Role", ["admin", "user"], 
                                      index=0 if user_data['role'] == 'admin' else 1)
                new_status = st.selectbox("Status", ["active", "inactive"], 
                                        index=0 if user_data['status'] == 'active' else 1)
            
            # Tombol diletakkan di kolom kecil agar tidak terlalu lebar
            btn_col, _ = st.columns([1, 4])
            with btn_col:
                if st.form_submit_button("Simpan", type="primary", use_container_width=True):
                    if update_user(user_id, new_username, new_nama, new_role, new_status):
                        st.success("Berhasil diperbarui")
                        st.rerun()
                    else:
                        st.error("Gagal memperbarui")