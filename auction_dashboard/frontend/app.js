let currentOffset = 0;
const PAGE_SIZE = 24;
let currentView = "grid";
let debounceTimer = null;
let currentModal = null;

// ── Filters state ──────────────────────────────────────────────
function getFilters() {
  return {
    region: getActivePill("regionFilter"),
    max_price: document.getElementById("priceRange").value,
    is_new: getActivePill("showFilter") === "new" ? true : null,
    is_favourite: getActivePill("showFilter") === "fav" ? true : null,
    source: document.getElementById("sourceFilter").value || null,
    search: document.getElementById("searchInput").value || null,
  };
}

function getActivePill(groupId) {
  const active = document.querySelector(`#${groupId} .pill.active`);
  return active ? active.dataset.val : "";
}

// ── Init ───────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  setupPillGroups();
  loadStats();
  loadProperties();
});

function setupPillGroups() {
  document.querySelectorAll(".pill-group").forEach(group => {
    group.querySelectorAll(".pill").forEach(pill => {
      pill.addEventListener("click", () => {
        group.querySelectorAll(".pill").forEach(p => p.classList.remove("active"));
        pill.classList.add("active");
        currentOffset = 0;
        loadProperties();
      });
    });
  });
}

// ── Stats ──────────────────────────────────────────────────────
async function loadStats() {
  try {
    const data = await api("/api/stats");
    document.getElementById("statTotal").textContent = data.total.toLocaleString();
    document.getElementById("statNew").textContent = data.new;
    document.getElementById("statFav").textContent = data.favourites;
    if (data.last_scrape) {
      const d = new Date(data.last_scrape.ran_at);
      document.getElementById("lastScrape").textContent =
        `Last sync: ${d.toLocaleDateString("en-GB", {day: "numeric", month: "short"})}`;
    }
  } catch (e) {
    console.error("Stats error:", e);
  }
}

// ── Properties ─────────────────────────────────────────────────
async function loadProperties(append = false) {
  if (!append) currentOffset = 0;
  const filters = getFilters();
  const params = new URLSearchParams();
  if (filters.region) params.set("region", filters.region);
  if (filters.max_price) params.set("max_price", filters.max_price);
  if (filters.is_new) params.set("is_new", "true");
  if (filters.is_favourite) params.set("is_favourite", "true");
  if (filters.source) params.set("source", filters.source);
  if (filters.search) params.set("search", filters.search);
  params.set("limit", PAGE_SIZE);
  params.set("offset", currentOffset);

  try {
    const data = await api(`/api/properties?${params}`);
    const grid = document.getElementById("propertyGrid");

    if (!append) grid.innerHTML = "";

    if (data.properties.length === 0 && !append) {
      grid.innerHTML = emptyState();
    } else {
      data.properties.forEach(p => {
        grid.insertAdjacentHTML("beforeend", renderCard(p));
      });
    }

    const shown = currentOffset + data.properties.length;
    document.getElementById("resultCount").textContent =
      `${data.total.toLocaleString()} propert${data.total === 1 ? "y" : "ies"} found`;

    const loadMoreEl = document.getElementById("loadMore");
    loadMoreEl.style.display = shown < data.total ? "block" : "none";
    currentOffset = shown;
  } catch (e) {
    console.error("Load error:", e);
  }
}

function loadMore() {
  loadProperties(true);
}

function debounceLoad() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => loadProperties(), 350);
}

// ── Render ─────────────────────────────────────────────────────
const SOURCE_LABELS = {
  spain_boe: "🇪🇸 BOE",
  italy_astalegale: "🇮🇹 AstaLegale",
  france_licitor: "🇫🇷 Licitor",
  portugal_eleiloes: "🇵🇹 e-Leilões",
};

