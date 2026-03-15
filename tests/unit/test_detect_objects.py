from vigil.business_logic.use_cases.detect_objects import DetectObjectsUseCase


def test_should_detect_a_person():
    use_case = DetectObjectsUseCase()

    assert use_case is not None
