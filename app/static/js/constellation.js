(() => {
  const STAGE_WIDTH = 920;
  const STAGE_HEIGHT = 520;
  const ANCHORS = Object.freeze({
    tracksense: Object.freeze({ x: 225, y: 145 }),
    forebid: Object.freeze({ x: 700, y: 145 }),
    "engram-pipeline": Object.freeze({ x: 690, y: 378 }),
  });

  const root = document.querySelector("[data-constellation]");
  if (!root) return;

  const stage = root.querySelector(".constellation__stage");
  const items = Array.from(root.querySelectorAll("[data-node]"))
    .map((node) => {
      const key = node.dataset.node;
      return {
        key,
        node,
        path: root.querySelector(`[data-path="${key}"]`),
        concept: root.querySelector(`[data-concept="${key}"]`),
        anchor: ANCHORS[key],
      };
    })
    .filter((item) => item.anchor);

  const setActive = ({ node, path, concept }, active) => {
    node.dataset.active = String(active);
    if (path) path.dataset.active = String(active);
    if (concept) concept.dataset.active = String(active);
  };

  let focusedItem = null;
  let requestRender = () => {};

  items.forEach((item) => {
    item.node.addEventListener("focus", () => {
      focusedItem = item;
      setActive(item, true);
      requestRender();
    });
    item.node.addEventListener("blur", () => {
      focusedItem = null;
      setActive(item, false);
      requestRender();
    });
  });

  const reducedMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)"
  ).matches;
  const coarsePointer = window.matchMedia("(pointer: coarse)").matches;
  const saveData = navigator.connection && navigator.connection.saveData;
  const motionAllowed =
    stage && items.length && !reducedMotion && !coarsePointer && !saveData;
  if (!motionAllowed) return;

  const pointer = { x: 0, y: 0, active: false };
  let anchorCenters = [];
  let renderFrame = 0;
  let layoutFrame = 0;

  const refreshAnchors = () => {
    const bounds = stage.getBoundingClientRect();
    if (!bounds.width || !bounds.height) {
      anchorCenters = [];
      return;
    }

    const scaleX = bounds.width / STAGE_WIDTH;
    const scaleY = bounds.height / STAGE_HEIGHT;
    anchorCenters = items.map((item) => ({
      item,
      x: bounds.left + item.anchor.x * scaleX,
      y: bounds.top + item.anchor.y * scaleY,
    }));
  };

  const render = () => {
    let nearest = null;
    let nearestDistance = Number.POSITIVE_INFINITY;

    if (pointer.active) {
      anchorCenters.forEach((candidate) => {
        const distance = Math.hypot(
          pointer.x - candidate.x,
          pointer.y - candidate.y
        );
        if (distance < nearestDistance) {
          nearest = candidate;
          nearestDistance = distance;
        }
      });
    }

    const pointerTarget = nearestDistance < 220 ? nearest : null;
    items.forEach((item) => {
      const candidate = pointerTarget && pointerTarget.item === item;
      const active = Boolean(item === focusedItem || candidate);
      let moveX = 0;
      let moveY = 0;

      if (candidate) {
        const strength = Math.max(0, 1 - nearestDistance / 220);
        const dx = pointer.x - pointerTarget.x;
        const dy = pointer.y - pointerTarget.y;
        moveX = Math.max(-12, Math.min(12, dx * strength * 0.08));
        moveY = Math.max(-12, Math.min(12, dy * strength * 0.08));
      }

      // CSS applies translate3d from these custom properties.
      item.node.style.setProperty("--node-x", `${moveX}px`);
      item.node.style.setProperty("--node-y", `${moveY}px`);
      setActive(item, active);
    });

    renderFrame = 0;
  };

  requestRender = () => {
    if (!renderFrame) renderFrame = requestAnimationFrame(render);
  };

  const requestLayoutRefresh = () => {
    if (layoutFrame) return;
    layoutFrame = requestAnimationFrame(() => {
      refreshAnchors();
      layoutFrame = 0;
      requestRender();
    });
  };

  stage.addEventListener(
    "pointermove",
    (event) => {
      pointer.x = event.clientX;
      pointer.y = event.clientY;
      pointer.active = true;
      requestRender();
    },
    { passive: true }
  );

  stage.addEventListener("pointerleave", () => {
    pointer.active = false;
    requestRender();
  });

  window.addEventListener("resize", requestLayoutRefresh, { passive: true });
  window.addEventListener("scroll", requestLayoutRefresh, { passive: true });
  if ("ResizeObserver" in window) {
    new ResizeObserver(requestLayoutRefresh).observe(stage);
  }

  refreshAnchors();
})();
