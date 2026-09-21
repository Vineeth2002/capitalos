const caseId = document.querySelector(".container").getAttribute("data-case-id");

const TEMPORAL_OPTIONS = ["historical", "current", "forecast"];
const EPISTEMIC_OPTIONS = ["evidence", "interpretation", "assumption", "risk", "hypothesis"];
const SHAPE_OPTIONS = ["quantitative", "qualitative"];

let currentClaims = [];
let allSources = [];

function selectHtml(name, options, selected) {
  return "<select data-field=\"" + name + "\">" + options.map(function (o) {
    return "<option value=\"" + o + "\"" + (o === selected ? " selected" : "") + ">" + o + "</option>";
  }).join("") + "</select>";
}

async function loadWorkspace() {
  try {
    const caseResponse = await fetch("/research-cases/" + caseId);
    const caseData = await caseResponse.json();

    if (!caseResponse.ok) {
      document.getElementById("ws-title").textContent = "Research Case not found";
      return;
    }

    document.getElementById("ws-title").textContent = caseData.title;
    document.getElementById("ws-description").textContent =
      caseData.description || "No description provided.";

    await loadAllSources();
    await refreshClaims();

    const challengesResponse = await fetch("/research-cases/" + caseId + "/challenges");
    const challenges = await challengesResponse.json();
    renderChallenges(challenges);
  } catch (err) {
    document.getElementById("ws-title").textContent = "Failed to load workspace";
  }
}

async function loadAllSources() {
  try {
    const response = await fetch("/research-sources");
    if (response.ok) {
      allSources = await response.json();
    }
  } catch (err) {
    allSources = [];
  }
}

async function refreshClaims() {
  const claimsResponse = await fetch("/research-cases/" + caseId + "/claims");
  const claims = await claimsResponse.json();
  currentClaims = claims;
  renderClaims(claims);
  await refreshRelationships();
  populateRelationshipDropdowns();
}

function renderClaims(claims) {
  const container = document.getElementById("ws-claims");
  container.innerHTML = "";

  if (claims.length === 0) {
    container.innerHTML = "<p>No claims yet.</p>";
  }

  claims.forEach(function (claim) {
    const div = document.createElement("div");
    div.className = "claim-card";
    div.setAttribute("data-claim-id", claim.id);
    div.innerHTML = viewModeHtml(claim);
    container.appendChild(div);
  });

  wireClaimCardEvents(container);

  claims.forEach(function (claim) {
    loadSourcesForClaim(claim.id);
  });

  const existingAddBtn = document.getElementById("btn-add-claim");
  if (existingAddBtn) {
    existingAddBtn.remove();
  }

  const addBtn = document.createElement("button");
  addBtn.textContent = "+ Add Claim";
  addBtn.id = "btn-add-claim";
  addBtn.addEventListener("click", function () {
    addBlankClaimCard(container);
  });
  container.parentElement.insertBefore(addBtn, container.nextSibling);
}

function viewModeHtml(claim) {
  return (
    "<div class=\"view-mode\">" +
    "<div>" + claim.statement + "</div>" +
    "<div class=\"reason\">" +
    claim.temporal_orientation + " / " + claim.epistemic_role + " / " + claim.shape +
    " (origin: " + claim.origin + ")</div>" +
    "<div class=\"actions\">" +
    "<button data-action=\"edit\">Edit</button>" +
    "<button class=\"danger\" data-action=\"delete\">Delete</button>" +
    "</div>" +
    "<h4>Sources</h4>" +
    "<div class=\"sources-container\" id=\"sources-" + claim.id + "\">Loading sources...</div>" +
    "</div>"
  );
}

