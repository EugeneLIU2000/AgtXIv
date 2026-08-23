(() => {
  const maps = {
    literature: {
      index: "01",
      kicker: "Trace the source",
      title: "Literature map",
      description: "Follow a scientific claim back to frozen source occurrences and explicit provenance—not a citation-shaped shortcut.",
      status: "PREVIEW · SOURCE PATHS"
    },
    claim: {
      index: "02",
      kicker: "Resolve the dependency",
      title: "Claim map",
      description: "Inspect a candidate query-relative closure of load-bearing claims while keeping every relation typed and reviewable.",
      status: "ORACLE CANDIDATE"
    },
    contract: {
      index: "03",
      kicker: "Stabilize the interface",
      title: "Contract map",
      description: "Normalize objects, quantifiers, assumptions, and conclusions into MathClaimIR and reusable MathContracts.",
      status: "MATHCLAIMIR PREVIEW"
    },
    proof: {
      index: "04",
      kicker: "Check the local delta",
      title: "Proof map",
      description: "Expose where a Lean 4 boundary and source-alignment audit would attach without claiming a current proof mapping.",
      status: "LEAN BOUNDARY VISIBLE"
    }
  };

  const consoleElement = document.querySelector(".map-console");
  const nodes = Array.from(document.querySelectorAll(".map-node"));
  const mapIndex = document.querySelector("#mapIndex");
  const mapKicker = document.querySelector("#mapKicker");
  const mapTitle = document.querySelector("#mapTitle");
  const mapDescription = document.querySelector("#mapDescription");
  const mapStatus = document.querySelector("#mapStatus");
  const mapProgress = document.querySelector(".map-help span");

  function selectMap(node) {
    const content = maps[node.dataset.map];
    if (!content) return;

    nodes.forEach((item) => {
      const selected = item === node;
      item.classList.toggle("is-active", selected);
      item.setAttribute("aria-pressed", String(selected));
    });

    consoleElement.dataset.step = node.dataset.step;
    mapIndex.textContent = content.index;
    mapKicker.textContent = content.kicker;
    mapTitle.textContent = content.title;
    mapDescription.textContent = content.description;
    mapStatus.textContent = content.status;
    mapProgress.textContent = `${content.index} / 04`;
  }

  nodes.forEach((node, index) => {
    node.addEventListener("click", () => selectMap(node));
    node.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        selectMap(node);
      }
      if (event.key === "ArrowRight" || event.key === "ArrowDown") {
        event.preventDefault();
        const next = nodes[(index + 1) % nodes.length];
        next.focus();
        selectMap(next);
      }
      if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
        event.preventDefault();
        const previous = nodes[(index - 1 + nodes.length) % nodes.length];
        previous.focus();
        selectMap(previous);
      }
    });
  });

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const reveals = document.querySelectorAll(".reveal");

  if (!reduceMotion && "IntersectionObserver" in window) {
    const belowViewport = Array.from(reveals).filter((element) => {
      return element.getBoundingClientRect().top >= window.innerHeight;
    });

    belowViewport.forEach((element) => element.classList.add("reveal-pending"));

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -35px" });

    belowViewport.forEach((element) => observer.observe(element));
  }

  document.querySelectorAll(".mobile-menu a").forEach((link) => {
    link.addEventListener("click", () => link.closest("details").removeAttribute("open"));
  });
})();
