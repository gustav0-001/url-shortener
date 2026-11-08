const KEY = "shortlink.links";
const $ = (id) => document.getElementById(id);
const form = $("form"), input = $("url"), submit = $("submit"), message = $("message");
const result = $("result"), shortLink = $("short"), copyBtn = $("copy");
const list = $("list"), empty = $("empty");

const load = () => { try { return JSON.parse(localStorage.getItem(KEY)) || []; } catch { return []; } };
const save = (links) => { try { localStorage.setItem(KEY, JSON.stringify(links)); } catch {} };
const bare = (url) => url.replace(/^https?:\/\//, "");

function plural(n) {
  const m10 = n % 10, m100 = n % 100;
  if (m10 === 1 && m100 !== 11) return `${n} переход`;
  if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return `${n} перехода`;
  return `${n} переходов`;
}

function showMessage(text) { message.textContent = text; message.hidden = !text; }

function render() {
  const links = load();
  list.replaceChildren(...links.map((link) => {
    const li = document.createElement("li");
    const code = document.createElement("a");
    code.href = link.short_url; code.target = "_blank"; code.rel = "noopener";
    code.textContent = link.short_code;
    const orig = document.createElement("span");
    orig.className = "orig"; orig.textContent = link.original_url; orig.title = link.original_url;
    const clicks = document.createElement("span");
    clicks.textContent = plural(link.clicks ?? 0);
    li.append(code, orig, clicks);
    return li;
  }));
  empty.hidden = links.length > 0;
}

async function refreshStats() {
  const fresh = await Promise.all(load().map(async (link) => {
    try {
      const r = await fetch(`/links/${link.short_code}`);
      if (r.status === 404) return null;
      if (!r.ok) return link;
      return { ...link, clicks: (await r.json()).clicks };
    } catch { return link; }
  }));
  save(fresh.filter(Boolean));
  render();
}

function errorText(status, body) {
  const detail = JSON.stringify(body?.detail ?? "");
  if (status === 422) {
    return detail.includes("not allowed")
      ? "Ссылки на этот сервис сокращать нельзя."
      : "Некорректная ссылка. Нужен адрес вида https://example.com";
  }
  if (status === 503) return "Не удалось подобрать код. Попробуй ещё раз.";
  return "Что-то пошло не так. Попробуй ещё раз.";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  let url = input.value.trim();
  if (!/^https?:\/\//i.test(url)) url = `https://${url}`;
  showMessage(""); result.hidden = true; submit.disabled = true;
  const wake = setTimeout(() => showMessage("Сервер просыпается, это может занять до минуты…"), 4000);
  try {
    const response = await fetch("/links", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ original_url: url }),
    });
    const body = await response.json().catch(() => null);
    if (!response.ok) { showMessage(errorText(response.status, body)); return; }
    showMessage("");
    shortLink.href = body.short_url;
    shortLink.textContent = bare(body.short_url);
    result.hidden = false;
    save([body, ...load()]);
    render();
    input.value = "";
  } catch {
    showMessage("Нет связи с сервером. Проверь интернет и попробуй ещё раз.");
  } finally {
    clearTimeout(wake);
    submit.disabled = false;
  }
});

copyBtn.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(shortLink.href);
    copyBtn.textContent = "СКОПИРОВАНО";
  } catch {
    copyBtn.textContent = "ВЫДЕЛИ И СКОПИРУЙ";
  }
  setTimeout(() => { copyBtn.textContent = "КОПИРОВАТЬ"; }, 1500);
});

render();
refreshStats();