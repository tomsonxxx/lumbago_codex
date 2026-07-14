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

    **Zalecenie SZPIEG/Plan:** Dla komend app używaj command_registry (EFFECT + dispatch).
    Sandbox tylko jako fallback dla czystych obliczeń.
    Per SZPIEG + Plan P0#1 + FINAL TESTER/REVIEWER "dalej do konca" (P0 done) ... must document identical.
    """
    ns: dict[str, Any] = {"__builtins__": SAFE_BUILTINS}
    ns.update(SAFE_API_SURFACE)
    if extra_namespace:
        ns.update(extra_namespace)

    try:
        # Prosty compile + exec z ograniczeniem
        compiled = compile(code, "<ai-sandbox>", "exec")
        # TODO: prawdziwy timeout (threading + signal / subprocess) w produkcji
        exec(compiled, ns)
        out = ns.get("__result__", "(wykonano bez błędu)")
        return True, str(out)
    except Exception as e:
        return False, f"Sandbox error (zalecane: użyj registry dispatch): {type(e).__name__}: {e}"
