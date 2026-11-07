from datetime import datetime


def test_hourly_values_match_zero_based_axis_labels(analyze_script, mocker):
    records = [
        ("abcde", datetime(2026, 1, 1, 0)),
        ("xyz", datetime(2026, 1, 1, 1)),
        ("evening", datetime(2026, 1, 1, 23)),
        ("ignore", datetime(2025, 1, 1, 0)),
    ]
    mocker.patch.object(analyze_script, "load_weibo", return_value=records)
    plt = mocker.patch.object(analyze_script, "plt")
    analyze_script.plot_polar_by_hour(2026)
    heights = plt.subplot.return_value.bar.call_args.args[1]
    expected = [0] * 24
    expected[0], expected[1], expected[23] = 5, 3, 7
    assert heights.tolist() == expected
