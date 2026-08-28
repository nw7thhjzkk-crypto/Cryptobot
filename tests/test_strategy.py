import pandas as pd
from bot.strategy import detect_regime

def test_detect_regime_short_history():
    """
    Test that detect_regime returns 'transitional' when the provided
    price history DataFrame has fewer than 65 rows.
    """
    # Create a dummy DataFrame with 50 rows (less than 65)
    df = pd.DataFrame({'close': range(50)})

    # Call detect_regime
    result = detect_regime(df)

    # Assert that the result is 'transitional'
    assert result == "transitional"