function editModeHtml(claim) {
  return (
    "<div class=\"edit-mode\">" +
    "<textarea data-field=\"statement\">" + claim.statement + "</textarea>" +
    "<div class=\"fields\">" +
    selectHtml("temporal_orientation", TEMPORAL_OPTIONS, claim.temporal_orientation) +
    selectHtml("epistemic_role", EPISTEMIC_OPTIONS, claim.epistemic_role) +
    selectHtml("shape", SHAPE_OPTIONS, claim.shape) +
    "</div>" +
    "<div class=\"actions\">" +
    "<button data-action=\"save\">Save</button>" +
    "<button class=\"secondary\" data-action=\"cancel\">Cancel</button>" +
    "</div></div>"
  );
}

function wireClaimCardEvents(container) {
  container.querySelectorAll("[data-action='edit']").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const card = btn.closest(".claim-card");
      const claimId = card.getAttribute("data-claim-id");
      fetch("/claims/" + claimId)
        .then(function (r) { return r.json(); })
        .then(function (claim) {
          card.innerHTML = editModeHtml(claim);
          wireEditActions(card, claimId, claim);
        });
    });
  });

  container.querySelectorAll("[data-action='delete']").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      const card = btn.closest(".claim-card");
      const claimId = card.getAttribute("data-claim-id");

      if (!confirm("Delete this claim? This cannot be undone.")) {
        return;
      }

      const response = await fetch("/claims/" + claimId, { method: "DELETE" });
      if (response.status === 204) {
        logResearchEvent("CLAIM_DELETED", { claim_id: claimId });
        await refreshClaims();
      } else {
        const data = await response.json();
        alert(data.detail || "Could not delete claim.");
      }
    });
  });
}

function wireEditActions(card, claimId, originalClaim) {
  card.querySelector("[data-action='save']").addEventListener("click", async function () {
    const statement = card.querySelector("[data-field='statement']").value;
    const temporal = card.querySelector("[data-field='temporal_orientation']").value;
    const epistemic = card.querySelector("[data-field='epistemic_role']").value;
    const shape = card.querySelector("[data-field='shape']").value;

    const response = await fetch("/claims/" + claimId, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        statement: statement,
        temporal_orientation: temporal,
        epistemic_role: epistemic,
        shape: shape
      })
    });

    if (response.ok) {
      logResearchEvent("CLAIM_EDITED", {
        claim_id: claimId,
        before: originalClaim,
        after: {
          statement: statement,
          temporal_orientation: temporal,
          epistemic_role: epistemic,
          shape: shape
        }
      });
      await refreshClaims();
    } else {
      const data = await response.json();
      alert(data.detail || "Could not save claim.");
    }
  });

  card.querySelector("[data-action='cancel']").addEventListener("click", function () {
    refreshClaims();
  });
}

function addBlankClaimCard(container) {
  const div = document.createElement("div");
  div.className = "claim-card";
  div.innerHTML =
    "<div class=\"edit-mode\">" +
    "<textarea data-field=\"statement\" placeholder=\"New claim statement\"></textarea>" +
    "<div class=\"fields\">" +
    selectHtml("temporal_orientation", TEMPORAL_OPTIONS, "current") +
    selectHtml("epistemic_role", EPISTEMIC_OPTIONS, "assumption") +
    selectHtml("shape", SHAPE_OPTIONS, "qualitative") +
    "</div>" +
    "<div class=\"actions\">" +
    "<button data-action=\"save-new\">Save</button>" +
    "<button class=\"secondary\" data-action=\"cancel-new\">Cancel</button>" +
    "</div></div>";
  container.appendChild(div);

  div.querySelector("[data-action='save-new']").addEventListener("click", async function () {
    const statement = div.querySelector("[data-field='statement']").value.trim();
    if (!statement) {
      alert("Statement cannot be empty.");
      return;
    }
    const temporal = div.querySelector("[data-field='temporal_orientation']").value;
    const epistemic = div.querySelector("[data-field='epistemic_role']").value;
    const shape = div.querySelector("[data-field='shape']").value;

    const response = await fetch("/research-cases/" + caseId + "/claims", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        entity_id: null,
        statement: statement,
        temporal_orientation: temporal,
        epistemic_role: epistemic,
        shape: shape,
        confidence_band: null,
        lifecycle_status: "active",
        lens: null,
        origin: "user"
      })
    });

    if (response.ok) {
      const created = await response.json();
      logResearchEvent("CLAIM_ADDED_LOCALLY", { claim: created });
      await refreshClaims();
    } else {
      const data = await response.json();
      alert(data.detail || "Could not add claim.");
    }
  });

  div.querySelector("[data-action='cancel-new']").addEventListener("click", function () {
    div.remove();
  });
}

