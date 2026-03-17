async function requestJSON(url, options = {}) {
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || 'Request failed');
  }
  return data;
}

async function apiStartGame(payload) {
  return requestJSON('/api/game/start/', {
    method: 'POST',
    body: JSON.stringify(payload || {}),
  });
}

async function apiChoose(payload) {
  return requestJSON('/api/game/choose/', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

async function apiResult(sessionId) {
  return requestJSON(`/api/game/result/${sessionId}/`, {
    method: 'GET',
  });
}
