"""
Isolated test file that doesn't depend on the application code.
"""

def test_simple():
    """A simple test to verify that pytest is working."""
    assert True

if __name__ == "__main__":
    import pytest
    pytest.main(["-v", __file__])
