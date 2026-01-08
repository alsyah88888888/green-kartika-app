#!/usr/bin/env python3
"""
CLEANUP DATABASE TOOL
Untuk membersihkan data rusak/bermasalah di database
Jalankan: python scripts/cleanup_database.py
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime

def cleanup_database():
    """Cleanup database dari data bermasalah"""
    print("🧹 DATABASE CLEANUP TOOL")
    print("=" * 60)
    
    db_path = 'data/database.db'
    
    if not os.path.exists(db_path):
        print("❌ Database tidak ditemukan")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Scan masalah
    print("\n🔍 SCANNING FOR PROBLEMS...")
    
    problems = []
    
    # Cek warga_id yang tidak valid
    cursor.execute("""
        SELECT COUNT(*) 
        FROM pembayaran p 
        LEFT JOIN warga w ON p.warga_id = w.id 
        WHERE w.id IS NULL
    """)
    invalid_warga = cursor.fetchone()[0]
    if invalid_warga > 0:
        problems.append(("❌ Data dengan warga_id tidak valid", invalid_warga))
    
    # Cek duplikat bukti bayar
    cursor.execute("""
        SELECT COUNT(*) 
        FROM (
            SELECT bukti_bayar, COUNT(*) as jumlah 
            FROM pembayaran 
            WHERE bukti_bayar != '' 
            GROUP BY bukti_bayar 
            HAVING COUNT(*) > 1
        )
    """)
    duplicate_bukti = cursor.fetchone()[0]
    if duplicate_bukti > 0:
        problems.append(("⚠️  Bukti bayar duplikat", duplicate_bukti))
    
    # Cek data dengan tanggal invalid
    cursor.execute("""
        SELECT COUNT(*) 
        FROM pembayaran 
        WHERE tanggal_bayar IS NULL 
        OR tanggal_bayar = ''
        OR LENGTH(tanggal_bayar) != 10
    """)
    invalid_tanggal = cursor.fetchone()[0]
    if invalid_tanggal > 0:
        problems.append(("📅 Tanggal bayar invalid", invalid_tanggal))
    
    # Cek data dengan jumlah 0 atau negatif
    cursor.execute("SELECT COUNT(*) FROM pembayaran WHERE jumlah <= 0")
    invalid_jumlah = cursor.fetchone()[0]
    if invalid_jumlah > 0:
        problems.append(("💰 Jumlah invalid (<= 0)", invalid_jumlah))
    
    # Cek bulan/tahun invalid
    cursor.execute("SELECT COUNT(*) FROM pembayaran WHERE bulan < 1 OR bulan > 12")
    invalid_bulan = cursor.fetchone()[0]
    if invalid_bulan > 0:
        problems.append(("📆 Bulan invalid", invalid_bulan))
    
    cursor.execute("SELECT COUNT(*) FROM pembayaran WHERE tahun < 2000 OR tahun > 2100")
    invalid_tahun = cursor.fetchone()[0]
    if invalid_tahun > 0:
        problems.append(("📅 Tahun invalid", invalid_tahun))
    
    # Tampilkan masalah
    if not problems:
        print("\n✅ Tidak ada masalah ditemukan!")
        conn.close()
        return
    
    print("\n⚠️  MASALAH YANG DITEMUKAN:")
    for problem, count in problems:
        print(f"  {problem}: {count} data")
    
    # 2. Menu cleanup
    print("\n" + "=" * 60)
    print("🛠️  CLEANUP OPTIONS")
    print("=" * 60)
    
    print("1. Hapus data dengan warga_id tidak valid")
    print("2. Perbaiki warga_id (set ke warga pertama)")
    print("3. Hapus data dengan tanggal invalid")
    print("4. Hapus data dengan jumlah invalid")
    print("5. Hapus data dengan bulan/tahun invalid")
    print("6. Hapus duplikat bukti bayar (keep latest)")
    print("7. Lakukan SEMUA cleanup")
    print("8. Tampilkan detail masalah")
    print("9. Keluar")
    
    choice = input("\nPilihan (1-9): ").strip()
    
    if choice == '1':
        # Hapus data dengan warga_id tidak valid
        cursor.execute("""
            DELETE FROM pembayaran 
            WHERE warga_id NOT IN (SELECT id FROM warga)
        """)
        deleted = cursor.rowcount
        conn.commit()
        print(f"✅ {deleted} data dihapus")
    
    elif choice == '2':
        # Perbaiki warga_id
        cursor.execute("SELECT id FROM warga LIMIT 1")
        default_warga_id = cursor.fetchone()
        
        if default_warga_id:
            cursor.execute("""
                UPDATE pembayaran 
                SET warga_id = ?
                WHERE warga_id NOT IN (SELECT id FROM warga)
            """, default_warga_id)
            updated = cursor.rowcount
            conn.commit()
            print(f"✅ {updated} data diperbaiki (warga_id = {default_warga_id[0]})")
    
    elif choice == '3':
        # Hapus data tanggal invalid
        cursor.execute("""
            DELETE FROM pembayaran 
            WHERE tanggal_bayar IS NULL 
            OR tanggal_bayar = ''
            OR LENGTH(tanggal_bayar) != 10
        """)
        deleted = cursor.rowcount
        conn.commit()
        print(f"✅ {deleted} data dihapus")
    
    elif choice == '4':
        # Hapus data jumlah invalid
        cursor.execute("DELETE FROM pembayaran WHERE jumlah <= 0")
        deleted = cursor.rowcount
        conn.commit()
        print(f"✅ {deleted} data dihapus")
    
    elif choice == '5':
        # Hapus data bulan/tahun invalid
        cursor.execute("DELETE FROM pembayaran WHERE bulan < 1 OR bulan > 12")
        deleted1 = cursor.rowcount
        
        cursor.execute("DELETE FROM pembayaran WHERE tahun < 2000 OR tahun > 2100")
        deleted2 = cursor.rowcount
        
        conn.commit()
        print(f"✅ {deleted1 + deleted2} data dihapus")
    
    elif choice == '6':
        # Hapus duplikat bukti bayar (keep latest)
        cursor.execute("""
            DELETE FROM pembayaran 
            WHERE id NOT IN (
                SELECT MAX(id) 
                FROM pembayaran 
                WHERE bukti_bayar != '' 
                GROUP BY bukti_bayar
            ) 
            AND bukti_bayar IN (
                SELECT bukti_bayar 
                FROM pembayaran 
                WHERE bukti_bayar != '' 
                GROUP BY bukti_bayar 
                HAVING COUNT(*) > 1
            )
        """)
        deleted = cursor.rowcount
        conn.commit()
        print(f"✅ {deleted} duplikat dihapus (keep latest)")
    
    elif choice == '7':
        # Lakukan semua cleanup
        print("\n🚀 MELAKUKAN SEMUA CLEANUP...")
        
        total_fixed = 0
        
        # 1. Hapus invalid warga_id
        cursor.execute("DELETE FROM pembayaran WHERE warga_id NOT IN (SELECT id FROM warga)")
        total_fixed += cursor.rowcount
        
        # 2. Hapus invalid tanggal
        cursor.execute("DELETE FROM pembayaran WHERE tanggal_bayar IS NULL OR tanggal_bayar = '' OR LENGTH(tanggal_bayar) != 10")
        total_fixed += cursor.rowcount
        
        # 3. Hapus invalid jumlah
        cursor.execute("DELETE FROM pembayaran WHERE jumlah <= 0")
        total_fixed += cursor.rowcount
        
        # 4. Hapus invalid bulan/tahun
        cursor.execute("DELETE FROM pembayaran WHERE bulan < 1 OR bulan > 12")
        total_fixed += cursor.rowcount
        
        cursor.execute("DELETE FROM pembayaran WHERE tahun < 2000 OR tahun > 2100")
        total_fixed += cursor.rowcount
        
        conn.commit()
        print(f"✅ Total {total_fixed} data bermasalah dibersihkan!")
    
    elif choice == '8':
        # Tampilkan detail masalah
        print("\n📋 DETAIL MASALAH:")
        
        if invalid_warga > 0:
            print(f"\n❌ Data dengan warga_id tidak valid ({invalid_warga}):")
            cursor.execute("""
                SELECT p.id, p.warga_id, p.bulan, p.tahun, p.status
                FROM pembayaran p 
                LEFT JOIN warga w ON p.warga_id = w.id 
                WHERE w.id IS NULL
                LIMIT 10
            """)
            for row in cursor.fetchall():
                print(f"  ID {row[0]}: warga_id={row[1]}, {row[2]}/{row[3]}, {row[4]}")
        
        # ... detail lainnya ...
    
    elif choice == '9':
        print("👋 Keluar")
    
    else:
        print("❌ Pilihan tidak valid")
    
    conn.close()
    print("\n✨ Cleanup selesai!")

if __name__ == "__main__":
    cleanup_database()