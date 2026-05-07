const API = "https://backend-reserva-n8ru.onrender.com";

let linhaSel = null;
let colunaSel = null;

async function carregar() {
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
        if (celula === "LIVRE") td.className = "livre";
        else if (celula === "BLOQUEADO") td.className = "bloqueado";
        else td.className = "reservado";

        td.onclick = () => reservar(i + 1, j + 1);
      }

      tr.appendChild(td);
    });

    tabela.appendChild(tr);
  });
}

/* RESERVA SIMPLES (PROFESSOR) */
async function reservar(linha, coluna) {
  const nome = prompt("Digite seu nome:");

  if (!nome) return;

  const res = await fetch(`${API}/editar`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      linha,
      coluna,
      valor: nome
    })
  });

  const data = await res.json();

  if (!res.ok) {
    alert(data.erro || "Erro ao reservar");
    return;
  }

  carregar();
}

/* atualização automática */
setInterval(carregar, 5000);

carregar();