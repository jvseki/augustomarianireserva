from flask import Flask, jsonify, request
from flask_cors import CORS
from sheets import get_all_data, update_cell, client, sheet
import re

app = Flask(__name__)
CORS(app)

try:
    print("📊 Planilhas detectadas:", client.list_spreadsheet_files())
except Exception as e:
    print("❌ Erro ao conectar Sheets:", e)

# ── Aba de lista de espera ──
SHEET_ID = "1uixhu6rN03HrMy-1ECf2U-Gr5bpKkbbiToiHGMOglk0"

def get_espera_sheet():
    """Retorna a aba 'Espera', criando-a se não existir.
    Garante também que o cabeçalho tenha a coluna 'email' (migração de abas antigas).
    """
    spreadsheet = client.open_by_key(SHEET_ID)
    try:
        ws = spreadsheet.worksheet("Espera")
        header = ws.row_values(1)
        if header and "email" not in header:
            ws.insert_cols([[""]] * 1, 3)
            ws.update_cell(1, 3, "email")
        return ws
    except Exception:
        ws = spreadsheet.add_worksheet(title="Espera", rows=500, cols=7)
        ws.append_row(["id", "nome", "email", "linha", "coluna", "equipamentos", "timestamp"])
        return ws


def formatar_reserva_agenda(nome, email, equip):
    """Mesmo formato das reservas normais — permite editar no app pelo e-mail."""
    nome = (nome or "").strip()
    email = (email or "").strip().lower()
    tag = f" [{email}]" if email and "@" in email else ""
    return f"{nome}{tag} | {equip}"


@app.route("/")
def home():
    return jsonify({"status": "API rodando 🚀"})


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
    try:
        ws = get_espera_sheet()
        return jsonify(ws.get_all_records())
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@app.route("/espera", methods=["POST"])
def entrar_espera():
    try:
        data = request.json or {}
        nome = (data.get("nome") or "").strip()
        email = (data.get("email") or "").strip().lower()
        if not nome:
            return jsonify({"erro": "Nome obrigatório"}), 400
        if not email or "@" not in email:
            return jsonify({
                "erro": "É necessário estar logado com Google para entrar na fila (e-mail obrigatório)."
            }), 400

        ws = get_espera_sheet()
        import time
        import random

        uid = f"{int(time.time())}-{random.randint(100, 999)}"
        timestamp = time.strftime("%d/%m/%Y %H:%M")

        ws.append_row([
            uid,
            nome,
            email,
            int(data["linha"]),
            int(data["coluna"]),
            data["equipamentos"],
            timestamp,
        ])
        return jsonify({"status": "ok", "id": uid})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@app.route("/espera/<uid>", methods=["DELETE"])
def remover_espera(uid):
    try:
        ws = get_espera_sheet()
        registros = ws.get_all_values()
        for i, row in enumerate(registros):
            if row and row[0] == uid:
                ws.delete_rows(i + 1)
                return jsonify({"status": "ok"})
        return jsonify({"status": "nao_encontrado"}), 404
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


RE_EQUIP = re.compile(
    r"(\d+)\s*(tv remota|notebook prata|notebook preto|tablet)",
    re.IGNORECASE,
)


def _parse_equip_segment(seg):
    uso = {"tablet": 0, "prata": 0, "preto": 0, "tvremota": 0}
    for m in RE_EQUIP.finditer(seg):
        qtd = int(m.group(1))
        tipo = m.group(2).lower()
        if tipo == "tablet":
            uso["tablet"] += qtd
        elif tipo == "notebook prata":
            uso["prata"] += qtd
        elif tipo == "notebook preto":
            uso["preto"] += qtd
        elif tipo == "tv remota":
            uso["tvremota"] += qtd
    return uso


