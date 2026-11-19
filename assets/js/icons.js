/*
 * Bibliothèque d'icônes de la formation (pictogrammes neutres, trait régulier).
 * Chaque icône est dessinée dans une grille 24×24, sans remplissage, trait en currentColor.
 * Source unique : ce fichier alimente les decks (via deck.js / pipeline.js)
 * et génère le sprite assets/icons.svg (node scripts/build-icons.js).
 */
(function (root) {
  const ICONS = {
    database:  '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
    model:     '<circle cx="12" cy="5" r="2.2"/><circle cx="5" cy="19" r="2.2"/><circle cx="19" cy="19" r="2.2"/><circle cx="12" cy="13" r="2.2"/><path d="M12 7.2v3.6M10.4 14.6l-4 2.8M13.6 14.6l4 2.8"/>',
    code:      '<path d="m8 7-5 5 5 5M16 7l5 5-5 5M14 4l-4 16"/>',
    notebook:  '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 3v18M12 8h5M12 12h5"/>',
    file:      '<path d="M6 2h8l5 5v15H6Z"/><path d="M14 2v5h5M9 13h6M9 17h6"/>',
    terminal:  '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="m7 9 3 3-3 3M12 15h5"/>',
    server:    '<rect x="3" y="4" width="18" height="6" rx="1.5"/><rect x="3" y="14" width="18" height="6" rx="1.5"/><path d="M7 7h.01M7 17h.01"/>',
    api:       '<path d="M4 12h5M15 12h5"/><rect x="9" y="8" width="6" height="8" rx="1.5"/><path d="M4 8v8M20 8v8"/>',
    browser:   '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M7 6.5h.01M10 6.5h.01"/>',
    user:      '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 3.6-7 8-7s8 3 8 7"/>',
    cloud:     '<path d="M7 18a4 4 0 0 1-.6-7.95A6 6 0 0 1 18 9a4.5 4.5 0 0 1-.5 9H7Z"/>',
    container: '<path d="M12 2 3 7v10l9 5 9-5V7l-9-5Z"/><path d="M3 7l9 5 9-5M12 12v10"/>',
    layers:    '<path d="m12 3 9 5-9 5-9-5 9-5Z"/><path d="m3 13 9 5 9-5M3 17l9 5 9-5"/>',
    rocket:    '<path d="M14 3c3 0 7 1 7 7-3 3-6 6-9 7l-4-4c1-3 3-7 6-10Z"/><path d="M8 13l-4 1 3-5M11 16l-1 4 5-3"/><circle cx="15" cy="9" r="1.5"/>',
    deploy:    '<path d="M12 16V4M6 10l6-6 6 6M4 20h16"/>',
    lock:      '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    key:       '<circle cx="8" cy="15" r="4"/><path d="M11 12 20 3M16 7l3 3M14 9l2 2"/>',
    gear:      '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1 7 17M17 7l2.1-2.1"/>',
    chart:     '<path d="M3 21h18M6 17v-6M11 17V7M16 17v-3"/>',
    branch:    '<circle cx="6" cy="5" r="2.2"/><circle cx="6" cy="19" r="2.2"/><circle cx="18" cy="8" r="2.2"/><path d="M6 7.2v9.6M18 10.2c0 4-4 5-8 5.5"/>',
    check:     '<path d="m5 12 5 5L20 7"/>',
    cross:     '<path d="M6 6l12 12M18 6 6 18"/>',
    play:      '<path d="M7 4v16l13-8Z"/>',
    globe:     '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
    clock:     '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    flask:     '<path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 1.7 3h10.6A2 2 0 0 0 19 18l-5-9V3"/><path d="M7.5 15h9"/>',
    sparkle:   '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3Z"/><path d="M19 16l.8 2.2L22 19l-2.2.8L19 22l-.8-2.2L16 19l2.2-.8L19 16Z"/>',
    shield:    '<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6l-8-3Z"/><path d="m9 12 2 2 4-4"/>',
    eye:       '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>',
    coins:     '<circle cx="9" cy="9" r="6"/><path d="M15.5 7.5A6 6 0 1 1 7.5 15.5"/>',
    list:      '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
    package:   '<path d="M20 7 12 3 4 7v10l8 4 8-4V7Z"/><path d="M4 7l8 4 8-4M12 11v10M8 5l8 4"/>',
    tag:       '<path d="M3 3h8l10 10-8 8L3 11V3Z"/><path d="M7.5 7.5h.01"/>',
    refresh:   '<path d="M20 11a8 8 0 0 0-14.5-4.5L3 9M4 13a8 8 0 0 0 14.5 4.5L21 15"/><path d="M3 4v5h5M21 20v-5h-5"/>',
    warning:   '<path d="M12 3 2 20h20L12 3Z"/><path d="M12 10v4M12 17h.01"/>',
    star:      '<path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2L12 17.3 6.4 20.2l1.1-6.2L3 9.6l6.2-.9L12 3Z"/>',
    arrow:     '<path d="M4 12h16M14 6l6 6-6 6"/>',
  };

  const ATTRS = 'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"';

  /** Balise <svg> inline prête à insérer dans du HTML. */
  function svg(name, cls) {
    const body = ICONS[name] || ICONS.gear;
    return '<svg class="icon ' + (cls || '') + '" ' + ATTRS + ' aria-hidden="true">' + body + '</svg>';
  }

  /** Sprite <symbol> complet, pour injection dans le document ou génération du fichier icons.svg. */
  function sprite() {
    return Object.keys(ICONS).map(function (k) {
      return '<symbol id="icon-' + k + '" ' + ATTRS + '>' + ICONS[k] + '</symbol>';
    }).join('\n');
  }

  const api = { ICONS: ICONS, ATTRS: ATTRS, svg: svg, sprite: sprite };
  root.CEAM_ICONS = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