function renderCard(p) {
  const price = p.price_eur
    ? `<span class="card-price">€${Math.round(p.price_eur).toLocaleString()}</span>`
    : `<span class="card-price tbd">Price TBD</span>`;

  const area = p.area_m2 ? `<span class="card-area">· ${Math.round(p.area_m2)}m²</span>` : "";
  const date = p.auction_date ? `<span class="card-date">· ${p.auction_date}</span>` : "";

  const tags = [
    p.is_historical ? `<span class="tag tag-hist">Historic</span>` : "",
    p.needs_refurbishment ? `<span class="tag tag-refurb">Restore</span>` : "",
    p.property_type !== "residential" ? `<span class="tag tag-type">${p.property_type}</span>` : "",
    `<span class="tag tag-source">${SOURCE_LABELS[p.source] || p.source}</span>`,
  ].filter(Boolean).join("");

  const img = p.image_url
    ? `<div class="card-img"><img src="${escHtml(p.image_url)}" alt="" loading="lazy" onerror="this.parentNode.innerHTML='🏛'"></div>`
    : `<div class="card-img">🏛</div>`;

  return `
  <div class="property-card${p.is_new ? " is-new" : ""}"
       data-id="${p.id}"
       onclick="openModal('${p.id}')">
    ${img}
    <div class="card-body">
      <div class="card-title">${escHtml(p.title)}</div>
      <div class="card-location">📍 ${escHtml(p.location)}</div>
      <div class="card-meta">${price}${area}${date}</div>
      <div class="card-tags">${tags}</div>
    </div>
    <div class="card-actions" onclick="event.stopPropagation()">
      <button class="${p.is_favourite ? "active" : ""}" onclick="toggleFav('${p.id}', this)">
        ${p.is_favourite ? "★ Saved" : "☆ Save"}
      </button>
      <button onclick="window.open('${escHtml(p.url)}', '_blank')">View ↗</button>
    </div>
  </div>`;
}

function emptyState() {
  return `<div class="empty-state">
    <div class="empty-icon">🏛</div>
    <h3>No properties yet</h3>
    <p>Click Refresh to scan all four auction platforms for heritage properties matching your profile.</p>
    <button class="btn-start" onclick="triggerScrape()">↻ Run first scan</button>
  </div>`;
}

// ── Modal ──────────────────────────────────────────────────────
async function openModal(id) {
  await markSeen(id);
  const card = document.querySelector(`[data-id="${id}"]`);
  if (card) card.classList.remove("is-new");

  // Fetch fresh data
  const params = new URLSearchParams({ search: id, limit: 1 });
  const data = await api(`/api/properties?${params}`);
  const p = data.properties.find(x => x.id === id);
  if (!p) return;

  currentModal = p;

  const img = p.image_url
    ? `<div class="modal-img"><img src="${escHtml(p.image_url)}" alt=""></div>`
    : `<div class="modal-img">🏛</div>`;

  const price = p.price_eur
    ? `€${Math.round(p.price_eur).toLocaleString()}`
    : "Price not disclosed";

  const cashBudget = 150000;
  const budgetNote = p.price_eur
    ? (p.price_eur <= cashBudget
        ? `<span style="color:var(--new-color);font-weight:600">✓ Within cash budget</span>`
        : p.price_eur <= 300000
          ? `<span style="color:var(--fav-color)">Needs financing · €${Math.round(p.price_eur - cashBudget).toLocaleString()} over 5 years</span>`
          : `<span style="color:#dc2626">Over budget</span>`)
    : "";

  document.getElementById("modalContent").innerHTML = `
    ${img}
    <h2 class="modal-title">${escHtml(p.title)}</h2>
    <div class="modal-location">📍 ${escHtml(p.location)}</div>
    <div class="modal-price">${price} <small style="font-size:14px;font-weight:400;color:var(--muted)">${budgetNote}</small></div>
    <div class="modal-grid">
      <div class="modal-field"><label>Source</label><span>${SOURCE_LABELS[p.source] || p.source}</span></div>
      <div class="modal-field"><label>Property Type</label><span style="text-transform:capitalize">${p.property_type}</span></div>
      <div class="modal-field"><label>Size</label><span>${p.area_m2 ? Math.round(p.area_m2) + " m²" : "—"}</span></div>
      <div class="modal-field"><label>Auction Date</label><span>${p.auction_date || "—"}</span></div>
      <div class="modal-field"><label>Auction Closes</label><span>${p.auction_end_date || "—"}</span></div>
      <div class="modal-field"><label>Payment Terms</label><span>${p.payment_conditions || "Standard"}</span></div>
    </div>
    ${p.description ? `<div class="modal-desc">${escHtml(p.description)}</div>` : ""}
    <div class="modal-notes">
      <label>Your Notes</label>
      <textarea id="modalNotes" placeholder="Add your thoughts about this property…">${escHtml(p.notes || "")}</textarea>
    </div>
    <div class="modal-actions">
      <a href="${escHtml(p.url)}" target="_blank" class="btn-primary">View Auction ↗</a>
      <button class="btn-fav" onclick="toggleFavModal('${p.id}')">
        ${p.is_favourite ? "★ Saved" : "☆ Save Property"}
      </button>
      <button class="btn-secondary" onclick="saveNotes('${p.id}')">Save Notes</button>
    </div>`;

  document.getElementById("modal").classList.add("open");
}

