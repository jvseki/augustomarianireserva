from flask import Flask, jsonify, request
from flask_cors import CORS

from sheets import get_all_data, update_cell, get_cell

app = Flask(__name__)
CORS(app)

# =========================
# 🔥 TESTE DE CONEXÃO
# =========================
try:
    from sheets import client
    print("📊 Planilhas detectadas:", client.list_spreadsheet_files())
except Exception as e:
    print("❌ Erro ao conectar Sheets:", e)


# =========================
# 🌐 ROTAS
# =========================

@app.route("/")
def home():
    return jsonify({"status": "API rodando 🚀"})


@app.route("/dados", methods=["GET"])
def dados():
    return jsonify(get_all_data())


@app.route("/celula", methods=["GET"])
def celula():
    row = int(request.args.get("row"))
    col = int(request.args.get("col"))

    value = get_cell(row, col)
    return jsonify({"value": value})


@app.route("/atualizar", methods=["POST"])
def atualizar():
    data = request.json

    row = data["row"]
    col = data["col"]
    value = data["value"]

    update_cell(row, col, value)

    return jsonify({"status": "ok"})


# =========================
# 🚀 RENDER FIX (PORTA OBRIGATÓRIA)
# =========================

if __name__ == "__main__":
    import os
port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)