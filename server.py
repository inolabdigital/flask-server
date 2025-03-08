from flask import Flask, request, jsonify, send_from_directory
import asyncio
import time
import uuid
import os
import requests
from playwright.async_api import async_playwright

app = Flask(__name__)

# Criar diretório para salvar imagens, se não existir
IMAGE_FOLDER = "images"
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# Função para gerar a imagem
async def generate_image(user_id, lancamentos):
    total_gasto = sum(float(item["value"]) for item in lancamentos)

    # Criar o HTML com os lançamentos (sem título e sem total gasto)
    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Extrato Financeiro</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');
            
            body {{ font-family: 'Montserrat', sans-serif; background-color: #fff; color: #333; text-align: center; padding: 20px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #008DC2; color: white; }}
        </style>
    </head>
    <body>
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

    filename = f"{IMAGE_FOLDER}/extrato_{user_id}_{int(time.time())}_{uuid.uuid4().hex[:6]}.png"

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        await page.set_viewport_size({"width": 750, "height": 1000})
        await page.set_content(html_content)

        await page.screenshot(path=filename, full_page=False, omit_background=True)

        await browser.close()
        print(f"Imagem gerada: {filename}")

    return filename, total_gasto  # Retornando também o total gasto

# Função para enviar a imagem via Ultramsg
def send_whatsapp_image(user_id, filename, total_gasto):
    instance_id = "instance108935"  # ID da instância no Ultramsg
    api_token = "kpqhxmm0ojg2ufqk"  # Token do Ultramsg

    # Criar URL pública para a imagem
    image_url = f"https://flask-server-production-e1cb.up.railway.app/images/{os.path.basename(filename)}"

    ultramsg_url = f"https://api.ultramsg.com/{instance_id}/messages/image?token={api_token}"

    payload = {
        "to": f"{user_id}@c.us",
        "image": image_url,
        "caption": f"📊 Segue seu extrato, total de gastos R$ {total_gasto:.2f}"
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
        return jsonify({"error": "user_id e lançamentos são obrigatórios"}), 400

    filename, total_gasto = asyncio.run(generate_image(user_id, lancamentos))

    # Enviar a imagem para o WhatsApp com o total gasto
    whatsapp_response = send_whatsapp_image(user_id, filename, total_gasto)

    return jsonify({"message": "Imagem gerada e enviada com sucesso!", "filename": filename, "whatsapp_response": whatsapp_response})

# Rota padrão para testar se o servidor está ativo
@app.route('/')
def home():
    return "Servidor Flask rodando no Railway!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
