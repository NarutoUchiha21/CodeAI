# Calculator Project

A simple calculator implementation with basic arithmetic operations.

## Features

- Addition
- Subtraction
- Multiplication
- Division
- Last result tracking

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

```python
from calculator import Calculator

calc = Calculator()
result = calc.add(5, 3)  # Returns 8
result = calc.subtract(10, 4)  # Returns 6
result = calc.multiply(2, 3)  # Returns 6
result = calc.divide(15, 3)  # Returns 5.0
```

## Testing

Run the tests using pytest:
```bash
pytest
```

For coverage report:
```bash
pytest --cov=.
```

## Project Structure

- `calculator.py`: Main calculator implementation
- `test_calculator.py`: Test cases
- `requirements.txt`: Project dependencies
- `README.md`: Project documentation 