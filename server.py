from flask import Flask, request, jsonify, send_from_directory
import asyncio
import time
import uuid
import os
import requests
import matplotlib.pyplot as plt

app = Flask(__name__)

IMAGE_FOLDER = "images"
os.makedirs(IMAGE_FOLDER, exist_ok=True)

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

        # Cores aleatórias para cada categoria, tornando o gráfico mais visualmente agradável
        colors = plt.cm.get_cmap("tab10", len(labels)).colors

        plt.figure(figsize=(6, 6))
        wedges, texts, autotexts = plt.pie(values, labels=None, autopct=None, startangle=140, colors=colors)

        # Ajusta os textos da legenda e exibe os percentuais ao lado esquerdo das categorias
        legend_labels = [f"{label} - {value / sum(values) * 100:.1f}%" for label, value in zip(labels, values)]
        plt.legend(wedges, legend_labels, title="Categorias", loc="lower center", bbox_to_anchor=(0.5, -0.1), ncol=2, frameon=False, fontsize=10)

        # Salvar imagem
        filename = f"{IMAGE_FOLDER}/grafico_pizza_{user_id}_{int(time.time())}_{uuid.uuid4().hex[:6]}.png"
        plt.savefig(filename, bbox_inches="tight")
        plt.close()

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
        "caption": f"📊 Segue seu gráfico com o total de gastos de R$ {total_gasto:.2f}"
    }

    response = requests.post(ultramsg_url, json=payload)

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Falha ao enviar imagem", "details": response.text}

@app.route('/images/<filename>')
def get_image(filename):
    return send_from_directory(IMAGE_FOLDER, filename)

@app.route('/generate_pizza', methods=['POST'])
def generate_pizza():
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

        filename, total_gasto = asyncio.run(generate_pizza_chart(user_id, lancamentos))

        if filename is None:
            return jsonify({"error": total_gasto}), 500

        whatsapp_response = send_whatsapp_image(user_id, filename, total_gasto)

        return jsonify({"message": "Imagem gerada e enviada com sucesso!", "filename": filename, "whatsapp_response": whatsapp_response})

    except Exception as e:
        return jsonify({"error": "Erro interno no servidor", "details": str(e)}), 500

@app.route('/')
def home():
    return "Servidor Flask (Gráfico de Pizza) rodando no Railway!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
