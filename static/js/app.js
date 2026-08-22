const form = document.querySelector("#searchForm");
const termInput = form.elements.term;
const sourceLabel = document.querySelector("#sourceLabel");
const resultCount = document.querySelector("#resultCount");
const averageRating = document.querySelector("#averageRating");
const averageReviews = document.querySelector("#averageReviews");
const topCategory = document.querySelector("#topCategory");
const resultsTitle = document.querySelector("#resultsTitle");
const businessList = document.querySelector("#businessList");
const categoryBreakdown = document.querySelector("#categoryBreakdown");
const ratingBreakdown = document.querySelector("#ratingBreakdown");

function dollars(price) {
  const value = Number(price || 0);
  return value > 0 ? "$".repeat(value) : "No price";
}

function initials(name) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase();
}

function renderBars(node, items) {
  node.innerHTML = "";
  const max = Math.max(...items.map((item) => item.count), 1);

  items.forEach((item) => {
    const row = document.createElement("div");
    row.className = "bar-row";
    row.innerHTML = `
      <div class="bar-label">
        <span>${item.label}</span>
        <strong>${item.count}</strong>
      </div>
      <div class="bar-track">
        <div class="bar-fill" style="--bar-width: ${(item.count / max) * 100}%"></div>
      </div>
    `;
    node.appendChild(row);
  });
}

function renderBusinesses(businesses) {
  businessList.innerHTML = "";

  if (!businesses.length) {
    businessList.innerHTML = '<p class="empty-state">No businesses matched this search.</p>';
    return;
  }

  businesses.forEach((business, index) => {
    const card = document.createElement("article");
    card.className = "business-card";
    card.innerHTML = `
      <div class="thumb" aria-hidden="true">${initials(business.business)}</div>
      <div>
        <h3>${index + 1}. ${business.business}</h3>
        <div class="meta">
          <span>${business.category || "Uncategorized"}</span>
          <span>${business.city}, ${business.state}</span>
          <span>${dollars(business.price)}</span>
          <span>${business.reviews.toLocaleString()} reviews</span>
        </div>
      </div>
      <div class="rating-badge">${business.rating.toFixed(1)}</div>
    `;
    businessList.appendChild(card);
  });
}

async function runSearch() {
  const params = new URLSearchParams(new FormData(form));
  sourceLabel.textContent = "Loading";

  const response = await fetch(`/api/search?${params.toString()}`);
  const payload = await response.json();

  sourceLabel.textContent = payload.source;
  resultsTitle.textContent = `${payload.location} ${payload.term}`;
  resultCount.textContent = payload.summary.result_count;
  averageRating.textContent = payload.summary.average_rating.toFixed(2);
  averageReviews.textContent = payload.summary.average_reviews.toLocaleString();
  topCategory.textContent = payload.summary.top_category;

  renderBusinesses(payload.businesses);
  renderBars(categoryBreakdown, payload.summary.category_breakdown);
  renderBars(ratingBreakdown, payload.summary.rating_breakdown);
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  runSearch().catch(() => {
    sourceLabel.textContent = "Search error";
    businessList.innerHTML = '<p class="empty-state">Something went wrong loading results.</p>';
  });
});

document.querySelectorAll(".nav-chip").forEach((button) => {
  button.addEventListener("click", () => {
    termInput.value = button.dataset.term;
    runSearch();
  });
});

runSearch();
