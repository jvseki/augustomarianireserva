const API = "https://backend-reserva-n8ru.onrender.com";
let linhaAtual, colunaAtual, acaoAtual;

// Função para carregar os dados da planilha
async function carregarAgenda() {
  document.getElementById("loading").style.display = "flex";
  document.getElementById("table-container").style.display = "none";

  try {
    const res = await fetch(`${API}/agenda`);
    const data = await res.json();

    const tabela = document.getElementById("tabela");
    tabela.innerHTML = "";

    let livre = 0, reservado = 0, bloqueado = 0;
    const cabecalhos = data[0] || [];

    data.forEach((linha, i) => {
      const tr = document.createElement("tr");
      linha.forEach((celula, j) => {
        const isHeader = i === 0;
        const isLabelCol = j === 0; 

        const td = document.createElement(isHeader ? "th" : "td");
        td.innerText = celula;

        if (!isHeader && !isLabelCol) {
          const val = celula.trim().toUpperCase();
          if (val === "LIVRE" || val === "")  { td.className = "livre"; livre++; }
          else if (val === "BLOQUEADO")        { td.className = "bloqueado"; bloqueado++; }
          else                                 { td.className = "reservado"; reservado++; }

          const horario = linha[0] || `Linha ${i + 1}`;
          const dia = cabecalhos[j] || `Coluna ${j + 1}`;

          td.onclick = () => abrirModal(i + 1, j + 1, celula, horario, dia);
        }
        tr.appendChild(td);
      });
      tabela.appendChild(tr);
    });

    document.getElementById("count-livre").innerText = livre;
    document.getElementById("count-reservado").innerText = reservado;
    document.getElementById("count-bloqueado").innerText = bloqueado;

    document.getElementById("loading").style.display = "none";
    document.getElementById("table-container").style.display = "block";

  } catch (e) {
    console.error("Erro ao carregar:", e);
    showToast("❌ Erro ao conectar com o servidor.", "error-toast");
  }
}

// Abre o modal e RESETA o estado do botão e campos
function abrirModal(linha, coluna, valor, horario, dia) {
  linhaAtual = linha;
  colunaAtual = coluna;
  acaoAtual = null;

  document.getElementById("modal-title").innerText = `📅 ${dia} às ${horario}`;
  document.getElementById("modal-subtitle").innerText = `Status atual: ${valor || "Livre"}`;
  
  // Reseta elementos do modal
  document.getElementById("senha-area").style.display = "block";
  document.getElementById("acao-area").style.display = "none";
  document.getElementById("nome-input").value = "";
  document.getElementById("senha-input").value = "";
  document.getElementById("error-msg").textContent = "";
  
  // Reseta o botão de confirmação para o estado inicial
  const btn = document.getElementById("confirm-btn");
  btn.style.display = "none";
  btn.disabled = false;
  btn.textContent = "✔ Confirmar";

  document.querySelectorAll(".action-btn").forEach(b => b.classList.remove("active"));
  document.getElementById("modal-overlay").classList.add("active");
}

function fecharModal() {
  document.getElementById("modal-overlay").classList.remove("active");
}

function verificarSenha() {
  const senha = document.getElementById("senha-input").value;
  if (senha === "123") {
    document.getElementById("senha-area").style.display = "none";
    document.getElementById("acao-area").style.display = "block";
    document.getElementById("error-msg").textContent = "";
  } else {
    document.getElementById("error-msg").textContent = "❌ Senha incorreta!";
  }
}

function selecionarAcao(acao, elemento) {
  acaoAtual = acao;
  document.querySelectorAll(".action-btn").forEach(b => b.classList.remove("active"));
  elemento.classList.add("active");

  if (acao === "reservar") {
    document.getElementById("name-area").classList.add("visible");
  } else {
    document.getElementById("name-area").classList.remove("visible");
  }
  
  document.getElementById("confirm-btn").style.display = "block";
  document.getElementById("error-msg").textContent = "";
}

// FUNÇÃO DE SALVAMENTO CORRIGIDA
async function confirmarAcao() {
  if (!acaoAtual) return;

  let novoValor = "";
  if (acaoAtual === "reservar") {
    const nome = document.getElementById("nome-input").value.trim();
    if (!nome) { 
        document.getElementById("error-msg").textContent = "✏️ Digite seu nome."; 
        return; 
    }
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
  btn.disabled = true; // Trava para evitar cliques duplos

  try {
    const response = await fetch(`${API}/editar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ linha: linhaAtual, coluna: colunaAtual, valor: novoValor })
    });

    if (response.ok) {
      fecharModal();
      showToast("✔ Alteração salva com sucesso!", "success");
      await carregarAgenda(); // Recarrega a tabela
    } else {
      throw new Error("Erro na resposta do servidor");
    }

  } catch (e) {
    console.error(e);
    showToast("✗ Erro ao salvar. Tente novamente.", "error-toast");
  } finally {
    // IMPORTANTE: Isso garante que o botão volte ao normal 
    // mesmo se der erro ou sucesso, permitindo usar de novo.
    btn.textContent = "✔ Confirmar";
    btn.disabled = false;
  }
}

function showToast(msg, type) {
  const toast = document.getElementById("toast");
  toast.innerText = msg;
  toast.className = `toast show ${type}`;
  setTimeout(() => { toast.classList.remove("show"); }, 3000);
}

// Inicia a aplicação
carregarAgenda();