function claimLabel(claimId) {
  const claim = currentClaims.find(function (c) { return c.id === claimId; });
  if (!claim) {
    return "Claim " + claimId;
  }
  const short = claim.statement.length > 50
    ? claim.statement.slice(0, 50) + "..."
    : claim.statement;
  return "#" + claimId + ": " + short;
}

async function refreshRelationships() {
  const container = document.getElementById("ws-relationships");
  container.innerHTML = "Loading...";

  const allRelationships = [];
  for (const claim of currentClaims) {
    const response = await fetch("/claims/" + claim.id + "/relationships");
    if (response.ok) {
      const rels = await response.json();
      rels.forEach(function (r) { allRelationships.push(r); });
    }
  }

  if (allRelationships.length === 0) {
    container.innerHTML = "<p>No relationships yet.</p>";
    return;
  }

  container.innerHTML = "";
  allRelationships.forEach(function (rel) {
    const div = document.createElement("div");
    div.className = "claim-card";
    div.innerHTML =
      "<div>" + claimLabel(rel.from_claim_id) + "</div>" +
      "<div class=\"reason\"><strong>" + rel.relationship_type + "</strong></div>" +
      "<div>" + claimLabel(rel.to_claim_id) + "</div>";
    container.appendChild(div);
  });
}

function populateRelationshipDropdowns() {
  const fromSelect = document.getElementById("rel-from");
  const toSelect = document.getElementById("rel-to");

  const optionsHtml = currentClaims.map(function (c) {
    return "<option value=\"" + c.id + "\">" + claimLabel(c.id) + "</option>";
  }).join("");

  fromSelect.innerHTML = optionsHtml;
  toSelect.innerHTML = optionsHtml;

  if (currentClaims.length > 1) {
    toSelect.selectedIndex = 1;
  }
}

document.getElementById("btn-add-relationship").addEventListener("click", async function () {
  const errorEl = document.getElementById("relationship-error");
  errorEl.textContent = "";

  const fromId = parseInt(document.getElementById("rel-from").value, 10);
  const toId = parseInt(document.getElementById("rel-to").value, 10);
  const relType = document.getElementById("rel-type").value;

  if (!fromId || !toId) {
    errorEl.textContent = "You need at least two claims to create a relationship.";
    return;
  }

  const response = await fetch("/claims/" + fromId + "/relationships", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ to_claim_id: toId, relationship_type: relType })
  });

  const data = await response.json();

  if (!response.ok) {
    errorEl.textContent = data.detail || "Could not create relationship.";
    return;
  }

  logResearchEvent("RELATIONSHIP_CREATED", { from: fromId, to: toId, type: relType });
  await refreshRelationships();
});

function sourceOptionsHtml() {
  let html = "<option value=\"\">-- select existing source --</option>";
  allSources.forEach(function (s) {
    html += "<option value=\"" + s.id + "\">" + s.title +
      (s.publisher ? " (" + s.publisher + ")" : "") + "</option>";
  });
  return html;
}

