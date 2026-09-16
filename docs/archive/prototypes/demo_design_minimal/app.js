(() => {
  const stages = {
    freeze: {
      index: "01",
      step: "0",
      kicker: "Freeze the source",
      title: "Anchor the occurrence",
      description: "Preserve the source statement and its exact location.",
      status: "FROZEN SOURCE",
      tone: "grounded",
      artifact: "FROZEN ARTIFACT · SOURCEANCHOR"
    },
    normalize: {
      index: "02",
      step: "1",
      kicker: "Normalize the claim",
      title: "Structure the meaning",
      description: "Record typed objects, quantifiers, assumptions, and one atomic conclusion in MathClaimIR.",
      status: "MATHCLAIMIR RECORD",
      tone: "neutral",
      artifact: "STRUCTURED CLAIM · MATHCLAIMIR"
    },
    resolve: {
      index: "03",
      step: "2",
      kicker: "Resolve the dependencies",
      title: "Find query roots",
      description: "Build the load-bearing dependency closure and keep unresolved sources explicit.",
      status: "ORACLE CANDIDATE",
      tone: "pending",
      artifact: "DEPENDENCY VIEW · QUERYRESOLUTION"
    },
    verify: {
      index: "04",
      step: "3",
      kicker: "Verify the local delta",
      title: "Check the local delta",
      description: "Route packages, construct in Lean 4, and audit alignment with the source claim.",
      status: "LEAN MAPPING · UNMAPPED",
      tone: "pending",
      artifact: "VERIFICATION BOUNDARY · LEAN 4 / MATHCONTRACT"
    }
  };

  const consoleElement = document.querySelector(".map-console");
  const mapIndex = document.querySelector("#mapIndex");
  const mapKicker = document.querySelector("#mapKicker");
  const mapTitle = document.querySelector("#mapTitle");
  const mapDescription = document.querySelector("#mapDescription");
  const mapStatus = document.querySelector("#mapStatus span");
  const mapProgress = document.querySelector(".map-help span");
  const artifactLabel = document.querySelector("#workflowArtifactLabel");
  const artifactTitle = document.querySelector("#workflowArtifactTitle");
  const artifactMeta = document.querySelector("#workflowArtifactMeta");
  const paperIntake = document.querySelector(".paper-intake");
  const meterSegments = Array.from(document.querySelectorAll(".workflow-meter i"));
  const groups = [
    Array.from(document.querySelectorAll(".map-node")),
    Array.from(document.querySelectorAll(".route-tab")),
    Array.from(document.querySelectorAll(".workflow-step"))
  ];

  function selectStage(stageName) {
    const content = stages[stageName];
    if (!content) return;

    groups.flat().forEach((control) => {
      const selected = control.dataset.map === stageName;
      control.classList.toggle("is-active", selected);
      control.setAttribute("aria-pressed", String(selected));
      if (control.classList.contains("workflow-step")) {
        control.closest("li").classList.toggle("is-active", selected);
      }
    });

    consoleElement.dataset.step = content.step;
    consoleElement.dataset.tone = content.tone;
    paperIntake.dataset.stage = stageName;
    mapIndex.textContent = content.index;
    mapKicker.textContent = content.kicker;
    mapTitle.textContent = content.title;
    mapDescription.textContent = content.description;
    mapStatus.textContent = content.status;
    mapProgress.textContent = `${content.index} / 04`;

    artifactLabel.textContent = content.artifact;
    artifactTitle.textContent = content.title;
    artifactMeta.textContent = content.description;
    meterSegments.forEach((segment, index) => {
      segment.classList.toggle("is-active", index === Number(content.step));
    });
  }

  function wireControlGroup(controls) {
    controls.forEach((control, index) => {
      control.addEventListener("click", () => selectStage(control.dataset.map));
      control.addEventListener("keydown", (event) => {
        if (control.getAttribute("role") === "button" && (event.key === "Enter" || event.key === " ")) {
          event.preventDefault();
          selectStage(control.dataset.map);
        }
        if (event.key === "ArrowRight" || event.key === "ArrowDown") {
          event.preventDefault();
          const next = controls[(index + 1) % controls.length];
          next.focus();
          selectStage(next.dataset.map);
        }
        if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
          event.preventDefault();
          const previous = controls[(index - 1 + controls.length) % controls.length];
          previous.focus();
          selectStage(previous.dataset.map);
        }
      });
    });
  }

  groups.forEach(wireControlGroup);

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const pilotId = "2607.26154";
  const resultPath = "scientific_claims/#claim=claim%3Agraph-theoretic-nonstabilizerness%3Asign-relaxation-exactness&facet=facet%3Apolytope-exactness";
  const runMessages = [
    "Retrieved the frozen source for arXiv:2607.26154v1.",
    "Matched the pilot source identity and reused existing source-grounded records.",
    "Constructed the candidate DAG; generated relations are not mathematically verified or scientifically accepted.",
    "Report complete: pilot source identity matched; 0 new records admitted to the database."
  ];

  function parseArxivInput(rawValue) {
    const value = rawValue.trim();
    if (!value) return { error: "empty" };

    let candidate = value;
    if (/^https?:\/\//i.test(value)) {
      let url;
      try {
        url = new URL(value);
      } catch (_error) {
        return { error: "malformed" };
      }
      if (!["arxiv.org", "www.arxiv.org"].includes(url.hostname.toLowerCase()) || url.search || url.hash) {
        return { error: "malformed" };
      }
      const pathMatch = url.pathname.match(/^\/(?:abs|pdf)\/(\d{4}\.\d{4,5})(v\d+)?(?:\.pdf)?\/?$/i);
      if (!pathMatch) return { error: "malformed" };
      candidate = `${pathMatch[1]}${pathMatch[2] || ""}`;
    } else if (/^[a-z][a-z0-9+.-]*:\/\//i.test(value)) {
      return { error: "malformed" };
    }

    const identifierMatch = candidate.match(/^(?:arxiv:\s*)?(\d{4}\.\d{4,5})(v\d+)?(?:\.pdf)?$/i);
    if (!identifierMatch) return { error: "malformed" };
    return { id: identifierMatch[1], version: (identifierMatch[2] || "v1").toLowerCase() };
  }

  const intakeForm = document.querySelector("#intake");
  const arxivInput = document.querySelector("#arxivInput");
  const intakeSubmit = document.querySelector("#intakeSubmit");
  const intakeError = document.querySelector("#intakeError");
  const runPanel = document.querySelector("#runPanel");
  const runCounter = document.querySelector("#runCounter");
  const runStatus = document.querySelector("#runStatus");
  const runStages = Array.from(document.querySelectorAll("[data-run-stage]"));
  let intakeRunning = false;

  function showIntakeError(message) {
    intakeError.textContent = message;
    intakeError.hidden = false;
    arxivInput.setAttribute("aria-invalid", "true");
    arxivInput.focus();
  }

  function startPilotRun() {
    intakeRunning = true;
    intakeSubmit.disabled = true;
    arxivInput.disabled = true;
    intakeError.hidden = true;
    arxivInput.removeAttribute("aria-invalid");
    runPanel.hidden = false;

    let stageIndex = 0;
    const stageDelay = reduceMotion ? 180 : 650;
    const updateStage = () => {
      runStages.forEach((stage, index) => {
        stage.classList.toggle("is-active", index === stageIndex);
        stage.classList.toggle("is-complete", index < stageIndex);
      });
      runCounter.textContent = `${stageIndex + 1} / ${runStages.length}`;
      runStatus.textContent = runMessages[stageIndex];

      if (stageIndex < runStages.length - 1) {
        stageIndex += 1;
        window.setTimeout(updateStage, stageDelay);
        return;
      }

      window.setTimeout(() => {
        runStages.forEach((stage) => {
          stage.classList.remove("is-active");
          stage.classList.add("is-complete");
        });
        window.location.assign(resultPath);
      }, reduceMotion ? 250 : 850);
    };

    updateStage();
  }

  intakeForm.addEventListener("submit", (event) => {
    event.preventDefault();
    if (intakeRunning) return;

    const parsed = parseArxivInput(arxivInput.value);
    if (parsed.error === "empty") {
      showIntakeError("Enter an arXiv URL or identifier.");
      return;
    }
    if (parsed.error) {
      showIntakeError("Enter a valid arXiv URL or identifier, such as https://arxiv.org/abs/2607.26154.");
      return;
    }
    if (parsed.id !== pilotId || parsed.version !== "v1") {
      showIntakeError("This static demo only supports arXiv:2607.26154v1.");
      return;
    }
    startPilotRun();
  });

  document.querySelectorAll("[data-example-input]").forEach((button) => {
    button.addEventListener("click", () => {
      arxivInput.value = button.dataset.exampleInput;
      intakeError.hidden = true;
      arxivInput.removeAttribute("aria-invalid");
      arxivInput.focus();
    });
  });

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

  document.querySelectorAll(".mobile-menu").forEach((menu) => {
    const summary = menu.querySelector("summary");
    menu.addEventListener("toggle", () => {
      summary.setAttribute("aria-label", menu.open ? "Close navigation" : "Open navigation");
    });
    menu.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => menu.removeAttribute("open"));
    });
  });
})();
