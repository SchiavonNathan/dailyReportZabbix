"""
Script para testar manualmente os jobs do agendador.
"""
from auto_scheduler import daily_job, weekly_job, monthly_job

print("=" * 80)
print("TESTE MANUAL DOS JOBS DO AGENDADOR")
print("=" * 80)
print("\nEscolha qual job testar:")
print("1 - Job Diário")
print("2 - Job Semanal")
print("3 - Job Mensal")
print("4 - Todos")
print()

choice = input("Digite sua escolha (1-4): ")

if choice == "1":
    print("\n🔄 Executando job diário...\n")
    daily_job()
elif choice == "2":
    print("\n🔄 Executando job semanal...\n")
    weekly_job()
elif choice == "3":
    print("\n🔄 Executando job mensal...\n")
    monthly_job()
elif choice == "4":
    print("\n🔄 Executando todos os jobs...\n")
    daily_job()
    print("\n")
    weekly_job()
    print("\n")
    monthly_job()
else:
    print("\n❌ Opção inválida!")

print("\n✅ Teste concluído!")
