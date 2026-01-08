#!/usr/bin/env python3
"""
QUICK DELETE TOOL - VERSI UPDATE
Untuk menghapus data spesifik dari database dengan cepat
Jalankan: python scripts/quick_delete.py
"""

import sqlite3
import os
import sys
from datetime import datetime

def show_menu():
    """Tampilkan menu pilihan"""
    print("=" * 60)
    print("🗑️  QUICK DELETE TOOL - UPDATE")
    print("=" * 60)
    print("\nPILIH DATA YANG INGIN DIHAPUS:")
    print("1. Hapus SEMUA data tahun 2026")
    print("2. Hapus SEMUA data tahun 2024")
    print("3. Hapus SEMUA data tahun 2025")
    print("4. Hapus data Verified tahun tertentu")
    print("5. Hapus data Pending tahun tertentu")
    print("6. Hapus berdasarkan ID spesifik")
    print("7. Hapus berdasarkan range ID")
    print("8. Tampilkan data saat ini")
    print("9. Keluar")
    print("=" * 60)

def get_db_connection():
    """Dapatkan koneksi database"""
    db_path = 'data/database.db'
    
    # Cek apakah database ada
    if not os.path.exists(db_path):
        print(f"❌ Database tidak ditemukan di: {db_path}")
        print("📁 Lokasi saat ini:", os.path.abspath('.'))
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        return conn
    except Exception as e:
        print(f"❌ Tidak bisa connect ke database: {e}")
        return None

def show_current_data():
    """Tampilkan data saat ini"""
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    print("\n📊 DATA SAAT INI:")
    print("-" * 60)
    
    # Total data
    cursor.execute("SELECT COUNT(*) FROM pembayaran")
    total = cursor.fetchone()[0]
    print(f"Total data pembayaran: {total}")
    
    # Per tahun
    cursor.execute("SELECT tahun, COUNT(*) as jumlah FROM pembayaran GROUP BY tahun ORDER BY tahun")
    print("\n📅 Data per tahun:")
    years_data = cursor.fetchall()
    for tahun, jumlah in years_data:
        print(f"  - Tahun {tahun}: {jumlah} data")
    
    # Per status
    cursor.execute("SELECT status, COUNT(*) as jumlah FROM pembayaran GROUP BY status")
    print("\n🏷️ Data per status:")
    for status, jumlah in cursor.fetchall():
        print(f"  - Status '{status}': {jumlah} data")
    
    # Tampilkan tahun yang ada
    available_years = [str(year) for year, _ in years_data]
    print(f"\n🎯 Tahun yang tersedia: {', '.join(available_years)}")
    
    conn.close()
    print("-" * 60)

def delete_by_year(year):
    """Hapus semua data tahun tertentu"""
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    # Hitung sebelum
    cursor.execute("SELECT COUNT(*) FROM pembayaran WHERE tahun=?", (year,))
    count_before = cursor.fetchone()[0]
    
    if count_before == 0:
        print(f"\nℹ️ Tidak ada data tahun {year}")
        conn.close()
        return
    
    print(f"\n⚠️  Akan menghapus {count_before} data tahun {year}")
    confirm = input("Yakin? (y/n): ").strip().lower()
    
    if confirm == 'y':
        cursor.execute("DELETE FROM pembayaran WHERE tahun=?", (year,))
        deleted = cursor.rowcount
        conn.commit()
        
        # Verifikasi
        cursor.execute("SELECT COUNT(*) FROM pembayaran WHERE tahun=?", (year,))
        count_after = cursor.fetchone()[0]
        
        print(f"\n✅ {deleted} data tahun {year} dihapus!")
        print(f"📊 Data tahun {year} tersisa: {count_after}")
    else:
        print("❌ Penghapusan dibatalkan")
    
    conn.close()

def delete_by_year_status(year, status):
    """Hapus data tahun tertentu dengan status tertentu"""
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    # Hitung sebelum
    cursor.execute("SELECT COUNT(*) FROM pembayaran WHERE tahun=? AND status=?", (year, status))
    count_before = cursor.fetchone()[0]
    
    if count_before == 0:
        print(f"\nℹ️ Tidak ada data {status} tahun {year}")
        conn.close()
        return
    
    print(f"\n⚠️  Akan menghapus {count_before} data {status} tahun {year}")
    confirm = input("Yakin? (y/n): ").strip().lower()
    
    if confirm == 'y':
        cursor.execute("DELETE FROM pembayaran WHERE tahun=? AND status=?", (year, status))
        deleted = cursor.rowcount
        conn.commit()
        
        print(f"\n✅ {deleted} data {status} tahun {year} dihapus!")
    else:
        print("❌ Penghapusan dibatalkan")
    
    conn.close()

def delete_by_ids():
    """Hapus berdasarkan ID spesifik"""
    conn = get_db_connection()
    if not conn:
        return
    
    # Tampilkan 20 data terbaru untuk referensi
    print("\n📋 20 data terbaru untuk referensi:")
    cursor = conn.cursor()
    cursor.execute("SELECT id, tahun, status, jumlah FROM pembayaran ORDER BY id DESC LIMIT 20")
    
    for row in cursor.fetchall():
        print(f"  ID {row[0]:3}: Tahun {row[1]}, Status {row[2]:8}, Jumlah Rp {row[3]:,}")
    
    # Input IDs
    print("\n📝 Masukkan ID yang ingin dihapus")
    ids_input = input("Pisahkan dengan koma (contoh: 1,2,3): ").strip()
    
    if not ids_input:
        print("❌ Tidak ada ID yang dimasukkan")
        conn.close()
        return
    
    # Parse IDs
    ids = []
    for id_str in ids_input.split(','):
        id_str = id_str.strip()
        if id_str.isdigit():
            ids.append(int(id_str))
    
    if not ids:
        print("❌ Tidak ada ID yang valid")
        conn.close()
        return
    
    print(f"\n⚠️  Akan menghapus {len(ids)} data: ID {ids}")
    confirm = input("Yakin? (y/n): ").strip().lower()
    
    if confirm == 'y':
        deleted_total = 0
        for pid in ids:
            cursor.execute("DELETE FROM pembayaran WHERE id=?", (pid,))
            deleted_total += cursor.rowcount
        
        conn.commit()
        print(f"\n✅ {deleted_total} data dihapus!")
    else:
        print("❌ Penghapusan dibatalkan")
    
    conn.close()

