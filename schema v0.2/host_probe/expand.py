"""Host-side macro table extraction. CONTRACT.md section 4: programs do mechanical work.

The host reads the paper's own macro definitions out of the supplied preamble sources and
publishes a table. It does NOT rewrite the source: byte offsets stay offsets into the original
bytes, and source_locator resolution is unaffected. The table is supplied to the model as a
context input so the model can write a statement with the paper's shorthand expanded, instead of
inventing an interpretation for a macro it has never seen.

A macro used in the source but defined nowhere supplied is reported, never guessed. HOST.md:
"do not interpret unavailable macros from memory".

STOCK below is a curated allowlist of LaTeX and TeX control sequences, not a complete inventory
of either - no such list exists. A name in unresolved_macros therefore means "not defined in the
supplied sources and not on the curated list": a prompt to go and look, not proof of a defect.
That is why PARTIALLY_EXPANDED is a reportable outcome rather than a failure.
"""
import hashlib, json, pathlib, re

PROFILE = "agtxiv.macro-expansion/1.0.0"

# \newcommand{\name}[n][default]{body} and \def\name{body}, plus the starred/renew variants.
DEF = re.compile(
    r"\\(?:new|renew|provide)command\*?\s*\{?\s*(\\[A-Za-z@]+)\s*\}?"
    r"(?:\s*\[(\d+)\])?(?:\s*\[[^\]]*\])?\s*", re.S)
DEFOLD = re.compile(r"\\def\s*(\\[A-Za-z@]+)((?:#\d)*)\s*", re.S)
USE = re.compile(r"\\([A-Za-z@]+)")

# Control sequences that are LaTeX/TeX itself, not this paper's shorthand. Names containing @
# are TeX-internal (\makeatletter, natbib, the .bbl) and are excluded separately.
STOCK = set("""begin end label ref eqref cite citep citet input include section subsection
subsubsection paragraph textbf textit emph mathbb mathcal mathrm mathbf mathit operatorname
frac sum prod int lim sup inf max min log exp sin cos tan sqrt left right big Big bigg Bigg
langle rangle lvert rvert lVert rVert quad qquad text texttt textsf mbox hspace vspace
alpha beta gamma delta epsilon varepsilon zeta eta theta vartheta iota kappa lambda mu nu xi
pi varpi rho varrho sigma varsigma tau upsilon phi varphi chi psi omega Gamma Delta Theta
Lambda Xi Pi Sigma Upsilon Phi Psi Omega leq geq neq approx equiv sim simeq cong propto
in notin subset subseteq supset supseteq cup cap setminus emptyset forall exists neg land lor
to mapsto rightarrow leftarrow Rightarrow Leftarrow leftrightarrow implies iff cdot cdots
dots ldots vdots ddots times otimes oplus dagger ast star circ bullet partial nabla infty
item itemize enumerate footnote caption centering hline toprule midrule bottomrule
usepackage documentclass newtheorem theoremstyle DeclareMathOperator renewcommand newcommand
providecommand def let relax overline underline hat tilde bar vec dot ddot binom choose
displaystyle scriptstyle small large Large LARGE huge Huge normalsize bm boldsymbol
author affiliation altaffiliation title date maketitle abstract acknowledgments appendix
bibliography bibliographystyle bibitem citation newblock url doi eprint
bra ket braket bigotimes bigoplus bigcup bigcap bigsqcup sqcup coloneqq eqqcolon colon
lfloor rfloor lceil rceil mid parallel perp angle ang deg pm mp div ne le ge ll gg
baselineskip addvspace addtolength setlength arraystretch tabcolsep linewidth textwidth
columnwidth noindent newpage clearpage pagebreak linebreak smallskip medskip bigskip
label@ makeatletter makeatother expandafter csname endcsname protect ensuremath
""".split())

def digest(b): return "sha256:" + hashlib.sha256(b).hexdigest()

