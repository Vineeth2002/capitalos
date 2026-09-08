let objectiveContext = "";
let claims = [];       // {statement, temporal_orientation, epistemic_role, shape, origin}
let researchCaseId = null;

const TEMPORAL_OPTIONS = ["historical", "current", "forecast"];
const EPISTEMIC_OPTIONS = ["evidence", "interpretation", "assumption", "risk", "hypothesis"];
const SHAPE_OPTIONS = ["quantitative", "qualitative"];

function selectHtml(name, options, selected) {
  return "<select data-field=\"" + name + "\">" + options.map(function (o) {
    return "<option value=\"" + o + "\"" + (o === selected ? " selected" : "") + ">" + o + "</option>";
  }).join("") + "</select>";
}

function renderDraftClaims() {
  const container = document.getElementById("draft-claims");
  container.innerHTML = "";
  claims.forEach(function (claim, index) {
    const div = document.createElement("div");
    div.className = "claim-card";
    div.innerHTML =
      "<textarea data-index=\"" + index + "\" data-field=\"statement\">" + claim.statement + "</textarea>" +
      "<div class=\"fields\">" +
      selectHtml("temporal_orientation", TEMPORAL_OPTIONS, claim.temporal_orientation) +
      selectHtml("epistemic_role", EPISTEMIC_OPTIONS, claim.epistemic_role) +
      selectHtml("shape", SHAPE_OPTIONS, claim.shape) +
      "</div>" +
      "<div class=\"actions\"><button class=\"danger\" data-action=\"remove\" data-index=\"" + index + "\">Remove</button></div>";
    container.appendChild(div);
  });

  container.querySelectorAll("[data-field]").forEach(function (el) {
    el.addEventListener("change", function () {
      const idx = parseInt(el.getAttribute("data-index"), 10);
      const field = el.getAttribute("data-field");
      claims[idx][field] = el.value;
    });
  });
  container.querySelectorAll("[data-action='remove']").forEach(function (el) {
    el.addEventListener("click", function () {
      const idx = parseInt(el.getAttribute("data-index"), 10);
      claims.splice(idx, 1);
      renderDraftClaims();
    });
  });
}

function renderCandidates(candidates) {
  const container = document.getElementById("inferred-candidates");
  container.innerHTML = "";
  if (candidates.length === 0) {
    container.innerHTML = "<p>None.</p>";
    return;
  }
  candidates.forEach(function (candidate, index) {
    const div = document.createElement("div");
    div.className = "candidate-card";
    div.innerHTML =
      "<div>" + candidate.statement + "</div>" +
      "<div class=\"reason\">Why inferred: " + candidate.reason + "</div>" +
      "<div class=\"actions\">" +
      "<button data-action=\"promote\" data-index=\"" + index + "\">Promote to claim</button>" +
      "<button class=\"secondary\" data-action=\"reject\" data-index=\"" + index + "\">Reject</button>" +
      "</div>";
    container.appendChild(div);
  });

  container.querySelectorAll("[data-action='promote']").forEach(function (el) {
    el.addEventListener("click", function () {
      const idx = parseInt(el.getAttribute("data-index"), 10);
      const candidate = candidates[idx];
      claims.push({
        statement: candidate.statement,
        temporal_orientation: "current",
        epistemic_role: "hypothesis",
        shape: "qualitative",
        origin: "ai_suggested"
      });
      candidates.splice(idx, 1);
      renderDraftClaims();
      renderCandidates(candidates);
    });
  });
  container.querySelectorAll("[data-action='reject']").forEach(function (el) {
    el.addEventListener("click", function () {
      const idx = parseInt(el.getAttribute("data-index"), 10);
      candidates.splice(idx, 1);
      renderCandidates(candidates);
    });
  });
}

