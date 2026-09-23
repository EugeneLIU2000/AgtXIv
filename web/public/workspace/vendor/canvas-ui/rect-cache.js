// Local adapter for the shared helper omitted from the Canvas UI registry item.
// Read geometry once per frame; invalidate when the viewport or element changes.
export function createRectCache(element) {
  let rect = null;
  let frame = 0;
  const invalidate = () => { rect = null; };
  const observer = new ResizeObserver(invalidate);
  observer.observe(element);
  window.addEventListener('scroll', invalidate, true);
  window.addEventListener('resize', invalidate);
  return {
    get current() {
      if (!rect) rect = element.getBoundingClientRect();
      if (!frame) frame = requestAnimationFrame(() => { frame = 0; rect = null; });
      return rect;
    },
    destroy() {
      cancelAnimationFrame(frame);
      observer.disconnect();
      window.removeEventListener('scroll', invalidate, true);
      window.removeEventListener('resize', invalidate);
    },
  };
}
