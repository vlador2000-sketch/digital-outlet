/* DiGiTaL OUTLET: local, network-independent fallback for failed game covers. */
(() => {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="480" height="640" viewBox="0 0 480 640">
    <rect width="480" height="640" fill="#071321"/>
    <rect x="18" y="18" width="444" height="604" rx="18" fill="none" stroke="#284a70" stroke-width="4"/>
    <text x="240" y="284" text-anchor="middle" fill="#c4d8ec" font-family="Arial, sans-serif" font-size="34" font-weight="bold">DiGiTaL</text>
    <text x="240" y="334" text-anchor="middle" fill="#c4d8ec" font-family="Arial, sans-serif" font-size="23">Omot trenutno</text>
    <text x="240" y="367" text-anchor="middle" fill="#c4d8ec" font-family="Arial, sans-serif" font-size="23">nije dostupan</text>
  </svg>`;
  const placeholder = 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(svg);

  for (const img of document.querySelectorAll('img.cover')) {
    const showFallback = () => {
      if (img.dataset.coverFallbackApplied === '1') return;
      img.dataset.coverFallbackApplied = '1';
      img.removeAttribute('srcset');
      img.src = placeholder;
    };

    img.addEventListener('error', showFallback);
    // An image may have failed before the handler was attached (e.g. cached failure).
    if (img.complete && img.naturalWidth === 0) showFallback();
  }
})();