function closeModal(event) {
  if (event && event.target !== document.getElementById("modal")) return;
  document.getElementById("modal").classList.remove("open");
  currentModal = null;
}

async function saveNotes(id) {
  const notes = document.getElementById("modalNotes").value;
  await api(`/api/properties/${id}/notes`, "POST", { notes });
}

async function toggleFavModal(id) {
  const isFav = await toggleFav(id);
  const btn = document.querySelector(".modal-actions .btn-fav");
  if (btn) btn.textContent = isFav ? "★ Saved" : "☆ Save Property";
}

// ── Actions ────────────────────────────────────────────────────
async function markSeen(id) {
  await api(`/api/properties/${id}/seen`, "POST");
}

async function toggleFav(id, btn) {
  const data = await api(`/api/properties/${id}/favourite`, "POST");
  if (btn) {
    btn.textContent = data.is_favourite ? "★ Saved" : "☆ Save";
    btn.classList.toggle("active", data.is_favourite);
  }
  loadStats();
  return data.is_favourite;
}

async function triggerScrape() {
  const toast = showToast("Scanning auction platforms…");
  const btn = document.getElementById("btnScrape");
  btn.disabled = true;
  btn.textContent = "Scanning…";
  try {
    const data = await api("/api/scrape", "POST");
    toast.textContent = `✓ Done — ${data.new_count} new propert${data.new_count === 1 ? "y" : "ies"} found`;
    setTimeout(() => hideToast(), 3000);
    loadStats();
    loadProperties();
  } catch (e) {
    toast.textContent = "Error during scan — check console";
    setTimeout(() => hideToast(), 4000);
  } finally {
    btn.disabled = false;
    btn.textContent = "↻ Refresh";
  }
}

// ── View toggle ────────────────────────────────────────────────
function setView(view) {
  currentView = view;
  const grid = document.getElementById("propertyGrid");
  grid.classList.toggle("list-view", view === "list");
  document.getElementById("viewGrid").classList.toggle("active", view === "grid");
  document.getElementById("viewList").classList.toggle("active", view === "list");
}

// ── Price range ────────────────────────────────────────────────
function updatePriceLabel() {
  const val = parseInt(document.getElementById("priceRange").value);
  document.getElementById("priceLabel").textContent = `€${val.toLocaleString()}`;
}

function setPrice(val) {
  document.getElementById("priceRange").value = val;
  updatePriceLabel();
  currentOffset = 0;
  loadProperties();
}

// ── Toast ──────────────────────────────────────────────────────
let toastEl = null;
function showToast(msg) {
  if (!toastEl) {
    toastEl = document.createElement("div");
    toastEl.className = "scraping-toast";
    toastEl.innerHTML = `<div class="spinner"></div><span></span>`;
    document.body.appendChild(toastEl);
  }
  toastEl.querySelector("span").textContent = msg;
  toastEl.classList.add("show");
  return toastEl.querySelector("span");
}
function hideToast() { if (toastEl) toastEl.classList.remove("show"); }

// ── Helpers ────────────────────────────────────────────────────
async function api(url, method = "GET", body = null) {
  const opts = { method, headers: { "Content-Type": "application/json" } };
  if (body) opts.body = JSON.stringify(body);
  const resp = await fetch(url, opts);
  if (!resp.ok) throw new Error(`API ${resp.status}: ${url}`);
  return resp.json();
}

function escHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
