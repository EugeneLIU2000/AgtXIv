from __future__ import annotations

import json
import subprocess
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo_design"
RESULT_PATH = (
    "scientific_claims/#claim=claim%3Agraph-theoretic-nonstabilizerness%3A"
    "sign-relaxation-exactness&facet=facet%3Apolytope-exactness"
)


class IntakeParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.labels: list[dict[str, str | None]] = []
        self.anchors: list[dict[str, str | None]] = []
        self.references: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"])
        if tag == "label":
            self.labels.append(values)
        if tag == "a":
            self.anchors.append(values)
        for attribute in ("href", "src"):
            if values.get(attribute):
                self.references.append(values[attribute])


class DemoIntakeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = (DEMO / "index.html").read_text(encoding="utf-8")
        cls.javascript = (DEMO / "app.js").read_text(encoding="utf-8")
        cls.result_html = (DEMO / "scientific_claims/index.html").read_text(encoding="utf-8")

    def test_intake_is_accessible_and_result_links_work_from_both_serving_bases(self) -> None:
        landing = IntakeParser()
        landing.feed(self.html)
        result = IntakeParser()
        result.feed(self.result_html)

        self.assertIn("intake", landing.ids)
        self.assertIn("arxivInput", landing.ids)
        self.assertTrue(any(label.get("for") == "arxivInput" for label in landing.labels))
        self.assertIn('id="intakeError" role="alert"', self.html)
        self.assertIn('id="runStatus" role="status"', self.html)

        direct_href = next(
            anchor["href"] for anchor in landing.anchors
            if "button-ghost" in (anchor.get("class") or "") and (anchor.get("href") or "").startswith("scientific_claims/")
        )
        return_href = next(
            anchor["href"] for anchor in result.anchors
            if "intake-return" in (anchor.get("class") or "")
        )
        self.assertEqual(direct_href, RESULT_PATH)
        self.assertEqual(return_href, "../index.html#intake")

        cases = (
            (
                "http://127.0.0.1:8000/demo_design/",
                "http://127.0.0.1:8000/demo_design/scientific_claims/" + RESULT_PATH.split("/", 1)[1],
                "http://127.0.0.1:8000/demo_design/scientific_claims/",
                "http://127.0.0.1:8000/demo_design/index.html#intake",
            ),
            (
                "http://127.0.0.1:8000/",
                "http://127.0.0.1:8000/scientific_claims/" + RESULT_PATH.split("/", 1)[1],
                "http://127.0.0.1:8000/scientific_claims/",
                "http://127.0.0.1:8000/index.html#intake",
            ),
        )
        for landing_base, expected_direct, result_base, expected_return in cases:
            with self.subTest(landing_base=landing_base):
                self.assertEqual(urljoin(landing_base, direct_href), expected_direct)
                self.assertEqual(urljoin(result_base, return_href), expected_return)

        for reference in landing.references + result.references:
            if reference.startswith(("http://", "https://")):
                continue
            self.assertFalse(reference.startswith("/"), reference)

    def test_supported_equivalent_inputs_and_error_categories(self) -> None:
        start = self.javascript.index("  function parseArxivInput")
        end = self.javascript.index("\n\n  const intakeForm", start)
        function_source = self.javascript[start:end]
        values = [
            "https://arxiv.org/abs/2607.26154",
            "https://arxiv.org/pdf/2607.26154",
            "https://arxiv.org/pdf/2607.26154.pdf",
            "https://arxiv.org/abs/2607.26154v1",
            "arXiv:2607.26154v1",
            "2607.26154",
            "",
            "https://example.com/abs/2607.26154",
            "not-an-arxiv-id",
            "2501.00001",
            "2607.26154v2",
        ]
        script = f"""
{function_source}
const values = {json.dumps(values)};
console.log(JSON.stringify(values.map(parseArxivInput)));
"""
        completed = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        parsed = json.loads(completed.stdout)
        for item in parsed[:6]:
            self.assertEqual(item, {"id": "2607.26154", "version": "v1"})
        self.assertEqual(parsed[6], {"error": "empty"})
        self.assertEqual(parsed[7], {"error": "malformed"})
        self.assertEqual(parsed[8], {"error": "malformed"})
        self.assertEqual(parsed[9], {"id": "2501.00001", "version": "v1"})
        self.assertEqual(parsed[10], {"id": "2607.26154", "version": "v2"})

    def test_submit_events_timers_duplicate_guard_and_reduced_motion(self) -> None:
        harness = r"""
const fs = require("fs");
const vm = require("vm");
const source = fs.readFileSync(APP_PATH, "utf8");

class ClassList {
  constructor() { this.values = new Set(); }
  add(...names) { names.forEach((name) => this.values.add(name)); }
  remove(...names) { names.forEach((name) => this.values.delete(name)); }
  contains(name) { return this.values.has(name); }
  toggle(name, force) {
    const enabled = force === undefined ? !this.values.has(name) : Boolean(force);
    if (enabled) this.values.add(name); else this.values.delete(name);
    return enabled;
  }
  snapshot() { return [...this.values].sort(); }
}

class Element {
  constructor(dataset = {}) {
    this.dataset = dataset;
    this.classList = new ClassList();
    this.listeners = {};
    this.attributes = {};
    this.hidden = false;
    this.disabled = false;
    this.value = "";
    this.textContent = "";
    this.parent = null;
  }
  addEventListener(type, callback) { (this.listeners[type] ||= []).push(callback); }
  dispatch(type) {
    const event = { type, prevented: false, preventDefault() { this.prevented = true; } };
    (this.listeners[type] || []).forEach((callback) => callback(event));
    return event;
  }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  getAttribute(name) { return this.attributes[name] ?? null; }
  removeAttribute(name) { delete this.attributes[name]; }
  focus() { this.focused = true; }
  closest() { return this.parent || this; }
  querySelector() { return new Element(); }
  querySelectorAll() { return []; }
  getBoundingClientRect() { return { top: 0 }; }
}

function run(reduceMotion) {
  const timers = [];
  const assigned = [];
  const form = new Element();
  const input = new Element();
  const submit = new Element();
  const error = new Element(); error.hidden = true;
  const panel = new Element(); panel.hidden = true;
  const counter = new Element();
  const status = new Element();
  const stages = Array.from({ length: 4 }, (_, index) => new Element({ runStage: String(index) }));
  const elements = new Map([
    [".map-console", new Element()], ["#mapIndex", new Element()], ["#mapKicker", new Element()],
    ["#mapTitle", new Element()], ["#mapDescription", new Element()], ["#mapStatus span", new Element()],
    [".map-help span", new Element()], ["#workflowArtifactLabel", new Element()],
    ["#workflowArtifactTitle", new Element()], ["#workflowArtifactMeta", new Element()],
    [".paper-intake", new Element()], ["#intake", form], ["#arxivInput", input],
    ["#intakeSubmit", submit], ["#intakeError", error], ["#runPanel", panel],
    ["#runCounter", counter], ["#runStatus", status]
  ]);
  const document = {
    querySelector(selector) { return elements.get(selector) || null; },
    querySelectorAll(selector) {
      if (selector === "[data-run-stage]") return stages;
      return [];
    }
  };
  const window = {
    innerHeight: 900,
    matchMedia() { return { matches: reduceMotion }; },
    setTimeout(callback, delay) { timers.push({ callback, delay }); return timers.length; },
    location: { assign(value) { assigned.push(value); } }
  };
  vm.runInNewContext(source, { window, document, URL, console });

  function submitValue(value) {
    input.value = value;
    return form.dispatch("submit");
  }

  const emptyEvent = submitValue("");
  const emptyError = error.textContent;
  const malformedEvent = submitValue("https://example.com/abs/2607.26154");
  const malformedError = error.textContent;
  const unsupportedEvent = submitValue("2501.00001");
  const unsupportedError = error.textContent;
  const validEvent = submitValue("https://arxiv.org/pdf/2607.26154v1.pdf");
  const initial = { counter: counter.textContent, status: status.textContent };
  const timerCountBeforeDuplicate = timers.length;
  const duplicateEvent = submitValue("2607.26154");
  const duplicatePrevented = timers.length === timerCountBeforeDuplicate;

  const delays = [];
  const snapshots = [initial];
  while (timers.length) {
    const timer = timers.shift();
    delays.push(timer.delay);
    timer.callback();
    snapshots.push({ counter: counter.textContent, status: status.textContent });
  }

  return {
    eventsPrevented: [emptyEvent, malformedEvent, unsupportedEvent, validEvent, duplicateEvent].every((event) => event.prevented),
    errors: { emptyError, malformedError, unsupportedError },
    disabled: input.disabled && submit.disabled,
    panelVisible: !panel.hidden,
    duplicatePrevented,
    delays,
    snapshots,
    stageClasses: stages.map((stage) => stage.classList.snapshot()),
    assigned
  };
}

console.log(JSON.stringify({ regular: run(false), reduced: run(true) }));
"""
        script = f"const APP_PATH = {json.dumps(str(DEMO / 'app.js'))};\n{harness}"
        completed = subprocess.run(["node", "-e", script], check=True, text=True, capture_output=True)
        runs = json.loads(completed.stdout)

        for name, run in runs.items():
            with self.subTest(mode=name):
                self.assertTrue(run["eventsPrevented"])
                self.assertEqual(run["errors"]["emptyError"], "Enter an arXiv URL or identifier.")
                self.assertIn("valid arXiv URL or identifier", run["errors"]["malformedError"])
                self.assertEqual(run["errors"]["unsupportedError"], "This static demo only supports arXiv:2607.26154v1.")
                self.assertTrue(run["disabled"])
                self.assertTrue(run["panelVisible"])
                self.assertTrue(run["duplicatePrevented"])
                self.assertEqual(run["snapshots"][0]["counter"], "1 / 4")
                self.assertEqual(run["snapshots"][-2]["counter"], "4 / 4")
                self.assertIn("source identity matched", run["snapshots"][-2]["status"])
                self.assertEqual(run["assigned"], [RESULT_PATH])
                self.assertTrue(all(classes == ["is-complete"] for classes in run["stageClasses"]))

        self.assertEqual(runs["regular"]["delays"], [650, 650, 650, 850])
        self.assertEqual(runs["reduced"]["delays"], [180, 180, 180, 250])
        candidate_statuses = [snapshot["status"] for snapshot in runs["regular"]["snapshots"]]
        self.assertTrue(any("not mathematically verified or scientifically accepted" in status for status in candidate_statuses))

    def test_outcome_copy_names_the_matched_axis_without_claiming_verification(self) -> None:
        self.assertIn("Matched the pilot source identity", self.javascript)
        self.assertIn("generated relations are not mathematically verified or scientifically accepted", self.javascript)
        self.assertIn("0 new records admitted to the database", self.javascript)
        self.assertIn("Source match / reuse", self.result_html)
        self.assertIn("Pilot source identity matched; existing source-grounded records reused", self.result_html)
        self.assertIn("Generated / candidate", self.result_html)
        self.assertIn("Admitted to database", self.result_html)
        self.assertNotIn("reused knowledge verified", (self.html + self.javascript + self.result_html).lower())
        self.assertNotIn("Reused / verified", self.result_html)


if __name__ == "__main__":
    unittest.main()
