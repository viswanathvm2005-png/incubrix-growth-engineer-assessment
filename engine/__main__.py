"""CLI for source intake, asset history, generation, pipeline runs, and human review."""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from pydantic import ValidationError

from .content_brief import ContentBrief
from .generation_contract import GenerationRequest
from .generation_workflow import GenerationWorkflow
from .history_cli import (
    find_asset_duplicates,
    revise_asset,
    save_asset,
    show_asset_history,
)
from .mock_provider import MockGenerationProvider
from .openrouter_provider import OpenRouterGenerationProvider
from .output_store import save_generation_result
from .review_store import ReviewStore
from .revision_workflow import save_generated_draft
from .source_intake import intake_source


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="engine",
        description="Source validation, asset history, generation, and review.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    intake_parser = subparsers.add_parser(
        "intake",
        help="Validate a candidate-provided .txt or .md source.",
    )
    intake_parser.add_argument("--input", required=True)
    intake_parser.add_argument("--source-id", required=True)
    intake_parser.add_argument("--max-bytes", type=int, default=5 * 1024 * 1024)

    history_parser = subparsers.add_parser(
        "history",
        help="Save, revise, show, or check asset history.",
    )
    history_subparsers = history_parser.add_subparsers(
        dest="history_action",
        required=True,
    )

    def add_database_argument(command_parser):
        command_parser.add_argument(
            "--database",
            default="data/asset-history.sqlite3",
            help="SQLite database path.",
        )

    save_parser = history_subparsers.add_parser(
        "save", help="Save the first version of an asset JSON file."
    )
    save_parser.add_argument("--asset", required=True)
    add_database_argument(save_parser)

    revise_parser = history_subparsers.add_parser(
        "revise", help="Append the next version of an existing asset."
    )
    revise_parser.add_argument("--asset", required=True)
    add_database_argument(revise_parser)

    show_parser = history_subparsers.add_parser(
        "show", help="Show all saved versions for an asset ID."
    )
    show_parser.add_argument("--asset-id", required=True)
    add_database_argument(show_parser)

    duplicates_parser = history_subparsers.add_parser(
        "duplicates", help="Check for similar assets requiring human review."
    )
    duplicates_parser.add_argument("--asset", required=True)
    duplicates_parser.add_argument("--threshold", type=float, default=0.85)
    add_database_argument(duplicates_parser)

    generate_parser = subparsers.add_parser(
        "generate", help="Generate content drafts using a selected provider."
    )
    generate_parser.add_argument("--brief", required=True)
    generate_parser.add_argument(
        "--request-id",
        default="cli-generation-001",
        help="Unique identifier for this generation request.",
    )
    generate_parser.add_argument(
        "--draft-count", type=int, default=3,
        help="Number of drafts to request (1-10).",
    )
    generate_parser.add_argument(
        "--authorized-capability-ids",
        nargs="*",
        default=[],
        help="Capability IDs explicitly authorized for this request.",
    )
    generate_parser.add_argument(
        "--provider",
        choices=["mock", "openrouter"],
        default="mock",
        help="Provider to use; OpenRouter requires a local API key.",
    )
    generate_parser.add_argument(
        "--save-output",
        action="store_true",
        help="Save successful generation results as JSON.",
    )
    generate_parser.add_argument(
        "--output-dir", default="outputs",
        help="Directory for saved generation JSON files.",
    )

    review_parser = subparsers.add_parser(
        "review", help="Submit and manage human reviews of generated drafts."
    )
    review_subparsers = review_parser.add_subparsers(
        dest="review_action", required=True
    )

    review_submit = review_subparsers.add_parser(
        "submit", help="Submit drafts from a saved generation JSON file."
    )
    review_submit.add_argument("--output", required=True)
    review_submit.add_argument(
        "--database",
        default="data/content-reviews.sqlite3",
        help="Review database path.",
    )

    review_list = review_subparsers.add_parser(
        "list", help="List review records."
    )
    review_list.add_argument(
        "--status",
        choices=["pending", "approved", "rejected"],
        default=None,
    )
    review_list.add_argument(
        "--database", default="data/content-reviews.sqlite3"
    )

    review_show = review_subparsers.add_parser(
        "show", help="Show a draft and its review record."
    )
    review_show.add_argument("--brief-id", required=True)
    review_show.add_argument("--draft-id", required=True)
    review_show.add_argument(
        "--database", default="data/content-reviews.sqlite3"
    )

    review_decide = review_subparsers.add_parser(
        "decide", help="Approve or reject a pending draft."
    )
    review_decide.add_argument("--brief-id", required=True)
    review_decide.add_argument("--draft-id", required=True)
    review_decide.add_argument(
        "--decision", required=True, choices=["approved", "rejected"]
    )
    review_decide.add_argument("--reviewer", required=True)
    review_decide.add_argument(
        "--feedback",
        default="",
        help="Required when rejecting a draft.",
    )
    review_decide.add_argument(
        "--database", default="data/content-reviews.sqlite3"
    )

    revision_parser = subparsers.add_parser(
        "revision",
        help="Save a generated draft as a versioned asset.",
    )
    revision_subparsers = revision_parser.add_subparsers(
        dest="revision_action",
        required=True,
    )
    revision_save = revision_subparsers.add_parser(
        "save",
        help="Save one generated draft to asset history as a pending draft.",
    )
    revision_save.add_argument("--output", required=True,
                               help="Saved generation-result JSON file.")
    revision_save.add_argument("--draft-id", required=True)
    revision_save.add_argument("--asset-id", required=True)
    revision_save.add_argument("--source-id", required=True)
    revision_save.add_argument(
        "--platform",
        required=True,
        choices=["linkedin", "instagram", "youtube_shorts", "tiktok",
                 "x", "threads", "facebook", "reddit"],
    )
    revision_save.add_argument(
        "--asset-format",
        required=True,
        choices=["text", "graphic", "carousel", "video"],
    )
    revision_save.add_argument("--utm-url", required=True)
    revision_save.add_argument("--target-metric", required=True)
    revision_save.add_argument("--created-by-run-id", required=True)
    revision_save.add_argument("--video-duration-seconds", type=float)
    revision_save.add_argument("--aspect-ratio")
    revision_save.add_argument("--final-file")
    revision_save.add_argument("--editable-source-file")
    revision_save.add_argument(
        "--database",
        default="data/asset-history.sqlite3",
        help="SQLite asset-history database path.",
    )

    pipeline_parser = subparsers.add_parser(
        "pipeline",
        help="Run one long input through generation, checks, dedupe, and export.",
    )
    pipeline_parser.add_argument("--input", required=True, help=".txt or .md source.")
    pipeline_parser.add_argument("--source-id", required=True)
    pipeline_parser.add_argument(
        "--provider", choices=["mock", "openrouter"], default="mock",
        help="mock = offline test provider; openrouter needs a local API key.",
    )
    pipeline_parser.add_argument("--per-platform", type=int, default=4,
                                 help="Drafts per platform (1-10).")
    pipeline_parser.add_argument("--config", default="config/pipeline-config.yaml")
    pipeline_parser.add_argument("--out-dir", default="outputs/pipeline-runs")
    pipeline_parser.add_argument("--ledger", default=None,
                                 help="Duplicate ledger path (default from config).")
    pipeline_parser.add_argument("--utm-base", default=None,
                                 help="Approved destination URL; unknown if omitted.")
    pipeline_parser.add_argument("--campaign", default="incubrix_content_engine")
    pipeline_parser.add_argument("--start-date", default=None, help="YYYY-MM-DD.")
    pipeline_parser.add_argument("--cta",
                                 default="Save this for your next content-planning session.")
    pipeline_parser.add_argument("--similarity-threshold", type=float, default=None)
    pipeline_parser.add_argument("--simulate-failure-once", action="store_true",
                                 help="Demo flag: fail the first provider call to show retry.")
    pipeline_parser.add_argument("--refresh", action="store_true",
                                 help="Update existing items for the same source-id in place.")

    return parser


