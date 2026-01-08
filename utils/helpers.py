import pandas as pd
from datetime import datetime
import json

def format_currency(value):
    """Format angka ke format mata uang Indonesia"""
    if pd.isna(value) or value is None:
        return "Rp 0"
    return f"Rp {int(value):,}"

def format_date(date_str, format_from='%Y-%m-%d', format_to='%d-%m-%Y'):
    """Format tanggal dari satu format ke format lain"""
    if pd.isna(date_str) or date_str is None:
        return ""
    
    try:
        date_obj = datetime.strptime(str(date_str), format_from)
        return date_obj.strftime(format_to)
    except:
        return str(date_str)

def get_month_name(month_num):
    """Dapatkan nama bulan dari angka bulan"""
    months = [
        '', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
        'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
    ]
    return months[month_num] if 1 <= month_num <= 12 else ''

def calculate_age(tanggal_lahir):
    """Hitung umur dari tanggal lahir"""
    if pd.isna(tanggal_lahir) or tanggal_lahir is None:
        return 0
    
    try:
        birth_date = datetime.strptime(str(tanggal_lahir), '%Y-%m-%d')
        today = datetime.now()
        age = today.year - birth_date.year
        
        # Kurangi 1 jika belum ulang tahun tahun ini
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1
        
        return age
    except:
        return 0

def validate_email(email):
    """Validasi format email sederhana"""
    if pd.isna(email) or email is None or email == '':
        return True
    
    return '@' in email and '.' in email.split('@')[-1]

def validate_phone(phone):
    """Validasi nomor telepon Indonesia"""
    if pd.isna(phone) or phone is None or phone == '':
        return True
    
    # Hapus karakter non-digit
    phone_digits = ''.join(filter(str.isdigit, str(phone)))
    
    # Cek panjang minimal 10 digit, maksimal 13 digit
    return 10 <= len(phone_digits) <= 13

def create_summary_statistics(df, numeric_column):
    """Buat statistik ringkasan untuk kolom numerik"""
    if df.empty or numeric_column not in df.columns:
        return {}
    
    stats = {
        'total': df[numeric_column].sum(),
        'average': df[numeric_column].mean(),
        'median': df[numeric_column].median(),
        'min': df[numeric_column].min(),
        'max': df[numeric_column].max(),
        'count': len(df),
        'non_null_count': df[numeric_column].count()
    }
    
    return stats

def export_to_excel(dataframes, sheet_names, filename):
    """Export multiple dataframes ke file Excel"""
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        for df, sheet_name in zip(dataframes, sheet_names):
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    return filename

def backup_database(source_path='data/database.db', backup_dir='data/backup'):
    """Backup database ke folder backup"""
    import shutil
    import os
    
    # Buat folder backup jika belum ada
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Generate nama file backup dengan timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'database_backup_{timestamp}.db')
    
    # Salin file database
    shutil.copy2(source_path, backup_file)
    
    # Hapus backup lama (simpan hanya 10 terbaru)
    backup_files = sorted([os.path.join(backup_dir, f) for f in os.listdir(backup_dir) 
                          if f.startswith('database_backup_')], 
                         key=os.path.getmtime, reverse=True)
    
    for old_file in backup_files[10:]:
        os.remove(old_file)
    
    return backup_file

def load_json_safe(json_str, default=None):
    """Load JSON dengan error handling"""
    if json_str is None or json_str == '':
        return default if default is not None else {}
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return default if default is not None else {}

def format_datetime_for_display(dt_str):
    """Format datetime string untuk display"""
    if pd.isna(dt_str) or dt_str is None:
        return ""
    
    try:
        # Coba berbagai format
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%d-%m-%Y %H:%M:%S',
            '%d-%m-%Y'
        ]
        
        for fmt in formats:
            try:
                dt_obj = datetime.strptime(str(dt_str), fmt)
                return dt_obj.strftime('%d-%m-%Y %H:%M')
            except:
                continue
        
        return str(dt_str)
    except:
        return str(dt_str)