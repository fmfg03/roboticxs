from __future__ import annotations


def build_token_usage_event(
    *,
    user_id: str,
    robot_id: str,
    task_id: str,
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    estimated_cost_usd: float,
) -> dict[str, str | int | float]:
    return {
        "user_id": user_id,
        "robot_id": robot_id,
        "task_id": task_id,
        "provider": provider,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost_usd": estimated_cost_usd,
        "status": "estimated",
    }
