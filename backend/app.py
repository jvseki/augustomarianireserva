from flask import Flask, jsonify, request
from flask_cors import CORS

from sheets import get_all_data, update_cell, get_cell

app = Flask(__name__)
CORS(app)

# 🔥 HOME
@app.route("/")
def home():
    return "API rodando 🚀"


# 📊 PEGAR DADOS
@app.route("/agenda", methods=["GET"])
def agenda():
    data = get_all_data()
    return jsonify(data)


# ✏️ EDITAR CÉLULA
@app.route("/editar", methods=["POST"])
def editar():
    data = request.json

    linha = data["linha"]
    coluna = data["coluna"]
    valor = data["valor"]

    try:
        update_cell(linha, coluna, valor)
        return jsonify({"msg": "Atualizado com sucesso"})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# 🧪 RESERVA SIMPLES (OPCIONAL)
@app.route("/reservar", methods=["POST"])
def reservar():
    data = request.json

    linha = data["linha"]
    coluna = data["coluna"]
    nome = data["nome"]

    atual = get_cell(linha, coluna)

    if atual != "LIVRE":
        return jsonify({"erro": "Indisponível"}), 400

    update_cell(linha, coluna, nome)

    return jsonify({"msg": "Reservado"})


if __name__ == "__main__":
    app.run(debug=True)