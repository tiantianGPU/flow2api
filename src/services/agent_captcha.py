"""Optional bridge to reg-factory's agent-captcha solver.

The reg-factory project provides both ``common.agent_captcha`` for Arkose and
``vision_solver`` for reCAPTCHA/hCaptcha image challenges. Flow2API still
obtains the normal Google reCAPTCHA Enterprise token itself; this bridge only
runs when a visual challenge is actually present in the headed page.
"""

from __future__ import annotations

import asyncio
import importlib
import importlib.util
import os
import sys
from pathlib import Path
from typing import Any, Optional

from ..core.config import config
from ..core.logger import debug_logger


_module: Optional[Any] = None
_vision_module: Optional[Any] = None
_vision_spec_path: Optional[str] = None
_module_key = ""
_module_lock = asyncio.Lock()


def _configured_path() -> str:
    return str(getattr(config, "agent_captcha_module_path", "") or "").strip()


def _candidate_module_paths(configured: str) -> list[Path]:
    if not configured:
        return []
    path = Path(configured).expanduser()
    if path.is_file():
        return [path]
    if path.is_dir():
        return [path / "common" / "agent_captcha.py", path / "agent_captcha.py"]
    return []


def _load_module_sync(configured: str) -> Optional[Any]:
    for module_path in _candidate_module_paths(configured):
        if not module_path.is_file():
            continue
        module_name = "flow2api_external_agent_captcha"
        spec = importlib.util.spec_from_file_location(module_name, str(module_path))
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        if callable(getattr(module, "solve_puzzle_voting", None)):
            return module

    try:
        module = importlib.import_module("common.agent_captcha")
    except Exception:
        return None
    return module if callable(getattr(module, "solve_puzzle_voting", None)) else None


def _load_vision_sync(configured: str) -> tuple[Optional[Any], Optional[str]]:
    path = Path(configured).expanduser()
    root = path if path.is_dir() else path.parent.parent
    if not (root / "vision_solver").is_dir():
        return None, None
    sys.path.insert(0, str(root))
    try:
        module = importlib.import_module("vision_solver")
        spec_path = root / "vision_solver" / "presets" / "recaptcha_v2.json"
        if callable(getattr(module, "solve", None)) and spec_path.is_file():
            return module, str(spec_path)
    except Exception:
        pass
    return None, None


async def _get_module() -> Optional[Any]:
    global _module, _vision_module, _vision_spec_path, _module_key
    configured = _configured_path()
    if _module_key == configured:
        return _module
    async with _module_lock:
        if _module_key == configured:
            return _module
        _module_key = configured
        _module = None
        _vision_module = None
        _vision_spec_path = None
        if not configured:
            return None
        try:
            _module = await asyncio.to_thread(_load_module_sync, configured)
            _vision_module, _vision_spec_path = await asyncio.to_thread(_load_vision_sync, configured)
        except Exception as exc:
            debug_logger.log_warning(f"[agent-captcha] 加载模块失败: {type(exc).__name__}: {exc}")
        return _module


def _has_arkose_frame(page: Any) -> bool:
    for frame in getattr(page, "frames", []) or []:
        url = str(getattr(frame, "url", "") or "").lower()
        if any(marker in url for marker in ("arkose", "funcaptcha", "octocaptcha")):
            return True
    return False


def _has_vision_frame(page: Any) -> bool:
    for frame in getattr(page, "frames", []) or []:
        url = str(getattr(frame, "url", "") or "").lower()
        if any(marker in url for marker in ("recaptcha/api2", "api2/bframe", "hcaptcha.com")):
            return True
    return False


async def solve_if_present(page: Any, *, shot_dir: str = "tmp/agent-captcha") -> bool:
    """Solve an Arkose challenge on a Playwright page when one is present."""
    has_arkose = _has_arkose_frame(page)
    has_vision = _has_vision_frame(page)
    if not (has_arkose or has_vision):
        return False

    module = await _get_module()
    if has_vision and _vision_module is not None and _vision_spec_path:
        timeout = max(10, int(getattr(config, "agent_captcha_timeout", 180) or 180))
        try:
            Path(shot_dir).mkdir(parents=True, exist_ok=True)
            result = await asyncio.wait_for(
                _vision_module.solve(page, _vision_spec_path, shot_dir=shot_dir),
                timeout=timeout,
            )
            solved = result is True
            debug_logger.log_info(f"[agent-captcha] reCAPTCHA vision challenge solved={solved}")
            return solved
        except asyncio.TimeoutError:
            debug_logger.log_warning(f"[agent-captcha] reCAPTCHA vision 求解超时 ({timeout}s)")
        except Exception as exc:
            debug_logger.log_warning(f"[agent-captcha] reCAPTCHA vision 求解失败: {type(exc).__name__}: {exc}")

    if has_vision and not has_arkose:
        debug_logger.log_warning(
            "[agent-captcha] 检测到 reCAPTCHA/hCaptcha 视觉挑战，但 vision_solver 不可用；"
            "请确认 AGENT_CAPTCHA_MODULE_PATH 指向包含 vision_solver 的 reg-factory"
        )
        return False

    if module is None:
        debug_logger.log_warning(
            "[agent-captcha] 检测到视觉挑战，但未加载求解器；"
            "请设置 AGENT_CAPTCHA_MODULE_PATH 指向 reg-factory"
        )
        return False

    timeout = max(10, int(getattr(config, "agent_captcha_timeout", 180) or 180))
    try:
        Path(shot_dir).mkdir(parents=True, exist_ok=True)
        result = await asyncio.wait_for(
            module.solve_puzzle_voting(page, shot_dir=shot_dir),
            timeout=timeout,
        )
        solved = result is True
        debug_logger.log_info(f"[agent-captcha] Arkose challenge solved={solved}")
        return solved
    except asyncio.TimeoutError:
        debug_logger.log_warning(f"[agent-captcha] 求解超时 ({timeout}s)")
    except Exception as exc:
        debug_logger.log_warning(f"[agent-captcha] 求解失败: {type(exc).__name__}: {exc}")
    return False
