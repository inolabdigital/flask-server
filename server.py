from flask import Flask, request, jsonify, send_from_directory
import asyncio
import time
import uuid
import os
import requests
from playwright.async_api import async_playwright

app = Flask(__name__)

# Criar diretório para salvar imagens se não existir
IMAGE_FOLDER = "images"
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# Função para gerar a imagem com os lançamentos recebidos
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
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: Arial, sans-serif; background-color: #fff; color: #333; width: 100vw; height: 100vh; display: flex; justify-content: center; align-items: center; overflow: hidden; }}
            .container {{ width: 100%; height: 100%; display: flex; flex-direction: column; justify-content: space-between; padding: 10px; }}
            h1 {{ font-size: 24px; font-weight: bold; color: #1d4ed8; text-align: center; }}
            .summary {{ font-size: 18px; font-weight: bold; color: #2563eb; text-align: center; margin-bottom: 5px; }}
            .table-container {{ width: 100%; flex-grow: 1; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 5px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; font-size: 14px; }}
            th {{ background-color: #2563eb; color: white; }}
            tr:nth-child(even) {{ background-color: #f8f9fa; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📜 Extrato Financeiro</h1>
            <p class="summary">Total Gasto: R$ {total_gasto:.2f}</p>
            <div class="table-container">
                <table>
                    <tr>
                        <th>Data</th>
                        <th>Descrição</th>
                        <th>Categoria</th>
                        <th>Valor (R$)</th>
                    </tr>
                    {''.join(f"<tr><td>{item['date']}</td><td>{item['description']}</td><td>{item['category']}</td><td>{item['value']}</td></tr>" for item in lancamentos)}
                </table>
            </div>
        </div>
    </body>
    </html>
    """

    filename = f"{IMAGE_FOLDER}/extrato_{user_id}_{int(time.time())}_{uuid.uuid4().hex[:6]}.png"

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
    instance_id = "instance108935"
    api_token = "kpqhxmm0ojg2ufqk"

    image_url = f"https://flask-server-production-e1cb.up.railway.app/images/{os.path.basename(filename)}"

    ultramsg_url = f"https://api.ultramsg.com/{instance_id}/messages/image?token={api_token}"

    payload = {
        "to": f"{user_id}@c.us",
        "image": image_url,
        "caption": "📊 Seu extrato financeiro gerado automaticamente."
    }

    response = requests.post(ultramsg_url, json=payload)

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Falha ao enviar imagem", "details": response.text}

# Rota para servir imagens geradas
@app.route('/images/<filename>')
def get_image(filename):
    return send_from_directory(IMAGE_FOLDER, filename)

# Rota principal para gerar e enviar a imagem
@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    
    user_id = data.get("user_id")
    lancamentos = data.get("lancamentos", [])

    if not user_id or not lancamentos:
        return jsonify({"error": "user_id e lancamentos são obrigatórios"}), 400

    filename = asyncio.run(generate_image(user_id, lancamentos))

    whatsapp_response = send_whatsapp_image(user_id, filename)

    return jsonify({"message": "Imagem gerada e enviada com sucesso!", "filename": filename, "whatsapp_response": whatsapp_response})

# Rota padrão para testar se o servidor está ativo
@app.route('/')
def home():
    return "Servidor Flask rodando no Railway!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
