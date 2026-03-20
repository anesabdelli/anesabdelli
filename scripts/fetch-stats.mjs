import { mkdir, writeFile } from "node:fs/promises";

const GH_API = "https://api.github.com";
const GH_GRAPHQL = "https://api.github.com/graphql";

const username = (process.env.GH_USERNAME || "").trim();
const token = (process.env.GH_STATS_TOKEN || process.env.GITHUB_TOKEN || "").trim();

if (!username) {
  throw new Error("GH_USERNAME is required.");
}

function headers() {
  const base = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "github-statistics-dashboard"
  };

  if (!token) {
    return base;
  }

  return {
    ...base,
    "Authorization": `Bearer ${token}`
  };
}

async function requestJson(url, init = {}) {
  const response = await fetch(url, {
    ...init,
    headers: {
      ...headers(),
      ...(init.headers || {})
    }
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${text}`);
  }

  return response.json();
}

async function getUserProfile(name) {
  return requestJson(`${GH_API}/users/${encodeURIComponent(name)}`);
}

async function getViewer() {
  if (!token) {
    return null;
  }

  try {
    return await requestJson(`${GH_API}/user`);
  } catch {
    return null;
  }
}

async function getOwnedRepos({ includePrivate }) {
  const repos = [];
  let page = 1;

  while (true) {
    let endpoint;

    if (includePrivate) {
      endpoint = `${GH_API}/user/repos?visibility=all&affiliation=owner&per_page=100&page=${page}&sort=updated`;
    } else {
      endpoint = `${GH_API}/users/${encodeURIComponent(username)}/repos?type=owner&per_page=100&page=${page}&sort=updated`;
    }

    const batch = await requestJson(endpoint);
    if (!Array.isArray(batch) || batch.length === 0) {
      break;
    }

    repos.push(...batch);
    page += 1;
  }

  return repos;
}

async function getContributionsLastYear({ canUseViewerData }) {
  if (!token || !canUseViewerData) {
    return { value: null, source: null };
  }

  const query = `
    query {
      viewer {
        contributionsCollection {
          contributionCalendar {
            totalContributions
          }
        }
      }
    }
  `;

  try {
    const body = JSON.stringify({ query });
    const data = await requestJson(GH_GRAPHQL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body
    });

    const value = data?.data?.viewer?.contributionsCollection?.contributionCalendar?.totalContributions;

    if (typeof value === "number") {
      return { value, source: "GitHub GraphQL viewer.contributionsCollection" };
    }

    return { value: null, source: null };
  } catch {
    return { value: null, source: null };
  }
}

function sumBy(items, selector) {
  return items.reduce((acc, item) => acc + (Number(selector(item)) || 0), 0);
}

function countPrivateRepos(items) {
  return items.reduce((acc, repo) => acc + (repo.private ? 1 : 0), 0);
}

function buildStats({ profile, repos, includePrivate, contributions }) {
  const followers = typeof profile.followers === "number" ? profile.followers : null;
  const following = typeof profile.following === "number" ? profile.following : null;

  const publicRepos = repos.reduce((acc, repo) => acc + (repo.private ? 0 : 1), 0);
  const privateRepos = includePrivate ? countPrivateRepos(repos) : null;
  const totalRepos = includePrivate ? repos.length : publicRepos;

  const totalStarsOwned = sumBy(repos, (repo) => repo.stargazers_count);
  const totalForksOwned = sumBy(repos, (repo) => repo.forks_count);
  const openIssuesOwned = sumBy(repos, (repo) => repo.open_issues_count);

  const metrics = {
    followers,
    following,
    publicRepos,
    privateRepos,
    totalRepos,
    totalStarsOwned,
    totalForksOwned,
    openIssuesOwned,
    contributionsLastYear: contributions.value
  };

  const sources = {
    followers: "GitHub REST /users/{username}",
    following: "GitHub REST /users/{username}",
    publicRepos: includePrivate ? "GitHub REST /user/repos filtered by visibility" : "GitHub REST /users/{username}/repos",
    privateRepos: includePrivate ? "GitHub REST /user/repos (private=true)" : undefined,
    totalRepos: includePrivate ? "GitHub REST /user/repos" : "GitHub REST /users/{username}/repos",
    totalStarsOwned: includePrivate ? "GitHub REST /user/repos stargazers_count" : "GitHub REST /users/{username}/repos stargazers_count",
    totalForksOwned: includePrivate ? "GitHub REST /user/repos forks_count" : "GitHub REST /users/{username}/repos forks_count",
    openIssuesOwned: includePrivate ? "GitHub REST /user/repos open_issues_count" : "GitHub REST /users/{username}/repos open_issues_count",
    contributionsLastYear: contributions.source || undefined
  };

  const unavailable = Object.entries(metrics)
    .filter(([, value]) => typeof value !== "number")
    .map(([key]) => key);

  Object.keys(sources).forEach((key) => {
    if (!sources[key]) {
      delete sources[key];
    }
  });

  return { metrics, unavailable, sources };
}

async function main() {
  const profile = await getUserProfile(username);
  const viewer = await getViewer();

  const canUsePrivate = Boolean(
    token &&
    viewer &&
    typeof viewer.login === "string" &&
    viewer.login.toLowerCase() === username.toLowerCase()
  );

  const repos = await getOwnedRepos({ includePrivate: canUsePrivate });
  const contributions = await getContributionsLastYear({ canUseViewerData: canUsePrivate });

  const { metrics, unavailable, sources } = buildStats({
    profile,
    repos,
    includePrivate: canUsePrivate,
    contributions
  });

  const output = {
    generatedAt: new Date().toISOString(),
    username,
    scope: {
      includesPrivate: canUsePrivate,
      reason: canUsePrivate
        ? "Private data included because token owner matches GH_USERNAME."
        : "Public-only mode (no token, invalid scope, or token owner differs from GH_USERNAME)."
    },
    metrics,
    meta: {
      unavailable,
      sources
    }
  };

  await mkdir("assets", { recursive: true });
  await writeFile("assets/stats.json", `${JSON.stringify(output, null, 2)}\n`, "utf8");

  console.log("Generated assets/stats.json successfully.");
  console.log(`Mode: ${output.scope.includesPrivate ? "public + private" : "public only"}`);
}

main().catch((error) => {
  console.error("Failed to generate stats:", error);
  process.exit(1);
});
