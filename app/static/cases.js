async function loadCases() {
  const container = document.getElementById("case-list");
  try {
    const response = await fetch("/research-cases");
    const cases = await response.json();

    if (cases.length === 0) {
      container.innerHTML = "<p>No Research Cases yet. <a href=\"/\">Start one</a>.</p>";
      return;
    }

    container.innerHTML = "";
    cases.forEach(function (c) {
      const div = document.createElement("div");
      div.className = "claim-card";
      div.innerHTML =
        "<a href=\"/cases/" + c.id + "\"><strong>" + c.title + "</strong></a>" +
        "<div class=\"reason\">" + (c.description || "No description") + "</div>";
      container.appendChild(div);
    });
  } catch (err) {
    container.innerHTML = "<p class=\"error\">Failed to load Research Cases.</p>";
  }
}

loadCases();