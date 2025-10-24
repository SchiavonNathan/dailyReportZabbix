"""
Script de migração para adicionar coluna 'templates' ao banco de dados.
"""
import sqlite3
import os

db_path = 'zabbix_hosts.db'

if not os.path.exists(db_path):
    print(f"❌ Banco de dados não encontrado: {db_path}")
    exit(1)

print("=" * 80)
print("MIGRAÇÃO DO BANCO DE DADOS - Adicionando coluna 'templates'")
print("=" * 80)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Verifica se a coluna já existe
    cursor.execute("PRAGMA table_info(hosts_history)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'templates' in columns:
        print("\n✅ Coluna 'templates' já existe no banco de dados")
    else:
        print("\n🔄 Adicionando coluna 'templates'...")
        
        # Adiciona a coluna templates
        cursor.execute('''
            ALTER TABLE hosts_history 
            ADD COLUMN templates TEXT DEFAULT 'N/A'
        ''')
        
        conn.commit()
        print("✅ Coluna 'templates' adicionada com sucesso!")
    
    # Mostra estrutura da tabela
    print("\n📋 Estrutura atual da tabela hosts_history:")
    print("-" * 80)
    cursor.execute("PRAGMA table_info(hosts_history)")
    for column in cursor.fetchall():
        print(f"  {column[1]}: {column[2]}")
    
    print("\n" + "=" * 80)
    print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ Erro durante a migração: {e}")
    conn.rollback()
finally:
    conn.close()
