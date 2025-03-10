from flask import Flask, request, jsonify, send_from_directory
import asyncio
import time
import uuid
import os
import requests
from playwright.async_api import async_playwright
import matplotlib.pyplot as plt

app = Flask(__name__)

IMAGE_FOLDER = "images"
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# Função para gerar imagem do extrato
async def generate_image(user_id, lancamentos):
    try:
        if not lancamentos:
            return None, "Nenhum lançamento recebido"

        total_gasto = 0
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

        return filename, total_gasto

    except Exception as e:
        return None, f"Erro ao gerar imagem: {str(e)}"

# Função para gerar gráfico em pizza
async def generate_pizza_chart(user_id, lancamentos):
    try:
        if not lancamentos:
            return None, "Nenhum lançamento recebido"

        categorias = {}
        total_gasto = 0

        for item in lancamentos:
            try:
                valor_formatado = item["value"].replace("R$", "").replace(",", ".").strip()
                valor_float = float(valor_formatado)
                total_gasto += valor_float

                if item["category"] in categorias:
                    categorias[item["category"]] += valor_float
                else:
                    categorias[item["category"]] = valor_float

            except Exception as e:
                return None, f"Erro ao processar lançamento: {item}, Erro: {str(e)}"

        labels = list(categorias.keys())
        values = list(categorias.values())

        plt.figure(figsize=(6, 6))
        plt.pie(values, labels=labels, autopct="%1.1f%%", startangle=140, colors=["#008DC2", "#00A3E0", "#50C1E9", "#87D9F7"])
        plt.title("Distribuição de Gastos")

        filename = f"{IMAGE_FOLDER}/grafico_pizza_{user_id}_{int(time.time())}_{uuid.uuid4().hex[:6]}.png"
        plt.savefig(filename, bbox_inches="tight")
        plt.close()

        return filename, total_gasto

    except Exception as e:
        return None, f"Erro ao gerar gráfico: {str(e)}"

def send_whatsapp_image(user_id, filename, total_gasto, tipo):
    instance_id = "instance108935"
    api_token = "kpqhxmm0ojg2ufqk"
    image_url = f"https://flask-server-production-e1cb.up.railway.app/images/{os.path.basename(filename)}"
    ultramsg_url = f"https://api.ultramsg.com/{instance_id}/messages/image?token={api_token}"

    caption = f"📊 Segue seu {tipo} com o total de gastos de R$ {total_gasto:.2f}"

    payload = {
        "to": f"{user_id}@c.us",
        "image": image_url,
        "caption": caption
    }

    response = requests.post(ultramsg_url, json=payload)

    return response.json() if response.status_code == 200 else {"error": "Falha ao enviar imagem", "details": response.text}

@app.route('/images/<filename>')
def get_image(filename):
    return send_from_directory(IMAGE_FOLDER, filename)

@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    user_id = data.get("user_id")
    lancamentos = data.get("lancamentos", [])

    if not user_id or not lancamentos:
        return jsonify({"error": "Dados inválidos"}), 400

    filename, total_gasto = asyncio.run(generate_image(user_id, lancamentos))
    if filename is None:
        return jsonify({"error": total_gasto}), 500

    whatsapp_response = send_whatsapp_image(user_id, filename, total_gasto, "extrato")
    return jsonify({"message": "Imagem gerada e enviada!", "filename": filename, "whatsapp_response": whatsapp_response})

@app.route('/generate_pizza', methods=['POST'])
def generate_pizza():
    data = request.get_json()
    user_id = data.get("user_id")
    lancamentos = data.get("lancamentos", [])

    if not user_id or not lancamentos:
        return jsonify({"error": "Dados inválidos"}), 400

    filename, total_gasto = asyncio.run(generate_pizza_chart(user_id, lancamentos))
    if filename is None:
        return jsonify({"error": total_gasto}), 500

    whatsapp_response = send_whatsapp_image(user_id, filename, total_gasto, "gráfico de pizza")
    return jsonify({"message": "Imagem gerada e enviada!", "filename": filename, "whatsapp_response": whatsapp_response})

@app.route('/')
def home():
    return "Servidor Flask rodando no Railway!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
