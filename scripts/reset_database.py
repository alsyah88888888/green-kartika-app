#!/usr/bin/env python3
"""
RESET DATABASE TOOL (CLEAN VERSION)
Menghapus semua data transaksi dan warga, menyisakan struktur tabel kosong.
Jalankan: python scripts/reset_database.py --force
"""

import os
import sqlite3
import shutil
from datetime import datetime
import sys

def reset_database():
    """Reset database ke kondisi nol (tanpa data sample)"""
    print("🔄 RESET DATABASE TO ZERO (CLEAN)")
    print("=" * 60)
    
    db_path = 'data/database.db'
    
    # Pastikan folder data ada
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # 1. Backup database lama jika ada
    if os.path.exists(db_path):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f'data/backup_database_{timestamp}.db'
        
        try:
            shutil.copy2(db_path, backup_path)
            print(f"📦 Database lama di-backup ke: {backup_path}")
        except Exception as e:
            print(f"⚠️  Gagal backup: {e}")
            confirm = input("Lanjutkan tanpa backup? (y/n): ").strip().lower()
            if confirm != 'y':
                print("❌ Reset dibatalkan")
                return
    
    # 2. Konfirmasi reset ketat
    print("\n⚠️  ⚠️  ⚠️  PERINGATAN KERAS ⚠️  ⚠️  ⚠️")
    print("Ini akan menghapus SELURUH data warga, pembayaran, dan pengeluaran.")
    print("Database akan kembali KOSONG (0).")
    
    confirm = input("\nKetik 'KOSONGKAN' untuk konfirmasi: ").strip()
    
    if confirm != "KOSONGKAN":
        print("❌ Konfirmasi salah. Reset dibatalkan.")
        return
    
    # 3. Hapus database lama untuk memastikan schema fresh
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
            print("\n🗑️ File database lama telah dihapus.")
    except Exception as e:
        print(f"❌ Gagal hapus database: {e}")
        return
    
    # 4. Buat database dan tabel baru (Schema Only)
    print("🆕 Membuat database bersih...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Tabel warga (Kosong)
        cursor.execute('''
            CREATE TABLE warga (
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
        
        # Tabel pembayaran (Kosong)
        cursor.execute('''
            CREATE TABLE pembayaran (
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
                FOREIGN KEY (warga_id) REFERENCES warga (id)
            )
        ''')
        
        # Tabel users (Hanya Admin)
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                nama_lengkap TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabel pengeluaran (Kosong)
        cursor.execute('''
            CREATE TABLE pengeluaran (
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
        
        # Insert HANYA 1 user admin untuk akses awal
        print("👤 Menambahkan akun administrator default...")
        cursor.execute('''
            INSERT INTO users (username, password, nama_lengkap, role) 
            VALUES ('admin', 'admin123', 'Super Admin', 'admin')
        ''')
        
        conn.commit()
        print("\n✅ DATABASE BERHASIL DIRESET KE NOL!")
        print("📊 STATUS SAAT INI:")
        print("   - Data Warga      : 0 (Kosong)")
        print("   - Data Pembayaran : 0 (Kosong)")
        print("   - Data Pengeluaran: 0 (Kosong)")
        print("   - User Tersedia   : 1 (Admin)")
        
        print("\n🔑 LOGIN ADMIN:")
        print("   Username: admin")
        print("   Password: admin123")
        
    except sqlite3.Error as e:
        print(f"❌ Terjadi kesalahan SQL: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚨 RESET DATABASE TOOL - MODE BERSIH TOTAL")
    print("=" * 60)
    
    # Cek argumen --force agar tidak sengaja menjalankan
    if len(sys.argv) > 1 and sys.argv[1] == "--force":
        reset_database()
    else:
        print("\n⚠️  Bahaya! Tool ini akan mengosongkan seluruh isi database.")
        print("📌 Gunakan perintah berikut jika Anda yakin:")
        print("   python scripts/reset_database.py --force")
        print("")