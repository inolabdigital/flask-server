from flask import Flask, request, jsonify
import asyncio
import time
import uuid
import requests
from playwright.async_api import async_playwright

app = Flask(__name__)

# Função para gerar a imagem
async def generate_image(user_id):
    html_content = """
    <!DOCTYPE html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Extrato Financeiro</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: Arial, sans-serif; background-color: #fff; color: #333; width: 100vw; height: 100vh; display: flex; justify-content: center; align-items: center; overflow: hidden; }
            .container { width: 100%; height: 100%; display: flex; flex-direction: column; justify-content: space-between; padding: 10px; }
            h1 { font-size: 24px; font-weight: bold; color: #1d4ed8; text-align: center; }
            .summary { font-size: 18px; font-weight: bold; color: #2563eb; text-align: center; margin-bottom: 5px; }
            .table-container { width: 100%; flex-grow: 1; }
            table { width: 100%; border-collapse: collapse; margin-top: 5px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; font-size: 14px; }
            th { background-color: #2563eb; color: white; }
            tr:nth-child(even) { background-color: #f8f9fa; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📜 Extrato Financeiro</h1>
            <p class="summary">Total Gasto: R$ 1234.56</p>
            <div class="table-container">
                <table>
                    <tr>
                        <th>Data</th>
                        <th>Descrição</th>
                        <th>Categoria</th>
                        <th>Valor (R$)</th>
                    </tr>
                    <tr><td>2025-03-04</td><td>Água</td><td>Moradia</td><td>20</td></tr>
                    <tr><td>2025-03-05</td><td>Aluguel</td><td>Moradia</td><td>1200</td></tr>
                </table>
            </div>
        </div>
    </body>
    </html>
    """

    filename = f"extrato_{user_id}_{int(time.time())}_{uuid.uuid4().hex[:6]}.png"

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        await page.set_viewport_size({"width": 750, "height": 1000})
        await page.set_content(html_content)

        await page.screenshot(path=filename, full_page=False, omit_background=True)

        await browser.close()
        print(f"Imagem gerada: {filename}")

    return filename

# Função para enviar a imagem via Ultramsg
def send_whatsapp_image(user_id, filename):
    ultramsg_url = "https://api.ultramsg.com/instance108935/messages/image"
    api_token = "9ufrew1imscgvwja"

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
    data = request.get_json()
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id é obrigatório"}), 400

    filename = asyncio.run(generate_image(user_id))

    # Enviar a imagem para o WhatsApp
    whatsapp_response = send_whatsapp_image(user_id, filename)

    return jsonify({"message": "Imagem gerada e enviada com sucesso!", "filename": filename, "whatsapp_response": whatsapp_response})

# Rota padrão para testar se o servidor está ativo
@app.route('/')
def home():
    return "Servidor Flask rodando no Railway!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
