const API = "https://backend-reserva-n8ru.onrender.com";
let linhaAtual, colunaAtual;

const ESTOQUE = {
  tablet: { label: "tablet",           total: 12,  emoji: "📱" },
  prata:  { label: "notebook prata",   total: 23,  emoji: "💻" },
  preto:  { label: "notebook preto",   total: 11,  emoji: "🖥️" },
};

// Guarda quantos de cada tipo estão em uso NO HORÁRIO atual selecionado
let usoNoHorario = { tablet: 0, prata: 0, preto: 0 };

const HORARIOS = {
  2:  ["07:00", "07:50"],
  3:  ["07:50", "08:40"],
  4:  ["08:40", "09:30"],
  5:  ["09:30", "09:50"],
  6:  ["09:50", "10:40"],
  7:  ["10:40", "11:30"],
  8:  ["11:30", "12:30"],
  9:  ["12:30", "13:20"],
  10: ["13:20", "14:10"],
  11: ["14:10", "15:00"],
  12: ["15:00", "15:20"],
  13: ["15:20", "16:10"],
  14: ["16:10", "17:00"],
  15: ["17:00", "17:50"],
};

function horaAtualEmMinutos() {
  const d = new Date();
  return d.getHours() * 60 + d.getMinutes();
}

function paraMinutos(hhmm) {
  const [h, m] = hhmm.split(":").map(Number);
  return h * 60 + m;
}

// Retorna true se o horário da linha ainda está ativo (não passou)
function horarioEstaAtivo(linhaNumero) {
  const h = HORARIOS[linhaNumero];
  if (!h) return true; // linha sem horário mapeado = não interfere
  const agora = horaAtualEmMinutos();
  return agora < paraMinutos(h[1]); // ativo se ainda não terminou
}

// Extrai tipo e quantidade de um valor reservado ex: "João | 10 notebook prata"
function extrairReserva(valor) {
  if (!valor) return null;
  const v = valor.trim().toUpperCase();
  if (v === "" || v === "LIVRE" || v === "BLOQUEADO") return null;
  const partes = valor.split("|");
  if (partes.length < 2) return null;
  const equipPart = partes[1].trim().toLowerCase();
  let tipo = null;
  let qtd = 1;
  const match = equipPart.match(/(\d+)\s*(tablet|notebook prata|notebook preto)/i);
  if (match) {
    qtd = parseInt(match[1]);
    const nome = match[2].toLowerCase();
    if (nome === "tablet") tipo = "tablet";
    else if (nome === "notebook prata") tipo = "prata";
    else if (nome === "notebook preto") tipo = "preto";
  } else {
    if (equipPart.includes("tablet")) tipo = "tablet";
    else if (equipPart.includes("prata")) tipo = "prata";
    else if (equipPart.includes("preto")) tipo = "preto";
  }
  return tipo ? { tipo, qtd } : null;
}

// Calcula uso total de equipamentos em uma linha inteira (todas as colunas)
function calcularUsoNaLinha(linhaData) {
  const uso = { tablet: 0, prata: 0, preto: 0 };
  for (let col = 1; col < linhaData.length; col++) {
    const r = extrairReserva(linhaData[col]);
    if (r && uso[r.tipo] !== undefined) uso[r.tipo] += r.qtd;
  }
  return uso;
}

// =====================================================================
// CORREÇÃO: Calcula uso global SOMENTE dos horários que ainda estão
// ativos (não passados). Horários passados já foram resetados para LIVRE
// e não devem contar no estoque disponível.
// =====================================================================
function calcularUsoGlobal(dados) {
  const uso = { tablet: 0, prata: 0, preto: 0 };
  for (let i = 1; i < dados.length; i++) {
    const linhaNumero = i + 1; // linha 1 = cabeçalho, linha 2 = dados[1], etc.
    if (!horarioEstaAtivo(linhaNumero)) continue; // pula horários passados
    const linha = dados[i];
    for (let col = 1; col < linha.length; col++) {
      const r = extrairReserva(linha[col]);
      if (r && uso[r.tipo] !== undefined) uso[r.tipo] += r.qtd;
    }
  }
  return uso;
}

async function resetarHorariosPassados(dados) {
  const agora = horaAtualEmMinutos();
  for (const [linhaStr, [, fim]] of Object.entries(HORARIOS)) {
    const linha = parseInt(linhaStr);
    if (agora < paraMinutos(fim)) continue;
    const linhaData = dados[linha - 1];
    if (!linhaData) continue;
    for (let col = 1; col < linhaData.length; col++) {
      const val = (linhaData[col] || "").trim().toUpperCase();
      if (val !== "" && val !== "LIVRE" && val !== "BLOQUEADO") {
        try {
          await fetch(`${API}/editar`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ linha, coluna: col + 1, valor: "LIVRE" })
          });
        } catch (e) { console.warn("Erro reset", linha, col + 1); }
      }
    }
  }
}

