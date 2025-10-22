"""
Script de teste para verificar configuração de envio de email.
"""
import sys
from dotenv import load_dotenv
import os
from email_sender import EmailSender
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_email():
    """Testa o envio de email com as configurações do .env"""
    
    print("=" * 70)
    print("TESTE DE ENVIO DE EMAIL - RELATÓRIO ZABBIX")
    print("=" * 70)
    print()
    
    # Carrega configurações
    load_dotenv()
    
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.office365.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    smtp_use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
    email_recipients = os.getenv('EMAIL_RECIPIENTS', '').split(',') if os.getenv('EMAIL_RECIPIENTS') else []
    
    # Validação
    print("📋 Configurações carregadas:")
    print(f"   Servidor SMTP: {smtp_server}")
    print(f"   Porta: {smtp_port}")
    print(f"   Usar TLS: {smtp_use_tls}")
    print(f"   Remetente: {smtp_username}")
    print(f"   Destinatários: {', '.join(email_recipients) if email_recipients else 'Nenhum'}")
    print()
    
    # Verifica se as configurações estão completas
    if not smtp_username:
        print("❌ ERRO: SMTP_USERNAME não configurado no arquivo .env")
        print("   Configure seu email em SMTP_USERNAME")
        return False
    
    if not smtp_password:
        print("❌ ERRO: SMTP_PASSWORD não configurado no arquivo .env")
        print("   Configure sua senha em SMTP_PASSWORD")
        return False
    
    if not email_recipients:
        print("❌ ERRO: EMAIL_RECIPIENTS não configurado no arquivo .env")
        print("   Configure os destinatários em EMAIL_RECIPIENTS")
        return False
    
    print("-" * 70)
    print("🔍 Validação: OK")
    print("-" * 70)
    print()
    
    # Confirmação
    print("📧 Email de teste será enviado para:")
    for email in email_recipients:
        print(f"   • {email.strip()}")
    print()
    
    response = input("Deseja continuar com o teste? (s/n): ").lower()
    if response != 's':
        print("\n❌ Teste cancelado pelo usuário")
        return False
    
    print()
    print("=" * 70)
    print("Iniciando teste de envio...")
    print("=" * 70)
    print()
    
    # Cria o enviador de email
    try:
        email_sender = EmailSender(
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            username=smtp_username,
            password=smtp_password,
            use_tls=smtp_use_tls
        )
        
        # Dados de teste
        summary = {
            'hosts_added': 5,
            'hosts_removed': 2,
            'hosts_modified': 3,
            'total_current': 150,
            'total_previous': 147,
            'net_change': 3
        }
        
        # Dados de comparação de teste
        comparison = {
            'added': [
                {'host_id': '10001', 'hostname': 'server-web-01', 'ip_address': '192.168.1.10', 'host_groups': 'Linux Servers, Web'},
                {'host_id': '10002', 'hostname': 'server-db-01', 'ip_address': '192.168.1.20', 'host_groups': 'Linux Servers, Database'},
                {'host_id': '10003', 'hostname': 'server-app-01', 'ip_address': '192.168.1.30', 'host_groups': 'Linux Servers, Application'},
                {'host_id': '10004', 'hostname': 'workstation-01', 'ip_address': '192.168.2.100', 'host_groups': 'Windows, Workstations'},
                {'host_id': '10005', 'hostname': 'firewall-01', 'ip_address': '192.168.0.1', 'host_groups': 'Network, Security'},
            ],
            'removed': [
                {'host_id': '9001', 'hostname': 'old-server-01', 'ip_address': '192.168.1.99', 'host_groups': 'Deprecated, Linux Servers'},
                {'host_id': '9002', 'hostname': 'test-machine', 'ip_address': '192.168.3.50', 'host_groups': 'Test Environment'},
            ],
            'modified': [
                {
                    'host_id': '8001',
                    'hostname': 'server-web-02',
                    'old_ip': '192.168.1.11',
                    'new_ip': '192.168.1.15',
                    'old_groups': 'Linux Servers',
                    'new_groups': 'Linux Servers, Web',
                    'ip_changed': True,
                    'groups_changed': True
                },
                {
                    'host_id': '8002',
                    'hostname': 'server-db-02',
                    'old_ip': '192.168.1.21',
                    'new_ip': '192.168.1.21',
                    'old_groups': 'Linux Servers',
                    'new_groups': 'Linux Servers, Database',
                    'ip_changed': False,
                    'groups_changed': True
                },
                {
                    'host_id': '8003',
                    'hostname': 'router-main',
                    'old_ip': '10.0.0.1',
                    'new_ip': '10.0.0.254',
                    'old_groups': 'Network',
                    'new_groups': 'Network',
                    'ip_changed': True,
                    'groups_changed': False
                }
            ],
            'total_current': 150,
            'total_previous': 147
        }
        
        # Envia email de teste
        success = email_sender.send_simple_report(
            recipient_emails=[email.strip() for email in email_recipients],
            report_date="2025-10-21 (TESTE)",
            summary=summary,
            has_changes=True,
            comparison=comparison,
            report_files=None  # Sem anexos no teste
        )
        
        print()
        print("=" * 70)
        if success:
            print("✅ SUCESSO! Email de teste enviado com sucesso!")
            print()
            print("📬 Verifique a caixa de entrada dos destinatários:")
            for email in email_recipients:
                print(f"   • {email.strip()}")
            print()
            print("💡 Dica: Se não recebeu, verifique a pasta de SPAM/Lixo Eletrônico")
        else:
            print("❌ FALHA! Não foi possível enviar o email.")
            print()
            print("🔍 Possíveis causas:")
            print("   • Usuário ou senha incorretos")
            print("   • Servidor SMTP incorreto")
            print("   • Porta bloqueada por firewall")
            print("   • Conta requer autenticação multifator (MFA)")
            print()
            print("💡 Para Office 365 com MFA:")
            print("   1. Acesse: https://account.microsoft.com/security")
            print("   2. Vá em 'Opções de segurança avançadas'")
            print("   3. Crie uma 'Senha de aplicativo'")
            print("   4. Use essa senha no arquivo .env")
        print("=" * 70)
        
        return success
        
    except Exception as e:
        print()
        print("=" * 70)
        print(f"❌ ERRO DURANTE O TESTE: {e}")
        print("=" * 70)
        logger.error("Erro detalhado:", exc_info=True)
        return False


if __name__ == "__main__":
    try:
        success = test_email()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Teste interrompido pelo usuário")
        sys.exit(1)
