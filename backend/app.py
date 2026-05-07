import os
from flask import Flask, jsonify, request
from flask_cors import CORS

from sheets import get_all_data, update_cell, get_cell

app = Flask(__name__)
CORS(app)

# 🔥 PORTA DO RENDER
port = int(os.environ.get("PORT", 5000))


@app.route("/")
def home():
    return jsonify({"status": "API rodando 🚀"})


@app.route("/dados")
def dados():
    return jsonify(get_all_data())


@app.route("/get")
def get():
    row = int(request.args.get("row"))
    col = int(request.args.get("col"))
    return jsonify({"value": get_cell(row, col)})


@app.route("/update", methods=["POST"])
def update():
    data = request.json
    update_cell(data["row"], data["col"], data["value"])
    return jsonify({"status": "ok"})


# 🔥 IMPORTANTE: 0.0.0.0 + PORT
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port, debug=True)