function sourceCardHtml(claimSource) {
  const s = claimSource.source;
  const urlHtml = s.url
    ? "<a href=\"" + s.url + "\" target=\"_blank\" rel=\"noopener\">" + s.url + "</a>"
    : "";
  return (
    "<div class=\"claim-card\" data-claim-source-id=\"" + claimSource.id + "\">" +
    "<div><strong>" + s.title + "</strong> (" + s.source_type + ")</div>" +
    (s.publisher ? "<div class=\"reason\">Publisher: " + s.publisher + "</div>" : "") +
    (urlHtml ? "<div class=\"reason\">" + urlHtml + "</div>" : "") +
    "<div class=\"reason\"><strong>" + claimSource.relationship_type + "</strong></div>" +
    (claimSource.excerpt ? "<div class=\"reason\">Excerpt: " + claimSource.excerpt + "</div>" : "") +
    "<div class=\"actions\">" +
    "<button class=\"danger\" data-action=\"detach-source\" data-claim-id=\"" +
    claimSource.claim_id + "\" data-source-id=\"" + claimSource.source_id + "\">Remove</button>" +
    "</div></div>"
  );
}

async function loadSourcesForClaim(claimId) {
  const container = document.getElementById("sources-" + claimId);
  if (!container) {
    return;
  }
  container.innerHTML = "Loading sources...";

  try {
    const response = await fetch("/claims/" + claimId + "/sources");
    if (!response.ok) {
      container.innerHTML = "<p>Could not load sources.</p>";
      return;
    }
    const claimSources = await response.json();

    let html = "";
    if (claimSources.length === 0) {
      html += "<p>No sources attached.</p>";
    } else {
      claimSources.forEach(function (cs) {
        html += sourceCardHtml(cs);
      });
    }

    html +=
      "<div class=\"source-attach-form\">" +
      "<select data-field=\"existing-source\">" + sourceOptionsHtml() + "</select>" +
      "<button type=\"button\" data-action=\"toggle-new-source\">+ New source</button>" +
      "<div class=\"new-source-fields hidden\" id=\"new-source-" + claimId + "\">" +
      "<input type=\"text\" placeholder=\"Title\" data-field=\"new-title\">" +
      "<input type=\"text\" placeholder=\"URL (optional)\" data-field=\"new-url\">" +
      "<input type=\"text\" placeholder=\"Publisher (optional)\" data-field=\"new-publisher\">" +
      "<select data-field=\"new-source-type\">" +
      "<option value=\"filing\">filing</option>" +
      "<option value=\"regulator\">regulator</option>" +
      "<option value=\"annual_report\">annual_report</option>" +
      "<option value=\"company\">company</option>" +
      "<option value=\"research\">research</option>" +
      "<option value=\"news\" selected>news</option>" +
      "<option value=\"dataset\">dataset</option>" +
      "<option value=\"other\">other</option>" +
      "</select>" +
      "</div>" +
      "<select data-field=\"relationship-type\">" +
      "<option value=\"supports\">supports</option>" +
      "<option value=\"contradicts\">contradicts</option>" +
      "<option value=\"context\">context</option>" +
      "</select>" +
      "<textarea placeholder=\"Excerpt (optional)\" data-field=\"excerpt\"></textarea>" +
      "<button type=\"button\" data-action=\"attach-source\">Attach Source</button>" +
      "<div class=\"error\" id=\"source-error-" + claimId + "\"></div>" +
      "</div>";

    container.innerHTML = html;
    wireSourceEvents(container, claimId);
  } catch (err) {
    container.innerHTML = "<p>Could not load sources.</p>";
  }
}

