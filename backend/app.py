from flask import Flask, jsonify, request
from flask_cors import CORS
from sheets import get_all_data, get_cell, update_cell
from config import ADMIN_PASSWORD
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


@app.route("/")
def home():
    return "API rodando 🚀"


@app.route("/agenda", methods=["GET"])
def agenda():
    data = get_all_data()
    return jsonify(data)


@app.route("/reservar", methods=["POST"])
def reservar():
    data = request.json
    linha = data["linha"]
    coluna = data["coluna"]
    nome = data["nome"]

    valor_atual = get_cell(linha, coluna)

    if valor_atual != "LIVRE":
        return jsonify({"erro": "Horário indisponível"}), 400

    update_cell(linha, coluna, nome)

    return jsonify({"msg": "Reservado com sucesso"})


# 🔐 edição protegida por senha
@app.route("/editar", methods=["POST"])
def editar():
    data = request.json
    linha = data["linha"]
    coluna = data["coluna"]
    valor = data["valor"]
    senha = data.get("senha")

    if senha != ADMIN_PASSWORD:
        return jsonify({"erro": "Senha incorreta"}), 403

    update_cell(linha, coluna, valor)

    return jsonify({"msg": "Atualizado com sucesso"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)