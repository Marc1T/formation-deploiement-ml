/*
 * Initialisation commune des decks de la formation.
 * Charge après : reveal.js, les plugins, icons.js et pipeline.js.
 *
 * Fonctions :
 *  - injecte le sprite d'icônes et remplace <i data-icon="cloud"></i> par le SVG inline ;
 *  - construit les composants .pipeline ;
 *  - bascule clair / sombre (touche D, bouton en bas à droite, mémorisée dans le navigateur) ;
 *  - minuteur des diapos de lab : <section class="lab" data-minutes="25"> (touche T) ;
 *  - configure reveal.js (16:9, numéros, notes, zoom, recherche, coloration syntaxique).
 */
(function () {
  const SVG_NS = 'http://www.w3.org/2000/svg';

  // --- Icônes ---------------------------------------------------------------
  function injectIcons() {
    const holder = document.createElementNS(SVG_NS, 'svg');
    holder.setAttribute('style', 'display:none');
    holder.setAttribute('aria-hidden', 'true');
    holder.innerHTML = window.CEAM_ICONS.sprite();
    document.body.prepend(holder);
    document.querySelectorAll('[data-icon]').forEach(function (e) {
      e.innerHTML = window.CEAM_ICONS.svg(e.dataset.icon);
    });
  }

  // --- Thème ----------------------------------------------------------------
  const THEME_KEY = 'ceam-deck-theme';
  function applyTheme(t) {
    if (t) document.documentElement.setAttribute('data-theme', t);
    else document.documentElement.removeAttribute('data-theme');
  }
  function currentTheme() {
    const forced = document.documentElement.getAttribute('data-theme');
    if (forced) return forced;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  function toggleTheme() {
    const next = currentTheme() === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    try { localStorage.setItem(THEME_KEY, next); } catch (e) { /* stockage indisponible */ }
  }
  function initTheme() {
    let saved = null;
    try { saved = localStorage.getItem(THEME_KEY); } catch (e) { /* ignore */ }
    // ?ceamTheme=light ou ?ceamTheme=dark force le thème (export PDF, captures) ; sinon préférence mémorisée.
    // reveal.js lit tous les paramètres de l'URL comme des options et son mode d'impression (?print-pdf)
    // ne supporte pas de paramètre supplémentaire : on retire le nôtre de l'URL avant l'initialisation.
    const params = new URLSearchParams(window.location.search);
    const forced = params.get('ceamTheme');
    if (forced === 'dark' || forced === 'light') {
      saved = forced;
      params.delete('ceamTheme');
      const query = params.toString().replace(/=(&|$)/g, '$1'); // print-pdf= -> print-pdf
      try {
        window.history.replaceState(null, '', window.location.pathname + (query ? '?' + query : '') + window.location.hash);
      } catch (e) { /* URL non modifiable : on garde le thème, reveal fera au mieux */ }
    }
    if (saved === 'dark' || saved === 'light') applyTheme(saved);
    const btn = document.createElement('button');
    btn.className = 'theme-toggle';
    btn.type = 'button';
    btn.title = 'Basculer clair / sombre (touche D)';
    btn.setAttribute('aria-label', 'Basculer le thème clair ou sombre');
    btn.innerHTML = window.CEAM_ICONS.svg('eye');
    btn.addEventListener('click', toggleTheme);
    document.body.appendChild(btn);
  }

  // --- Minuteur des labs ----------------------------------------------------
  const timers = new Map();
  function fmt(s) {
    const m = Math.floor(s / 60), r = s % 60;
    return (m < 10 ? '0' : '') + m + ':' + (r < 10 ? '0' : '') + r;
  }
  function initLabTimers() {
    document.querySelectorAll('section.lab[data-minutes]').forEach(function (sec) {
      const total = parseInt(sec.dataset.minutes, 10) * 60;
      const box = document.createElement('div');
      box.className = 'lab-timer';
      box.innerHTML = window.CEAM_ICONS.svg('clock') + '<span class="time">' + fmt(total) + '</span><button type="button">Démarrer (T)</button>';
      sec.appendChild(box);
      const state = { left: total, total: total, handle: null, box: box };
      timers.set(sec, state);
      box.querySelector('button').addEventListener('click', function () { toggleTimer(sec); });
    });
  }
  function toggleTimer(sec) {
    sec = sec || Reveal.getCurrentSlide();
    const st = timers.get(sec);
    if (!st) return;
    const label = st.box.querySelector('.time');
    const btn = st.box.querySelector('button');
    if (st.handle) {
      clearInterval(st.handle); st.handle = null; btn.textContent = 'Reprendre (T)';
      return;
    }
    if (st.left <= 0) { st.left = st.total; st.box.classList.remove('done'); }
    btn.textContent = 'Pause (T)';
    st.handle = setInterval(function () {
      st.left -= 1;
      label.textContent = fmt(Math.max(st.left, 0));
      if (st.left <= 60) st.box.classList.add('warning');
      if (st.left <= 0) {
        clearInterval(st.handle); st.handle = null;
        st.box.classList.remove('warning'); st.box.classList.add('done');
        btn.textContent = 'Relancer (T)';
      }
    }, 1000);
  }

  // --- Lancement --------------------------------------------------------------
  function start() {
    injectIcons();
    initTheme();
    initLabTimers();
    window.CEAM_PIPELINE.buildAll();

    Reveal.initialize({
      width: 1280,
      height: 720,
      margin: 0.04,
      minScale: 0.2,
      maxScale: 2.0,
      hash: true,
      center: false,
      slideNumber: 'c/t',
      showSlideNumber: 'all',
      progress: true,
      controls: true,
      controlsTutorial: false,
      controlsLayout: 'bottom-right',
      transition: 'slide',
      backgroundTransition: 'fade',
      autoAnimateDuration: 0.7,
      autoAnimateEasing: 'cubic-bezier(.4, 0, .2, 1)',
      pdfSeparateFragments: false,
      pdfMaxPagesPerSlide: 1,
      keyboard: {
        68: toggleTheme,            // D : thème
        84: function () { toggleTimer(); } // T : minuteur du lab affiché
      },
      plugins: [RevealNotes, RevealHighlight, RevealZoom, RevealSearch],
      highlight: { highlightOnLoad: true }
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
