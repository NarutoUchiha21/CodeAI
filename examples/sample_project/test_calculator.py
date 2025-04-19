#!/usr/bin/env python3
"""
Tests for the Calculator class.
"""

import pytest
from calculator import Calculator


@pytest.fixture
def calculator():
    """Create a calculator instance for testing."""
    return Calculator()


def test_calculator_initialization():
    """Test calculator initialization."""
    calc = Calculator()
    assert calc.last_result == 0


def test_addition():
    """Test addition operation."""
    calc = Calculator()
    assert calc.add(2, 3) == 5
    assert calc.last_result == 5
    assert calc.add(-1, 1) == 0
    assert calc.last_result == 0


def test_subtraction():
    """Test subtraction operation."""
    calc = Calculator()
    assert calc.subtract(5, 3) == 2
    assert calc.last_result == 2
    assert calc.subtract(1, 1) == 0
    assert calc.last_result == 0


def test_multiplication():
    """Test multiplication operation."""
    calc = Calculator()
    assert calc.multiply(2, 3) == 6
    assert calc.last_result == 6
    assert calc.multiply(-2, 3) == -6
    assert calc.last_result == -6


def test_division():
    """Test division operation."""
    calc = Calculator()
    assert calc.divide(6, 2) == 3
    assert calc.last_result == 3
    assert calc.divide(5, 2) == 2.5
    assert calc.last_result == 2.5


def test_division_by_zero():
    """Test division by zero raises error."""
    calc = Calculator()
    with pytest.raises(ZeroDivisionError):
        calc.divide(5, 0)


def test_last_result_property():
    """Test last_result property updates correctly."""
    calc = Calculator()
    calc.add(2, 3)
    assert calc.last_result == 5
    calc.subtract(10, 4)
    assert calc.last_result == 6
    calc.multiply(2, 3)
    assert calc.last_result == 6
    calc.divide(10, 2)
    assert calc.last_result == 5 