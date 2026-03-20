const STATUS = document.getElementById("statusBox");
const GRID = document.getElementById("statsGrid");
const GENERATED_AT = document.getElementById("generatedAt");
const SOURCE_NOTE = document.getElementById("sourceNote");
const SCOPE_BADGE = document.getElementById("scopeBadge");
const REFRESH_BTN = document.getElementById("refreshBtn");
const GREETING = document.getElementById("timeGreeting");

const METRIC_LABELS = {
  followers: "Followers",
  following: "Following",
  publicRepos: "Public Repos",
  privateRepos: "Private Repos",
  totalRepos: "Total Repos",
  totalStarsOwned: "Total Stars (owned repos)",
  totalForksOwned: "Total Forks (owned repos)",
  openIssuesOwned: "Open Issues (owned repos)",
  contributionsLastYear: "Contributions (last 12 months)"
};

function setGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) {
    GREETING.textContent = "Good morning";
  } else if (hour < 18) {
    GREETING.textContent = "Good afternoon";
  } else {
    GREETING.textContent = "Good evening";
  }
}

function animateValue(el, target) {
  if (typeof target !== "number") {
    el.textContent = "Unavailable";
    el.classList.add("unavailable");
    return;
  }
  const duration = 700;
  const start = performance.now();

  function tick(now) {
    const ratio = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - ratio, 3);
    el.textContent = Math.floor(target * eased).toLocaleString();
    if (ratio < 1) requestAnimationFrame(tick);
  }

  requestAnimationFrame(tick);
}

function metricNote(key, unavailableSet, sources) {
  if (unavailableSet.has(key)) {
    return "Unavailable due to token/scope limits or API access restrictions.";
  }
  if (sources && sources[key]) {
    return `Source: ${sources[key]}`;
  }
  return "Source: GitHub API";
}

function renderStats(data) {
  const metrics = data?.metrics || {};
  const unavailable = new Set(data?.meta?.unavailable || []);
  const sources = data?.meta?.sources || {};

  GRID.innerHTML = "";

  Object.entries(METRIC_LABELS).forEach(([key, label], index) => {
    const card = document.createElement("article");
    card.className = "card";
    card.style.animationDelay = `${index * 50}ms`;

    const title = document.createElement("h3");
    title.textContent = label;

    const value = document.createElement("p");
    value.className = "value";

    const note = document.createElement("p");
    note.className = "note";
    note.textContent = metricNote(key, unavailable, sources);

    card.appendChild(title);
    card.appendChild(value);
    card.appendChild(note);
    GRID.appendChild(card);

    animateValue(value, metrics[key]);
  });
}

function formatGeneratedAt(isoDate) {
  if (!isoDate) return "Generated at: unknown";
  const date = new Date(isoDate);
  return `Generated at: ${date.toLocaleString()}`;
}

async function loadStats() {
  STATUS.textContent = "Loading latest stats...";

  try {
    const response = await fetch(`assets/stats.json?t=${Date.now()}`, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    renderStats(data);

    const username = data?.username || "unknown";
    const scope = data?.scope?.includesPrivate ? "public + private" : "public only";
    const reason = data?.scope?.reason || "";

    STATUS.textContent = `Showing statistics for @${username}.`;
    SCOPE_BADGE.textContent = `Scope: ${scope}`;
    GENERATED_AT.textContent = formatGeneratedAt(data?.generatedAt);
    SOURCE_NOTE.textContent = reason ? `Scope note: ${reason}` : "Source: GitHub REST + GraphQL APIs";
  } catch (error) {
    GRID.innerHTML = "";
    STATUS.textContent = "Could not load stats.json. Run the workflow once to generate it.";
    GENERATED_AT.textContent = "Generated at: unavailable";
    SOURCE_NOTE.textContent = `Error: ${error.message}`;
    SCOPE_BADGE.textContent = "Scope: unavailable";
  }
}

REFRESH_BTN.addEventListener("click", loadStats);

setGreeting();
loadStats();
