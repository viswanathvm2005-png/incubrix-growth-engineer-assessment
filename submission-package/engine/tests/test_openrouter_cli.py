from engine.__main__ import build_parser


def test_generate_defaults_to_mock_provider():
    args = build_parser().parse_args([
        "generate",
        "--brief",
        "inputs/sample-brief.json",
    ])
    assert args.provider == "mock"


def test_generate_accepts_openrouter_provider():
    args = build_parser().parse_args([
        "generate",
        "--brief",
        "inputs/sample-brief.json",
        "--provider",
        "openrouter",
    ])
    assert args.provider == "openrouter"


def test_generate_still_accepts_mock_provider_explicitly():
    args = build_parser().parse_args([
        "generate",
        "--brief",
        "inputs/sample-brief.json",
        "--provider",
        "mock",
    ])
    assert args.provider == "mock"
