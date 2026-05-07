const API = "https://backend-reserva-n8ru.onrender.com";

async function carregarAgenda() {
  const res = await fetch(`${API}/agenda`);
  const data = await res.json();

  const tabela = document.getElementById("tabela");
  tabela.innerHTML = "";

  data.forEach((linha, i) => {
    const tr = document.createElement("tr");

    linha.forEach((celula, j) => {
      const td = document.createElement(i === 0 ? "th" : "td");
      td.innerText = celula;

      if (i !== 0) {
        const val = celula.toUpperCase();
        if (val === "LIVRE" || val === "") td.className = "livre";
        else if (val === "BLOQUEADO") td.className = "bloqueado";
        else td.className = "reservado";

        td.onclick = () => menuEdicao(i + 1, j + 1, celula);
      }

      tr.appendChild(td);
    });

    tabela.appendChild(tr);
  });
}


async function menuEdicao(linha, coluna, valorAtual) {
  const senha = prompt("Digite a senha:");
  if (senha !== "1234") return;

  const opcao = prompt(
    "O que deseja fazer?\n1 - Reservar\n2 - Bloquear\n3 - Liberar\n4 - Limpar"
  );

  let novoValor = valorAtual;

  if (opcao === "1") {
    const nome = prompt("Digite seu nome:");
    if (!nome) return;
    novoValor = nome;
  } else if (opcao === "2") {
    novoValor = "BLOQUEADO";
  } else if (opcao === "3") {
    novoValor = "LIVRE";
  } else if (opcao === "4") {
    novoValor = "";
  } else {
    return; // opção inválida, não faz nada
  }

  await fetch(`${API}/editar`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ linha, coluna, valor: novoValor })
  });

  carregarAgenda();
}

carregarAgenda();
