"""DuckOS gaming policy, process detection and session lifecycle primitives."""
from .detection import GamingDetectionError, detect_game_processes, enumerate_host_processes, load_game_profiles
from .policy import GamingPolicyError, assess_capabilities, load_rule_catalog, plan_session_transition

__all__ = [
    "GamingDetectionError",
    "GamingPolicyError",
    "assess_capabilities",
    "detect_game_processes",
    "enumerate_host_processes",
    "load_game_profiles",
    "load_rule_catalog",
    "plan_session_transition",
]
