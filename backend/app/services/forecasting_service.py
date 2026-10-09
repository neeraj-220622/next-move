"""
Forecasting service — Phase 1 interface definition.

This module defines a minimal, replaceable interface for the numerical
prediction layer.  No model is loaded or trained in Phase 1.

Design constraints
------------------
* Hindsight (memory), LLM (explanation), and forecasting (numbers) are
  separate services.  This module must not call ``HindsightService`` or
  ``LLMService`` directly; orchestration happens in the agent layer (Phase 4).
* The forecasting backend (baseline / sklearn / xgboost) is selected via
  the ``FORECASTING_MODEL`` environment variable.
* All methods that are not yet implemented raise ``NotImplementedError``
  with a clear message indicating the target phase.
"""

from __future__ import annotations

import logging
from typing import Any

from app.core.config import Settings, get_settings
from app.schemas.common import DependencyInfo, ServiceStatus

logger = logging.getLogger(__name__)


class ForecastingService:
    """
    Minimal forecasting interface — numerical prediction layer.

    Phase 1 — implemented
    ─────────────────────
    * ``check_availability`` — report which backend is configured and
      whether its dependencies are importable.

    Phase 4 / 5 — planned
    ──────────────────────
    * ``predict_competitor_action`` — produce a probability estimate for a
      future competitor action given structured feature inputs.
    * ``evaluate_prediction``       — score a past prediction against the
      observed outcome.
    * ``list_supported_models``     — enumerate available backends.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    # ── Availability check ────────────────────────────────────────────────────

    def check_availability(self) -> DependencyInfo:
        """
        Report which forecasting backend is configured and if it is usable.

        The ``baseline`` backend is always available because it has no extra
        dependencies.  ``sklearn`` and ``xgboost`` are reported as
        ``unavailable`` if their packages are not installed.
        """
        backend = self._settings.forecasting_model.lower()

        if backend == "baseline":
            return DependencyInfo(
                name="forecasting",
                status=ServiceStatus.OK,
                message="Baseline (heuristic) forecasting — no ML dependencies required.",
            )

        # Check optional ML libraries.
        if backend in {"sklearn", "scikit-learn"}:
            try:
                import sklearn  # noqa: F401
                return DependencyInfo(
                    name="forecasting",
                    status=ServiceStatus.OK,
                    message=f"scikit-learn {sklearn.__version__} available.",
                )
            except ImportError:
                return DependencyInfo(
                    name="forecasting",
                    status=ServiceStatus.UNAVAILABLE,
                    message=(
                        "scikit-learn is not installed. "
                        "Run: pip install scikit-learn"
                    ),
                )

        if backend == "xgboost":
            try:
                import xgboost  # noqa: F401
                return DependencyInfo(
                    name="forecasting",
                    status=ServiceStatus.OK,
                    message=f"XGBoost {xgboost.__version__} available.",
                )
            except ImportError:
                return DependencyInfo(
                    name="forecasting",
                    status=ServiceStatus.UNAVAILABLE,
                    message=(
                        "xgboost is not installed. "
                        "Run: pip install xgboost"
                    ),
                )

        return DependencyInfo(
            name="forecasting",
            status=ServiceStatus.UNKNOWN,
            message=f"Unknown FORECASTING_MODEL value: '{backend}'.",
        )

    # ── Phase 4 / 5 stubs ────────────────────────────────────────────────────

    def predict_competitor_action(
        self, features: dict[str, Any]
    ) -> dict[str, Any]:
        """
        [Phase 4/5] Predict the probability of a future competitor action.

        Parameters
        ----------
        features:
            Structured feature dictionary derived from competitor signals
            and recalled Hindsight memories.

        Returns
        -------
        dict
            Prediction result including probability estimates and confidence.
        """
        raise NotImplementedError(
            "predict_competitor_action is planned for Phase 4/5."
        )

    def evaluate_prediction(
        self, prediction: dict[str, Any], outcome: dict[str, Any]
    ) -> dict[str, Any]:
        """
        [Phase 5] Score a past prediction against an observed outcome.

        Parameters
        ----------
        prediction:
            The original prediction payload.
        outcome:
            The real-world result that was observed.

        Returns
        -------
        dict
            Evaluation metrics (e.g. Brier score, accuracy, calibration).
        """
        raise NotImplementedError(
            "evaluate_prediction is planned for Phase 5."
        )