def delete_by_range():
    """Hapus berdasarkan range ID"""
    conn = get_db_connection()
    if not conn:
        return
    
    print("\n🎯 Hapus berdasarkan range ID")
    
    # Tampilkan range ID yang ada
    cursor = conn.cursor()
    cursor.execute("SELECT MIN(id), MAX(id) FROM pembayaran")
    min_id, max_id = cursor.fetchone()
    
    if min_id is None:
        print("❌ Tidak ada data")
        conn.close()
        return
    
    print(f"📊 ID tersedia: {min_id} - {max_id}")
    
    start_id = input("ID awal: ").strip()
    end_id = input("ID akhir: ").strip()
    
    if not start_id.isdigit() or not end_id.isdigit():
        print("❌ ID harus angka")
        conn.close()
        return
    
    start_id = int(start_id)
    end_id = int(end_id)
    
    if start_id > end_id:
        print("❌ ID awal harus lebih kecil dari ID akhir")
        conn.close()
        return
    
    # Hitung data dalam range
    cursor.execute("SELECT COUNT(*) FROM pembayaran WHERE id BETWEEN ? AND ?", (start_id, end_id))
    count = cursor.fetchone()[0]
    
    if count == 0:
        print(f"ℹ️ Tidak ada data dengan ID {start_id}-{end_id}")
        conn.close()
        return
    
    print(f"\n⚠️  Akan menghapus {count} data (ID {start_id}-{end_id})")
    confirm = input("Yakin? (y/n): ").strip().lower()
    
    if confirm == 'y':
        cursor.execute("DELETE FROM pembayaran WHERE id BETWEEN ? AND ?", (start_id, end_id))
        deleted = cursor.rowcount
        conn.commit()
        
        print(f"\n✅ {deleted} data (ID {start_id}-{end_id}) dihapus!")
    else:
        print("❌ Penghapusan dibatalkan")
    
    conn.close()

def main():
    """Main function"""
    
    # Cek apakah database ada
    if not os.path.exists('data/database.db'):
        print("❌ Database tidak ditemukan")
        print("📌 Pastikan Anda berada di folder yang benar")
        print(f"📁 Lokasi saat ini: {os.path.abspath('.')}")
        return
    
    while True:
        show_menu()
        
        try:
            choice = input("\nPilihan (1-9): ").strip()
            
            if choice == '1':
                delete_by_year(2026)
            elif choice == '2':
                delete_by_year(2024)
            elif choice == '3':
                delete_by_year(2025)
            elif choice == '4':
                year = input("Masukkan tahun: ").strip()
                if year.isdigit():
                    delete_by_year_status(int(year), 'verified')
                else:
                    print("❌ Tahun harus angka")
            elif choice == '5':
                year = input("Masukkan tahun: ").strip()
                if year.isdigit():
                    delete_by_year_status(int(year), 'pending')
                else:
                    print("❌ Tahun harus angka")
            elif choice == '6':
                delete_by_ids()
            elif choice == '7':
                delete_by_range()
            elif choice == '8':
                show_current_data()
            elif choice == '9':
                print("👋 Sampai jumpa!")
                break
            else:
                print("❌ Pilihan tidak valid")
            
            input("\n📌 Tekan Enter untuk melanjutkan...")
            
        except KeyboardInterrupt:
            print("\n\n👋 Program dihentikan")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    # Cek jika dijalankan dengan argumen langsung
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "delete2026":
            delete_by_year(2026)
        elif command == "delete2024":
            delete_by_year(2024)
        elif command == "delete2025":
            delete_by_year(2025)
        elif command == "show":
            show_current_data()
        elif command.startswith("delete"):
            # Coba ekstrak tahun dari command
            try:
                year = int(command.replace("delete", ""))
                delete_by_year(year)
            except:
                print(f"❌ Argumen tidak dikenal: {command}")
                print("\n📌 Penggunaan:")
                print("  python scripts/quick_delete.py                    # Menu interaktif")
                print("  python scripts/quick_delete.py delete2026         # Hapus data 2026")
                print("  python scripts/quick_delete.py delete2024         # Hapus data 2024")
                print("  python scripts/quick_delete.py delete2025         # Hapus data 2025")
                print("  python scripts/quick_delete.py delete[TAHUN]      # Hapus data tahun tertentu")
                print("  python scripts/quick_delete.py show               # Tampilkan data")
        else:
            print(f"❌ Argumen tidak dikenal: {command}")
            print("\n📌 Penggunaan:")
            print("  python scripts/quick_delete.py                    # Menu interaktif")
            print("  python scripts/quick_delete.py delete2026         # Hapus data 2026")
            print("  python scripts/quick_delete.py delete2024         # Hapus data 2024")
            print("  python scripts/quick_delete.py delete2025         # Hapus data 2025")
            print("  python scripts/quick_delete.py delete[TAHUN]      # Hapus data tahun tertentu")
            print("  python scripts/quick_delete.py show               # Tampilkan data")
    else:
        main()