def _body(text, i):
    """Read one balanced {...} group starting at or after i. Returns (body, end) or (None, i)."""
    while i < len(text) and text[i] in " \t\r\n": i += 1
    if i >= len(text) or text[i] != "{": return None, i
    depth, j = 0, i
    while j < len(text):
        c = text[j]
        if c == "\\": j += 2; continue
        if c == "{": depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0: return text[i+1:j], j+1
        j += 1
    return None, i

def definitions(preamble_text):
    """Every macro this paper defines, as {name_with_arity: body}."""
    out = {}
    for m in DEF.finditer(preamble_text):
        name, arity = m.group(1), m.group(2)
        body, _ = _body(preamble_text, m.end())
        if body is None: continue
        if "@" in name: continue          # TeX-internal, not the paper's mathematical shorthand
        key = f"{name}{{#1}}" if arity and int(arity) >= 1 else name
        out[key] = " ".join(body.split())
    for m in DEFOLD.finditer(preamble_text):
        body, _ = _body(preamble_text, m.end())
        if body is None: continue
        if "@" in m.group(1): continue
        args = m.group(2) or ""
        key = f"{m.group(1)}{{#1}}" if args else m.group(1)
        out.setdefault(key, " ".join(body.split()))
    return dict(sorted(out.items()))

def used(source_text):
    return {m.group(1) for m in USE.finditer(source_text)}

def build(source_alias, source_bytes, preambles):
    r"""preambles: {alias: bytes}. Returns an entry conforming to run.schema expansions[].

    Definitions are collected from the preambles AND from the source itself: a paper is free to
    define its shorthand in its own main file, and this one does - \Mcal is defined on line 8 of
    draft.tex, not in the preamble it inputs. Scanning only the preamble reports the paper's own
    notation as unresolved, which is wrong and would push the model toward guessing it."""
    src = source_bytes.decode("utf-8", "replace")
    defs = {}
    for alias, raw in preambles.items():
        defs.update(definitions(raw.decode("utf-8", "replace")))
    defs.update(definitions(src))
    defs = dict(sorted(defs.items()))
    names = {k.split("{")[0].lstrip("\\") for k in defs}
    unresolved = sorted(n for n in used(src)
                        if n not in names and n not in STOCK and "@" not in n)
    table = json.dumps({"profile": PROFILE, "macros": defs}, ensure_ascii=False,
                       sort_keys=True, indent=1).encode()
    if not defs:      outcome = "NOT_APPLICABLE" if not preambles else "EXPANSION_FAILED"
    elif unresolved:  outcome = "PARTIALLY_EXPANDED"
    else:             outcome = "EXPANDED"
    return {"input": source_alias, "profile": PROFILE, "outcome": outcome,
            "macro_table": {"sha256": digest(table), "byte_size": len(table),
                            "media_type": "application/json"},
            "included_sources": sorted(list(preambles) + [source_alias]),
            "unresolved_macros": unresolved}, table

if __name__ == "__main__":
    REPO = pathlib.Path(__file__).resolve().parents[2]
    d = REPO / "Stabilizerness/arXiv-2607.26154v1"
    src = (d / "draft.tex").read_bytes()
    head = (d / "head.tex").read_bytes()
    entry, table = build("draft_tex", src, {"head_tex": head})
    macros = json.loads(table)["macros"]
    print(f"source            draft.tex  {len(src):,} bytes")
    print(f"preamble          head.tex   {len(head):,} bytes")
    print(f"outcome           {entry['outcome']}")
    print(f"macros defined    {len(macros)}")
    print(f"macro_table       {entry['macro_table']['sha256'][:26]}…  {entry['macro_table']['byte_size']:,} B")
    print(f"unresolved        {len(entry['unresolved_macros'])}"
          + (f"  {entry['unresolved_macros'][:12]}" if entry['unresolved_macros'] else ""))
    print()
    print("the paper's own shorthand, as the host reads it:")
    for k, v in list(macros.items())[:22]:
        print(f"   {k:20s} -> {v}")
