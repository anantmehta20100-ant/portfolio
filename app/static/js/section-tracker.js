(() => {
  const SECTION_ROUTES = Object.freeze({
    "hero": "/",
    "project-explorer": "/projects",
    "featured-projects": "/projects",
    "experience": "/experience",
    "research": "/research",
    "skills": "/about",
    "leadership": "/about",
    "about": "/about",
    "contact": "/contact",
  });

  const sections = Array.from(
    document.querySelectorAll("[data-home-section]")
  ).filter((section) => SECTION_ROUTES[section.id]);
  const links = Array.from(
    document.querySelectorAll("[data-primary-navigation] a")
  );
  if (!sections.length || !links.length || !("IntersectionObserver" in window)) {
    return;
  }

  const ratios = new Map(sections.map((section) => [section, 0]));
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        ratios.set(
          entry.target,
          entry.isIntersecting ? entry.intersectionRatio : 0
        );
      });

      const visible = sections
        .filter((section) => ratios.get(section) > 0)
        .sort((a, b) => ratios.get(b) - ratios.get(a))[0];
      if (!visible) return;

      const activeRoute = SECTION_ROUTES[visible.id];
      links.forEach((link) => {
        link.removeAttribute("aria-current");
        if (link.getAttribute("href") === activeRoute) {
          link.setAttribute("aria-current", "location");
        }
      });
    },
    { rootMargin: "-25% 0px -60%", threshold: [0, 0.15, 0.5] }
  );

  sections.forEach((section) => observer.observe(section));
})();
