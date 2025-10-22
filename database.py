"""
Módulo de gerenciamento do banco de dados SQLite para hosts do Zabbix.
"""
import sqlite3
from datetime import datetime
from typing import List, Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Gerenciador de banco de dados para armazenar hosts do Zabbix."""
    
    def __init__(self, db_path: str = "zabbix_hosts.db"):
        """
        Inicializa o gerenciador de banco de dados.
        
        Args:
            db_path: Caminho para o arquivo do banco de dados SQLite
        """
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Cria as tabelas necessárias se não existirem."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela para armazenar histórico de hosts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hosts_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host_id TEXT NOT NULL,
                hostname TEXT NOT NULL,
                ip_address TEXT,
                host_groups TEXT,
                collection_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Índice para melhorar performance de consultas por data
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_collection_date 
            ON hosts_history(collection_date)
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Banco de dados inicializado: {self.db_path}")
    
    def save_hosts(self, hosts: List[Dict[str, str]], collection_date: str = None):
        """
        Salva a lista de hosts no banco de dados.
        
        Args:
            hosts: Lista de dicionários com informações dos hosts
            collection_date: Data da coleta (formato YYYY-MM-DD). Se None, usa data atual
        """
        if collection_date is None:
            collection_date = datetime.now().strftime("%Y-%m-%d")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for host in hosts:
            cursor.execute('''
                INSERT INTO hosts_history (host_id, hostname, ip_address, host_groups, collection_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                host.get('host_id'),
                host.get('hostname'),
                host.get('ip_address'),
                host.get('host_groups'),
                collection_date
            ))
        
        conn.commit()
        conn.close()
        logger.info(f"Salvos {len(hosts)} hosts para a data {collection_date}")
    
    def get_hosts_by_date(self, date: str) -> List[Dict[str, str]]:
        """
        Recupera todos os hosts de uma data específica.
        
        Args:
            date: Data no formato YYYY-MM-DD
            
        Returns:
            Lista de dicionários com informações dos hosts
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT host_id, hostname, ip_address, host_groups
            FROM hosts_history
            WHERE collection_date = ?
            ORDER BY hostname
        ''', (date,))
        
        rows = cursor.fetchall()
        conn.close()
        
        hosts = [
            {
                'host_id': row[0],
                'hostname': row[1],
                'ip_address': row[2],
                'host_groups': row[3]
            }
            for row in rows
        ]
        
        return hosts
    
    def get_latest_collection_date(self) -> str:
        """
        Retorna a data da última coleta realizada.
        
        Returns:
            Data no formato YYYY-MM-DD ou None se não houver dados
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT collection_date
            FROM hosts_history
            ORDER BY collection_date DESC
            LIMIT 1
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def check_date_exists(self, date: str) -> bool:
        """
        Verifica se já existe uma coleta para a data especificada.
        
        Args:
            date: Data no formato YYYY-MM-DD
            
        Returns:
            True se existir, False caso contrário
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM hosts_history
            WHERE collection_date = ?
        ''', (date,))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    
    def get_all_collection_dates(self) -> List[str]:
        """
        Retorna todas as datas de coleta disponíveis.
        
        Returns:
            Lista de datas no formato YYYY-MM-DD
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT collection_date
            FROM hosts_history
            ORDER BY collection_date DESC
        ''')
        
        dates = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return dates