function wireSourceEvents(container, claimId) {
  container.querySelectorAll("[data-action='detach-source']").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      const cId = btn.getAttribute("data-claim-id");
      const sId = btn.getAttribute("data-source-id");
      if (!confirm("Remove this source from the claim?")) {
        return;
      }
      const response = await fetch("/claims/" + cId + "/sources/" + sId, {
        method: "DELETE"
      });
      if (response.status === 204) {
        logResearchEvent("SOURCE_DETACHED_FROM_CLAIM", {
          claim_id: cId,
          source_id: sId
        });
        loadSourcesForClaim(cId);
      } else {
        const data = await response.json();
        alert(data.detail || "Could not remove source.");
      }
    });
  });

  const toggleBtn = container.querySelector("[data-action='toggle-new-source']");
  if (toggleBtn) {
    toggleBtn.addEventListener("click", function () {
      const newFields = document.getElementById("new-source-" + claimId);
      newFields.classList.toggle("hidden");
    });
  }

  const attachBtn = container.querySelector("[data-action='attach-source']");
  if (attachBtn) {
    attachBtn.addEventListener("click", async function () {
      const errorEl = document.getElementById("source-error-" + claimId);
      errorEl.textContent = "";

      const existingSelect = container.querySelector("[data-field='existing-source']");
      const relType = container.querySelector("[data-field='relationship-type']").value;
      const excerpt = container.querySelector("[data-field='excerpt']").value.trim();

      let sourceId = existingSelect.value ? parseInt(existingSelect.value, 10) : null;

      if (!sourceId) {
        const title = container.querySelector("[data-field='new-title']").value.trim();
        if (!title) {
          errorEl.textContent = "Select an existing source or enter a title for a new one.";
          return;
        }
        const url = container.querySelector("[data-field='new-url']").value.trim();
        const publisher = container.querySelector("[data-field='new-publisher']").value.trim();
        const sourceType = container.querySelector("[data-field='new-source-type']").value;

        const createResponse = await fetch("/research-sources", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            title: title,
            url: url || null,
            publisher: publisher || null,
            source_type: sourceType
          })
        });
        const createdSource = await createResponse.json();
        if (!createResponse.ok) {
          errorEl.textContent = createdSource.detail || "Could not create source.";
          return;
        }
        logResearchEvent("SOURCE_CREATED", { source: createdSource });
        allSources.push(createdSource);
        sourceId = createdSource.id;
      }

      const attachResponse = await fetch("/claims/" + claimId + "/sources", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source_id: sourceId,
          relationship_type: relType,
          excerpt: excerpt || null
        })
      });
      const attachData = await attachResponse.json();
      if (!attachResponse.ok) {
        errorEl.textContent = attachData.detail || "Could not attach source.";
        return;
      }
      logResearchEvent("SOURCE_ATTACHED_TO_CLAIM", {
        claim_id: claimId,
        claim_source: attachData
      });
      loadSourcesForClaim(claimId);
    });
  }
}

function renderChallenges(challenges) {
  const container = document.getElementById("ws-challenges");
  if (challenges.length === 0) {
    container.innerHTML = "<p>No challenges generated yet.</p>";
    return;
  }
  container.innerHTML = "";
  challenges.forEach(function (challenge) {
    const div = document.createElement("div");
    div.className = "challenge-card";
    div.innerHTML =
      "<div class=\"category\">" + challenge.category.replace(/_/g, " ") + "</div>" +
      "<div>" + challenge.text + "</div>" +
      "<div class=\"claim-refs\">References claim IDs: " + challenge.claim_ids.join(", ") + "</div>";
    container.appendChild(div);
  });
}

document.getElementById("btn-challenge").addEventListener("click", async function () {
  const errorEl = document.getElementById("challenge-error");
  errorEl.textContent = "";
  this.disabled = true;
  this.textContent = "Challenging...";

  logResearchEvent("CHALLENGE_REQUESTED", { research_case_id: caseId });

  try {
    const response = await fetch("/research-cases/" + caseId + "/challenge", {
      method: "POST"
    });
    const data = await response.json();

    if (!response.ok) {
      errorEl.textContent = data.detail || "Something went wrong.";
      return;
    }

    logResearchEvent("CHALLENGE_COMPLETED", { challenges: data });
    renderChallenges(data);
  } catch (err) {
    errorEl.textContent = "Network error: " + err.message;
  } finally {
    this.disabled = false;
    this.textContent = "Challenge My Reasoning";
  }
});

loadWorkspace();