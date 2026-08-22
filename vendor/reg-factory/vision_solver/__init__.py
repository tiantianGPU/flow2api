# -*- coding: utf-8 -*-
"""
vision_solver — 通用视觉验证码求解器（库）

用 CaptchaSpec 描述一类验证码（frame/选择器/prompt/交互模式），用多模型视觉投票求解，
通用 driver 据答案驱动浏览器（多选点格子+Verify / 单选导航+Submit）。

快速用法：
    from vision_solver import solve, CaptchaSpec
    spec = CaptchaSpec.from_json("vision_solver/presets/recaptcha_v2.json")
    ok = await solve(page, spec)

内核（ask_vision / vote_answer / vote_picklist / 图像工具）从 common/agent_captcha
复制而来，独立演进，不影响现有 GitHub Arkose 流程。视觉网关 key 复用 .env 现有变量。
"""

from .schema import CaptchaSpec, build_prompt, GRID_PROMPT, SINGLE_PROMPT, DRAG_PROMPT
from .solver import solve, VisionSolver
from .vision import ask_vision, vote_answer, vote_picklist, vote_points
from .imaging import (
    shot_element, screenshot_frame_region, stitch_options_grid,
    enhance_local, annotate_choice, parse_json_answer,
    overlay_grid_numbers, annotate_canvas_choice,
)

__all__ = [
    "CaptchaSpec", "build_prompt", "GRID_PROMPT", "SINGLE_PROMPT", "DRAG_PROMPT",
    "solve", "VisionSolver",
    "ask_vision", "vote_answer", "vote_picklist", "vote_points",
    "shot_element", "screenshot_frame_region", "stitch_options_grid",
    "enhance_local", "annotate_choice", "parse_json_answer",
    "overlay_grid_numbers", "annotate_canvas_choice",
]
