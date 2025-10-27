"""
Módulo para coletar informações de hosts do Zabbix.
"""
from pyzabbix import ZabbixAPI
from typing import List, Dict
import logging
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class ZabbixCollector:
    def __init__(self, url: str, username: str, password: str):
        self.url = url
        self.username = username
        self.password = password
        self.zapi = None
    
    def connect(self):
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
        if self.zapi:
            self.zapi.user.logout()
            logger.info("Desconectado do Zabbix")
    
    def get_all_hosts(self) -> List[Dict[str, str]]:
        if not self.zapi:
            raise Exception("Não conectado ao Zabbix. Execute connect() primeiro.")
        
        try:
            hosts = self.zapi.host.get(
                output=['hostid', 'host', 'name'],
                selectInterfaces=['type', 'ip', 'main'],
                selectGroups=['groupid', 'name'],
                selectParentTemplates=['templateid', 'name'],
                filter={'status': 0}
            )
            
            hosts_data = []
            
            for host in hosts:
                ip_address = None
                if host.get('interfaces'):
                    for interface in host['interfaces']:
                        if interface.get('main') == '1':
                            ip_address = interface.get('ip')
                            break
                    
                    if not ip_address and host['interfaces']:
                        ip_address = host['interfaces'][0].get('ip')
                
                host_groups = []
                if host.get('groups'):
                    host_groups = [group.get('name') for group in host['groups']]
                
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
