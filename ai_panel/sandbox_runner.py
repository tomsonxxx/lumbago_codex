from __future__ import annotations

"""
SandboxRunner — **ograniczony** runner dla wygenerowanego kodu AI.

**WAŻNE (per SZPIEG research + Plan lista P0 #1 + prompt security):**
- **Preferuj zawsze registry dispatch** (command_registry.py + dispatcher) dla akcji aplikacji (open dialog, scan, pobierz itp.).
- Sandbox tylko dla czystych obliczeń / bezpiecznych helperów.
- In-proc exec jest **ryzykowne** (prompt injection, escape). Używaj tylko z bardzo ograniczonym surface.
- Zawsze: whitelist, brak fs/os/sys, timeout, potwierdzenie użytkownika (EFFECT preview).
- Dla pełnego bezpieczeństwa: rozważ subprocess lub registry-only (bez codegen dla app actions).
- **HARDEN (FIXER post-dalej):** registry-primary; in-proc fallback tylko compute; brak dostępu do repo/fs/net w sandbox; portable-safe (no side effects).

Zgodne z: 100% darmowe, no conflict z istniejącym kodem, EFFECT descriptions, Lumbago patterns.
Per SZPIEG research + consolidated raw + detailed prompt 2026-06-27 + CHECKLIST_Downloader_AI_Panel.md + PLAN + "dalej" (search B, est dialog+disk, wiring, A info) ... must document identical.
"""

import builtins as _builtins
from typing import Any

SAFE_BUILTINS = {
    "len": len,
    "range": range,
    "print": print,
    "str": str,
    "int": int,
    "float": float,
    "list": list,
    "dict": dict,
    "set": set,
    "bool": bool,
    "enumerate": enumerate,
    "sorted": sorted,
    "sum": sum,
    "min": min,
    "max": max,
}

# Powierzchnia API — wstrzykiwana z zewnątrz TYLKO safe/read-only rzeczy.
# Dla akcji app używaj registry + MainWindow signals (nie daj bezpośredniego repo/fs).
SAFE_API_SURFACE: dict[str, Any] = {}


def run_in_sandbox(code: str, extra_namespace: dict[str, Any] | None = None, timeout_s: float = 8.0) -> tuple[bool, str]:
    """
    Wykonuje kod w bardzo ograniczonym środowisku.
    Zwraca (success, output_or_error).

    **Zalecenie SZPIEG/Plan (dalej continuation item 2):** 
    - **Zawsze preferuj command_registry dispatch** dla akcji aplikacji (open DL, duplicates, scan itp.). Patrz EFFECT w registry.
    - Sandbox **tylko** dla czystych obliczeń (math, string ops). Nie fs, net, repo, UI.
    - Dla AI komend z efektem ubocznym: registry + opcjonalny confirm w UI (EFFECT preview).
    - In-proc exec jest ryzykowny — używaj tylko gdy absolutnie konieczne + whitelist.
    Per SZPIEG research 2026-07-14 + "dalej" + "chce dodać nowe..." ... must document identical.
    """
    ns: dict[str, Any] = {"__builtins__": SAFE_BUILTINS}
    ns.update(SAFE_API_SURFACE)
    if extra_namespace:
        ns.update(extra_namespace)

    # Hardening: blokuj niebezpieczne próby (nawet jeśli w whitelist nie ma)
    if any(danger in (code or "").lower() for danger in ("import os", "import sys", "open(", "__import__", "subprocess", "eval(", "exec(")):
        return False, "Sandbox blocked: use registry dispatch for app actions (EFEKT: safe structured commands only)."

    try:
        # Prosty compile + exec z ograniczeniem
        compiled = compile(code, "<ai-sandbox>", "exec")

        # Timeout implementation (thread + join) — basic but effective for Windows (no signal).
        # Per item 25 NOWA_LISTA + SZPIEG/Plan Faza4 hardening. Best-effort (thread not forcibly killed).
        import threading
        import time as _time
        result_box = {"ok": False, "out": ""}
        def _exec_target():
            try:
                exec(compiled, ns)
                result_box["out"] = str(ns.get("__result__", "(wykonano bez błędu)"))
                result_box["ok"] = True
            except Exception as ex:
                result_box["out"] = f"Sandbox exec error: {type(ex).__name__}: {ex}"
        t = threading.Thread(target=_exec_target, daemon=True)
        t.start()
        t.join(timeout=timeout_s)
        if t.is_alive():
            return False, f"Sandbox timeout after {timeout_s}s (zalecane: krótsze compute; użyj registry dispatch dla app actions)"
        if result_box["ok"]:
            return True, result_box["out"]
        else:
            return False, result_box["out"] or "Sandbox error"
    except Exception as e:
        return False, f"Sandbox error (zalecane: użyj registry dispatch): {type(e).__name__}: {e}"
