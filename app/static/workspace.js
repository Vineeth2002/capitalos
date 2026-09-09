const caseId = document.querySelector(".container").getAttribute("data-case-id");

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

    const claimsResponse = await fetch("/research-cases/" + caseId + "/claims");
    const claims = await claimsResponse.json();
    renderClaims(claims);

    const challengesResponse = await fetch("/research-cases/" + caseId + "/challenges");
    const challenges = await challengesResponse.json();
    renderChallenges(challenges);
  } catch (err) {
    document.getElementById("ws-title").textContent = "Failed to load workspace";
  }
}

function renderClaims(claims) {
  const container = document.getElementById("ws-claims");
  if (claims.length === 0) {
    container.innerHTML = "<p>No claims yet.</p>";
    return;
  }
  container.innerHTML = "";
  claims.forEach(function (claim) {
    const div = document.createElement("div");
    div.className = "claim-card";
    div.innerHTML =
      "<div>" + claim.statement + "</div>" +
      "<div class=\"reason\">" +
      claim.temporal_orientation + " / " + claim.epistemic_role + " / " + claim.shape +
      " (origin: " + claim.origin + ")</div>";
    container.appendChild(div);
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