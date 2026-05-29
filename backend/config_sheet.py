"""Aba Config na planilha — evita enviar o mesmo aviso semanal duas vezes."""
from sheets import client

SHEET_ID = "1uixhu6rN03HrMy-1ECf2U-Gr5bpKkbbiToiHGMOglk0"


def get_config_ws():
    spreadsheet = client.open_by_key(SHEET_ID)
    try:
        return spreadsheet.worksheet("Config")
    except Exception:
        ws = spreadsheet.add_worksheet(title="Config", rows=20, cols=2)
        ws.update("A1:B1", [["chave", "valor"]])
        return ws


def config_get(chave, default=""):
    ws = get_config_ws()
    rows = ws.get_all_values()
    for row in rows[1:]:
        if row and row[0] == chave:
            return row[1] if len(row) > 1 else default
    return default


def config_set(chave, valor):
    ws = get_config_ws()
    rows = ws.get_all_values()
    for i, row in enumerate(rows[1:], start=2):
        if row and row[0] == chave:
            ws.update_cell(i, 2, valor)
            return
    ws.append_row([chave, valor])