def run_generation_command(args) -> dict:
    """Load a brief, select a provider, and validate the result."""
    brief_path = Path(args.brief)
    raw_text = brief_path.read_text(encoding="utf-8-sig")
    brief_data = json.loads(raw_text)
    brief = ContentBrief.model_validate(brief_data)

    request = GenerationRequest(
        request_id=args.request_id,
        brief=brief,
        requested_draft_count=args.draft_count,
        authorized_capability_ids=args.authorized_capability_ids,
    )

    if args.provider == "mock":
        provider = MockGenerationProvider()
    elif args.provider == "openrouter":
        provider = OpenRouterGenerationProvider()
    else:
        raise ValueError(f"Unsupported provider: {args.provider}")

    result = GenerationWorkflow(provider).run(request)
    return result.model_dump(mode="json")


def run_review_command(args) -> dict:
    """Run one review operation using the persistent review store."""
    store = ReviewStore(args.database)

    if args.review_action == "submit":
        return store.submit_output(args.output)

    if args.review_action == "list":
        return store.list_reviews(status=args.status)

    if args.review_action == "show":
        return store.show_review(args.brief_id, args.draft_id)

    if args.review_action == "decide":
        if not args.reviewer.strip():
            raise ValueError("A non-empty reviewer identity is required.")
        if args.decision == "rejected" and not args.feedback.strip():
            raise ValueError("Feedback is required when rejecting a draft.")
        return store.decide(
            brief_id=args.brief_id,
            draft_id=args.draft_id,
            decision=args.decision,
            reviewer=args.reviewer,
            feedback=args.feedback,
        )

    raise ValueError("Unsupported review action.")


