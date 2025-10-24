import sqlite3

conn = sqlite3.connect('zabbix_hosts.db')
cursor = conn.cursor()

# Conta quantos registros existem por data
cursor.execute('''
    SELECT collection_date, COUNT(*) as total
    FROM hosts_history
    GROUP BY collection_date
    ORDER BY collection_date DESC
''')

print("=" * 80)
print("REGISTROS POR DATA NO BANCO")
print("=" * 80)

rows = cursor.fetchall()
for date, total in rows:
    print(f"{date}: {total} registros")

print("\n" + "=" * 80)

# Verifica se há duplicatas (mesmo host_id na mesma data)
cursor.execute('''
    SELECT collection_date, host_id, COUNT(*) as count
    FROM hosts_history
    GROUP BY collection_date, host_id
    HAVING COUNT(*) > 1
    LIMIT 10
''')

duplicates = cursor.fetchall()
if duplicates:
    print("⚠️  DUPLICATAS ENCONTRADAS:")
    print("=" * 80)
    for date, host_id, count in duplicates:
        print(f"{date} - Host {host_id}: {count} vezes")
else:
    print("✅ Nenhuma duplicata encontrada")

conn.close()
