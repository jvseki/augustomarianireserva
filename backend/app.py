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
            int(data["linha"]),
            int(data["coluna"]),
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


def calcular_uso_celula(cel_valor):
    """Retorna {tablet, prata, preto} com total em uso na célula."""
    uso = {"tablet": 0, "prata": 0, "preto": 0}
    if not cel_valor or not "|" in cel_valor:
        return uso
    import re
    for bloco in cel_valor.split("§"):
        partes = bloco.split("|")
        if len(partes) < 2:
            continue
        for seg in partes[1].split("+"):
            m = re.search(r"(\d+)\s*(tablet|notebook prata|notebook preto)", seg.strip(), re.IGNORECASE)
            if m:
                qtd = int(m.group(1))
                tipo = m.group(2).lower()
                if tipo == "tablet":           uso["tablet"] += qtd
                elif tipo == "notebook prata": uso["prata"]  += qtd
                elif tipo == "notebook preto": uso["preto"]  += qtd
    return uso

def equip_str_para_dict(equip_str):
    """Converte '23 notebook prata + 5 notebook preto' em {tablet:0, prata:23, preto:5}."""
    import re
    res = {"tablet": 0, "prata": 0, "preto": 0}
    for seg in equip_str.split("+"):
        m = re.search(r"(\d+)\s*(tablet|notebook prata|notebook preto)", seg.strip(), re.IGNORECASE)
        if m:
            qtd = int(m.group(1))
            tipo = m.group(2).lower()
            if tipo == "tablet":           res["tablet"] += qtd
            elif tipo == "notebook prata": res["prata"]  += qtd
            elif tipo == "notebook preto": res["preto"]  += qtd
    return res

ESTOQUE_TOTAL = {"tablet": 12, "prata": 23, "preto": 11}

@app.route("/promover", methods=["POST"])
def promover_espera():
    """
    Verifica se há espaço suficiente para cada item da lista de espera
    considerando APENAS os equipamentos pedidos — não exige slot totalmente livre.
    Ex: Marcos quer 23 pratas → verifica se sobrou 23 pratas, independente
    de outros equipamentos ainda ocupados pelo Luís.
    """
    try:
        ws = get_espera_sheet()
        registros = ws.get_all_records()
        promovidos = []

        agenda_vals = sheet.get_all_values()

        # Processa cada item da espera em ordem (FIFO)
        for reg in registros:
            linha  = int(reg["linha"])
            coluna = int(reg["coluna"])
            equip  = reg["equipamentos"]
            nome   = reg.get("nome", "")
            uid    = reg.get("id", "")

            try:
                cel_atual = agenda_vals[linha - 1][coluna - 1]
            except IndexError:
                continue

            cel_up = (cel_atual or "").strip().upper()
            if cel_up == "BLOQUEADO":
                continue  # slot bloqueado manualmente, pula

            # Calcula quanto está em uso neste slot
            uso = calcular_uso_celula(cel_atual)

            # Calcula quanto o professor da espera precisa
            pedido = equip_str_para_dict(equip)

            # Verifica se cabe (por tipo de equipamento)
            cabe = all(
                uso.get(tipo, 0) + pedido.get(tipo, 0) <= ESTOQUE_TOTAL[tipo]
                for tipo in pedido
                if pedido[tipo] > 0
            )

            if not cabe:
                continue  # ainda não tem espaço suficiente

            # Cabe! Promove
            if not cel_atual.strip() or cel_up == "":
                novo_valor = f"{nome} | {equip}"
            else:
                novo_valor = f"{cel_atual} § {nome} | {equip}"

            sheet.update_cell(linha, coluna, novo_valor)
            # Atualiza cache local para os próximos da fila
            while len(agenda_vals) < linha:
                agenda_vals.append([])
            while len(agenda_vals[linha-1]) < coluna:
                agenda_vals[linha-1].append("")
            agenda_vals[linha-1][coluna-1] = novo_valor

            # Remove da espera
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
