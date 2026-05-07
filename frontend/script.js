const API = "https://backend-reserva-n8ru.onrender.com";
let linhaAtual, colunaAtual, acaoAtual;

async function carregarAgenda() {
  document.getElementById("loading").style.display = "flex";
  document.getElementById("table-container").style.display = "none";

  try {
    const res = await fetch(`${API}/agenda`);
    const data = await res.json();

    const tabela = document.getElementById("tabela");
    tabela.innerHTML = "";

    let livre = 0, reservado = 0, bloqueado = 0;

    // Guarda cabeçalhos (linha 0) para usar no modal
    const cabecalhos = data[0] || [];

    data.forEach((linha, i) => {
      const tr = document.createElement("tr");
      linha.forEach((celula, j) => {
        const isHeader = i === 0;
        const isLabelCol = j === 0; // coluna Horário — nunca editável

        const td = document.createElement(isHeader ? "th" : "td");
        td.innerText = celula;

        if (!isHeader && !isLabelCol) {
          const val = celula.trim().toUpperCase();
          if (val === "LIVRE" || val === "")  { td.className = "livre"; livre++; }
          else if (val === "BLOQUEADO")        { td.className = "bloqueado"; bloqueado++; }
          else                                 { td.className = "reservado"; reservado++; }

          const horario = linha[0] || `Linha ${i + 1}`;
          const dia     = cabecalhos[j] || `Col. ${j + 1}`;
          td.onclick = () => abrirModal(i + 1, j + 1, celula, horario, dia);
        }

        if (!isHeader && isLabelCol) {
          td.className = "label-col";
        }

        tr.appendChild(td);
      });
      tabela.appendChild(tr);
    });

    document.getElementById("count-livre").textContent = livre;
    document.getElementById("count-reservado").textContent = reservado;
    document.getElementById("count-bloqueado").textContent = bloqueado;

    document.getElementById("loading").style.display = "none";
    document.getElementById("table-container").style.display = "block";

  } catch (e) {
    document.getElementById("loading").innerHTML =
      `<p style="color:#c0302a;font-family:'Architects Daughter',cursive;font-size:16px">⚠️ Erro ao conectar com o servidor</p>`;
  }
}

function abrirModal(linha, coluna, valor, horario, dia) {
  linhaAtual = linha;
  colunaAtual = coluna;
  acaoAtual = null;

  document.getElementById("modal-title").textContent = `${dia} — ${horario}`;
  document.getElementById("modal-sub").textContent = valor ? `Situação atual: ${valor}` : "Célula vazia";

  document.getElementById("senha-area").style.display = "block";
  document.getElementById("acao-area").style.display = "none";
  document.getElementById("name-area").classList.remove("visible");
  document.getElementById("confirm-btn").style.display = "none";
  document.getElementById("senha-input").value = "";
  document.getElementById("nome-input").value = "";
  document.getElementById("error-msg").textContent = "";

  document.querySelectorAll(".action-btn").forEach(b => b.classList.remove("active"));

  document.getElementById("overlay").classList.add("open");
  setTimeout(() => document.getElementById("senha-input").focus(), 100);
}

function fecharModal() {
  document.getElementById("overlay").classList.remove("open");
}

document.getElementById("overlay").addEventListener("click", function (e) {
  if (e.target === this) fecharModal();
});

function verificarSenha() {
  const senha = document.getElementById("senha-input").value;
  if (senha !== "1234") {
    document.getElementById("error-msg").textContent = "❌ Senha incorreta.";
    document.getElementById("senha-input").value = "";
    return;
  }
  document.getElementById("senha-area").style.display = "none";
  document.getElementById("acao-area").style.display = "block";
  document.getElementById("error-msg").textContent = "";
}

function selecionarAcao(acao, btn) {
  acaoAtual = acao;
  document.querySelectorAll(".action-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");

  if (acao === "reservar") {
    document.getElementById("name-area").classList.add("visible");
    setTimeout(() => document.getElementById("nome-input").focus(), 100);
  } else {
    document.getElementById("name-area").classList.remove("visible");
  }
  document.getElementById("confirm-btn").style.display = "block";
  document.getElementById("error-msg").textContent = "";
}

async function confirmarAcao() {
  if (!acaoAtual) return;

  let novoValor = "";
  if (acaoAtual === "reservar") {
    const nome = document.getElementById("nome-input").value.trim();
    if (!nome) { document.getElementById("error-msg").textContent = "✏️ Digite seu nome."; return; }
    novoValor = nome;
  } else if (acaoAtual === "bloquear") {
    novoValor = "BLOQUEADO";
  } else if (acaoAtual === "liberar") {
    novoValor = "LIVRE";
  } else if (acaoAtual === "limpar") {
    novoValor = "";
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
    showToast("✔ Alteração salva com sucesso!", "success");
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
