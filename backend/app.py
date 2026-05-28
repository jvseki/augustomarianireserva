from flask import Flask, jsonify, request
from flask_cors import CORS
from sheets import get_all_data, update_cell, get_cell, client, sheet
import os
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
        # Migração: garante que o cabeçalho tenha 7 colunas com email
        header = ws.row_values(1)
        if header and "email" not in header:
            # Insere coluna email na posição 3 (após nome)
            ws.insert_cols([[""]] * 1, 3)
            ws.update_cell(1, 3, "email")
        return ws
    except Exception:
        ws = spreadsheet.add_worksheet(title="Espera", rows=500, cols=7)
        ws.append_row(["id", "nome", "email", "linha", "coluna", "equipamentos", "timestamp"])
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
            data.get("email", ""),
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


RE_EQUIP = re.compile(
    r"(\d+)\s*(tv remota|notebook prata|notebook preto|tablet)",
    re.IGNORECASE,
)

def _parse_equip_segment(seg):
    """Soma quantidades de um trecho '2 tablet + 1 tv remota'."""
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
    """Retorna uso por tipo de equipamento na célula."""
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
    """Converte string de equipamentos em dict de quantidades."""
    res = {"tablet": 0, "prata": 0, "preto": 0, "tvremota": 0}
    for seg in equip_str.split("+"):
        parsed = _parse_equip_segment(seg.strip())
        for k in res:
            res[k] += parsed[k]
    return res

ESTOQUE_TOTAL = {"tablet": 12, "prata": 23, "preto": 11, "tvremota": 1}

@app.route("/promover", methods=["POST"])
def promover_espera():
    """
    Verifica se há espaço suficiente para cada item da lista de espera
    considerando APENAS os equipamentos pedidos — não exige slot totalmente livre.
    Usa get_all_values() com mapeamento por cabeçalho para ser robusto
    mesmo com abas legadas ou em migração.
    """
    try:
        ws = get_espera_sheet()

        # Lê todas as linhas incluindo cabeçalho e mapeia colunas pelo nome
        todas_linhas = ws.get_all_values()
        if not todas_linhas:
            return jsonify({"promovidos": []})

        header = todas_linhas[0]
        def col_idx(nome_col):
            try: return header.index(nome_col)
            except ValueError: return None

        idx_id    = col_idx("id")
        idx_nome  = col_idx("nome")
        idx_linha = col_idx("linha")
        idx_col   = col_idx("coluna")
        idx_equip = col_idx("equipamentos")

        # Valida que os campos essenciais existem no cabeçalho
        if None in (idx_id, idx_nome, idx_linha, idx_col, idx_equip):
            return jsonify({"erro": "Cabeçalho da aba Espera inválido", "header": header}), 500

        registros_raw = todas_linhas[1:]  # pula cabeçalho
        print(f"[promover] {len(registros_raw)} item(s) na fila | header: {header}")

        promovidos = []
        agenda_vals = sheet.get_all_values()

        # Processa cada item da espera em ordem (FIFO)
        for reg_row in registros_raw:
            if not reg_row or not reg_row[idx_id]:
                continue  # linha vazia
            try:
                uid    = reg_row[idx_id]
                nome   = reg_row[idx_nome]
                linha  = int(reg_row[idx_linha])
                coluna = int(reg_row[idx_col])
                equip  = reg_row[idx_equip]
            except (ValueError, IndexError):
                continue  # linha corrompida, pula

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

            print(f"[promover] ✅ Promovido: {nome} → linha {linha}, col {coluna}, equip: {equip}")
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
