"""
Módulo para coletar informações de hosts do Zabbix.
"""
from pyzabbix import ZabbixAPI
from typing import List, Dict
import logging
import urllib3

# Desabilita avisos de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Não configura logging aqui - deixa para o módulo principal configurar
logger = logging.getLogger(__name__)


class ZabbixCollector:
    """Coletor de informações de hosts do Zabbix."""
    
    def __init__(self, url: str, username: str, password: str):
        """
        Inicializa o coletor do Zabbix.
        
        Args:
            url: URL da API do Zabbix (ex: http://zabbix.example.com)
            username: Nome de usuário para autenticação
            password: Senha para autenticação
        """
        self.url = url
        self.username = username
        self.password = password
        self.zapi = None
    
    def connect(self):
        """Estabelece conexão com a API do Zabbix."""
        try:
            self.zapi = ZabbixAPI(self.url)
            # Desabilita verificação SSL
            self.zapi.session.verify = False
            self.zapi.login(self.username, self.password)
            logger.info(f"Conectado ao Zabbix: {self.url}")
            logger.info(f"Versão do Zabbix: {self.zapi.api_version()}")
        except Exception as e:
            logger.error(f"Erro ao conectar ao Zabbix: {e}")
            raise
    
    def disconnect(self):
        """Encerra a conexão com a API do Zabbix."""
        if self.zapi:
            self.zapi.user.logout()
            logger.info("Desconectado do Zabbix")
    
    def get_all_hosts(self) -> List[Dict[str, str]]:
        """
        Coleta todos os hosts cadastrados no Zabbix com nome, IP, grupos e templates.
        
        Returns:
            Lista de dicionários contendo host_id, hostname, ip_address, host_groups e templates
        """
        if not self.zapi:
            raise Exception("Não conectado ao Zabbix. Execute connect() primeiro.")
        
        try:
            # Busca todos os hosts com suas interfaces, grupos e templates
            hosts = self.zapi.host.get(
                output=['hostid', 'host', 'name'],
                selectInterfaces=['type', 'ip', 'main'],
                selectGroups=['groupid', 'name'],
                selectParentTemplates=['templateid', 'name'],  # Adiciona templates
                filter={'status': 0}  # 0 = hosts habilitados
            )
            
            hosts_data = []
            
            for host in hosts:
                # Pega o IP da interface principal (geralmente Agent interface)
                ip_address = None
                if host.get('interfaces'):
                    # Procura pela interface principal
                    for interface in host['interfaces']:
                        if interface.get('main') == '1':
                            ip_address = interface.get('ip')
                            break
                    
                    # Se não encontrou interface principal, pega a primeira
                    if not ip_address and host['interfaces']:
                        ip_address = host['interfaces'][0].get('ip')
                
                # Pega os nomes dos grupos do host
                host_groups = []
                if host.get('groups'):
                    host_groups = [group.get('name') for group in host['groups']]
                
                # Pega os nomes dos templates do host
                templates = []
                if host.get('parentTemplates'):
                    templates = [template.get('name') for template in host['parentTemplates']]
                
                hosts_data.append({
                    'host_id': host['hostid'],
                    'hostname': host.get('name') or host.get('host'),
                    'ip_address': ip_address or 'N/A',
                    'host_groups': ', '.join(host_groups) if host_groups else 'N/A',
                    'templates': ', '.join(templates) if templates else 'N/A'
                })
            
            logger.info(f"Coletados {len(hosts_data)} hosts do Zabbix")
            return hosts_data
            
        except Exception as e:
            logger.error(f"Erro ao coletar hosts: {e}")
            raise
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