document.getElementById("btn-analyze").addEventListener("click", async function () {
  const text = document.getElementById("reasoning-text").value.trim();
  const errorEl = document.getElementById("analyze-error");
  errorEl.textContent = "";

  if (!text) {
    errorEl.textContent = "Please describe your reasoning first.";
    return;
  }

  this.disabled = true;
  this.textContent = "Analyzing...";

  try {
    const response = await fetch("/reasoning-intake", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text })
    });
    const data = await response.json();

    if (!response.ok) {
      errorEl.textContent = data.detail || "Something went wrong.";
      return;
    }

    document.getElementById("step-review").classList.remove("hidden");

    if (data.needs_more_reasoning) {
      document.getElementById("needs-more").classList.remove("hidden");
      document.getElementById("needs-more").textContent = data.message;
      document.getElementById("review-content").classList.add("hidden");
      return;
    }

    document.getElementById("needs-more").classList.add("hidden");
    document.getElementById("review-content").classList.remove("hidden");

    objectiveContext = data.objective_context || "";
    document.getElementById("objective-context").value = objectiveContext;

    claims = data.draft_claims.map(function (c) {
      return {
        statement: c.statement,
        temporal_orientation: c.temporal_orientation,
        epistemic_role: c.epistemic_role,
        shape: c.shape,
        origin: "user"
      };
    });
    renderDraftClaims();
    renderCandidates(data.inferred_candidates || []);
  } catch (err) {
    errorEl.textContent = "Network error: " + err.message;
  } finally {
    this.disabled = false;
    this.textContent = "Analyze My Reasoning";
  }
});

document.getElementById("btn-confirm").addEventListener("click", async function () {
  const errorEl = document.getElementById("confirm-error");
  errorEl.textContent = "";

  if (claims.length === 0) {
    errorEl.textContent = "You need at least one claim to confirm.";
    return;
  }

  const title = document.getElementById("title").value.trim() || "Untitled reasoning case";
  const description = document.getElementById("objective-context").value;

  this.disabled = true;
  this.textContent = "Confirming...";

  try {
    const response = await fetch("/reasoning-intake/confirm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        entity_id: null,
        title: title,
        description: description,
        claims: claims.map(function (c) {
          return {
            entity_id: null,
            statement: c.statement,
            temporal_orientation: c.temporal_orientation,
            epistemic_role: c.epistemic_role,
            shape: c.shape,
            confidence_band: null,
            lifecycle_status: "active",
            lens: null,
            origin: c.origin
          };
        })
      })
    });
    const data = await response.json();

    if (!response.ok) {
      errorEl.textContent = data.detail || "Something went wrong.";
      return;
    }

    researchCaseId = data.research_case.id;
    document.getElementById("step-challenge").classList.remove("hidden");
    document.getElementById("btn-confirm").textContent = "Confirmed ✓";
  } catch (err) {
    errorEl.textContent = "Network error: " + err.message;
  } finally {
    this.disabled = false;
  }
});

document.getElementById("btn-challenge").addEventListener("click", async function () {
  const errorEl = document.getElementById("challenge-error");
  errorEl.textContent = "";
  this.disabled = true;
  this.textContent = "Challenging...";

  try {
    const response = await fetch("/research-cases/" + researchCaseId + "/challenge", {
      method: "POST"
    });
    const data = await response.json();

    if (!response.ok) {
      errorEl.textContent = data.detail || "Something went wrong.";
      return;
    }

    const container = document.getElementById("challenge-results");
    container.innerHTML = "";
    if (data.length === 0) {
      container.innerHTML = "<p>No challenges generated.</p>";
    }
    data.forEach(function (challenge) {
      const div = document.createElement("div");
      div.className = "challenge-card";
      div.innerHTML =
        "<div class=\"category\">" + challenge.category.replace(/_/g, " ") + "</div>" +
        "<div>" + challenge.text + "</div>" +
        "<div class=\"claim-refs\">References claim IDs: " + challenge.claim_ids.join(", ") + "</div>";
      container.appendChild(div);
    });
  } catch (err) {
    errorEl.textContent = "Network error: " + err.message;
  } finally {
    this.disabled = false;
    this.textContent = "Challenge My Reasoning";
  }
});