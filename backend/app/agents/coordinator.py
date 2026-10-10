import logging
from uuid import uuid4, UUID
from datetime import datetime, timezone
import time

from app.schemas.prediction import PredictionRequest, PredictionResponse, PredictionStatus
from .interfaces import MemoryStore, ForecastingEngine, ExplanationEngine
from .context import OrchestrationContext
from .stages import StageResult, StageName, StageStatus
from .exceptions import WorkflowAbortedError

logger = logging.getLogger(__name__)

class WorkflowCoordinator:
    def __init__(
        self,
        memory_store: MemoryStore,
        forecasting_engine: ForecastingEngine,
        explanation_engine: ExplanationEngine
    ):
        self.memory = memory_store
        self.forecast = forecasting_engine
        self.explain = explanation_engine

    async def execute_prediction(self, request: PredictionRequest) -> tuple[PredictionResponse, OrchestrationContext]:
        ctx = OrchestrationContext(request=request)
        prediction_id = uuid4()
        
        try:
            await self._run_recall(ctx)
            await self._run_analyze(ctx)
            await self._run_predict(ctx)
            await self._run_explain(ctx)
        except Exception as e:
            logger.exception("Orchestration pipeline failed unrecoverably")
            ctx.stage_results.append(StageResult(
                stage=StageName.PREDICT, # Catch-all for fatal unexpected
                status=StageStatus.FAILED,
                message=f"Unexpected error: {str(e)}"
            ))
            
        # Determine overall status
        overall_status = PredictionStatus.UNAVAILABLE
        if ctx.probability is not None:
            overall_status = PredictionStatus.COMPLETED

        response = PredictionResponse(
            prediction_id=prediction_id,
            competitor_id=request.competitor_id,
            cluster=request.cluster,
            cutoff_date=request.cutoff_date,
            horizon_days=request.horizon_days,
            probability=ctx.probability,
            model_version=ctx.model_version,
            explanation=ctx.explanation,
            evidence_ids=[e.evidence_id for e in ctx.valid_historical_evidence],
            created_at=datetime.now(timezone.utc),
            status=overall_status
        )
        
        # RETAIN runs after response construction
        await self._run_retain(prediction_id, response, ctx)
        
        return response, ctx

    async def _run_recall(self, ctx: OrchestrationContext):
        start = time.perf_counter()
        try:
            evidence = await self.memory.recall_evidence(
                competitor_id=ctx.request.competitor_id,
                cluster=ctx.request.cluster
            )
            ctx.recalled_evidence = evidence
            duration = (time.perf_counter() - start) * 1000
            ctx.stage_results.append(StageResult(
                stage=StageName.RECALL,
                status=StageStatus.COMPLETED,
                message=f"Recalled {len(evidence)} evidence items",
                duration_ms=duration,
                records_affected=[str(e.evidence_id) for e in evidence]
            ))
        except NotImplementedError:
            ctx.stage_results.append(StageResult(
                stage=StageName.RECALL,
                status=StageStatus.UNAVAILABLE,
                message="Memory store interface not implemented",
                duration_ms=(time.perf_counter() - start) * 1000
            ))
        except Exception as e:
            logger.error(f"RECALL stage failed: {e}")
            ctx.stage_results.append(StageResult(
                stage=StageName.RECALL,
                status=StageStatus.FAILED,
                message="Memory store recall failed",
                duration_ms=(time.perf_counter() - start) * 1000
            ))

    async def _run_analyze(self, ctx: OrchestrationContext):
        start = time.perf_counter()
        
        # Filter for historical integrity using observation_time
        valid = []
        for e in ctx.recalled_evidence:
            if e.observation_time <= ctx.request.cutoff_date:
                valid.append(e)
                
        ctx.valid_historical_evidence = valid
        
        duration = (time.perf_counter() - start) * 1000
        msg = f"Filtered {len(ctx.recalled_evidence)} down to {len(valid)} historically valid items."
        
        if not valid and ctx.recalled_evidence:
            msg += " No valid historical evidence remained."
            
        ctx.stage_results.append(StageResult(
            stage=StageName.ANALYZE,
            status=StageStatus.COMPLETED,
            message=msg,
            duration_ms=duration,
            records_affected=[str(e.evidence_id) for e in valid]
        ))

    async def _run_predict(self, ctx: OrchestrationContext):
        start = time.perf_counter()
        
        payload = ctx.build_analysis_payload()
        try:
            res = await self.forecast.predict_action(payload)
            if res.get("status") == "unavailable":
                ctx.stage_results.append(StageResult(
                    stage=StageName.PREDICT,
                    status=StageStatus.UNAVAILABLE,
                    message="Forecasting service is configured but unavailable",
                    duration_ms=(time.perf_counter() - start) * 1000
                ))
            else:
                ctx.probability = res.get("probability")
                # Validate probability bounds
                if ctx.probability is not None and not (0.0 <= ctx.probability <= 1.0):
                    raise ValueError(f"Probability {ctx.probability} is out of bounds [0.0, 1.0]")
                    
                ctx.model_version = res.get("model_version")
                ctx.stage_results.append(StageResult(
                    stage=StageName.PREDICT,
                    status=StageStatus.COMPLETED,
                    message=f"Forecasting complete. Probability: {ctx.probability}",
                    duration_ms=(time.perf_counter() - start) * 1000
                ))
        except NotImplementedError:
            ctx.stage_results.append(StageResult(
                stage=StageName.PREDICT,
                status=StageStatus.UNAVAILABLE,
                message="Forecasting interface not implemented",
                duration_ms=(time.perf_counter() - start) * 1000
            ))
        except Exception as e:
            logger.error(f"PREDICT stage failed: {e}")
            ctx.probability = None # fail safe
            ctx.stage_results.append(StageResult(
                stage=StageName.PREDICT,
                status=StageStatus.FAILED,
                message=f"Forecasting execution failed: {str(e)}",
                duration_ms=(time.perf_counter() - start) * 1000
            ))

    async def _run_explain(self, ctx: OrchestrationContext):
        start = time.perf_counter()
        if ctx.probability is None:
            ctx.stage_results.append(StageResult(
                stage=StageName.EXPLAIN,
                status=StageStatus.SKIPPED,
                message="Skipped explanation because forecasting was unavailable/failed.",
                duration_ms=(time.perf_counter() - start) * 1000
            ))
            return
            
        payload = {
            "prediction": ctx.probability,
            "evidence": [e.description for e in ctx.valid_historical_evidence]
        }
        
        try:
            explanation = await self.explain.generate_explanation(payload)
            if explanation is None:
                ctx.stage_results.append(StageResult(
                    stage=StageName.EXPLAIN,
                    status=StageStatus.UNAVAILABLE,
                    message="Explanation engine is unavailable",
                    duration_ms=(time.perf_counter() - start) * 1000
                ))
            else:
                ctx.explanation = explanation
                ctx.stage_results.append(StageResult(
                    stage=StageName.EXPLAIN,
                    status=StageStatus.COMPLETED,
                    message="Explanation generated successfully",
                    duration_ms=(time.perf_counter() - start) * 1000
                ))
        except NotImplementedError:
            ctx.stage_results.append(StageResult(
                stage=StageName.EXPLAIN,
                status=StageStatus.UNAVAILABLE,
                message="Explanation interface not implemented",
                duration_ms=(time.perf_counter() - start) * 1000
            ))
        except Exception as e:
            logger.error(f"EXPLAIN stage failed: {e}")
            ctx.stage_results.append(StageResult(
                stage=StageName.EXPLAIN,
                status=StageStatus.FAILED,
                message="Explanation generation failed",
                duration_ms=(time.perf_counter() - start) * 1000
            ))

    async def _run_retain(self, prediction_id: UUID, response: PredictionResponse, ctx: OrchestrationContext):
        start = time.perf_counter()
        
        payload = response.model_dump(mode="json")
        payload["trace"] = [s.model_dump(mode="json") for s in ctx.stage_results]
        if ctx.explanation:
            payload["explanation"] = ctx.explanation
            
        try:
            success = await self.memory.retain_prediction(prediction_id, payload)
            if success:
                ctx.stage_results.append(StageResult(
                    stage=StageName.RETAIN,
                    status=StageStatus.COMPLETED,
                    message="Prediction retained in memory store",
                    duration_ms=(time.perf_counter() - start) * 1000
                ))
            else:
                ctx.stage_results.append(StageResult(
                    stage=StageName.RETAIN,
                    status=StageStatus.FAILED,
                    message="Memory store rejected retention",
                    duration_ms=(time.perf_counter() - start) * 1000
                ))
        except NotImplementedError:
            ctx.stage_results.append(StageResult(
                stage=StageName.RETAIN,
                status=StageStatus.UNAVAILABLE,
                message="Retention interface not implemented",
                duration_ms=(time.perf_counter() - start) * 1000
            ))
        except Exception as e:
            logger.error(f"RETAIN stage failed: {e}")
            ctx.stage_results.append(StageResult(
                stage=StageName.RETAIN,
                status=StageStatus.FAILED,
                message="Retention execution failed",
                duration_ms=(time.perf_counter() - start) * 1000
            ))
