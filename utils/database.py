import sqlite3
import pandas as pd
from datetime import datetime
import os
import streamlit as st

# ==================== FUNGSI UTAMA ====================

def get_connection():
    """Membuat koneksi ke database dengan proteksi multithreading dan foreign keys"""
    if not os.path.exists('data'):
        os.makedirs('data')
    conn = sqlite3.connect('data/database.db', check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON") # Tambahkan baris ini
    return conn

def init_db():
    """Inisialisasi database dan semua tabel yang dibutuhkan"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Tabel warga
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS warga (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            no_rumah TEXT NOT NULL UNIQUE,
            nama_kepala_keluarga TEXT NOT NULL,
            anggota_keluarga INTEGER DEFAULT 1,
            telepon TEXT,
            email TEXT,
            tanggal_masuk DATE DEFAULT CURRENT_DATE,
            status TEXT DEFAULT 'aktif',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Tabel pembayaran
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pembayaran (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            warga_id INTEGER,
            bulan INTEGER,
            tahun INTEGER,
            jumlah INTEGER,
            tanggal_bayar DATE DEFAULT CURRENT_DATE,
            metode_bayar TEXT,
            bukti_bayar TEXT,
            status TEXT DEFAULT 'pending',
            catatan TEXT DEFAULT '',
            verified_by INTEGER,
            verified_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (warga_id) REFERENCES warga (id) ON DELETE CASCADE,
            UNIQUE(warga_id, bulan, tahun)
        )
    ''')
    
    # 3. Tabel pengeluaran
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pengeluaran (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kategori TEXT NOT NULL,
            deskripsi TEXT,
            jumlah INTEGER NOT NULL,
            tanggal DATE DEFAULT CURRENT_DATE,
            bukti TEXT,
            disetujui_oleh INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 4. Tabel users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nama_lengkap TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 5. Tabel pending_changes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pending_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT,
            record_id INTEGER,
            action TEXT,
            old_data TEXT,
            new_data TEXT,
            requested_by INTEGER,
            status TEXT DEFAULT 'pending',
            reviewed_by INTEGER,
            review_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# ==================== FUNGSI WARGA ====================

@st.cache_data(ttl=300)
def get_all_warga(active_only=True):
    """Ambil data warga dengan cache untuk mencegah kedap-kedip"""
    conn = get_connection()
    try:
        query = "SELECT * FROM warga WHERE status='aktif' ORDER BY no_rumah" if active_only else "SELECT * FROM warga ORDER BY no_rumah"
        return pd.read_sql_query(query, conn)
    finally:
        conn.close()

def add_warga(data):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO warga (no_rumah, nama_kepala_keluarga, anggota_keluarga, telepon, email, tanggal_masuk, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', data)
        conn.commit()
        st.cache_data.clear() # Reset cache agar data baru langsung muncul
        return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def update_warga(warga_id, data):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE warga SET no_rumah=?, nama_kepala_keluarga=?, anggota_keluarga=?, 
            telepon=?, email=?, tanggal_masuk=?, status=? WHERE id=?
        ''', (*data, warga_id))
        conn.commit()
        st.cache_data.clear()
        return True
    except:
        return False
    finally:
        conn.close()

def delete_warga(warga_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM warga WHERE id = ?', (warga_id,))
        conn.commit()
        st.cache_data.clear()
        return True
    except:
        return False
    finally:
        conn.close()

def get_warga_by_id(warga_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM warga WHERE id=?", (warga_id,))
    warga = cursor.fetchone()
    conn.close()
    return warga

@st.cache_data(ttl=60)
def search_warga(keyword):
    if not keyword:
        return get_all_warga()
    conn = get_connection()
    try:
        query = "SELECT * FROM warga WHERE (nama_kepala_keluarga LIKE ? OR no_rumah LIKE ?) ORDER BY no_rumah"
        return pd.read_sql_query(query, conn, params=(f'%{keyword}%', f'%{keyword}%'))
    finally:
        conn.close()

# ==================== FUNGSI PEMBAYARAN ====================

@st.cache_data(ttl=300)
def get_all_pembayaran():
    conn = get_connection()
    try:
        query = '''
            SELECT p.*, w.no_rumah, w.nama_kepala_keluarga 
            FROM pembayaran p
            JOIN warga w ON p.warga_id = w.id
            ORDER BY p.tahun DESC, p.bulan DESC, p.tanggal_bayar DESC
        '''
        return pd.read_sql_query(query, conn)
    finally:
        conn.close()

def add_pembayaran(data):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        warga_id, bulan, tahun, jumlah, tanggal_bayar, metode_bayar, bukti_bayar, status, catatan = data
        if status == 'verified':
            query = 'INSERT INTO pembayaran (warga_id, bulan, tahun, jumlah, tanggal_bayar, metode_bayar, bukti_bayar, status, catatan, verified_by, verified_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
            params = (warga_id, bulan, tahun, jumlah, tanggal_bayar, metode_bayar, bukti_bayar, status, catatan, 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        else:
            query = 'INSERT INTO pembayaran (warga_id, bulan, tahun, jumlah, tanggal_bayar, metode_bayar, bukti_bayar, status, catatan) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'
            params = (warga_id, bulan, tahun, jumlah, tanggal_bayar, metode_bayar, bukti_bayar, status, catatan)
        
        cursor.execute(query, params)
        conn.commit()
        st.cache_data.clear()
        return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def update_pembayaran_status(pembayaran_id, status, verified_by=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if status == 'verified' and verified_by:
            cursor.execute('UPDATE pembayaran SET status=?, verified_by=?, verified_at=datetime("now") WHERE id=?', (status, verified_by, pembayaran_id))
        else:
            cursor.execute('UPDATE pembayaran SET status=? WHERE id=?', (status, pembayaran_id))
        conn.commit()
        st.cache_data.clear()
    finally:
        conn.close()

# ==================== FUNGSI REPORT & ADMIN ====================

@st.cache_data(ttl=300)
def get_pembayaran_report():
    conn = get_connection()
    try:
        query = '''
            SELECT p.id, w.no_rumah, w.nama_kepala_keluarga, p.bulan, p.tahun, 
                   p.jumlah, p.tanggal_bayar, p.metode_bayar, p.status
            FROM pembayaran p
            JOIN warga w ON p.warga_id = w.id
            ORDER BY p.tahun DESC, p.bulan DESC
        '''
        df = pd.read_sql_query(query, conn)
        # Proteksi: Konversi ke tipe data Python standar agar tidak error numpy.int64
        if not df.empty:
            df['tahun'] = df['tahun'].astype(int)
            df['bulan'] = df['bulan'].astype(int)
        return df
    except:
        return pd.DataFrame()
    finally:
        conn.close()

def get_pending_changes():
    conn = get_connection()
    try:
        query = '''
            SELECT pc.*, u.username as requested_by_name 
            FROM pending_changes pc
            LEFT JOIN users u ON pc.requested_by = u.id
            WHERE pc.status = 'pending'
            ORDER BY pc.created_at DESC
        '''
        return pd.read_sql_query(query, conn)
    except:
        return pd.DataFrame()
    finally:
        conn.close()

def update_pending_change_status(change_id, status, reviewer_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE pending_changes 
            SET status = ?, reviewed_by = ?, review_date = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, reviewer_id, change_id))
        conn.commit()
        st.cache_data.clear()
        return True
    except:
        return False
    finally:
        conn.close()

def get_change_history():
    conn = get_connection()
    try:
        query = '''
            SELECT pc.*, u1.username as requested_by_name, u2.username as reviewed_by_name
            FROM pending_changes pc
            LEFT JOIN users u1 ON pc.requested_by = u1.id
            LEFT JOIN users u2 ON pc.reviewed_by = u2.id
            WHERE pc.status != 'pending'
            ORDER BY pc.review_date DESC
        '''
        return pd.read_sql_query(query, conn)
    except:
        return pd.DataFrame()
    finally:
        conn.close()

# ==================== FUNGSI Pengaturan ====================
def update_user(user_id, username, nama_lengkap, role, status):
    """Memperbarui data user berdasarkan ID."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users 
            SET username = ?, nama_lengkap = ?, role = ?, status = ?
            WHERE id = ?
        """, (username, nama_lengkap, role, status, user_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error update_user: {e}")
        return False
    

# ==================== FUNGSI USERS & PENGELUARAN ====================

def authenticate_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=? AND password=? AND status='active'", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

def get_all_users():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM users ORDER BY created_at DESC", conn)
    conn.close()
    return df

def add_user(data):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (username, password, nama_lengkap, role, status) VALUES (?, ?, ?, ?, ?)', data)
        conn.commit()
        return True
    finally:
        conn.close()

@st.cache_data(ttl=300)
def get_all_pengeluaran():
    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM pengeluaran ORDER BY tanggal DESC", conn)
        return df
    except:
        return pd.DataFrame()
    finally:
        conn.close()

def add_pengeluaran(data):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO pengeluaran (kategori, deskripsi, jumlah, tanggal, bukti, disetujui_oleh) VALUES (?, ?, ?, ?, ?, ?)', data)
        conn.commit()
        st.cache_data.clear()
        return cursor.lastrowid
    finally:
        conn.close()


def delete_pengeluaran(pengeluaran_id):
    """Menghapus data pengeluaran berdasarkan ID"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM pengeluaran WHERE id = ?', (pengeluaran_id,))
        conn.commit()
        st.cache_data.clear() # Membersihkan cache agar daftar di UI langsung terupdate
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error delete_pengeluaran: {e}")
        return False
    finally:
        conn.close()

# ==================== INISIALISASI ====================

if __name__ == "__main__":
    init_db()