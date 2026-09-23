// Optional enhancement: the ordinary DOM is complete before motion initializes.
const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
const storageKey = 'agtxiv.workspace.motion';
let explicitlyOff = false;
try { explicitlyOff = localStorage.getItem(storageKey) === 'off'; } catch { /* Private browsing. */ }
let grid = null;
let gridGeneration = 0;
let entrance = null;
const contexts = new Set();
export const motionEnabled = () => !explicitlyOff && !preference.matches;

export function enter(elements) {
  if (!motionEnabled() || !window.gsap) return;
  const targets = Array.from(elements).filter(Boolean);
  if (!targets.length) return;
  const tween = window.gsap.fromTo(targets, { opacity: 0, y: 9 }, {
    opacity: 1, y: 0, duration: .38, stagger: .035, ease: 'power2.out',
    clearProps: 'opacity,transform', overwrite: true,
    onComplete: () => contexts.delete(tween),
    onInterrupt: () => contexts.delete(tween),
  });
  contexts.add(tween);
}

export function destroyGrid() {
  gridGeneration += 1;
  grid?.destroy();
  grid = null;
  document.querySelectorAll('.map-canvas-output, .map-canvas-source').forEach(node => node.remove());
}

export async function enhanceMap(area) {
  destroyGrid();
  if (!area || !motionEnabled() || !window.matchMedia('(hover: hover) and (pointer: fine)').matches) return;
  const generation = gridGeneration;
  try {
    const { createGrid, supportsHtmlInCanvas } = await import('./vendor/canvas-ui/grid.js');
    if (generation !== gridGeneration || !area.isConnected || !motionEnabled()) return;
    const source = document.createElement('canvas');
    source.className = 'map-canvas-source';
    source.setAttribute('aria-hidden', 'true');
    const output = document.createElement('canvas');
    output.className = 'map-canvas-output';
    output.setAttribute('aria-hidden', 'true');
    let content = area;
    if (supportsHtmlInCanvas()) {
      source.setAttribute('layoutsubtree', '');
      content = document.createElement('div');
      content.className = 'map-canvas-content';
      source.append(content);
    }
    area.append(source, output);
    grid = createGrid({ source, output, content }, {
      tileSize: 48, gap: .3, amplitude: .35, maxLift: .16,
      liftHeight: 9, perspective: 1800, tilt: .08, shading: .045,
      tint: [.34, .47, .26], tintStrength: .08,
      fadeTime: .3, waveWidth: .13, idleRipples: 0,
    });
    if (!grid) { source.remove(); output.remove(); }
    output.addEventListener('webglcontextlost', event => {
      event.preventDefault();
      destroyGrid();
    }, { once: true });
  } catch {
    // WebGL or enhancement failure never removes the HTML graph or its controls.
    destroyGrid();
  }
}

export function initializeMotion(onChange) {
  const button = document.querySelector('#motion-toggle');
  function sync() {
    const enabled = motionEnabled();
    document.body.dataset.motion = enabled ? 'on' : 'off';
    button.setAttribute('aria-pressed', String(!enabled));
    button.setAttribute('aria-label', preference.matches ? 'Reduced motion is enabled in system settings' : enabled ? 'Turn off motion' : 'Turn on motion');
    button.title = preference.matches ? 'Following the system reduced-motion preference' : enabled ? 'Turn off motion' : 'Turn on motion';
    if (!enabled) {
      entrance?.revert();
      contexts.forEach(tween => tween.progress(1));
      contexts.clear();
      destroyGrid();
    }
    onChange?.();
  }
  button.addEventListener('click', () => {
    if (preference.matches) {
      document.querySelector('#announcement').textContent = 'Motion follows your system reduced-motion preference.';
      return;
    }
    explicitlyOff = !explicitlyOff;
    try { localStorage.setItem(storageKey, explicitlyOff ? 'off' : 'on'); } catch { /* Optional preference. */ }
    sync();
  });
  preference.addEventListener('change', sync);
  sync();
  // GSAP's matchMedia reverts entrances if the system preference changes.
  if (window.gsap && !explicitlyOff) {
    entrance = window.gsap.matchMedia();
    entrance.add('(prefers-reduced-motion: no-preference)', () => {
      if (explicitlyOff) return;
      window.gsap.from('[data-reveal]', { opacity: 0, y: 15, duration: .7, stagger: .09, ease: 'power2.out', clearProps: 'opacity,transform' });
      window.gsap.from('.art-trace', { strokeDasharray: '450', strokeDashoffset: 450, duration: 1.3, delay: .15, ease: 'power2.out', clearProps: 'all' });
    });
  }
  // No background GPU work when the tab is hidden, including bfcache navigation.
  const visibility = () => { if (document.hidden) destroyGrid(); else onChange?.(); };
  document.addEventListener('visibilitychange', visibility);
  window.addEventListener('pagehide', () => {
    destroyGrid();
    contexts.forEach(tween => tween.progress(1));
    contexts.clear();
    entrance?.revert();
  });
  window.addEventListener('pageshow', event => { if (event.persisted) sync(); });
}