def run_revision_command(args) -> dict:
    """Save a selected generated draft as a pending asset-history version."""
    from .generation_contract import GenerationResult

    output_path = Path(args.output)
    result_data = json.loads(output_path.read_text(encoding="utf-8-sig"))
    result = GenerationResult.model_validate(result_data)

    if result.status.value != "success":
        raise ValueError("Only successful generation results can be imported.")

    matching = [draft for draft in result.drafts if draft.draft_id == args.draft_id]
    if len(matching) != 1:
        raise ValueError(
            f"Expected exactly one draft with ID {args.draft_id!r}; "
            f"found {len(matching)}."
        )

    saved = save_generated_draft(
        matching[0],
        database_path=args.database,
        asset_id=args.asset_id,
        source_id=args.source_id,
        platform=args.platform,
        asset_format=args.asset_format,
        utm_url=args.utm_url,
        target_metric=args.target_metric,
        created_by_run_id=args.created_by_run_id,
        video_duration_seconds=args.video_duration_seconds,
        aspect_ratio=args.aspect_ratio,
        final_file=args.final_file,
        editable_source_file=args.editable_source_file,
    )
    return saved

def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "intake":
            result = intake_source(
                args.input,
                source_id=args.source_id,
                max_bytes=args.max_bytes,
            )
            print(json.dumps(
                result.model_dump(mode="json"),
                ensure_ascii=False,
                indent=2,
            ))
            return 0 if result.status == "ACCEPTED" else 1

        if args.command == "history":
            if args.history_action == "save":
                result = save_asset(args.asset, args.database)
            elif args.history_action == "revise":
                result = revise_asset(args.asset, args.database)
            elif args.history_action == "show":
                result = show_asset_history(args.asset_id, args.database)
            elif args.history_action == "duplicates":
                result = find_asset_duplicates(
                    args.asset, args.database, args.threshold
                )
            else:
                parser.error("Unsupported history action.")
                return 2

            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0

        if args.command == "generate":
            result = run_generation_command(args)
            if args.save_output:
                if result.get("status") != "success":
                    raise ValueError(
                        "Only successful generation results can be saved."
                    )
                result["saved_output"] = save_generation_result(
                    result, output_dir=args.output_dir
                )
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0

        if args.command == "pipeline":
            from .pipeline import PipelineError, run_pipeline
            if args.provider == "mock":
                provider = MockGenerationProvider()
            else:
                provider = OpenRouterGenerationProvider()
            try:
                record = run_pipeline(
                    input_path=args.input, source_id=args.source_id,
                    provider=provider, provider_name=args.provider,
                    config_path=args.config, out_dir=args.out_dir,
                    per_platform=args.per_platform, utm_base=args.utm_base,
                    campaign=args.campaign, start_date=args.start_date,
                    cta=args.cta, similarity_threshold=args.similarity_threshold,
                    simulate_failure_once=args.simulate_failure_once,
                    ledger_path=args.ledger, refresh=args.refresh,
                )
            except PipelineError as exc:
                raise ValueError(str(exc)) from exc
            print(json.dumps(record, ensure_ascii=False, indent=2))
            return 1 if record["status"] == "failed" else 0

        if args.command == "review":
            result = run_review_command(args)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0

        if args.command == "revision":
            if args.revision_action == "save":
                result = run_revision_command(args)
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return 0
    except (
        ValueError,
        OSError,
        RuntimeError,
        ValidationError,
        sqlite3.Error,
    ) as exc:
        print(json.dumps({
            "status": "ERROR",
            "message": str(exc),
        }, ensure_ascii=False, indent=2))
        return 1

    parser.error("Unsupported command.")
    return 2


if __name__ == "__main__":
    sys.exit(main())


