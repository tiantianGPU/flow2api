# -*- coding: utf-8 -*-
"""
vision_solver/solver.py — VisionSolver：按 CaptchaSpec 编排求解
"""

from .schema import CaptchaSpec
from .drivers import solve_grid_select, solve_single_pick, solve_canvas_grid, solve_canvas_drag


async def solve(page, spec, shot_dir="screenshots_vision"):
    """通用入口：在 page 上按 spec 求解一个视觉验证码。
    page: Playwright Page（验证码已触发/已出现）。
    spec: CaptchaSpec 或 dict 或 json 路径。
    返回 True=通过 / False=失败。"""
    if isinstance(spec, str):
        spec = CaptchaSpec.from_json(spec)
    elif isinstance(spec, dict):
        spec = CaptchaSpec.from_dict(spec)
    if spec.mode == "grid_select":
        return await solve_grid_select(page, spec, shot_dir)
    if spec.mode == "single_pick":
        return await solve_single_pick(page, spec, shot_dir)
    if spec.mode == "canvas_grid":
        return await solve_canvas_grid(page, spec, shot_dir)
    if spec.mode == "canvas_drag":
        return await solve_canvas_drag(page, spec, shot_dir)
    raise ValueError(f"unknown mode: {spec.mode}")


class VisionSolver:
    """面向对象封装，便于复用同一 spec 多次求解。"""

    def __init__(self, spec, shot_dir="screenshots_vision"):
        if isinstance(spec, str):
            spec = CaptchaSpec.from_json(spec)
        elif isinstance(spec, dict):
            spec = CaptchaSpec.from_dict(spec)
        self.spec = spec
        self.shot_dir = shot_dir

    async def solve(self, page):
        return await solve(page, self.spec, self.shot_dir)
