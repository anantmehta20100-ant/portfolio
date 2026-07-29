(() => {
  const reducedMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)"
  ).matches;
  const finePointer = window.matchMedia("(pointer: fine)").matches;
  if (reducedMotion || !finePointer) return;

  const dot = document.createElement("div");
  dot.className = "cursor-dot";
  dot.setAttribute("aria-hidden", "true");

  const ring = document.createElement("div");
  ring.className = "cursor-ring";
  ring.setAttribute("aria-hidden", "true");

  const label = document.createElement("span");
  label.className = "cursor-ring__label";
  ring.appendChild(label);

  document.body.append(dot, ring);
  document.body.dataset.customCursor = "true";

  // dot tracks 1:1; ring eases toward the pointer a frame behind
  let pointerX = window.innerWidth / 2;
  let pointerY = window.innerHeight / 2;
  let ringX = pointerX;
  let ringY = pointerY;
  let frame = 0;

  const onMove = (event) => {
    pointerX = event.clientX;
    pointerY = event.clientY;
    dot.style.transform = `translate(${pointerX}px, ${pointerY}px)`;
    if (!frame) frame = requestAnimationFrame(render);
  };

  const render = () => {
    ringX += (pointerX - ringX) * 0.18;
    ringY += (pointerY - ringY) * 0.18;
    ring.style.transform = `translate(${ringX}px, ${ringY}px)`;
    // keep easing until the ring has settled onto the pointer
    if (Math.abs(pointerX - ringX) > 0.1 || Math.abs(pointerY - ringY) > 0.1) {
      frame = requestAnimationFrame(render);
    } else {
      frame = 0;
    }
  };

  // interactive elements the ring should react to, and the label it shows
  const VIEW_TARGET =
    "a[href^='/projects/'], .constellation__node, .project-preview a, .tag-list";
  const readCue = (element) => {
    const explicit = element.closest("[data-cursor-label]");
    if (explicit) return explicit.dataset.cursorLabel;
    if (element.closest(".constellation__node, a[href^='/projects/'], .project-preview a")) {
      return "View";
    }
    return "";
  };

  const onOver = (event) => {
    const target = event.target.closest(VIEW_TARGET + ", a, button");
    const editable = event.target.closest("input, textarea, [contenteditable]");
    document.body.classList.toggle("cursor-text", Boolean(editable));

    const cue = target ? readCue(target) : "";
    if (cue) {
      label.textContent = cue;
      ring.classList.add("is-view");
    } else {
      ring.classList.remove("is-view");
      ring.classList.toggle("is-active", Boolean(target));
    }
  };

  const onLeaveWindow = () => {
    dot.classList.add("is-hidden");
    ring.classList.add("is-hidden");
  };
  const onEnterWindow = () => {
    dot.classList.remove("is-hidden");
    ring.classList.remove("is-hidden");
  };
  const onDown = () => ring.classList.add("is-press");
  const onUp = () => ring.classList.remove("is-press");

  window.addEventListener("pointermove", onMove, { passive: true });
  window.addEventListener("pointerover", onOver, { passive: true });
  window.addEventListener("pointerdown", onDown, { passive: true });
  window.addEventListener("pointerup", onUp, { passive: true });
  document.addEventListener("mouseleave", onLeaveWindow);
  document.addEventListener("mouseenter", onEnterWindow);
})();
