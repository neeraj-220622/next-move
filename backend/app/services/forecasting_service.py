"""
Forecasting service — Phase 5C implementation.

This module provides a replaceable interface for numerical prediction.
The backend is selected via the ``FORECASTING_MODEL`` environment variable.

Design constraints
------------------
* Hindsight (memory), LLM (explanation), and forecasting (numbers) are
  separate services.  This module must not call ``HindsightService`` or
  ``LLMService`` directly; orchestration happens in the agent layer.
* The forecasting backend (baseline / sklearn / xgboost) is selected via
  the ``FORECASTING_MODEL`` environment variable.
* A baseline heuristic is always available as fallback; it is clearly
  labelled ``model_version="baseline"`` and must never be misrepresented
  as a trained model.
* When the sklearn backend is selected, model artifacts must be present
  at ``backend/models/forecasting_model.pkl`` and ``metadata.json``.
  Missing artifacts degrade availability to ``DEGRADED``; prediction calls
  return an explicit unavailability result rather than falling back silently.

Training details (Phase 5C)
---------------------------
Trained on 2,000 synthetic observations using chronological splitting
(TimeSeriesSplit, n_splits=5) with a LogisticRegression model.
Features: evidence_count, horizon_days, cluster one-hot encoding.
Metrics (test split): Brier=0.197, AUC=0.739, Accuracy=0.694.

Limitation: the model is trained on synthetic data; real-world performance
is unknown.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

from app.core.config import Settings, get_settings
from app.schemas.common import DependencyInfo, ServiceStatus

logger = logging.getLogger(__name__)

# Path relative to this file: ../../models/
_MODELS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "models")
)
_MODEL_PATH = os.path.join(_MODELS_DIR, "forecasting_model.pkl")
_METADATA_PATH = os.path.join(_MODELS_DIR, "metadata.json")


class ForecastingService:
    """
    Numerical prediction layer for competitor action forecasting.

    Backends
    --------
    * ``baseline``             — Cluster-based heuristic; always available.
    * ``sklearn``/``scikit-learn`` — LogisticRegression trained on synthetic
                                 data (Phase 5C); requires artifacts under
                                 ``backend/models/``.
    * ``xgboost``              — Planned; not yet trained.

    Phase 5C — implemented
    ──────────────────────
    * ``check_availability``      — reports whether the configured backend
                                   and its model artifacts are loadable.
    * ``predict_competitor_action`` — returns a calibrated probability using
                                   the loaded model, or an explicit error
                                   status if artifacts are missing.

    Remaining limitation
    ────────────────────
    * ``evaluate_prediction`` — requires an observed binary outcome field
                                not yet present in the prediction schema.
                                Implemented as a documented stub.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._model = None
        self._metadata: dict[str, Any] | None = None

        backend = self._settings.forecasting_model.lower()
        if backend in {"sklearn", "scikit-learn"}:
            self._try_load_model()

    def _try_load_model(self) -> None:
        """Attempt to load the pickled sklearn model and metadata JSON."""
        try:
            import joblib

            if os.path.exists(_MODEL_PATH) and os.path.exists(_METADATA_PATH):
                self._model = joblib.load(_MODEL_PATH)
                with open(_METADATA_PATH, "r") as f:
                    self._metadata = json.load(f)
                version = self._metadata.get("version", "unknown")
                metrics = self._metadata.get("metrics", {})
                logger.info(
                    "Forecasting model loaded version=%s auc=%.3f brier=%.3f",
                    version,
                    metrics.get("roc_auc", 0.0),
                    metrics.get("brier_score", 0.0),
                )
            else:
                logger.warning(
                    "Forecasting model artifacts not found at %s — "
                    "predictions will return unavailable",
                    _MODELS_DIR,
                )
        except Exception as exc:
            logger.error("Failed to load forecasting model: %s", exc)

    # ── Availability check ────────────────────────────────────────────────────

    def check_availability(self) -> DependencyInfo:
        """
        Report which forecasting backend is configured and if it is usable.

        The ``baseline`` backend is always available.  ``sklearn`` reports
        ``ok`` only when both scikit-learn is importable AND model artifacts
        are loaded; missing artifacts degrade to ``DEGRADED``.
        """
        backend = self._settings.forecasting_model.lower()

        if backend == "baseline":
            return DependencyInfo(
                name="forecasting",
                status=ServiceStatus.OK,
                message="Baseline (heuristic) forecasting — no ML dependencies required.",
            )

        if backend in {"sklearn", "scikit-learn"}:
            try:
                import sklearn  # noqa: F401

                if self._model is None or self._metadata is None:
                    return DependencyInfo(
                        name="forecasting",
                        status=ServiceStatus.DEGRADED,
                        message=(
                            f"scikit-learn {sklearn.__version__} available, "
                            "but model artifacts (pkl/json) are missing. "
                            f"Run: python scripts/train_forecasting_model.py"
                        ),
                    )
                version = self._metadata.get("version", "unknown")
                metrics = self._metadata.get("metrics", {})
                return DependencyInfo(
                    name="forecasting",
                    status=ServiceStatus.OK,
                    message=(
                        f"scikit-learn {sklearn.__version__} — model v{version} loaded "
                        f"(AUC={metrics.get('roc_auc', 0):.3f}, trained on synthetic data)."
                    ),
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
                    status=ServiceStatus.DEGRADED,
                    message=(
                        f"XGBoost {xgboost.__version__} installed, "
                        "but no trained model artifacts exist yet."
                    ),
                )
            except ImportError:
                return DependencyInfo(
                    name="forecasting",
                    status=ServiceStatus.UNAVAILABLE,
                    message="xgboost is not installed. Run: pip install xgboost",
                )

        return DependencyInfo(
            name="forecasting",
            status=ServiceStatus.UNKNOWN,
            message=f"Unknown FORECASTING_MODEL value: '{backend}'.",
        )

    # ── Prediction ────────────────────────────────────────────────────────────

    def predict_competitor_action(
        self, features: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Predict the probability of a future competitor action.

        Parameters
        ----------
        features:
            Structured feature dict from ``OrchestrationContext.build_analysis_payload()``.
            Expected keys: ``evidence_count``, ``horizon_days``, ``cluster``.

        Returns
        -------
        dict with keys:
            * ``status``        — ``"ok"``, ``"unavailable"``, or ``"error"``
            * ``probability``   — float in [0, 1] (only when status="ok")
            * ``model_version`` — version string; ``"baseline"`` for heuristic
            * ``message``       — present when status != "ok"

        Notes
        -----
        When the sklearn backend is selected but artifacts are missing, returns
        ``status="unavailable"`` rather than silently falling back to baseline.
        This makes model availability explicit in the prediction trace.
        """
        backend = self._settings.forecasting_model.lower()

        if backend in {"sklearn", "scikit-learn"}:
            if not self._model or not self._metadata:
                logger.warning(
                    "Forecasting prediction requested but model artifacts missing "
                    "(backend=%s). Returning unavailable.",
                    backend,
                )
                return {
                    "status": "unavailable",
                    "message": "sklearn model artifacts missing — run train_forecasting_model.py",
                }

            t0 = time.perf_counter()
            try:
                import pandas as pd

                # Build feature vector matching training schema
                input_data = {
                    "evidence_count": features.get("evidence_count", 0),
                    "horizon_days": features.get("horizon_days", 30),
                    "cluster_marketing_blitz": 0,
                    "cluster_price_cut": 0,
                    "cluster_product_launch": 0,
                }

                cluster_name = features.get("cluster", "")
                if cluster_name in {"marketing_blitz", "price_cut", "product_launch"}:
                    input_data[f"cluster_{cluster_name}"] = 1

                df = pd.DataFrame([input_data])[self._metadata["features"]]
                prob = float(self._model.predict_proba(df)[0][1])
                latency_ms = (time.perf_counter() - t0) * 1000
                version = self._metadata.get("version", "unknown")
                logger.info(
                    "Forecasting inference OK backend=sklearn version=%s "
                    "probability=%.3f latency_ms=%.1f",
                    version,
                    prob,
                    latency_ms,
                )
                return {
                    "status": "ok",
                    "probability": prob,
                    "model_version": version,
                }
            except Exception as exc:
                latency_ms = (time.perf_counter() - t0) * 1000
                logger.error(
                    "Forecasting inference failed backend=sklearn latency_ms=%.1f: %s",
                    latency_ms,
                    exc,
                )
                return {"status": "error", "message": "Model inference failed."}

        # Baseline heuristic — always available, clearly labelled
        base = 0.5
        cluster = features.get("cluster", "")
        if cluster == "price_cut":
            base = 0.3
        elif cluster == "product_launch":
            base = 0.6
        elif cluster == "expansion":
            base = 0.4

        logger.debug(
            "Forecasting baseline prediction cluster=%s probability=%.2f",
            cluster,
            base,
        )
        return {
            "status": "ok",
            "probability": base,
            "model_version": "baseline",
        }

    # ── Evaluation stub ───────────────────────────────────────────────────────

    def evaluate_prediction(
        self, prediction: dict[str, Any], outcome: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Score a past prediction against an observed binary outcome.

        Current limitation
        ------------------
        The ``PredictionResponse`` schema does not yet include an
        ``observed_outcome`` field (a binary 0/1 indicating whether the
        predicted competitor action actually occurred).  Until that field
        is added to the schema and populated via a feedback endpoint,
        evaluation cannot be implemented without inventing an evaluation
        contract that the rest of the system does not support.

        When the schema is extended, this method should compute:
        - Brier score
        - Log-loss
        - Calibration (reliability diagram)

        Raises
        ------
        NotImplementedError
            Always, until the outcome schema is defined.
        """
        raise NotImplementedError(
            "evaluate_prediction requires an observed_outcome field in "
            "PredictionResponse, which is not yet defined in the schema. "
            "This will be implemented when the feedback endpoint is added."
        )
