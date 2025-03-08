from flask import Flask, request, jsonify
import asyncio
import time
import uuid
import requests
from playwright.async_api import async_playwright

app = Flask(__name__)

# User ID fixo para teste
USER_ID = "5511982252058"

# Lançamentos de exemplo (simulando os 10 mais recentes)
LANCAMENTOS = [
    {"date": "2025-03-25", "description": "Uber", "category": "Transporte", "value": 80},
    {"date": "2025-03-24", "description": "Supermercado", "category": "Alimentação", "value": 250},
    {"date": "2025-03-23", "description": "Cinema", "category": "Lazer", "value": 45},
    {"date": "2025-03-22", "description": "Aluguel", "category": "Moradia", "value": 1200},
    {"date": "2025-03-21", "description": "Internet", "category": "Utilidades", "value": 100},
    {"date": "2025-03-20", "description": "Academia", "category": "Saúde", "value": 90},
    {"date": "2025-03-19", "description": "Farmácia", "category": "Saúde", "value": 150},
    {"date": "2025-03-18", "description": "Restaurante", "category": "Alimentação", "value": 180},
    {"date": "2025-03-17", "description": "Táxi", "category": "Transporte", "value": 60},
    {"date": "2025-03-16", "description": "Energia", "category": "Moradia", "value": 200}
]

# Função para gerar a imagem
async def generate_image(user_id, lancamentos):
    total_gasto = sum(float(item["value"]) for item in lancamentos)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Extrato Financeiro</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #fff; color: #333; text-align: center; padding: 20px; }}
            h1 {{ color: #1d4ed8; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #2563eb; color: white; }}
        </style>
    </head>
    <body>
        <h1>📜 Extrato Financeiro</h1>
        <p><strong>Total Gasto: R$ {total_gasto:.2f}</strong></p>
        <table>
            <tr>
                <th>Data</th>
                <th>Descrição</th>
                <th>Categoria</th>
                <th>Valor (R$)</th>
            </tr>
            {''.join(f"<tr><td>{item['date']}</td><td>{item['description']}</td><td>{item['category']}</td><td>{item['value']}</td></tr>" for item in lancamentos)}
        </table>
    </body>
    </html>
    """

    filename = f"extrato_{user_id}_{int(time.time())}_{uuid.uuid4().hex[:6]}.png"

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        await page.set_viewport_size({"width": 750, "height": 1000})
        await page.set_content(html_content)

        await page.screenshot(path=filename, full_page=False)

        await browser.close()
        print(f"Imagem gerada: {filename}")

    return filename

# Função para enviar a imagem via Ultramsg
def send_whatsapp_image(user_id, filename):
    ultramsg_url = "https://api.ultramsg.com/instance108935/messages/image"
    api_token = "kpqhxmm0ojg2ufqk"

    payload = {
        "token": api_token,
        "to": f"{user_id}@c.us",
        "image": f"https://flask-server-production-e1cb.up.railway.app/images/{filename}",
        "caption": "📊 Seu extrato financeiro gerado automaticamente."
    }

    response = requests.post(ultramsg_url, json=payload)

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Falha ao enviar imagem", "details": response.text}

# Rota principal para gerar e enviar a imagem
@app.route('/generate', methods=['POST'])
def generate():
    filename = asyncio.run(generate_image(USER_ID, LANCAMENTOS))

    # Enviar a imagem para o WhatsApp
    whatsapp_response = send_whatsapp_image(USER_ID, filename)

    return jsonify({"message": "Imagem gerada e enviada com sucesso!", "filename": filename, "whatsapp_response": whatsapp_response})

# Rota padrão para testar se o servidor está ativo
@app.route('/')
def home():
    return "Servidor Flask rodando no Railway!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
