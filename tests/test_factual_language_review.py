from engine.factual_language_review import find_factual_language_flags


def test_flags_first_person_testing_statement():
    flags = find_factual_language_flags(
        "We test API connectivity and compatibility."
    )
    assert len(flags) == 1
    assert "verify against evidence" in flags[0]


def test_flags_claim_that_assessment_checked_something():
    flags = find_factual_language_flags(
        "This assessment checks the iteration cycle length."
    )
    assert len(flags) == 1


def test_flags_results_claim():
    flags = find_factual_language_flags(
        "Results show improved performance."
    )
    assert len(flags) == 1


def test_ordinary_educational_copy_is_not_flagged():
    flags = find_factual_language_flags(
        "A clear content workflow can help teams organize their drafts."
    )
    assert flags == []


def test_empty_input_is_not_flagged():
    assert find_factual_language_flags("", None) == []


def test_flag_does_not_change_or_reject_text():
    text = "We measured turnaround time."
    flags = find_factual_language_flags(text)
    assert flags
    assert text == "We measured turnaround time."
