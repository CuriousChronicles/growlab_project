from app.services.entry_level_filter import score_listing, tag_entry_level_listings


def test_entry_level_signals_mark_listing_relevant():
    listing = {
        "title": "Graduate Automation Engineer",
        "description": "Entry level role for a recent graduate with 0-2 years experience.",
    }

    result = score_listing(listing)

    assert result.relevant is True
    assert result.score > 0


def test_senior_and_years_required_mark_listing_not_relevant():
    listing = {
        "title": "Senior Automation Lead",
        "description": "Must have 5+ years required experience managing automation projects.",
    }

    result = score_listing(listing)

    assert result.relevant is False
    assert result.score < 0


def test_listing_without_entry_level_keywords_is_relevant_by_default():
    listing = {
        "title": "Automation Engineer",
        "description": "Build workflow automation with Python and cloud services.",
    }

    result = score_listing(listing)

    assert result.relevant is True
    assert result.score == 0


def test_filter_tags_keep_both_relevant_and_not_relevant():
    results = tag_entry_level_listings(
        [
            {"title": "Junior Developer", "description": "Graduate friendly."},
            {"title": "Principal Engineer", "description": "Requires 5+ years experience."},
            {"title": "Automation Engineer", "description": "Python workflow automation."},
        ]
    )

    assert len(results) == 3
    assert [result.relevant for result in results] == [True, False, True]
