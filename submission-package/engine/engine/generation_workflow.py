"""Orchestration layer for provider-independent content generation.

The workflow validates inputs and provider results. It does not publish content
or establish that generated product claims are factually true.
"""
from typing import Protocol

from .generation_contract import (
    GenerationRequest,
    GenerationResult,
    GenerationStatus,
    validate_generation_result,
)
from .factual_language_review import find_factual_language_flags


class GenerationProvider(Protocol):
    """Interface that mock and future real providers must implement."""

    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Return a structured generation result."""
        ...


class GenerationWorkflow:
    """Run a provider and consistently validate its structured response."""

    def __init__(self, provider: GenerationProvider):
        self.provider = provider

    def run(self, request: GenerationRequest) -> GenerationResult:
        """Generate drafts and reject structurally invalid provider output."""
        result = self.provider.generate(request)
        result = validate_generation_result(request, result)

        factual_warnings = []
        for draft in result.drafts:
            texts = [draft.hook, draft.caption]
            if draft.video_script:
                texts.extend(draft.video_script)
            for warning in find_factual_language_flags(*texts):
                if warning not in factual_warnings:
                    factual_warnings.append(warning)

        if factual_warnings:
            existing_warnings = list(result.warnings)
            for warning in factual_warnings:
                if warning not in existing_warnings:
                    existing_warnings.append(warning)
            result = result.model_copy(update={"warnings": existing_warnings})

        return result


def run_generation(
    request: GenerationRequest,
    provider: GenerationProvider,
) -> GenerationResult:
    """Convenience function for running one generation request."""
    return GenerationWorkflow(provider).run(request)


def describe_generation_result(result: GenerationResult) -> dict:
    """Return a simple serializable status summary for logs or a CLI."""
    return {
        "brief_id": result.brief_id,
        "status": result.status.value,
        "draft_count": len(result.drafts),
        "provider_name": result.provider_name,
        "model_name": result.model_name,
        "warnings": list(result.warnings),
        "is_success": result.status == GenerationStatus.SUCCESS,
    }
