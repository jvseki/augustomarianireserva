// ══════════════════════════════════════
// Service Worker — Agendamento de Notebooks
// Estratégia: cache para assets estáticos,
//             network-first para a API
// ══════════════════════════════════════

const CACHE_NAME = "notebooks-v2";

const ASSETS_ESTATICOS = [
  "/",
  "/index.html",
  "/style.css",
  "/manifest.json",
  "https://fonts.googleapis.com/css2?family=Architects+Daughter&family=DM+Sans:ital,wght@0,400;0,600;0,700;0,800;1,400&family=DM+Mono:wght@500;600&display=swap"
];

// ── Mensagens da página (ex: SKIP_WAITING para forçar update) ──
self.addEventListener("message", event => {
  if (event.data && event.data.type === "SKIP_WAITING") {
    self.skipWaiting();
  }
});

// ── Instalação: pré-cache dos assets ──
self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      // Ignora falhas individuais (ex: fontes offline durante install)
      return Promise.allSettled(
        ASSETS_ESTATICOS.map(url => cache.add(url).catch(() => {}))
      );
    })
  );
  self.skipWaiting();
});

// ── Ativação: limpa caches antigos ──
self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(k => k !== CACHE_NAME)
          .map(k => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

// ── Fetch: network-first para API, cache-first para o resto ──
self.addEventListener("fetch", event => {
  const url = new URL(event.request.url);

  // API do backend — sempre tenta a rede, nunca cacheamos respostas da API
  if (url.hostname.includes("onrender.com") || url.pathname.startsWith("/agenda")) {
    event.respondWith(
      fetch(event.request).catch(() =>
        new Response(
          JSON.stringify({ erro: "Sem conexão. Verifique sua internet." }),
          { status: 503, headers: { "Content-Type": "application/json" } }
        )
      )
    );
    return;
  }

  // Google Sign-In — sempre rede
  if (url.hostname.includes("accounts.google.com") || url.hostname.includes("googleapis.com")) {
    event.respondWith(fetch(event.request).catch(() => new Response("", { status: 503 })));
    return;
  }

  // Assets estáticos — cache first, fallback rede
  event.respondWith(
    caches.match(event.request).then(cached => {
      if (cached) return cached;
      return fetch(event.request).then(response => {
        // Só cacheia respostas válidas de assets
        if (response && response.status === 200 && response.type !== "opaque") {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      });
    })
  );
});
