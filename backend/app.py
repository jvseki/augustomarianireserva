from flask import Flask, jsonify, request
from flask_cors import CORS
from sheets import get_all_data, update_cell, get_cell
import os

app = Flask(__name__)
CORS(app)

try:
    from sheets import client
    print("📊 Planilhas detectadas:", client.list_spreadsheet_files())
except Exception as e:
    print("❌ Erro ao conectar Sheets:", e)


@app.route("/")
def home():
    return jsonify({"status": "API rodando 🚀"})


# Retorna os dados como array de arrays (linha 0 = cabeçalho)
@app.route("/agenda", methods=["GET"])
def agenda():
    from sheets import sheet
    valores = sheet.get_all_values()  # retorna lista de listas, perfeito pro frontend
    return jsonify(valores)


# Edita uma célula
@app.route("/editar", methods=["POST"])
def editar():
    data = request.json
    linha = data["linha"]
    coluna = data["coluna"]
    valor = data["valor"]
    update_cell(linha, coluna, valor)
    return jsonify({"status": "ok"})


# Rotas antigas mantidas por compatibilidade
@app.route("/dados", methods=["GET"])
def dados():
    return jsonify(get_all_data())


@app.route("/atualizar", methods=["POST"])
def atualizar():
    data = request.json
    update_cell(data["row"], data["col"], data["value"])
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
