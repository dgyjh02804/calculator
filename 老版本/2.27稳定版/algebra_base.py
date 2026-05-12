import math


class ExpressionType:
    """表达式类型枚举（保持简单，可不依赖Enum）"""
    TERM = "term"
    ABSOLUTE_VALUE = "absolute_value"
    SQRT = "sqrt"


class Fraction:
    """分数类，用于精确表示有理数"""

    def __init__(self, numerator=0, denominator=1):
        self.numerator = numerator
        self.denominator = denominator
        self.normalize()

    def __abs__(self):
        return Fraction(abs(self.numerator), self.denominator)

    def normalize(self):
        if self.denominator == 0:
            raise ValueError("分母不能为零")
        gcd_val = math.gcd(abs(self.numerator), abs(self.denominator))
        if gcd_val > 0:
            self.numerator //= gcd_val
            self.denominator //= gcd_val
        if self.denominator < 0:
            self.numerator = -self.numerator
            self.denominator = -self.denominator

    def __add__(self, other):
        if isinstance(other, int):
            other = Fraction(other, 1)
        elif not isinstance(other, Fraction):
            raise TypeError("只能与分数或整数相加")
        new_numerator = self.numerator * other.denominator + other.numerator * self.denominator
        new_denominator = self.denominator * other.denominator
        return Fraction(new_numerator, new_denominator)

    def __sub__(self, other):
        if isinstance(other, int):
            other = Fraction(other, 1)
        elif not isinstance(other, Fraction):
            raise TypeError("只能与分数或整数相减")
        new_numerator = self.numerator * other.denominator - other.numerator * self.denominator
        new_denominator = self.denominator * other.denominator
        return Fraction(new_numerator, new_denominator)

    def __mul__(self, other):
        if isinstance(other, int):
            other = Fraction(other, 1)
        elif isinstance(other, Fraction):
            new_numerator = self.numerator * other.numerator
            new_denominator = self.denominator * other.denominator
            return Fraction(new_numerator, new_denominator)
        else:
            return NotImplemented

    def __truediv__(self, other):
        if isinstance(other, int):
            other = Fraction(other, 1)
        elif not isinstance(other, Fraction):
            raise TypeError("只能被分数或整数除")
        new_numerator = self.numerator * other.denominator
        new_denominator = self.denominator * other.numerator
        return Fraction(new_numerator, new_denominator)

    def __pow__(self, other):
        if isinstance(other, int):
            return Fraction(self.numerator ** other, self.denominator ** other)
        raise TypeError("指数必须是整数")

    def __neg__(self):
        return Fraction(-self.numerator, self.denominator)

    def __eq__(self, other):
        if isinstance(other, int):
            return self.numerator == other and self.denominator == 1
        elif isinstance(other, Fraction):
            return self.numerator == other.numerator and self.denominator == other.denominator
        return False

    def __str__(self):
        if self.denominator == 1:
            return str(self.numerator)
        else:
            return f"{self.numerator}/{self.denominator}"

    def __repr__(self):
        return f"Fraction({self.numerator}, {self.denominator})"

    def to_float(self):
        return self.numerator / self.denominator

    @staticmethod
    def from_string(s):
        s = s.strip()
        if '/' in s:
            num, den = s.split('/')
            return Fraction(int(num), int(den))
        elif '.' in s:
            integer_part, decimal_part = s.split('.')
            denominator = 10 ** len(decimal_part)
            numerator = int(integer_part) * denominator + int(decimal_part)
            if integer_part.startswith('-'):
                numerator = -abs(numerator)
            return Fraction(numerator, denominator)
        else:
            return Fraction(int(s), 1)