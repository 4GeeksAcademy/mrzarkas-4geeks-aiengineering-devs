from tests.compliance_fixtures import SYNTHETIC_COMPLIANCE_REVIEWS


def test_compliance_fixtures_are_stable_and_jurisdiction_scoped() -> None:
    assert set(SYNTHETIC_COMPLIANCE_REVIEWS) == {"us_open", "uk_open"}
    assert {
        review["review_identifier"] for review in SYNTHETIC_COMPLIANCE_REVIEWS.values()
    } == {"SYN-US-REVIEW-001", "SYN-UK-REVIEW-001"}
    assert len({review["jurisdiction_id"] for review in SYNTHETIC_COMPLIANCE_REVIEWS.values()}) == 2
