from flask import Flask, request, jsonify, send_from_directory
import asyncio
import time
import uuid
import os
import requests
from playwright.async_api import async_playwright

app = Flask(__name__)

IMAGE_FOLDER = "images"
os.makedirs(IMAGE_FOLDER, exist_ok=True)

async def generate_image(user_id, lancamentos):
    try:
        if not lancamentos:
            return None, "Nenhum lançamento recebido"

        total_gasto = 0

        # Criar a tabela de lançamentos
        lancamentos_html = ""
        for item in lancamentos:
            try:
                valor_formatado = item["value"].replace("R$", "").replace(",", ".").strip()
                valor_float = float(valor_formatado)
                total_gasto += valor_float
                lancamentos_html += f"<tr><td>{item['date']}</td><td>{item['description']}</td><td>{item['category']}</td><td>R$ {valor_float:.2f}</td></tr>"
            except Exception as e:
                return None, f"Erro ao processar lançamento: {item}, Erro: {str(e)}"

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
                {lancamentos_html}
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

        return filename, total_gasto

    except Exception as e:
        return None, f"Erro geral ao gerar imagem: {str(e)}"

def send_whatsapp_image(user_id, filename, total_gasto):
    instance_id = "instance108935"
    api_token = "kpqhxmm0ojg2ufqk"

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

@app.route('/images/<filename>')
def get_image(filename):
    return send_from_directory(IMAGE_FOLDER, filename)

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Nenhum dado foi enviado"}), 400

        user_id = data.get("user_id")
        lancamentos = data.get("lancamentos", [])

        if not user_id:
            return jsonify({"error": "user_id é obrigatório"}), 400

        if not isinstance(lancamentos, list) or not lancamentos:
            return jsonify({"error": "A lista de lançamentos está vazia ou inválida"}), 400

        filename, total_gasto = asyncio.run(generate_image(user_id, lancamentos))

        if filename is None:
            return jsonify({"error": total_gasto}), 500

        whatsapp_response = send_whatsapp_image(user_id, filename, total_gasto)

        return jsonify({"message": "Imagem gerada e enviada com sucesso!", "filename": filename, "whatsapp_response": whatsapp_response})

    except Exception as e:
        return jsonify({"error": "Erro interno no servidor", "details": str(e)}), 500

@app.route('/')
def home():
    return "Servidor Flask rodando no Railway!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
