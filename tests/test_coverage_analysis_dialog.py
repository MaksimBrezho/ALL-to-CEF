from gui.coverage_analysis_dialog import CoverageAnalysisDialog


def test_wrap_missing_lines():
    text = "1, 2, 3, 4, 5, 6, 7, 8, 9, 10"
    wrapped = CoverageAnalysisDialog._wrap_missing_lines(text, width=10)
    assert "\n" in wrapped
    joined = wrapped.replace("\n", "").replace(" ", "")
    assert joined == text.replace(" ", "")


def test_row_height_calculation():
    stats = {
        "a": (50.0, [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21]),
        "b": (80.0, []),
    }
    height = CoverageAnalysisDialog._calculate_row_height(
        stats, base_height=10, width=10
    )
    assert height == 40
