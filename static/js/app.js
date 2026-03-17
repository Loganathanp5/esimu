(function () {
  const sessionId = sessionStorage.getItem('emb_session_id');
  const bootstrapRaw = sessionStorage.getItem('emb_bootstrap');

  if (!sessionId || !bootstrapRaw) {
    window.location.href = '/';
    return;
  }

  let bootstrap;
  try {
    bootstrap = JSON.parse(bootstrapRaw);
  } catch (e) {
    window.location.href = '/';
    return;
  }

  const els = {
    progressLabel: document.getElementById('progress-label'),
    progressFill: document.getElementById('progress-fill'),
    timerPill: document.getElementById('timer-pill'),
    context: document.getElementById('scenario-context'),
    title: document.getElementById('scenario-title'),
    desc: document.getElementById('scenario-description'),
    choices: document.getElementById('choices'),
    outcomeBox: document.getElementById('outcome-box'),
    outcomeText: document.getElementById('outcome-text'),
    monologue: document.getElementById('inner-monologue'),
    witness: document.getElementById('witness-reaction'),
    continueBtn: document.getElementById('continue-btn'),
    confidenceValue: document.getElementById('confidence-value'),
    awkwardnessValue: document.getElementById('awkwardness-value'),
    embValue: document.getElementById('emb-value'),
    confidenceBar: document.getElementById('confidence-bar'),
    awkwardnessBar: document.getElementById('awkwardness-bar'),
    embBar: document.getElementById('emb-bar'),
    gameShell: document.getElementById('game-shell'),
  };

  const state = {
    sessionId,
    scenario: bootstrap.scenario,
    progress: bootstrap.progress,
    confidence: bootstrap.confidence,
    awkwardness: bootstrap.awkwardness,
    timerMode: Boolean(bootstrap.timer_mode),
    timerValue: 30,
    timerHandle: null,
    pendingNextScenario: null,
  };

  function calcEmb() {
    return state.awkwardness + (100 - state.confidence);
  }

  function updateMeters() {
    const emb = calcEmb();
    els.confidenceValue.textContent = state.confidence;
    els.awkwardnessValue.textContent = state.awkwardness;
    els.embValue.textContent = emb;

    els.confidenceBar.style.width = `${state.confidence}%`;
    els.awkwardnessBar.style.width = `${state.awkwardness}%`;
    els.embBar.style.width = `${Math.max(0, Math.min(100, emb))}%`;

    if (emb > 80) {
      els.gameShell.classList.add('shake');
      setTimeout(() => els.gameShell.classList.remove('shake'), 250);
    }
  }

  function updateProgress() {
    const pct = Math.round((state.progress.current / state.progress.total) * 100);
    els.progressLabel.textContent = `Progress ${state.progress.current}/${state.progress.total}`;
    els.progressFill.style.width = `${pct}%`;
  }

  function clearTimer() {
    if (state.timerHandle) {
      clearInterval(state.timerHandle);
      state.timerHandle = null;
    }
  }

  function startTimer() {
    clearTimer();
    if (!state.timerMode) {
      els.timerPill.classList.add('hidden');
      return;
    }

    els.timerPill.classList.remove('hidden');
    state.timerValue = 30;
    els.timerPill.textContent = `${state.timerValue}s`;

    state.timerHandle = setInterval(() => {
      state.timerValue -= 1;
      els.timerPill.textContent = `${state.timerValue}s`;
      if (state.timerValue <= 0) {
        clearTimer();
        autoPickChoice();
      }
    }, 1000);
  }

  function renderScenario() {
    if (!state.scenario) return;

    els.outcomeBox.classList.add('hidden');
    els.choices.classList.remove('hidden');

    els.context.textContent = `${state.scenario.location_name} - ${state.scenario.context_detail}`;
    els.title.textContent = state.scenario.title;
    els.desc.textContent = state.scenario.description;

    els.choices.innerHTML = '';
    state.scenario.choices.forEach((choice) => {
      const button = document.createElement('button');
      button.className = 'btn choice-btn';
      button.textContent = `${choice.emoji_hint} ${choice.text}`;
      button.addEventListener('click', () => choose(choice.id));
      els.choices.appendChild(button);
    });

    updateProgress();
    updateMeters();
    startTimer();
  }

  async function choose(choiceId) {
    clearTimer();
    disableChoices(true);
    try {
      const payload = await apiChoose({ session_id: state.sessionId, choice_id: choiceId });
      state.confidence = payload.updated_scores.confidence;
      state.awkwardness = payload.updated_scores.awkwardness;
      state.progress = payload.progress;
      state.pendingNextScenario = payload.next_scenario;

      els.outcomeText.textContent = payload.outcome_text;
      els.monologue.textContent = payload.inner_monologue;
      els.witness.textContent = payload.witness_reaction;
      els.outcomeBox.classList.remove('hidden');
      els.choices.classList.add('hidden');
      updateMeters();

      if (payload.is_completed) {
        sessionStorage.removeItem('emb_bootstrap');
        window.location.href = payload.result_url || `/result/${state.sessionId}/`;
      }
    } catch (err) {
      alert(err.message || 'Choice failed');
      disableChoices(false);
      startTimer();
    }
  }

  function autoPickChoice() {
    const options = Array.from(els.choices.querySelectorAll('button'));
    if (!options.length) return;
    const random = options[Math.floor(Math.random() * options.length)];
    random.click();
  }

  function disableChoices(disabled) {
    els.choices.querySelectorAll('button').forEach((button) => {
      button.disabled = disabled;
    });
  }

  els.continueBtn.addEventListener('click', () => {
    if (!state.pendingNextScenario) {
      window.location.href = `/result/${state.sessionId}/`;
      return;
    }
    state.scenario = state.pendingNextScenario;
    state.pendingNextScenario = null;
    disableChoices(false);
    renderScenario();
  });

  renderScenario();
})();
