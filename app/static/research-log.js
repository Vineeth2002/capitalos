function getResearchSessionId() {
  let sessionId = sessionStorage.getItem("capitalos_session_id");
  if (!sessionId) {
    sessionId = "sess-" + Math.random().toString(36).slice(2) + Date.now().toString(36);
    sessionStorage.setItem("capitalos_session_id", sessionId);
  }
  return sessionId;
}

function logResearchEvent(eventType, payload) {
  try {
    fetch("/research-events", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: getResearchSessionId(),
        event_type: eventType,
        payload: payload || {}
      })
    }).catch(function () {});
  } catch (err) {
    // Never let logging break the product experience.
  }
}