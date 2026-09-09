const caseId = document.querySelector(".container").getAttribute("data-case-id");

const TEMPORAL_OPTIONS = ["historical", "current", "forecast"];
const EPISTEMIC_OPTIONS = ["evidence", "interpretation", "assumption", "risk", "hypothesis"];
const SHAPE_OPTIONS = ["quantitative", "qualitative"];

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

    await refreshClaims();

    const challengesResponse = await fetch("/research-cases/" + caseId + "/challenges");
    const challenges = await challengesResponse.json();
    renderChallenges(challenges);
  } catch (err) {
    document.getElementById("ws-title").textContent = "Failed to load workspace";
  }
}

async function refreshClaims() {
  const claimsResponse = await fetch("/research-cases/" + caseId + "/claims");
  const claims = await claimsResponse.json();
  renderClaims(claims);
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
    "</div></div>"
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
          wireEditActions(card, claimId);
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
        await refreshClaims();
      } else {
        const data = await response.json();
        alert(data.detail || "Could not delete claim.");
      }
    });
  });
}

function wireEditActions(card, claimId) {
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

  try {
    const response = await fetch("/research-cases/" + caseId + "/challenge", {
      method: "POST"
    });
    const data = await response.json();

    if (!response.ok) {
      errorEl.textContent = data.detail || "Something went wrong.";
      return;
    }

    renderChallenges(data);
  } catch (err) {
    errorEl.textContent = "Network error: " + err.message;
  } finally {
    this.disabled = false;
    this.textContent = "Challenge My Reasoning";
  }
});

loadWorkspace();