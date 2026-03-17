(function () {
  const shell = document.getElementById('result-shell');
  if (!shell) return;

  const sessionId = shell.dataset.sessionId || sessionStorage.getItem('emb_session_id');
  if (!sessionId) {
    window.location.href = '/';
    return;
  }

  const els = {
    title: document.getElementById('ending-title'),
    score: document.getElementById('final-score'),
    desc: document.getElementById('ending-description'),
    stats: document.getElementById('stats-list'),
    achievements: document.getElementById('achievements-list'),
    shareBtn: document.getElementById('share-btn'),
  };

  let shareText = 'Embarrassment Simulator';

  function renderStats(stats) {
    const rows = [
      `Confidence: ${stats.confidence_final}`,
      `Awkwardness: ${stats.awkwardness_final}`,
      `Scenarios completed: ${stats.scenarios_completed}`,
      `Time taken: ${stats.time_taken}`,
      `Worst moment: ${stats.worst_moment || 'N/A'}`,
      `Witnesses traumatized: ${stats.witnesses_traumatized}`,
    ];
    els.stats.innerHTML = rows.map((line) => `<li>${line}</li>`).join('');
  }

  function renderAchievements(achievements) {
    if (!achievements.length) {
      els.achievements.innerHTML = '<li>No achievements this run.</li>';
      return;
    }
    els.achievements.innerHTML = achievements
      .map((item) => `<li>${item.badge} ${item.name}</li>`)
      .join('');
  }

  async function loadResult() {
    try {
      const payload = await apiResult(sessionId);
      els.title.textContent = payload.ending_title;
      els.score.textContent = payload.final_score;
      els.desc.textContent = payload.ending_description;
      renderStats(payload.stats);
      renderAchievements(payload.achievements);
      shareText = `${payload.share_card.title} - ${payload.share_card.subtitle}`;
      sessionStorage.removeItem('emb_session_id');
      sessionStorage.removeItem('emb_bootstrap');
    } catch (err) {
      alert(err.message || 'Failed to load result');
    }
  }

  els.shareBtn.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(shareText);
      els.shareBtn.textContent = 'Copied';
      setTimeout(() => {
        els.shareBtn.textContent = 'Copy Share Text';
      }, 1000);
    } catch {
      alert(shareText);
    }
  });

  loadResult();
})();