async function carregarAgenda() {
  document.getElementById("loading").style.display = "flex";
  document.getElementById("table-container").style.display = "none";
  try {
    const r1 = await fetch(`${API}/agenda`);
    const d1 = await r1.json();
    await resetarHorariosPassados(d1);
    const r2 = await fetch(`${API}/agenda`);
    const dados = await r2.json();
    renderTabela(dados);
    atualizarStockHeader(calcularUsoGlobal(dados), dados);
  } catch (e) {
    document.getElementById("loading").innerHTML =
      `<p style="color:#c0302a;font-family:'Architects Daughter',cursive;font-size:16px">⚠️ Erro ao conectar com o servidor</p>`;
  }
}

// Atualiza os badges de estoque no header com disponibilidade real
function atualizarStockHeader(usoGlobal, dados) {
  const tipos = ["tablet", "prata", "preto"];
  tipos.forEach(tipo => {
    const disponiveis = ESTOQUE[tipo].total - usoGlobal[tipo];
    const badge = document.getElementById(`stock-${tipo}`);
    if (!badge) return;
    const { emoji, label, total } = ESTOQUE[tipo];
    if (disponiveis <= 0) {
      badge.innerHTML = `${emoji} ${total} ${label === "tablet" ? "tablets" : label + "s"} <span class="stock-zero">0 disponíveis</span>`;
      badge.classList.add("esgotado");
    } else {
      badge.innerHTML = `${emoji} ${disponiveis}/${total} ${label === "tablet" ? "tablets" : label + "s"} disponíveis`;
      badge.classList.remove("esgotado");
    }
  });
}

function formatarCelulaReservada(valor) {
  const partes = valor.split("|");
  if (partes.length < 2) return `<span>${valor}</span>`;
  const nome = partes[0].trim();
  const equip = partes[1].trim();
  return `<span class="cell-nome">${nome}</span><span class="cell-equip">${equip}</span>`;
}

// Guarda os dados globais para uso no modal
let dadosGlobais = [];

function renderTabela(data) {
  dadosGlobais = data;
  const tabela = document.getElementById("tabela");
  tabela.innerHTML = "";
  let livre = 0, reservado = 0;
  const cabecalhos = data[0] || [];

  data.forEach((linha, i) => {
    const tr = document.createElement("tr");
    linha.forEach((celula, j) => {
      const isHeader = i === 0;
      const isLabelCol = j === 0;
      const td = document.createElement(isHeader ? "th" : "td");

      if (!isHeader && !isLabelCol) {
        // =====================================================================
        // CORREÇÃO: normaliza o valor antes de comparar.
        // Valores com espaços extras, caracteres invisíveis ou capitalização
        // diferente (ex: "livre", " LIVRE ") agora são tratados corretamente,
        // evitando que células das linhas 2 e 3 fiquem sem onclick.
        // =====================================================================
        const val = (celula || "").trim().toUpperCase().replace(/\s+/g, " ");

        if (val === "LIVRE" || val === "") {
          td.className = "livre";
          td.innerText = "LIVRE";
          livre++;
          const horario = linha[0] || `Linha ${i + 1}`;
          const dia = cabecalhos[j] || `Col. ${j + 1}`;
          td.onclick = () => abrirModal(i + 1, j + 1, celula, horario, dia, data[i]);
        } else if (val === "BLOQUEADO") {
          td.className = "bloqueado";
          td.innerText = "BLOQUEADO";
          td.style.cursor = "not-allowed";
        } else if (val.includes("|")) {
          // Reserva válida com separador
          td.className = "reservado";
          td.style.cursor = "default";
          td.innerHTML = formatarCelulaReservada(celula);
          reservado++;
        } else {
          // =====================================================================
          // CORREÇÃO: valor desconhecido (ex: texto sem "|", espaço, caractere
          // estranho). Antes caía no bloco "reservado" sem onclick, tornando a
          // célula inerte. Agora trata como LIVRE para permitir nova reserva.
          // =====================================================================
          td.className = "livre";
          td.innerText = "LIVRE";
          livre++;
          const horario = linha[0] || `Linha ${i + 1}`;
          const dia = cabecalhos[j] || `Col. ${j + 1}`;
          td.onclick = () => abrirModal(i + 1, j + 1, "", horario, dia, data[i]);
          console.warn(`Valor inesperado na célula [${i+1}, ${j+1}]: "${celula}" → tratado como LIVRE`);
        }
      } else {
        td.innerText = celula;
        if (!isHeader && isLabelCol) td.className = "label-col";
      }
      tr.appendChild(td);
    });
    tabela.appendChild(tr);
  });

  document.getElementById("count-livre").textContent = livre;
  document.getElementById("count-reservado").textContent = reservado;
  document.getElementById("loading").style.display = "none";
  document.getElementById("table-container").style.display = "block";
}

