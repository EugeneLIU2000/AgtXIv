"""Provider-neutral model adapter. One attempt issues at most one request.

Why raw HTTP and not a vendor SDK: the requirement is that ANY provider works, including a
model the user runs locally. No single vendor SDK spans Anthropic, Google and the
OpenAI-compatible ecosystem, and HOST.md is explicit that this delivery installs no
dependencies and selects no provider. The Python standard library is sufficient. If you only
ever need Anthropic, that vendor's official SDK is the better choice than this file.

The adapter does two separable things:

  render(profile, spec_text, brief, sources) -> request description
      Works with NO credential. Produces the lossless, reconstructible description HOST.md
      section 3 requires, including the hash of the actual request content.

  send(profile, description) -> normalized response
      Needs a credential. Raises MissingCredential with a reason string suitable for a
      NOT_STARTED receipt.

Nothing here interprets the model's content. Parsing and checking belong to check_output.py.
"""
import hashlib, json, os, pathlib, urllib.error, urllib.request

PROFILES = pathlib.Path(__file__).resolve().parent / "profiles"

class MissingCredential(Exception): pass
class ProviderError(Exception): pass

def digest(b): return "sha256:" + hashlib.sha256(b).hexdigest()

def load_profile(name):
    p = PROFILES / f"{name}.json"
    if not p.exists():
        avail = sorted(x.stem for x in PROFILES.glob("*.json"))
        raise ValueError(f"no profile {name!r}; available: {avail}")
    raw = p.read_bytes()
    prof = json.loads(raw)
    prof["_blob"] = {"sha256": digest(raw), "byte_size": len(raw), "media_type": "application/json"}
    return prof

# ---------------------------------------------------------------- request assembly

INSTRUCTION = (
 "You are producing one bounded research output under the AgtXIv research/0.2.0 contract.\n"
 "The full specification and all five JSON Schemas follow. Read them; they govern your reply.\n\n"
 "Reply with EXACTLY ONE JSON object conforming to output.schema.json, and nothing else:\n"
 "no Markdown fences, no prose before or after, no fields the schema does not define.\n\n"
 "Two rules the schemas cannot state for you:\n"
 "  1. For a source_locator, give only verbatim start_marker and end_marker copied exactly\n"
 "     from the supplied source. Never compute a byte offset or a hash; the host resolves them\n"
 "     and will reject a marker that is absent or occurs more than once.\n"
 "  2. If you did not read part of the supplied scope, say so in issues with code\n"
 "     UNREAD_SCOPE. An incomplete result that discloses its gaps is correct; a complete-looking\n"
 "     result that hides them is not.\n"
)

def render(profile, spec_text, brief, sources, operation):
    """sources: {alias: bytes}. Returns a reconstructible request description."""
    blocks = [{"role": "system", "kind": "instruction", "text": INSTRUCTION},
              {"role": "system", "kind": "spec", "sha256": digest(spec_text.encode()),
               "byte_size": len(spec_text.encode())},
              {"role": "user", "kind": "brief", "text": brief}]
    for alias, raw in sources.items():
        blocks.append({"role": "user", "kind": "source", "input": alias,
                       "sha256": digest(raw), "byte_size": len(raw)})
    prompt = INSTRUCTION + "\n\n" + spec_text + "\n\n===== TASK BRIEF =====\n" + brief
    for alias, raw in sources.items():
        prompt += (f"\n\n===== SOURCE input alias: {alias} =====\n"
                   + raw.decode("utf-8", "replace"))
    body = _body(profile, prompt, operation)
    content = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    return {"renderer_version": "adapter/1.0", "provider": profile["provider"],
            "model": profile["model"], "blocks": blocks,
            "generation": profile.get("generation", {}),
            "request_content_sha256": digest(content),
            "rendered_bytes": len(content), "_body": body}

