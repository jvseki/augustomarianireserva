from flask import Flask, jsonify, request
from flask_cors import CORS
from sheets import get_all_data, update_cell, get_cell, client, sheet
import os

app = Flask(__name__)
CORS(app)

try:
    print("📊 Planilhas detectadas:", client.list_spreadsheet_files())
except Exception as e:
    print("❌ Erro ao conectar Sheets:", e)

# ── Aba de lista de espera ──
SHEET_ID = "1uixhu6rN03HrMy-1ECf2U-Gr5bpKkbbiToiHGMOglk0"

def get_espera_sheet():
    """Retorna a aba 'Espera', criando-a se não existir."""
    spreadsheet = client.open_by_key(SHEET_ID)
    try:
        return spreadsheet.worksheet("Espera")
    except Exception:
        ws = spreadsheet.add_worksheet(title="Espera", rows=500, cols=6)
        ws.append_row(["id", "nome", "linha", "coluna", "equipamentos", "timestamp"])
        return ws


@app.route("/")
def home():
    return jsonify({"status": "API rodando 🚀"})


# ── Agenda principal ──
@app.route("/agenda", methods=["GET"])
def agenda():
    valores = sheet.get_all_values()
    return jsonify(valores)


@app.route("/editar", methods=["POST"])
def editar():
    data = request.json
    update_cell(data["linha"], data["coluna"], data["valor"])
    return jsonify({"status": "ok"})


# ════════════════════════════════════════
# LISTA DE ESPERA
# ════════════════════════════════════════

@app.route("/espera", methods=["GET"])
def listar_espera():
    """Retorna todas as entradas da lista de espera."""
    try:
        ws = get_espera_sheet()
        registros = ws.get_all_records()
        return jsonify(registros)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@app.route("/espera", methods=["POST"])
def entrar_espera():
    """Adiciona um professor na lista de espera."""
    try:
        data = request.json
        ws = get_espera_sheet()

        import time, random
        uid = f"{int(time.time())}-{random.randint(100,999)}"
        timestamp = time.strftime("%d/%m/%Y %H:%M")

        ws.append_row([
            uid,
            data["nome"],
            data["linha"],
            data["coluna"],
            data["equipamentos"],
            timestamp
        ])
        return jsonify({"status": "ok", "id": uid})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@app.route("/espera/<uid>", methods=["DELETE"])
def remover_espera(uid):
    """Remove um registro da lista de espera pelo id."""
    try:
        ws = get_espera_sheet()
        registros = ws.get_all_values()  # inclui cabeçalho
        for i, row in enumerate(registros):
            if row and row[0] == uid:
                ws.delete_rows(i + 1)
                return jsonify({"status": "ok"})
        return jsonify({"status": "nao_encontrado"}), 404
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@app.route("/promover", methods=["POST"])
def promover_espera():
    """
    Verifica se há alguém na espera para um slot que ficou livre
    e promove automaticamente o primeiro da fila.
    Chamado pelo frontend a cada carregarAgenda().
    """
    try:
        ws = get_espera_sheet()
        registros = ws.get_all_records()
        promovidos = []

        # Lê agenda atual
        agenda_vals = sheet.get_all_values()

        for reg in registros:
            linha  = int(reg["linha"])
            coluna = int(reg["coluna"])
            equip  = reg["equipamentos"]   # ex: "23 notebook prata"
            nome   = reg["nome"]
            uid    = reg["id"]

            # Valor atual da célula na planilha principal
            try:
                cel_atual = agenda_vals[linha - 1][coluna - 1]
            except IndexError:
                continue

            # Calcula quanto ainda cabe
            from sheets import sheet as sh
            # Reutiliza lógica: checa se o equip pedido ainda cabe
            # (verificação simples: se a célula voltou a ter espaço)
            cel_up = (cel_atual or "").strip().upper()

            # Célula livre → promove direto
            if cel_up == "" or cel_up == "LIVRE":
                novo_valor = f"{nome} | {equip}"
            elif "|" in cel_atual:
                # Tem outras reservas — concatena
                novo_valor = f"{cel_atual} § {nome} | {equip}"
            else:
                continue  # ainda ocupado, pula

            # Salva na planilha principal
            sheet.update_cell(linha, coluna, novo_valor)

            # Remove da lista de espera
            todos = ws.get_all_values()
            for i, row in enumerate(todos):
                if row and row[0] == uid:
                    ws.delete_rows(i + 1)
                    break

            promovidos.append({
                "nome": nome,
                "linha": linha,
                "coluna": coluna,
                "equipamentos": equip
            })

        return jsonify({"promovidos": promovidos})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# ── Rotas legadas ──
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
