import asyncio
from supabase import create_client, Client

# Substitua pelas suas credenciais do Supabase
SUPABASE_URL = 'https://qdinyobsivopfxabvrvq.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFkaW55b2JzaXZvcGZ4YWJ2cnZxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDA4NjE2OTksImV4cCI6MjA1NjQzNzY5OX0.geYKcbYBadGgYOpSa0z9J2_J05koCzpXhpY82Uu2bPM'

# Inicialize o cliente Supabase
client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Função para inserir dados na tabela
async def insert_data(description):
    try:
        response = await client.table('items').insert({
            'description': description
        }).execute()
        print("Dados inseridos com sucesso:", response)
    except Exception as e:
        print("Erro ao inserir dados:", e)

# Função para se inscrever nas alterações da tabela em tempo real
async def listen_to_changes():
    # Conecte-se ao canal Realtime
    channel = client.realtime.channel('public:items')  # 'public' é o schema, 'items' é a tabela

    # Inscreva-se para receber atualizações
    channel.on('INSERT', lambda payload: print("Novo item inserido:", payload))
    channel.on('UPDATE', lambda payload: print("Item atualizado:", payload))
    channel.on('DELETE', lambda payload: print("Item deletado:", payload))

    # Conecte ao canal
    await channel.subscribe()

    print("Escutando alterações na tabela 'items'...")

# Função principal para testar a inserção e o Realtime
async def main():
    # Inicie a escuta das alterações
    await listen_to_changes()

    # Insira um novo item para testar
    await insert_data("Item de teste para Realtime")

    # Mantenha o script rodando para continuar escutando
    while True:
        await asyncio.sleep(1)

# Execute o script
if __name__ == "__main__":
    asyncio.run(main())