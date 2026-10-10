class OrchestrationError(Exception):
    """Base exception for orchestration failures."""
    pass

class WorkflowAbortedError(OrchestrationError):
    """Raised when a workflow must halt immediately due to a critical missing prerequisite."""
    pass