def _body(profile, prompt, operation):
    g = profile.get("generation", {})
    mt = g.get("max_output_tokens", 16000)
    p = profile["provider"]
    if p == "anthropic":
        b = {"model": profile["model"], "max_tokens": mt,
             "messages": [{"role": "user", "content": prompt}]}
        if g.get("thinking"): b["thinking"] = g["thinking"]
        if g.get("effort"): b["output_config"] = {"effort": g["effort"]}
        return b
    if p == "gemini":
        b = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
             "generationConfig": {"maxOutputTokens": mt}}
        if g.get("json_mode"): b["generationConfig"]["responseMimeType"] = "application/json"
        if g.get("temperature") is not None: b["generationConfig"]["temperature"] = g["temperature"]
        return b
    if p == "openai_compatible":
        b = {"model": profile["model"], "max_tokens": mt,
             "messages": [{"role": "user", "content": prompt}]}
        if g.get("json_mode"): b["response_format"] = {"type": "json_object"}
        if g.get("temperature") is not None: b["temperature"] = g["temperature"]
        return b
    raise ValueError(f"unsupported provider {p!r}")

# ---------------------------------------------------------------- sending

def credential(profile):
    envs = profile["auth"]["env"]
    if isinstance(envs, str): envs = [envs]
    for e in envs:
        v = os.environ.get(e)
        if v: return v, e
    return None, envs

def send(profile, description, timeout=600):
    key, src = credential(profile)
    if not key:
        raise MissingCredential(
            f"No credential for provider {profile['provider']!r}: none of "
            f"{src} is set in the environment. No model call was attempted.")
    url = profile["endpoint"].format(model=profile["model"])
    headers = {"content-type": "application/json"}
    a = profile["auth"]
    if a["style"] == "header":       headers[a["header"]] = key
    elif a["style"] == "bearer":     headers["authorization"] = f"Bearer {key}"
    elif a["style"] == "query":      url += ("&" if "?" in url else "?") + f"{a['param']}={key}"
    else: raise ValueError(f"unsupported auth style {a['style']!r}")
    headers.update(profile.get("extra_headers", {}))
    payload = json.dumps(description["_body"]).encode()
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            rid = r.headers.get(profile.get("request_id_header", "")) or None
    except urllib.error.HTTPError as e:
        raise ProviderError(f"HTTP {e.code} from {profile['provider']}: "
                            f"{e.read()[:400].decode('utf-8','replace')}") from None
    except Exception as e:
        raise ProviderError(f"{type(e).__name__} contacting {profile['provider']}: {e}") from None
    return _normalize(profile, raw, rid)

def _normalize(profile, raw, rid):
    d = json.loads(raw)
    p = profile["provider"]
    if p == "anthropic":
        text = "".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text")
        u = d.get("usage", {})
        return _n(text, u.get("input_tokens"), u.get("output_tokens"), d.get("id") or rid, raw, d)
    if p == "gemini":
        cand = (d.get("candidates") or [{}])[0]
        text = "".join(x.get("text", "") for x in (cand.get("content") or {}).get("parts", []))
        u = d.get("usageMetadata", {})
        return _n(text, u.get("promptTokenCount"), u.get("candidatesTokenCount"),
                  d.get("responseId") or rid, raw, d)
    if p == "openai_compatible":
        ch = (d.get("choices") or [{}])[0]
        text = (ch.get("message") or {}).get("content") or ""
        u = d.get("usage", {})
        return _n(text, u.get("prompt_tokens"), u.get("completion_tokens"),
                  d.get("id") or rid, raw, d)
    raise ValueError(p)

def _n(text, itok, otok, rid, raw, parsed):
    return {"text": text, "input_tokens": itok, "output_tokens": otok,
            "provider_request_id": rid, "response_bytes": raw,
            "response_sha256": digest(raw), "finish": _finish(parsed)}

def _finish(d):
    for k in ("stop_reason", "finishReason"):
        if k in d: return d[k]
    ch = (d.get("choices") or [{}])[0]
    if "finish_reason" in ch: return ch["finish_reason"]
    cand = (d.get("candidates") or [{}])[0]
    return cand.get("finishReason")

if __name__ == "__main__":
    import sys
    names = sorted(p.stem for p in PROFILES.glob("*.json"))
    print(f"registered profiles: {names}\n")
    for n in names:
        pr = load_profile(n)
        key, src = credential(pr)
        print(f"  {n:22s} provider={pr['provider']:20s} model={pr['model']:28s} "
              f"credential={'PRESENT' if key else 'absent (' + ','.join(src if isinstance(src,list) else [src]) + ')'}")
