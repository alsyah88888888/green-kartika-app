#!/usr/bin/env python3
"""
CHECK DATA TOOL
Untuk diagnosis dan cek kondisi database
Jalankan: python scripts/check_data.py
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime

def check_database_health():
    """Cek kesehatan database secara menyeluruh"""
    print("🔍 DATABASE HEALTH CHECK")
    print("=" * 60)
    
    db_path = 'data/database.db'
    
    # 1. Cek file database
    if not os.path.exists(db_path):
        print("❌ Database file tidak ditemukan!")
        print(f"📁 Expected: {os.path.abspath(db_path)}")
        return
    
    file_size = os.path.getsize(db_path) / 1024  # KB
    print(f"📁 Database file: {db_path}")
    print(f"📏 Size: {file_size:.2f} KB")
    print(f"📅 Modified: {datetime.fromtimestamp(os.path.getmtime(db_path))}")
    
    # 2. Koneksi dan cek integritas
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n✅ Database bisa diakses")
        
        # Cek integrity
        cursor.execute("PRAGMA integrity_check")
        integrity = cursor.fetchone()[0]
        print(f"🔧 Integrity check: {integrity}")
        
        if integrity != "ok":
            print("❌ DATABASE RUSAK! Perlu perbaikan.")
        
        # 3. Cek semua tabel
        print("\n📋 TABEL DATABASE:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            
            # Cek struktur
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print(f"\n  🏷️  {table_name} ({count} rows)")
            for col in columns:
                print(f"     - {col[1]} ({col[2]})")
        
        # 4. ANALISIS DATA PEMBAYARAN
        print("\n" + "=" * 60)
        print("📊 ANALISIS DATA PEMBAYARAN")
        print("=" * 60)
        
        try:
            df = pd.read_sql_query("SELECT * FROM pembayaran", conn)
            
            if df.empty:
                print("📭 Tabel pembayaran kosong")
            else:
                print(f"📈 Total data: {len(df)}")
                
                # Per tahun
                print("\n📅 Distribusi per tahun:")
                year_counts = df['tahun'].value_counts().sort_index()
                for year, count in year_counts.items():
                    print(f"  - {year}: {count} data")
                
                # Per status
                print("\n🏷️ Distribusi per status:")
                status_counts = df['status'].value_counts()
                for status, count in status_counts.items():
                    print(f"  - {status}: {count} data")
                
                # Per bulan
                print("\n📆 Distribusi per bulan:")
                month_counts = df['bulan'].value_counts().sort_index()
                for month, count in month_counts.items():
                    month_name = datetime(2000, month, 1).strftime('%B')
                    print(f"  - {month_name}: {count} data")
                
                # Statistik keuangan
                print("\n💰 STATISTIK KEUANGAN:")
                total_amount = df['jumlah'].sum()
                avg_amount = df['jumlah'].mean()
                print(f"  - Total nilai: Rp {total_amount:,}")
                print(f"  - Rata-rata per transaksi: Rp {avg_amount:,.0f}")
                print(f"  - Nilai tertinggi: Rp {df['jumlah'].max():,}")
                print(f"  - Nilai terendah: Rp {df['jumlah'].min():,}")
                
                # Cek data anomali
                print("\n⚠️  CEK ANOMALI:")
                
                # Warga_id tidak valid
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM pembayaran p 
                    LEFT JOIN warga w ON p.warga_id = w.id 
                    WHERE w.id IS NULL
                """)
                invalid_warga = cursor.fetchone()[0]
                if invalid_warga > 0:
                    print(f"  ❌ {invalid_warga} data dengan warga_id tidak valid")
                
                # Duplikat bukti bayar
                cursor.execute("""
                    SELECT bukti_bayar, COUNT(*) as jumlah 
                    FROM pembayaran 
                    WHERE bukti_bayar != '' 
                    GROUP BY bukti_bayar 
                    HAVING COUNT(*) > 1
                """)
                duplicates = cursor.fetchall()
                if duplicates:
                    print(f"  ⚠️  {len(duplicates)} bukti bayar duplikat ditemukan")
        
        except Exception as e:
            print(f"❌ Error analisis pembayaran: {e}")
        
        # 5. ANALISIS DATA WARGA
        print("\n" + "=" * 60)
        print("👥 ANALISIS DATA WARGA")
        print("=" * 60)
        
        try:
            df_warga = pd.read_sql_query("SELECT * FROM warga", conn)
            
            if df_warga.empty:
                print("📭 Tabel warga kosong")
            else:
                print(f"👤 Total warga: {len(df_warga)}")
                
                # Per status
                print("\n🏷️ Status warga:")
                status_counts = df_warga['status'].value_counts()
                for status, count in status_counts.items():
                    print(f"  - {status}: {count} warga")
                
                # Jumlah anggota keluarga
                total_anggota = df_warga['anggota_keluarga'].sum()
                avg_anggota = df_warga['anggota_keluarga'].mean()
                print(f"\n👨‍👩‍👧‍👦 Total anggota keluarga: {total_anggota}")
                print(f"📊 Rata-rata anggota per keluarga: {avg_anggota:.1f}")
                
                # Warga tanpa pembayaran
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM warga w 
                    LEFT JOIN pembayaran p ON w.id = p.warga_id 
                    WHERE p.id IS NULL
                """)
                warga_tanpa_bayar = cursor.fetchone()[0]
                if warga_tanpa_bayar > 0:
                    print(f"\n⚠️  {warga_tanpa_bayar} warga belum pernah bayar")
        
        except Exception as e:
            print(f"❌ Error analisis warga: {e}")
        
        conn.close()
        print("\n✅ Health check selesai!")
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def export_report():
    """Export report ke file"""
    print("\n📤 GENERATING REPORT...")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"data/database_report_{timestamp}.txt"
    
    try:
        # Redirect output ke file
        import sys
        original_stdout = sys.stdout
        
        with open(report_file, 'w', encoding='utf-8') as f:
            sys.stdout = f
            check_database_health()
            sys.stdout = original_stdout
        
        print(f"✅ Report disimpan ke: {report_file}")
        
    except Exception as e:
        print(f"❌ Gagal export report: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "export":
        export_report()
    else:
        check_database_health()