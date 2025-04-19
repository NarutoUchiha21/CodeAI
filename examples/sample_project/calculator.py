class Calculator:
    """A simple calculator class that performs basic arithmetic operations."""
    
    def __init__(self):
        """Initialize the calculator with a last result of 0."""
        self._last_result = 0
    
    @property
    def last_result(self) -> float:
        """Get the last calculation result."""
        return self._last_result
    
    def add(self, a: float, b: float) -> float:
        """Add two numbers.
        
        Args:
            a: First number
            b: Second number
            
        Returns:
            The sum of a and b
        """
        self._last_result = a + b
        return self._last_result
    
    def subtract(self, a: float, b: float) -> float:
        """Subtract second number from first number.
        
        Args:
            a: First number
            b: Second number
            
        Returns:
            The difference between a and b
        """
        self._last_result = a - b
        return self._last_result
    
    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers.
        
        Args:
            a: First number
            b: Second number
            
        Returns:
            The product of a and b
        """
        self._last_result = a * b
        return self._last_result
    
    def divide(self, a: float, b: float) -> float:
        """Divide first number by second number.
        
        Args:
            a: First number (dividend)
            b: Second number (divisor)
            
        Returns:
            The quotient of a divided by b
            
        Raises:
            ZeroDivisionError: If b is 0
        """
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        self._last_result = a / b
        return self._last_result 