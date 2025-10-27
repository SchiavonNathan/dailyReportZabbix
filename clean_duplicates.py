"""
Script para limpar duplicatas do banco de dados.
Mantém apenas a versão mais recente de cada host por data.
"""
import sqlite3
from datetime import datetime

print("=" * 80)
print("LIMPEZA DE DUPLICATAS NO BANCO DE DADOS")
print("=" * 80)

conn = sqlite3.connect('zabbix_hosts.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT collection_date, COUNT(*) as total, COUNT(DISTINCT host_id) as unique_hosts
    FROM hosts_history
    GROUP BY collection_date
    ORDER BY collection_date DESC
''')

print("\n📊 SITUAÇÃO ATUAL:")
print("-" * 80)
rows = cursor.fetchall()
total_before = 0
for date, total, unique in rows:
    duplicates = total - unique
    status = "⚠️  COM DUPLICATAS" if duplicates > 0 else "✅ OK"
    print(f"{date}: {total} registros ({unique} únicos) {status}")
    total_before += total

print(f"\nTotal de registros no banco: {total_before}")

print("\n" + "=" * 80)
response = input("\n🗑️  Deseja limpar as duplicatas? (s/n): ")

if response.lower() != 's':
    print("\n❌ Operação cancelada")
    conn.close()
    exit()

print("\n🔄 Limpando duplicatas...")

cursor.execute('SELECT DISTINCT collection_date FROM hosts_history')
dates = cursor.fetchall()

for (date,) in dates:
    cursor.execute('''
        DELETE FROM hosts_history
        WHERE id NOT IN (
            SELECT MAX(id)
            FROM hosts_history
            WHERE collection_date = ?
            GROUP BY host_id
        )
        AND collection_date = ?
    ''', (date, date))
    
    deleted = cursor.rowcount
    if deleted > 0:
        print(f"  {date}: {deleted} duplicatas removidas")

conn.commit()

cursor.execute('''
    SELECT collection_date, COUNT(*) as total
    FROM hosts_history
    GROUP BY collection_date
    ORDER BY collection_date DESC
''')

print("\n" + "=" * 80)
print("✅ SITUAÇÃO FINAL:")
print("-" * 80)
rows = cursor.fetchall()
total_after = 0
for date, total in rows:
    print(f"{date}: {total} hosts")
    total_after += total

print(f"\nTotal de registros no banco: {total_after}")
print(f"Registros removidos: {total_before - total_after}")

print("\n🔧 Otimizando banco de dados...")
cursor.execute('VACUUM')
conn.commit()

conn.close()

print("\n" + "=" * 80)
print("✅ LIMPEZA CONCLUÍDA COM SUCESSO!")
print("=" * 80)
