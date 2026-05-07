const API = "https://backend-reserva-n8ru.onrender.com";
let linhaAtual, colunaAtual, acaoAtual;

const ESTOQUE = {
  tablet: { label: "tablet",           total: 12,  emoji: "📱" },
  prata:  { label: "notebook prata",   total: 23,  emoji: "💻" },
  preto:  { label: "notebook preto",   total: 11,  emoji: "🖥️" },
};

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
    renderTabela(await r2.json());
  } catch (e) {
    document.getElementById("loading").innerHTML =
      `<p style="color:#c0302a;font-family:'Architects Daughter',cursive;font-size:16px">⚠️ Erro ao conectar com o servidor</p>`;
  }
}

function formatarCelulaReservada(valor) {
  const partes = valor.split("|");
  if (partes.length < 2) return `<span>${valor}</span>`;
  const nome = partes[0].trim();
  const equip = partes[1].trim();
  return `<span class="cell-nome">${nome}</span><span class="cell-equip">${equip}</span>`;
}

function renderTabela(data) {
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
        const val = (celula || "").trim().toUpperCase();
        if (val === "LIVRE" || val === "") {
          td.className = "livre";
          td.innerText = celula;
          livre++;
          const horario = linha[0] || `Linha ${i + 1}`;
          const dia = cabecalhos[j] || `Col. ${j + 1}`;
          td.onclick = () => abrirModal(i + 1, j + 1, celula, horario, dia);
        } else if (val === "BLOQUEADO") {
          td.className = "bloqueado";
          td.innerText = celula;
          td.style.cursor = "not-allowed";
        } else {
          td.className = "reservado";
          td.style.cursor = "default";
          td.innerHTML = formatarCelulaReservada(celula);
          reservado++;
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

function abrirModal(linha, coluna, valor, horario, dia) {
  linhaAtual = linha;
  colunaAtual = coluna;
  acaoAtual = null;
  tipoSelecionado = null;

  document.getElementById("modal-title").textContent = `${dia} — ${horario}`;
  document.getElementById("modal-sub").textContent = "Horário livre — faça sua reserva";

  document.getElementById("reservar-form").style.display = "none";
  document.getElementById("bloquear-confirm").style.display = "none";
  document.getElementById("confirm-btn").style.display = "none";
  document.getElementById("nome-input").value = "";
  document.getElementById("qtd-input").value = "1";
  document.getElementById("error-msg").textContent = "";
  document.getElementById("equip-error").textContent = "";
  document.querySelectorAll(".equip-btn").forEach(b => b.classList.remove("active"));
  document.querySelectorAll(".action-btn2").forEach(b => b.classList.remove("active"));

  document.getElementById("overlay").classList.add("open");
}

function fecharModal() {
  document.getElementById("overlay").classList.remove("open");
}

document.getElementById("overlay").addEventListener("click", function (e) {
  if (e.target === this) fecharModal();
});

function selecionarAcao(acao, btn) {
  acaoAtual = acao;
  document.querySelectorAll(".action-btn2").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");

  document.getElementById("reservar-form").style.display = acao === "reservar" ? "block" : "none";
  document.getElementById("bloquear-confirm").style.display = acao === "bloquear" ? "block" : "none";
  document.getElementById("confirm-btn").style.display = "block";
  document.getElementById("error-msg").textContent = "";

  if (acao === "reservar") setTimeout(() => document.getElementById("nome-input").focus(), 100);
}

function selecionarEquip(tipo, btn) {
  tipoSelecionado = tipo;
  document.querySelectorAll(".equip-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  document.getElementById("equip-error").textContent = "";
  const max = ESTOQUE[tipo].total;
  document.getElementById("qtd-input").max = max;
  document.getElementById("qtd-label").textContent = `Quantidade (máx. ${max})`;
  const cur = parseInt(document.getElementById("qtd-input").value) || 1;
  if (cur > max) document.getElementById("qtd-input").value = max;
}

async function confirmarAcao() {
  if (!acaoAtual) return;

  let novoValor = "";

  if (acaoAtual === "reservar") {
    const nome = document.getElementById("nome-input").value.trim();
    if (!nome) {
      document.getElementById("error-msg").textContent = "✏️ Digite o nome do professor.";
      return;
    }
    if (!tipoSelecionado) {
      document.getElementById("equip-error").textContent = "⚠️ Selecione o tipo de equipamento.";
      return;
    }
    const qtd = parseInt(document.getElementById("qtd-input").value) || 1;
    const max = ESTOQUE[tipoSelecionado].total;
    if (qtd < 1 || qtd > max) {
      document.getElementById("equip-error").textContent = `⚠️ Quantidade entre 1 e ${max}.`;
      return;
    }
    novoValor = `${nome} | ${qtd} ${ESTOQUE[tipoSelecionado].label}`;
  } else if (acaoAtual === "bloquear") {
    novoValor = "BLOQUEADO";
  }

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