def calcular_uso_celula(cel_valor):
    uso = {"tablet": 0, "prata": 0, "preto": 0, "tvremota": 0}
    if not cel_valor or "|" not in cel_valor:
        return uso
    for bloco in cel_valor.split("§"):
        partes = bloco.split("|")
        if len(partes) < 2:
            continue
        for seg in partes[1].split("+"):
            parsed = _parse_equip_segment(seg.strip())
            for k in uso:
                uso[k] += parsed[k]
    return uso


def equip_str_para_dict(equip_str):
    res = {"tablet": 0, "prata": 0, "preto": 0, "tvremota": 0}
    for seg in equip_str.split("+"):
        parsed = _parse_equip_segment(seg.strip())
        for k in res:
            res[k] += parsed[k]
    return res


ESTOQUE_TOTAL = {"tablet": 12, "prata": 23, "preto": 11, "tvremota": 1}


@app.route("/promover", methods=["POST"])
def promover_espera():
    try:
        ws = get_espera_sheet()
        todas_linhas = ws.get_all_values()
        if not todas_linhas:
            return jsonify({"promovidos": []})

        header = todas_linhas[0]

        def col_idx(nome_col):
            try:
                return header.index(nome_col)
            except ValueError:
                return None

        idx_id = col_idx("id")
        idx_nome = col_idx("nome")
        idx_email = col_idx("email")
        idx_linha = col_idx("linha")
        idx_col = col_idx("coluna")
        idx_equip = col_idx("equipamentos")

        if None in (idx_id, idx_nome, idx_linha, idx_col, idx_equip):
            return jsonify({"erro": "Cabeçalho da aba Espera inválido", "header": header}), 500

        registros_raw = todas_linhas[1:]
        promovidos = []
        agenda_vals = sheet.get_all_values()

        for reg_row in registros_raw:
            if not reg_row or not reg_row[idx_id]:
                continue
            try:
                uid = reg_row[idx_id]
                nome = reg_row[idx_nome]
                email = ""
                if idx_email is not None and idx_email < len(reg_row):
                    email = (reg_row[idx_email] or "").strip().lower()
                linha = int(reg_row[idx_linha])
                coluna = int(reg_row[idx_col])
                equip = reg_row[idx_equip]
            except (ValueError, IndexError):
                continue

            try:
                cel_atual = agenda_vals[linha - 1][coluna - 1]
            except IndexError:
                continue

            cel_up = (cel_atual or "").strip().upper()
            if cel_up == "BLOQUEADO":
                continue

            uso = calcular_uso_celula(cel_atual)
            pedido = equip_str_para_dict(equip)

            cabe = all(
                uso.get(tipo, 0) + pedido.get(tipo, 0) <= ESTOQUE_TOTAL[tipo]
                for tipo in pedido
                if pedido[tipo] > 0
            )
            if not cabe:
                continue

            nova_reserva = formatar_reserva_agenda(nome, email, equip)
            if not cel_atual.strip() or cel_up == "":
                novo_valor = nova_reserva
            else:
                novo_valor = f"{cel_atual} § {nova_reserva}"

            sheet.update_cell(linha, coluna, novo_valor)

            while len(agenda_vals) < linha:
                agenda_vals.append([])
            while len(agenda_vals[linha - 1]) < coluna:
                agenda_vals[linha - 1].append("")
            agenda_vals[linha - 1][coluna - 1] = novo_valor

            todos = ws.get_all_values()
            for i, row in enumerate(todos):
                if row and row[0] == uid:
                    ws.delete_rows(i + 1)
                    break

            print(f"[promover] ✅ {nome} ({email or 'sem email'}) → L{linha} C{coluna}")
            promovidos.append({
                "nome": nome,
                "email": email,
                "linha": linha,
                "coluna": coluna,
                "equipamentos": equip,
            })

        return jsonify({"promovidos": promovidos})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@app.route("/dados", methods=["GET"])
def dados():
    return jsonify(get_all_data())


@app.route("/atualizar", methods=["POST"])
def atualizar():
    data = request.json
    update_cell(data["row"], data["col"], data["value"])
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
