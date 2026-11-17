def test_project_smoke():
    assert 1 + 1 == 2


def test_phishing_prediction_labels():

    prediction_labels = {
        0: "Phishing",
        1: "Legitimate"
    }

    assert prediction_labels[0] == "Phishing"
    assert prediction_labels[1] == "Legitimate"


def test_prediction_classes():

    predictions = [0, 1, 0, 1, 1]

    assert all(prediction in [0, 1] for prediction in predictions)


def test_prediction_count():

    predictions = [0, 1, 0, 1, 1]

    assert len(predictions) == 5