import math

class Complex:
    """Complex number representation for quantum states"""
    def __init__(self, real: float = 0, imag: float = 0) -> None:
        self.r = real
        self.i = imag

    def add(self, other: 'Complex') -> 'Complex':
        return Complex(self.r + other.r, self.i + other.i)

    def multiply(self, other: 'Complex') -> 'Complex':
        return Complex(
            self.r * other.r - self.i * other.i,
            self.r * other.i + self.i * other.r
        )

    def magnitude(self) -> float:
        return math.sqrt(self.r * self.r + self.i * self.i)
    
    def __str__(self) -> str:
        if abs(self.i) < 1e-10:
            return f"{self.r:.3f}"
        if abs(self.r) < 1e-10:
            return f"{self.i:.3f}i"
        return f"{self.r:.3f} + {self.i:.3f}i"
