import pandas as pd

from services.monitoring_logic import prepare_monitoring_frames


def test_prepare_monitoring_frames_splits_rows_and_excludes_post_contact_field():
    frame = pd.DataFrame(
        {
            "contact_id": range(10),
            "age": range(20, 30),
            "balance": range(10),
            "campaign": [1] * 10,
            "duration": [100] * 10,
            "propensity_score": [0.1 * index for index in range(10)],
            "actual_subscribed": [0, 1] * 5,
        }
    )

    reference, current = prepare_monitoring_frames(frame, reference_share=0.7)

    assert len(reference) == 7
    assert len(current) == 3
    assert "duration" not in reference.columns
    assert "propensity_score" in current.columns
    assert reference["contact_id"].max() < current["contact_id"].min()
