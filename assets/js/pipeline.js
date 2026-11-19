/*
 * Composant « pipeline animé » pour les decks reveal.js.
 *
 * Usage dans une diapo :
 *   <div class="pipeline" data-steps='[
 *     {"label":"Données","sub":"CSV","icon":"database","kind":"data","edge":"features"},
 *     {"label":"Entraînement","sub":"scikit-learn","icon":"model","kind":"code","edge":"model.joblib"},
 *     {"label":"API","icon":"api","kind":"infra","state":"done"}
 *   ]' data-fragments="true" data-start="1"></div>
 *
 * - kind  : data | code | infra | user | ai   (couleur du nœud, tokens --c-*)
 * - state : todo | running | done | error     (pastille d'état, facultatif)
 * - edge  : libellé de la flèche qui part de ce nœud (facultatif)
 * - data-fragments : "true" (défaut) → les étapes apparaissent une par une (fragments reveal.js)
 * - data-start     : nombre de nœuds visibles dès l'affichage (défaut 1)
 * - data-compact   : "true" → nœuds plus petits (jusqu'à 8 étapes)
 */
(function (root) {
  const NS = 'http://www.w3.org/2000/svg';

  function el(tag, attrs, parent) {
    const node = document.createElementNS(NS, tag);
    for (const k in attrs) if (attrs[k] !== undefined && attrs[k] !== null) node.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(node);
    return node;
  }

  function text(parent, x, y, str, cls, anchor) {
    const t = el('text', { x: x, y: y, 'text-anchor': anchor || 'middle', class: cls }, parent);
    t.textContent = str;
    return t;
  }

  function icon(parent, name, x, y, size, cls) {
    const g = el('g', {
      transform: 'translate(' + x + ' ' + y + ') scale(' + (size / 24) + ')',
      class: cls || 'pl-icon',
      fill: 'none', stroke: 'currentColor', 'stroke-width': '1.8',
      'stroke-linecap': 'round', 'stroke-linejoin': 'round'
    }, parent);
    const body = (root.CEAM_ICONS && root.CEAM_ICONS.ICONS[name]) || root.CEAM_ICONS.ICONS.gear;
    g.innerHTML = body;
    return g;
  }

  function build(container) {
    if (container.dataset.built) return;
    let steps;
    try { steps = JSON.parse(container.dataset.steps || '[]'); } catch (e) { console.error('pipeline: JSON invalide', e); return; }
    const n = steps.length;
    if (!n) return;

    const useFragments = container.dataset.fragments !== 'false';
    const start = Math.max(1, parseInt(container.dataset.start || '1', 10));
    const compact = container.dataset.compact === 'true';

    const W = 1200;
    const colW = W / n;
    const nodeW = Math.min(compact ? 150 : 190, colW - 34);
    const nodeH = compact ? 84 : 100;
    const top = 44;                   // place pour le libellé des flèches
    const subH = 34;                  // place pour le sous-titre sous le nœud
    const H = top + nodeH + subH + 8;
    const uid = 'pl' + Math.random().toString(36).slice(2, 7);

    const svg = el('svg', { viewBox: '0 0 ' + W + ' ' + H, class: 'pl', role: 'img', 'aria-label': steps.map(function (s) { return s.label; }).join(' → ') });
    const defs = el('defs', {}, svg);
    const marker = el('marker', { id: uid + '-arrow', viewBox: '0 0 10 10', refX: '9', refY: '5', markerWidth: '7', markerHeight: '7', orient: 'auto-start-reverse' }, defs);
    el('path', { d: 'M0 0 L10 5 L0 10 z', class: 'pl-arrow' }, marker);

    const centers = steps.map(function (_, i) { return colW * i + colW / 2; });
    let fragIndex = 0;

    steps.forEach(function (s, i) {
      const cx = centers[i];
      const x = cx - nodeW / 2;
      const y = top;
      const kind = s.kind || 'code';
      const visibleAtStart = i < start;
      const frag = useFragments && !visibleAtStart;
      if (frag) fragIndex += 1;

      // Flèche depuis le nœud précédent
      if (i > 0) {
        const x1 = centers[i - 1] + nodeW / 2 + 4;
        const x2 = x - 6;
        const ym = y + nodeH / 2;
        const eg = el('g', { class: 'pl-edge' + (frag ? ' fragment' : ''), 'data-fragment-index': frag ? fragIndex : null }, svg);
        el('line', { x1: x1, y1: ym, x2: x2, y2: ym, class: 'pl-line-bg' }, eg);
        el('line', { x1: x1, y1: ym, x2: x2, y2: ym, class: 'pl-line', 'marker-end': 'url(#' + uid + '-arrow)' }, eg);
        const lbl = steps[i - 1].edge;
        // Libellé au-dessus de la rangée (l'espace entre deux nœuds est trop étroit pour le texte)
        if (lbl) text(eg, (x1 + x2) / 2, top - 14, lbl, 'pl-edge-label');
      }

      // Nœud
      const g = el('g', { class: 'pl-node' + (frag ? ' fragment' : ''), 'data-kind': kind, 'data-state': s.state || '', 'data-fragment-index': frag ? fragIndex : null }, svg);
      el('rect', { x: x - 5, y: y - 5, width: nodeW + 10, height: nodeH + 10, rx: 20, class: 'pl-ring' }, g);
      el('rect', { x: x, y: y, width: nodeW, height: nodeH, rx: 16, class: 'pl-box' }, g);
      const iconSize = compact ? 28 : 32;
      icon(g, s.icon || 'gear', cx - iconSize / 2, y + 12, iconSize, 'pl-icon');
      text(g, cx, y + nodeH - 20, s.label, 'pl-label');
      if (s.sub) text(g, cx, y + nodeH + 24, s.sub, 'pl-sub');

      // Pastille d'état
      if (s.state && s.state !== 'todo') {
        const bx = x + nodeW - 4, by = y + 4;
        const badge = el('g', { class: 'pl-badge', 'data-state': s.state }, g);
        el('circle', { cx: bx, cy: by, r: 12 }, badge);
        if (s.state === 'done') icon(badge, 'check', bx - 8, by - 8, 16, 'pl-badge-icon');
        else if (s.state === 'error') icon(badge, 'cross', bx - 8, by - 8, 16, 'pl-badge-icon');
        else if (s.state === 'running') el('circle', { cx: bx, cy: by, r: 5, class: 'pl-badge-dot' }, badge);
      }
    });

    if (useFragments && n > start) svg.classList.add('has-fragments');
    container.appendChild(svg);
    container.dataset.built = '1';
  }

  function buildAll(scope) {
    (scope || document).querySelectorAll('.pipeline').forEach(build);
  }

  root.CEAM_PIPELINE = { build: build, buildAll: buildAll };
})(typeof window !== 'undefined' ? window : globalThis);