// ========================
// MODAL
// ========================

let tipoSelecionado = null;

function abrirModal(linha, coluna, valor, horario, dia, linhaData) {
  linhaAtual = linha;
  colunaAtual = coluna;
  tipoSelecionado = null;

  // Calcula uso já existente nesta linha (este horário)
  usoNoHorario = calcularUsoNaLinha(linhaData);

  document.getElementById("modal-title").textContent = `${dia} — ${horario}`;
  document.getElementById("modal-sub").textContent = "Horário livre — faça sua reserva";

  document.getElementById("nome-input").value = "";
  document.getElementById("qtd-input").value = "1";
  document.getElementById("error-msg").textContent = "";
  document.getElementById("equip-error").textContent = "";
  document.querySelectorAll(".equip-btn").forEach(b => b.classList.remove("active", "sem-estoque"));

  // Atualiza disponibilidade nos botões de equipamento
  atualizarBotoesEquip();

  document.getElementById("overlay").classList.add("open");
  setTimeout(() => document.getElementById("nome-input").focus(), 100);
}

// Mostra disponibilidade em tempo real nos botões do modal
function atualizarBotoesEquip() {
  Object.keys(ESTOQUE).forEach(tipo => {
    const disponiveis = ESTOQUE[tipo].total - usoNoHorario[tipo];
    const btn = document.querySelector(`.equip-btn.${tipo}`);
    if (!btn) return;
    const maxSpan = btn.querySelector(".equip-max");
    if (disponiveis <= 0) {
      maxSpan.textContent = "esgotado neste horário";
      maxSpan.style.color = "var(--red)";
      btn.classList.add("sem-estoque");
      btn.disabled = true;
    } else {
      maxSpan.textContent = `${disponiveis} disponíveis`;
      maxSpan.style.color = "";
      btn.classList.remove("sem-estoque");
      btn.disabled = false;
    }
  });
}

function fecharModal() {
  document.getElementById("overlay").classList.remove("open");
}

document.getElementById("overlay").addEventListener("click", function (e) {
  if (e.target === this) fecharModal();
});

function selecionarEquip(tipo, btn) {
  const disponiveis = ESTOQUE[tipo].total - usoNoHorario[tipo];
  if (disponiveis <= 0) {
    document.getElementById("equip-error").textContent = `⚠️ Todos os ${ESTOQUE[tipo].label}s já estão reservados neste horário.`;
    return;
  }
  tipoSelecionado = tipo;
  document.querySelectorAll(".equip-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  document.getElementById("equip-error").textContent = "";
  document.getElementById("qtd-input").max = disponiveis;
  document.getElementById("qtd-label").textContent = `Quantidade (máx. ${disponiveis} disponíveis)`;
  const cur = parseInt(document.getElementById("qtd-input").value) || 1;
  if (cur > disponiveis) document.getElementById("qtd-input").value = disponiveis;
}

async function confirmarAcao() {
  const nome = document.getElementById("nome-input").value.trim();
  if (!nome) {
    document.getElementById("error-msg").textContent = "✏️ Digite o nome do professor.";
    return;
  }
  if (!tipoSelecionado) {
    document.getElementById("equip-error").textContent = "⚠️ Selecione o tipo de equipamento.";
    return;
  }
  const disponiveis = ESTOQUE[tipoSelecionado].total - usoNoHorario[tipoSelecionado];
  const qtd = parseInt(document.getElementById("qtd-input").value) || 1;
  if (qtd < 1 || qtd > disponiveis) {
    document.getElementById("equip-error").textContent = `⚠️ Só há ${disponiveis} ${ESTOQUE[tipoSelecionado].label}(s) disponíveis neste horário.`;
    return;
  }

  const novoValor = `${nome} | ${qtd} ${ESTOQUE[tipoSelecionado].label}`;

  const btn = document.getElementById("confirm-btn");
  btn.textContent = "Salvando...";
  btn.disabled = true;

  try {
    await fetch(`${API}/editar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ linha: linhaAtual, coluna: colunaAtual, valor: novoValor })
    });
    fecharModal();
    showToast("✔ Reserva salva com sucesso!", "success");
    carregarAgenda();
  } catch (e) {
    showToast("✗ Erro ao salvar. Tente novamente.", "error-toast");
    btn.textContent = "✔ Confirmar";
    btn.disabled = false;
  }
}

function showToast(msg, type) {
  const toast = document.getElementById("toast");
  toast.textContent = msg;
  toast.className = `toast ${type} show`;
  setTimeout(() => toast.classList.remove("show"), 3000);
}

carregarAgenda();
setInterval(carregarAgenda, 60000);
