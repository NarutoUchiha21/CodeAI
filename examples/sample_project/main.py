#!/usr/bin/env python3
"""
A simple calculator implementation that demonstrates basic arithmetic operations.
"""

class Calculator:
    """A simple calculator class that performs basic arithmetic operations."""
    
    def __init__(self):
        """Initialize the calculator."""
        self.last_result = 0
    
    def add(self, a: float, b: float) -> float:
        """Add two numbers.
        
        Args:
            a: First number
            b: Second number
            
        Returns:
            The sum of a and b
        """
        self.last_result = a + b
        return self.last_result
    
    def subtract(self, a: float, b: float) -> float:
        """Subtract b from a.
        
        Args:
            a: First number
            b: Second number
            
        Returns:
            The difference between a and b
        """
        self.last_result = a - b
        return self.last_result
    
    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers.
        
        Args:
            a: First number
            b: Second number
            
        Returns:
            The product of a and b
        """
        self.last_result = a * b
        return self.last_result
    
    def divide(self, a: float, b: float) -> float:
        """Divide a by b.
        
        Args:
            a: First number
            b: Second number
            
        Returns:
            The quotient of a divided by b
            
        Raises:
            ZeroDivisionError: If b is zero
        """
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        self.last_result = a / b
        return self.last_result
    
    def get_last_result(self) -> float:
        """Get the result of the last operation.
        
        Returns:
            The result of the last operation
        """
        return self.last_result


def main():
    """Run a simple demonstration of the calculator."""
    calc = Calculator()
    
    # Perform some calculations
    print("Calculator Demo")
    print("==============")
    print(f"2 + 3 = {calc.add(2, 3)}")
    print(f"5 - 2 = {calc.subtract(5, 2)}")
    print(f"4 * 6 = {calc.multiply(4, 6)}")
    print(f"10 / 2 = {calc.divide(10, 2)}")
    print(f"Last result: {calc.get_last_result()}")


if __name__ == "__main__":
    main() 