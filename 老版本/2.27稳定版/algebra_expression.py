import re
import math
from algebra_base import Fraction, ExpressionType

# ========== 代数项 AlgebraicTerm ==========

class AlgebraicTerm:
    """表示代数项，如 2x, 3x^2y, 5/2a 等"""

    def __init__(self, coeff=Fraction(1, 1), vars_dict=None):
        self.coeff = coeff if isinstance(coeff, Fraction) else Fraction(coeff, 1)
        self.vars = vars_dict if vars_dict is not None else {}

    def __mul__(self, other):
        if isinstance(other, (int, Fraction)):
            return AlgebraicTerm(self.coeff * other, self.vars.copy())
        elif isinstance(other, AlgebraicTerm):
            new_coeff = self.coeff * other.coeff
            new_vars = self.vars.copy()
            for var, exp in other.vars.items():
                new_vars[var] = new_vars.get(var, 0) + exp
            new_vars = {k: v for k, v in new_vars.items() if v != 0}
            return AlgebraicTerm(new_coeff, new_vars)
        elif isinstance(other, AbsoluteValue):
            return AbsoluteValue(self * other.inner_expr)
        elif isinstance(other, SqrtExpression):
            TermWithSqrt = globals().get('TermWithSqrt')
            if TermWithSqrt is None:
                return AlgebraicExpression([self, other])
            return TermWithSqrt(self, other)
        elif isinstance(other, AlgebraicExpression):
            new_terms = []
            for term in other.terms:
                new_terms.append(self * term)
            return AlgebraicExpression(new_terms)
        elif isinstance(other, FractionExpression):
            term_as_expr = AlgebraicExpression([self])
            new_numerator = term_as_expr * other.numerator
            return FractionExpression(new_numerator, other.denominator)
        return NotImplemented

    def __truediv__(self, other):
        if isinstance(other, (int, Fraction)):
            return AlgebraicTerm(self.coeff / other, self.vars.copy())
        elif isinstance(other, AlgebraicTerm):
            new_coeff = self.coeff / other.coeff
            new_vars = self.vars.copy()
            for var, exp in other.vars.items():
                new_vars[var] = new_vars.get(var, 0) - exp
            new_vars = {k: v for k, v in new_vars.items() if v != 0}
            return AlgebraicTerm(new_coeff, new_vars)
        return NotImplemented

    def __add__(self, other):
        if not self.same_vars(other):
            raise ValueError("只有同类项才能相加")
        return AlgebraicTerm(self.coeff + other.coeff, self.vars.copy())

    def __sub__(self, other):
        if not self.same_vars(other):
            raise ValueError("只有同类项才能相减")
        return AlgebraicTerm(self.coeff - other.coeff, self.vars.copy())

    def __neg__(self):
        return AlgebraicTerm(-self.coeff, self.vars.copy())

    def __eq__(self, other):
        return self.coeff == other.coeff and self.vars == other.vars

    def same_vars(self, other):
        return self.vars == other.vars

    def is_constant(self):
        return len(self.vars) == 0

    def contains_var(self, var):
        return var in self.vars

    def get_coefficient_for_var(self, var):
        if len(self.vars) == 1 and var in self.vars and self.vars[var] == 1:
            return self.coeff
        elif var in self.vars and self.vars[var] >= 1:
            if self.vars[var] == 1:
                new_vars = self.vars.copy()
                del new_vars[var]
                return AlgebraicTerm(self.coeff, new_vars)
            else:
                return None
        else:
            return None

    def has_negative_exponents(self):
        for exp in self.vars.values():
            if exp < 0:
                return True
        return False

    def __str__(self):
        if self.coeff.numerator == 0:
            return "0"
        if not self.has_negative_exponents():
            coeff_str = str(self.coeff)
            if self.coeff == Fraction(1, 1) and self.vars:
                coeff_str = ""
            elif self.coeff == Fraction(-1, 1) and self.vars:
                coeff_str = "-"
            elif self.coeff.denominator != 1 and self.vars:
                coeff_str = f"({coeff_str})"
            var_parts = []
            for var in sorted(self.vars.keys()):
                exp = self.vars[var]
                if exp == 0:
                    continue
                if exp == 1:
                    var_parts.append(var)
                else:
                    var_parts.append(f"{var}^{exp}")
            var_str = "".join(var_parts) if var_parts else ""
            if coeff_str and var_str:
                return f"{coeff_str}{var_str}"
            elif coeff_str:
                return coeff_str
            elif var_str:
                return var_str
            else:
                return "1"
        pos_vars = {}
        neg_vars = {}
        for var, exp in self.vars.items():
            if exp > 0:
                pos_vars[var] = exp
            elif exp < 0:
                neg_vars[var] = -exp
        coeff_num = self.coeff.numerator
        coeff_den = self.coeff.denominator
        sign = 1 if coeff_num >= 0 else -1
        coeff_num = abs(coeff_num)
        num_parts = []
        if coeff_num != 1 or (coeff_num == 1 and not pos_vars):
            num_parts.append(str(coeff_num))
        for var in sorted(pos_vars.keys()):
            exp = pos_vars[var]
            if exp == 1:
                num_parts.append(var)
            else:
                num_parts.append(f"{var}^{exp}")
        den_parts = []
        if coeff_den != 1:
            den_parts.append(str(coeff_den))
        for var in sorted(neg_vars.keys()):
            exp = neg_vars[var]
            if exp == 1:
                den_parts.append(var)
            else:
                den_parts.append(f"{var}^{exp}")
        num_str = "".join(num_parts) if num_parts else "1"
        if len(den_parts) > 1:
            den_str = "(" + "".join(den_parts) + ")"
        else:
            den_str = "".join(den_parts) if den_parts else "1"
        if den_str == "1":
            if sign == -1:
                return f"-{num_str}"
            else:
                return num_str
        if num_str == "1" and not pos_vars:
            if sign == -1:
                return f"-1/{den_str}"
            else:
                return f"1/{den_str}"
        if sign == -1:
            return f"-{num_str}/{den_str}"
        else:
            return f"{num_str}/{den_str}"

    @staticmethod
    def from_string(s):
        s = s.strip()
        if not s:
            return AlgebraicTerm(Fraction(0, 1))
        sign = 1
        if s[0] == '-':
            sign = -1
            s = s[1:]
        coeff_str = ""
        var_part = ""
        i = 0
        while i < len(s) and (s[i].isdigit() or s[i] in './'):
            coeff_str += s[i]
            i += 1
        var_part = s[i:]
        if coeff_str:
            coeff = Fraction.from_string(coeff_str)
        else:
            coeff = Fraction(1, 1)
        coeff = coeff * sign
        vars_dict = {}
        if var_part:
            matches = re.findall(r'([a-zA-Z])(?:\^(\d+))?', var_part)
            for var, exp_str in matches:
                exp = int(exp_str) if exp_str else 1
                vars_dict[var] = vars_dict.get(var, 0) + exp
        vars_dict = {k: v for k, v in vars_dict.items() if v != 0}
        return AlgebraicTerm(coeff, vars_dict)

    def __pow__(self, exp):
        if isinstance(exp, int) and exp >= 0:
            new_coeff = self.coeff ** exp
            new_vars = {}
            for var, var_exp in self.vars.items():
                new_vars[var] = var_exp * exp
            new_vars = {k: v for k, v in new_vars.items() if v != 0}
            return AlgebraicTerm(new_coeff, new_vars)
        else:
            return AlgebraicExpression([self]) ** exp

    def substitute(self, var, expr, debug_callback=None):
        if var not in self.vars:
            from copy import deepcopy
            return AlgebraicExpression([deepcopy(self)])
        exp = self.vars[var]
        other_vars = {k: v for k, v in self.vars.items() if k != var}
        base_term = AlgebraicTerm(self.coeff, other_vars)
        pow_expr = expr ** exp
        result = base_term * pow_expr
        return result


# ========== 绝对值 AbsoluteValue ==========

class AbsoluteValue:
    """表示绝对值表达式，如 |x|, |x+y| 等"""

    def __init__(self, inner_expr):
        self.inner_expr = inner_expr
        self.expr_type = ExpressionType.ABSOLUTE_VALUE

    def simplify(self, debug_callback=None):
        if debug_callback:
            debug_callback(f"开始简化绝对值表达式: |{self.inner_expr}|", level=1)
        if isinstance(self.inner_expr, AlgebraicExpression):
            if self.inner_expr.is_constant():
                const = self.inner_expr.terms[0].coeff
                if const.numerator >= 0:
                    result = const
                else:
                    result = Fraction(-const.numerator, const.denominator)
                if debug_callback:
                    debug_callback(f"常数绝对值: |{const}| = {result}", level=2)
                return AlgebraicExpression([AlgebraicTerm(result)])
        simplified_inner = self.inner_expr.simplify(debug_callback)
        if simplified_inner != self.inner_expr:
            if debug_callback:
                debug_callback(f"内部表达式已简化: {self.inner_expr} -> {simplified_inner}", level=2)
            return AbsoluteValue(simplified_inner)
        if debug_callback:
            debug_callback(f"无法进一步简化绝对值表达式", level=3)
        return self

    def __str__(self):
        inner_str = str(self.inner_expr)
        if any(op in inner_str for op in '+-'):
            return f"|({inner_str})|"
        else:
            return f"|{inner_str}|"

    def __mul__(self, other):
        if isinstance(other, (int, Fraction, AlgebraicTerm, AlgebraicExpression, AbsoluteValue)):
            inner = self.inner_expr * other
            if inner is None:
                inner = AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])
            return AbsoluteValue(inner)
        elif isinstance(other, FractionExpression):
            new_numerator = self * other.numerator
            return FractionExpression(new_numerator, other.denominator)
        elif isinstance(other, SqrtExpression):
            return AlgebraicExpression([self, other])
        return NotImplemented

    def __rmul__(self, other):
        if isinstance(other, (int, Fraction)):
            return self * other
        return NotImplemented

    def __add__(self, other):
        if isinstance(other, AbsoluteValue) and self.inner_expr == other.inner_expr:
            return AbsoluteValue(AlgebraicExpression([AlgebraicTerm(Fraction(2, 1))]) * self.inner_expr)
        return AlgebraicExpression([self]) + other

    def __neg__(self):
        return self * Fraction(-1, 1)

    def __sub__(self, other):
        if isinstance(other, AbsoluteValue) and self.inner_expr == other.inner_expr:
            return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])
        return AlgebraicExpression([self]) - other

    def __eq__(self, other):
        if isinstance(other, AbsoluteValue):
            return self.inner_expr == other.inner_expr
        return False

    def contains_var(self, var):
        if isinstance(self.inner_expr, AlgebraicExpression):
            for term in self.inner_expr.terms:
                if term.contains_var(var):
                    return True
        elif isinstance(self.inner_expr, AlgebraicTerm):
            return self.inner_expr.contains_var(var)
        return False

    def expand_with_cases(self, debug_callback=None):
        if debug_callback:
            debug_callback(f"开始展开绝对值表达式: |{self.inner_expr}|", level=1)

        inner = self.inner_expr
        if not isinstance(inner, AlgebraicExpression):
            inner = AlgebraicExpression([inner])

        # 尝试将条件化简为线性不等式（单变量线性表达式）
        from algebra_base import Fraction
        coeff = Fraction(0, 1)
        const = Fraction(0, 1)
        var = None
        if isinstance(inner, AlgebraicExpression):
            for term in inner.terms:
                if isinstance(term, AlgebraicTerm):
                    if term.is_constant():
                        const = const + term.coeff
                    else:
                        if len(term.vars) == 1:
                            for v, exp in term.vars.items():
                                if exp == 1:
                                    if var is None:
                                        var = v
                                        coeff = term.coeff
                                    elif var == v:
                                        coeff = coeff + term.coeff
                                    else:
                                        var = None
                                        break
                                else:
                                    var = None
                                    break
                        else:
                            var = None
                            break
                else:
                    var = None
                    break
        else:
            var = None

        if var is not None and coeff != Fraction(0, 1):
            critical = (-const) / coeff
            if hasattr(critical, 'simplify'):
                critical = critical.simplify()
            # 根据系数符号构造条件（使用 numerator 判断正负）
            if coeff.numerator > 0:
                cond_ge = f"{var} ≥ {critical}"
                cond_lt = f"{var} < {critical}"
            else:
                cond_ge = f"{var} ≤ {critical}"
                cond_lt = f"{var} > {critical}"

            inner_str = str(inner)
            result = f"|{inner_str}| = {{\n"
            result += f"  {inner_str}, 当 {cond_ge}\n"
            result += f"  -{inner_str}, 当 {cond_lt}\n"
            result += "}"
            if debug_callback:
                debug_callback(f"绝对值展开结果（化简后）: {result}", level=2)
            return result

        # 无法化简，使用原始形式
        inner_str = str(inner)
        result = f"|{inner_str}| = {{\n"
        result += f"  {inner_str}, 当 {inner_str} ≥ 0\n"
        result += f"  -{inner_str}, 当 {inner_str} < 0\n"
        result += "}"
        if debug_callback:
            debug_callback(f"绝对值展开结果: {result}", level=2)
        return result

    def is_zero(self):
        inner = self.inner_expr
        if hasattr(inner, 'simplify'):
            inner = inner.simplify()
        return hasattr(inner, 'is_zero') and inner.is_zero()

    def substitute(self, var, expr, debug_callback=None):
        new_inner = self.inner_expr.substitute(var, expr, debug_callback)
        return AbsoluteValue(new_inner)

    def __pow__(self, exp):
        return AlgebraicExpression([self]) ** exp

    def __radd__(self, other):
        return AlgebraicExpression([self]) + other

    def __rsub__(self, other):
        return AlgebraicExpression([other]) - self


# ========== 平方根 SqrtExpression ==========

class SqrtExpression:
    """表示平方根表达式，如 √(x), √(x+y) 等"""

    def __init__(self, inner_expr):
        self.inner_expr = inner_expr
        self.expr_type = ExpressionType.SQRT

    def __eq__(self, other):
        if not isinstance(other, SqrtExpression):
            return False
        return self.inner_expr == other.inner_expr

    def simplify(self, debug_callback=None):
        if debug_callback:
            debug_callback(f"开始化简根号表达式: √({self.inner_expr})", level=1)
        if hasattr(self.inner_expr, 'simplify'):
            simplified_inner = self.inner_expr.simplify(debug_callback)
        else:
            simplified_inner = self.inner_expr
        # 如果是常数且为负数，则不化简，直接返回自身
        if isinstance(simplified_inner, AlgebraicExpression) and simplified_inner.is_constant():
            const = simplified_inner.terms[0].coeff
            if const.numerator < 0:
                if debug_callback:
                    debug_callback(f"常数 {const} 为负数，保留根号形式", level=3)
                return self
        if isinstance(simplified_inner, AlgebraicExpression) and simplified_inner.is_constant():
            const = simplified_inner.terms[0].coeff
            num = const.numerator
            den = const.denominator
            num_sqrt = self._is_perfect_square(num)
            den_sqrt = self._is_perfect_square(den)
            if num_sqrt and den_sqrt:
                result = Fraction(num_sqrt, den_sqrt)
                if debug_callback:
                    debug_callback(f"常数完全平方根: √({const}) = {result}", level=2)
                return AlgebraicExpression([AlgebraicTerm(result)])
            elif debug_callback:
                debug_callback(f"常数 {const} 不是完全平方数，保留根号形式", level=3)
        return self._extract_square_factors(simplified_inner, debug_callback)

    def _is_perfect_square(self, n):
        if n < 0:
            return None
        root = int(math.isqrt(n))
        return root if root * root == n else None

    def _max_square_factor(self, n):
        if isinstance(n, Fraction):
            n = n.numerator
        if not isinstance(n, int):
            return 1
        if n <= 1:
            return 1
        max_square = 1
        temp = n
        i = 2
        while i * i <= temp:
            count = 0
            while temp % i == 0:
                temp //= i
                count += 1
            even_count = count - (count % 2)
            if even_count > 0:
                max_square *= (i ** even_count)
            i += 1 if i == 2 else 2
        return max_square

    def _extract_square_factors(self, expr, debug_callback=None):
        if debug_callback:
            debug_callback(f"开始提取平方因子: √({expr})", level=2)
        if isinstance(expr, AlgebraicExpression) and len(expr.terms) == 1:
            term = expr.terms[0]
            if isinstance(term, AlgebraicTerm):
                coeff = term.coeff
                if not isinstance(coeff, Fraction):
                    coeff = Fraction(coeff, 1)
                num = abs(coeff.numerator)
                den = coeff.denominator
                num_square_factor = self._max_square_factor(num)
                den_square_factor = self._max_square_factor(den)
                extracted_num = int(math.isqrt(num_square_factor)) if num_square_factor > 0 else 1
                extracted_den = int(math.isqrt(den_square_factor)) if den_square_factor > 0 else 1
                remaining_num = num // num_square_factor if num_square_factor != 0 else num
                remaining_den = den // den_square_factor if den_square_factor != 0 else den
                sign = 1 if coeff.numerator >= 0 else -1
                extracted_coeff = Fraction(extracted_num, extracted_den)
                remaining_coeff = Fraction(sign * remaining_num, remaining_den)
                var_factors = {}
                var_remainders = {}
                for var, exp in term.vars.items():
                    factor_exp = exp // 2
                    remainder_exp = exp % 2
                    if factor_exp > 0:
                        var_factors[var] = factor_exp
                    if remainder_exp > 0:
                        var_remainders[var] = remainder_exp
                extracted_term = AlgebraicTerm(extracted_coeff, var_factors)
                remaining_term = AlgebraicTerm(remaining_coeff, var_remainders)
                if debug_callback:
                    debug_callback(f"提取因子: {extracted_term}", level=3)
                    debug_callback(f"剩余部分: {remaining_term}", level=3)
                if remaining_term.coeff == Fraction(1, 1) and not remaining_term.vars:
                    if debug_callback:
                        debug_callback(f"无剩余部分，结果为: {extracted_term}", level=3)
                    return extracted_term
                remaining_expr = AlgebraicExpression([remaining_term])
                sqrt_remaining = SqrtExpression(remaining_expr)
                if extracted_term.coeff == Fraction(1, 1) and not extracted_term.vars:
                    if debug_callback:
                        debug_callback(f"提取因子为1，结果为: √({remaining_term})", level=3)
                    return sqrt_remaining
                TermWithSqrt = globals().get('TermWithSqrt')
                if TermWithSqrt is None:
                    if debug_callback:
                        debug_callback(f"警告：TermWithSqrt 未定义，返回表达式", level=2)
                    return AlgebraicExpression([extracted_term, sqrt_remaining])
                result = TermWithSqrt(extracted_term, sqrt_remaining)
                if debug_callback:
                    debug_callback(f"结果为: {result}", level=2)
                return result
        if debug_callback:
            debug_callback(f"无法提取平方因子，返回原始表达式", level=3)
        return self

    def rationalize_denominator(self, denominator, debug_callback=None):
        if debug_callback:
            debug_callback(f"开始分母有理化: 1/√({self.inner_expr})", level=1)
        numerator = AlgebraicExpression([AlgebraicTerm(Fraction(1, 1))])
        new_numerator = numerator * self
        new_denominator = self.inner_expr
        return FractionExpression(new_numerator, new_denominator)

    def __str__(self):
        return f"√({self.inner_expr})"

    def __mul__(self, other, debug_callback=None):
        if debug_callback:
            debug_callback(f"构造 TermWithSqrt: {other} * √({self.inner_expr})", level=3)
        if isinstance(other, SqrtExpression):
            # 两个相同的根号相乘返回内部表达式
            if self == other:
                return self.inner_expr
            return SqrtExpression(self.inner_expr * other.inner_expr)
        elif isinstance(other, (int, Fraction)):
            if other == 1:
                return self
            TermWithSqrt = globals().get('TermWithSqrt')
            if TermWithSqrt is None:
                return AlgebraicExpression([AlgebraicTerm(other), self])
            return TermWithSqrt(AlgebraicTerm(other), self)
        elif isinstance(other, AlgebraicTerm):
            if other.coeff == Fraction(1, 1) and not other.vars:
                return self
            TermWithSqrt = globals().get('TermWithSqrt')
            if TermWithSqrt is None:
                return AlgebraicExpression([other, self])
            return TermWithSqrt(other, self)
        elif isinstance(other, AlgebraicExpression):
            new_terms = []
            for term in other.terms:
                if isinstance(term, (AlgebraicTerm, int, Fraction)):
                    new_terms.append(term * self)
                elif isinstance(term, AbsoluteValue):
                    new_terms.append(term * self)
                elif isinstance(term, SqrtExpression):
                    new_terms.append(term * self)
            return AlgebraicExpression(new_terms)
        elif isinstance(other, FractionExpression):
            new_numerator = self * other.numerator
            return FractionExpression(new_numerator, other.denominator)
        return NotImplemented

    def __rmul__(self, other):
        return self.__mul__(other)

    def __neg__(self):
        return self * Fraction(-1, 1)

    def __truediv__(self, other):
        if isinstance(other, (int, Fraction)):
            if isinstance(other, int):
                other = Fraction(other, 1)
            coeff = Fraction(1, 1) / other
            TermWithSqrt = globals().get('TermWithSqrt')
            if TermWithSqrt is None:
                return AlgebraicExpression([AlgebraicTerm(coeff), self])
            return TermWithSqrt(AlgebraicTerm(coeff), self)
        elif isinstance(other, SqrtExpression):
            return SqrtExpression(self.inner_expr / other.inner_expr)
        else:
            return NotImplemented

    def __pow__(self, exp):
        if exp == 2:
            return self.inner_expr
        else:
            return AlgebraicExpression([self]) ** exp

    def contains_var(self, var):
        if hasattr(self.inner_expr, 'contains_var'):
            return self.inner_expr.contains_var(var)
        elif isinstance(self.inner_expr, AlgebraicExpression):
            for term in self.inner_expr.terms:
                if hasattr(term, 'contains_var') and term.contains_var(var):
                    return True
        return False

    def __hash__(self):
        return hash(('sqrt', str(self.inner_expr)))

    def is_zero(self):
        inner = self.inner_expr
        if hasattr(inner, 'simplify'):
            inner = inner.simplify()
        return hasattr(inner, 'is_zero') and inner.is_zero()

    def substitute(self, var, expr, debug_callback=None):
        new_inner = self.inner_expr.substitute(var, expr, debug_callback)
        return SqrtExpression(new_inner)

    def __add__(self, other):
        return AlgebraicExpression([self]) + other

    def __radd__(self, other):
        return AlgebraicExpression([self]) + other

    def __sub__(self, other):
        return AlgebraicExpression([self]) - other

    def __rsub__(self, other):
        return AlgebraicExpression([other]) - self


# ========== 带平方根的项 TermWithSqrt ==========

class TermWithSqrt:
    """表示系数乘以平方根的项，如 2x√(y)"""

    def __init__(self, coeff, sqrt_expr):
        if isinstance(coeff, AlgebraicTerm):
            self.coeff = coeff
        else:
            self.coeff = AlgebraicTerm(coeff if isinstance(coeff, Fraction) else Fraction(coeff, 1))
        self.sqrt_expr = sqrt_expr

    def __eq__(self, other):
        if not isinstance(other, TermWithSqrt):
            return False
        return self.coeff == other.coeff and self.sqrt_expr == other.sqrt_expr

    def __str__(self):
        coeff = self.coeff
        coeff_term = coeff  # 类型为 AlgebraicTerm
        num = coeff_term.coeff.numerator
        den = coeff_term.coeff.denominator
        var_part = coeff_term.vars
        sqrt_str = str(self.sqrt_expr)

        # 处理分母不为1的情况（系数为分数）
        if den != 1:
            # 构建分子部分
            if num == 0:
                return "0"
            if num == 1:
                coeff_part = ""
            elif num == -1:
                coeff_part = "-"
            else:
                coeff_part = str(num) if num > 0 else f"-{abs(num)}"

            # 变量部分
            var_str = ""
            if var_part:
                sorted_vars = sorted(var_part.keys())
                for v in sorted_vars:
                    exp = var_part[v]
                    if exp == 1:
                        var_str += v
                    else:
                        var_str += f"{v}^{exp}"

            # 组合分子
            if coeff_part and var_str:
                numerator = f"{coeff_part}{var_str}{sqrt_str}"
            elif coeff_part:
                numerator = f"{coeff_part}{sqrt_str}"
            elif var_str:
                numerator = f"{var_str}{sqrt_str}"
            else:
                numerator = sqrt_str

            # 处理负号
            if numerator.startswith('-'):
                inner = numerator[1:]
                if inner:
                    return f"-({inner})/{den}"
                else:
                    return f"-/{den}"  # 理论上不会发生
            else:
                return f"({numerator})/{den}" if numerator else f"/{den}"

        # 分母为1的情况（系数为整数）
        else:
            coeff_str = str(coeff)
            if coeff_term.coeff == Fraction(1, 1) and not var_part:
                return sqrt_str
            if coeff_term.coeff == Fraction(-1, 1) and not var_part:
                return f"-{sqrt_str}"
            return f"{coeff_str}{sqrt_str}"

    def __mul__(self, other):
        if isinstance(other, (int, Fraction)):
            return TermWithSqrt(self.coeff * other, self.sqrt_expr)
        elif isinstance(other, AlgebraicTerm):
            new_coeff = self.coeff * other
            return TermWithSqrt(new_coeff, self.sqrt_expr)
        elif isinstance(other, TermWithSqrt):
            new_coeff = self.coeff * other.coeff
            new_sqrt = self.sqrt_expr * other.sqrt_expr
            # 如果平方后不再是根号表达式，则与系数合并为普通代数表达式
            if isinstance(new_sqrt, (SqrtExpression, TermWithSqrt)):
                return TermWithSqrt(new_coeff, new_sqrt)
            else:
                # 防御：如果 new_sqrt 为 None，返回零表达式
                if new_sqrt is None:
                    return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])
                return (new_coeff * new_sqrt).simplify()
        elif isinstance(other, AbsoluteValue):
            return AlgebraicExpression([self, other])
        elif isinstance(other, SqrtExpression):
            return TermWithSqrt(self.coeff, self.sqrt_expr * other)
        elif isinstance(other, AlgebraicExpression):
            new_terms = []
            for term in other.terms:
                new_terms.append(self * term)
            return AlgebraicExpression(new_terms)
        elif isinstance(other, FractionExpression):
            new_numerator = self * other.numerator
            return FractionExpression(new_numerator, other.denominator)
        return NotImplemented

    def __rmul__(self, other):
        if isinstance(other, (int, Fraction, AlgebraicTerm, AbsoluteValue, SqrtExpression)):
            return self.__mul__(other)
        return NotImplemented

    def __truediv__(self, other):
        if isinstance(other, (int, Fraction)):
            return TermWithSqrt(self.coeff / other, self.sqrt_expr)
        elif isinstance(other, AlgebraicTerm) and other.is_constant():
            return TermWithSqrt(self.coeff / other.coeff, self.sqrt_expr)
        else:
            return NotImplemented

    def __add__(self, other):
        if isinstance(other, TermWithSqrt) and self.sqrt_expr == other.sqrt_expr:
            new_coeff = self.coeff + other.coeff
            # 即使 new_coeff 为零，也返回 TermWithSqrt，后续会被过滤
            return TermWithSqrt(new_coeff, self.sqrt_expr)
        return AlgebraicExpression([self]) + other

    def __sub__(self, other):
        return self + (-other)

    def __neg__(self):
        return TermWithSqrt(-self.coeff, self.sqrt_expr)

    def contains_var(self, var):
        return self.coeff.contains_var(var) or self.sqrt_expr.contains_var(var)

    def simplify(self, debug_callback=None):
        if debug_callback:
            debug_callback(f"开始简化 TermWithSqrt: {self}", level=2)
        simplified_coeff = self.coeff.simplify(debug_callback) if hasattr(self.coeff, 'simplify') else self.coeff
        simplified_sqrt = self.sqrt_expr.simplify(debug_callback)

        # 如果 sqrt 部分不再是根号，则直接返回系数乘以其结果
        if not isinstance(simplified_sqrt, (SqrtExpression, TermWithSqrt)):
            product = simplified_coeff * simplified_sqrt
            if hasattr(product, 'simplify'):
                return product.simplify(debug_callback)
            return product

        # 如果 sqrt 部分是 TermWithSqrt，则将其系数合并到外层系数
        if isinstance(simplified_sqrt, TermWithSqrt):
            inner_coeff = simplified_sqrt.coeff
            inner_sqrt = simplified_sqrt.sqrt_expr
            new_coeff = simplified_coeff * inner_coeff
            # 重新化简结果，但要避免无限递归
            result = TermWithSqrt(new_coeff, inner_sqrt)
            return result.simplify(debug_callback)

        # 如果系数为零，返回零表达式
        if hasattr(simplified_coeff, 'coeff') and simplified_coeff.coeff.numerator == 0:
            return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])

        if simplified_coeff != self.coeff or simplified_sqrt != self.sqrt_expr:
            result = TermWithSqrt(simplified_coeff, simplified_sqrt)
            if debug_callback:
                debug_callback(f"简化 TermWithSqrt 结果: {result}", level=2)
            return result

        if debug_callback:
            debug_callback(f"TermWithSqrt 无需进一步简化", level=3)
        return self

    def is_zero(self):
        return self.coeff.coeff.numerator == 0

    def substitute(self, var, expr, debug_callback=None):
        new_coeff = self.coeff.substitute(var, expr, debug_callback)
        new_sqrt = self.sqrt_expr.substitute(var, expr, debug_callback)
        if hasattr(new_sqrt, 'simplify'):
            new_sqrt = new_sqrt.simplify(debug_callback)

        # 处理 new_coeff 为 AlgebraicTerm 的情况
        if isinstance(new_coeff, AlgebraicTerm):
            if new_coeff.coeff.numerator == 0:
                return AlgebraicExpression([])
            return TermWithSqrt(new_coeff, new_sqrt)

        # 处理 new_coeff 为 AlgebraicExpression 的情况
        if isinstance(new_coeff, AlgebraicExpression):
            if new_coeff.is_zero():
                return AlgebraicExpression([])
            if len(new_coeff.terms) == 1:
                only_term = new_coeff.terms[0]
                if isinstance(only_term, AlgebraicTerm):
                    if only_term.coeff.numerator == 0:
                        return AlgebraicExpression([])
                    return TermWithSqrt(only_term, new_sqrt)
            # 多系数项乘以根号
            product = new_coeff * new_sqrt
            if hasattr(product, 'simplify'):
                product = product.simplify(debug_callback)
            return product

        # 处理 new_coeff 为数字（int/Fraction）的情况
        if isinstance(new_coeff, (int, Fraction)):
            if new_coeff == 0:
                return AlgebraicExpression([])
            coeff_term = AlgebraicTerm(new_coeff)
            return TermWithSqrt(coeff_term, new_sqrt)

        # 其他情况，尝试转换为 AlgebraicTerm
        try:
            coeff_term = AlgebraicTerm(new_coeff)
            return TermWithSqrt(coeff_term, new_sqrt)
        except:
            # 如果转换失败，返回乘积
            product = AlgebraicExpression([new_coeff]) * new_sqrt
            if hasattr(product, 'simplify'):
                product = product.simplify(debug_callback)
            return product

    def __radd__(self, other):
        return AlgebraicExpression([self]) + other

    def __rsub__(self, other):
        return AlgebraicExpression([other]) - self


# ========== 代数表达式 AlgebraicExpression ==========

class AlgebraicExpression:
    """表示代数表达式，如 2x + 3y - 5"""

    def __init__(self, terms=None):
        if terms is None:
            self.terms = []
        elif isinstance(terms, AlgebraicTerm):
            self.terms = [terms]
        elif isinstance(terms, (int, Fraction)):
            self.terms = [AlgebraicTerm(terms if isinstance(terms, Fraction) else Fraction(terms, 1))]
        elif isinstance(terms, AbsoluteValue):
            self.terms = [terms]
        else:
            self.terms = terms

    def simplify(self, debug_callback=None):
        """化简代数表达式，合并同类项、处理零项等"""
        if debug_callback:
            debug_callback(f"开始化简代数表达式: {self}", level=1)
            debug_callback(f"原始项数: {len(self.terms)}", level=3)

        if not self.terms:
            return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])

        # 首先对每个项进行简化
        simplified_terms = []
        for term in self.terms:
            if hasattr(term, 'simplify'):
                simplified = term.simplify(debug_callback)
                if isinstance(simplified, AlgebraicExpression):
                    simplified_terms.extend(simplified.terms)
                else:
                    simplified_terms.append(simplified)
            else:
                simplified_terms.append(term)

        # 分离不同类型的项
        regular_terms = []      # AlgebraicTerm 类型
        abs_terms = []          # AbsoluteValue 类型
        sqrt_terms = []         # SqrtExpression 类型
        term_with_sqrt_terms = []  # TermWithSqrt 类型
        fraction_terms = []     # FractionExpression 类型

        for term in simplified_terms:
            if isinstance(term, FractionExpression):
                fraction_terms.append(term)
            elif isinstance(term, AbsoluteValue):
                abs_terms.append(term)
            elif isinstance(term, SqrtExpression):
                sqrt_terms.append(term)
            elif isinstance(term, TermWithSqrt):
                term_with_sqrt_terms.append(term)
            else:
                # 必须是 AlgebraicTerm 或可以转换为 AlgebraicTerm 的
                if isinstance(term, AlgebraicTerm) and term.coeff.numerator == 0:
                    continue  # 跳过零项
                regular_terms.append(term)

        # 如果没有分式项，则合并普通项和根号项
        if not fraction_terms:
            # 合并普通代数项（按变量字典分组）
            term_dict = {}
            for term in regular_terms:
                if isinstance(term, AlgebraicTerm):
                    key = frozenset(term.vars.items())
                    if key in term_dict:
                        term_dict[key] = term_dict[key] + term
                    else:
                        term_dict[key] = term
                else:
                    # 理论上不会出现其他类型
                    pass

            # 收集合并后的普通项
            merged_regular = []
            for key, term in term_dict.items():
                if term.coeff.numerator != 0:
                    merged_regular.append(term)

            # 合并绝对值项（保留所有，因为绝对值项无法合并同类项）
            # 但可以尝试合并相同内部表达式的绝对值（例如 |x| + |x| = 2|x|）
            abs_dict = {}
            for term in abs_terms:
                inner_key = str(term.inner_expr)
                if inner_key in abs_dict:
                    # 合并为 2 * |inner|
                    existing = abs_dict[inner_key]
                    # 构造 2 * |inner| 需要创建新的绝对值项
                    # 简单起见，先不合并，保持原样
                    # 但为了后续可能合并，我们可以记录计数
                    # 这里简化为不合并，直接保留
                    pass
                else:
                    abs_dict[inner_key] = term
            merged_abs = list(abs_dict.values())

            # 合并 SqrtExpression 项（按内部表达式分组）
            sqrt_dict = {}
            for term in sqrt_terms:
                key = str(term.inner_expr)
                if key in sqrt_dict:
                    sqrt_dict[key] += 1
                else:
                    sqrt_dict[key] = 1

            # 将多个相同的 sqrt 合并为 TermWithSqrt
            for key, count in sqrt_dict.items():
                if count > 0:
                    # 找到对应的 sqrt 项（只需取第一个）
                    inner_expr = None
                    for term in sqrt_terms:
                        if str(term.inner_expr) == key:
                            inner_expr = term.inner_expr
                            break
                    if inner_expr is not None:
                        if count == 1:
                            # 保留单个 sqrt
                            term_with_sqrt_terms.append(TermWithSqrt(AlgebraicTerm(1), SqrtExpression(inner_expr)))
                        else:
                            # 合并为 count * sqrt
                            coeff_term = AlgebraicTerm(Fraction(count, 1))
                            term_with_sqrt_terms.append(TermWithSqrt(coeff_term, SqrtExpression(inner_expr)))

            # 合并 TermWithSqrt 项（按 sqrt_expr 分组）
            tws_dict = {}
            for term in term_with_sqrt_terms:
                key = str(term.sqrt_expr)
                if key in tws_dict:
                    # 合并系数
                    existing = tws_dict[key]
                    new_coeff = existing.coeff + term.coeff
                    if isinstance(new_coeff, AlgebraicTerm) and new_coeff.coeff.numerator == 0:
                        # 系数为零，移除该项
                        del tws_dict[key]
                    else:
                        tws_dict[key] = TermWithSqrt(new_coeff, term.sqrt_expr)
                else:
                    tws_dict[key] = term

            merged_tws = []
            for term in tws_dict.values():
                if term.coeff.coeff.numerator != 0:
                    merged_tws.append(term)

            # 组合所有项
            all_terms = merged_regular + merged_abs + merged_tws

            # 如果没有任何项，返回零
            if not all_terms:
                return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])

            # 如果只有一项，可以直接返回该项（保持类型）
            if len(all_terms) == 1:
                return AlgebraicExpression(all_terms)

            return AlgebraicExpression(all_terms)

        else:
            # 包含分式项，需要统一处理为分式表达式
            if debug_callback:
                debug_callback("检测到分式项，统一转换为分式表达式处理", level=2)

            # 将所有非分式项转换为分母为1的分式
            all_fractions = []
            for term in regular_terms + abs_terms + sqrt_terms + term_with_sqrt_terms:
                if isinstance(term, AlgebraicTerm):
                    numerator = AlgebraicExpression([term])
                    denominator = AlgebraicExpression([AlgebraicTerm(Fraction(1, 1))])
                    all_fractions.append(FractionExpression(numerator, denominator))
                elif isinstance(term, (AbsoluteValue, SqrtExpression, TermWithSqrt)):
                    numerator = AlgebraicExpression([term])
                    denominator = AlgebraicExpression([AlgebraicTerm(Fraction(1, 1))])
                    all_fractions.append(FractionExpression(numerator, denominator))
                else:
                    # 不应发生
                    pass

            # 加上已有的分式项
            all_fractions.extend(fraction_terms)

            # 合并所有分式
            if not all_fractions:
                return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])

            result_frac = all_fractions[0]
            for frac in all_fractions[1:]:
                # 通分相加
                a = result_frac.numerator
                b = result_frac.denominator
                c = frac.numerator
                d = frac.denominator
                new_num = (a * d) + (c * b)
                new_den = b * d
                result_frac = FractionExpression(new_num, new_den).simplify(debug_callback)

            # 如果分母为1，返回分子
            if isinstance(result_frac.denominator, AlgebraicExpression) and \
               len(result_frac.denominator.terms) == 1 and \
               isinstance(result_frac.denominator.terms[0], AlgebraicTerm) and \
               result_frac.denominator.terms[0].is_constant() and \
               result_frac.denominator.terms[0].coeff == Fraction(1, 1):
                return result_frac.numerator.simplify(debug_callback)
            else:
                return result_frac

    def __str__(self):
        if not self.terms:
            return "0"
        def term_sort_key(term):
            if isinstance(term, AlgebraicTerm):
                var_str = ''.join(sorted([f"{var}^{exp}" for var, exp in term.vars.items()]))
                priority = 1 if not term.vars else 0
                return (priority, var_str)
            elif isinstance(term, AbsoluteValue):
                return (2, str(term))
            elif isinstance(term, SqrtExpression):
                return (3, str(term))
            elif isinstance(term, FractionExpression):
                return (4, str(term))
            else:
                return (5, str(term))
        sorted_terms = sorted(self.terms, key=term_sort_key)
        terms_str = []
        for i, term in enumerate(sorted_terms):
            term_str = str(term)
            if term_str == "0":
                continue
            if i == 0:
                terms_str.append(term_str)
            else:
                if isinstance(term, AlgebraicTerm) and term.coeff.numerator < 0:
                    neg_term = term * Fraction(-1, 1)
                    terms_str.append(f" - {str(neg_term)}")
                elif term_str.startswith('-'):
                    terms_str.append(f" - {term_str[1:]}")
                else:
                    terms_str.append(f" + {term_str}")
        if not terms_str:
            return "0"
        result = "".join(terms_str)
        result = result.replace(" ", "")
        return result

    def __add__(self, other):
        if isinstance(other, (int, Fraction)):
            other = AlgebraicExpression([AlgebraicTerm(Fraction(other, 1))])
        elif isinstance(other, AlgebraicTerm):
            other = AlgebraicExpression([other])
        elif isinstance(other, AbsoluteValue):
            other = AlgebraicExpression([other])
        elif isinstance(other, SqrtExpression):
            other = AlgebraicExpression([other])
        elif isinstance(other, FractionExpression):
            numerator = self
            denominator = AlgebraicExpression([AlgebraicTerm(Fraction(1, 1))])
            self_as_fraction = FractionExpression(numerator, denominator)
            return self_as_fraction + other
        elif not isinstance(other, AlgebraicExpression):
            return NotImplemented
        new_terms = self.terms + other.terms
        return AlgebraicExpression(new_terms)

    def __sub__(self, other):
        if isinstance(other, (int, Fraction)):
            other = AlgebraicExpression([AlgebraicTerm(Fraction(other, 1))])
        elif isinstance(other, AlgebraicTerm):
            other = AlgebraicExpression([other])
        elif isinstance(other, AbsoluteValue):
            other = AlgebraicExpression([other])
        elif isinstance(other, SqrtExpression):
            other = AlgebraicExpression([other])
        elif not isinstance(other, AlgebraicExpression):
            return NotImplemented
        neg_terms = []
        for term in other.terms:
            if isinstance(term, AbsoluteValue):
                neg_term = term * Fraction(-1, 1)
                if neg_term is None:
                    neg_term = AlgebraicTerm(Fraction(0, 1))
                neg_terms.append(neg_term)
            else:
                is_zero = False
                if hasattr(term, 'is_zero') and term.is_zero():
                    is_zero = True
                elif hasattr(term, 'coeff') and hasattr(term.coeff, 'numerator') and term.coeff.numerator == 0:
                    is_zero = True
                if not is_zero:
                    neg = term * Fraction(-1, 1)
                    if neg is None:
                        neg = AlgebraicTerm(Fraction(0, 1))
                    neg_terms.append(neg)
        new_terms = self.terms + neg_terms
        if new_terms is None:
            new_terms = []
        result = AlgebraicExpression(new_terms)
        if result is None:
            result = AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])
        return result

    def __mul__(self, other):
        if isinstance(other, (int, Fraction)):
            new_terms = []
            for term in self.terms:
                new_terms.append(term * other)
            return AlgebraicExpression(new_terms)
        elif isinstance(other, AlgebraicTerm):
            new_terms = []
            for term in self.terms:
                new_terms.append(term * other)
            return AlgebraicExpression(new_terms)
        elif isinstance(other, AlgebraicExpression):
            new_terms = []
            for t1 in self.terms:
                for t2 in other.terms:
                    if isinstance(t1, AbsoluteValue) and isinstance(t2, AbsoluteValue):
                        new_terms.append(t1 * t2)
                    elif isinstance(t1, SqrtExpression):
                        new_terms.append(t1 * t2)
                    elif isinstance(t2, AbsoluteValue):
                        new_terms.append(t2 * t1)
                    elif isinstance(t2, SqrtExpression):
                        new_terms.append(t2 * t1)
                    elif isinstance(t1, FractionExpression) or isinstance(t2, FractionExpression):
                        if isinstance(t1, FractionExpression):
                            new_terms.append(t1 * t2)
                        else:
                            new_terms.append(t2 * t1)
                    else:
                        new_terms.append(t1 * t2)
            return AlgebraicExpression(new_terms)
        elif isinstance(other, AbsoluteValue):
            return other * self
        elif isinstance(other, SqrtExpression):
            new_terms = []
            for term in self.terms:
                new_terms.append(term * other)
            return AlgebraicExpression(new_terms)
        # ========== 新增：处理 TermWithSqrt ==========
        elif isinstance(other, TermWithSqrt):
            new_terms = []
            for term in self.terms:
                new_terms.append(term * other)
            return AlgebraicExpression(new_terms)
        # ========== 结束 ==========
        elif isinstance(other, FractionExpression):
            new_numerator = self * other.numerator
            return FractionExpression(new_numerator, other.denominator)
        return NotImplemented

    def __rmul__(self, other):
        if isinstance(other, (int, Fraction)):
            return self * other
        return NotImplemented

    def __neg__(self):
        new_terms = []
        for term in self.terms:
            new_terms.append(-term)
        return AlgebraicExpression(new_terms)

    def __truediv__(self, other):
        if isinstance(other, (int, Fraction)):
            new_terms = []
            for term in self.terms:
                if isinstance(term, AbsoluteValue):
                    new_terms.append(AbsoluteValue(term.inner_expr / other))
                else:
                    new_terms.append(term / other)
            return AlgebraicExpression(new_terms)
        elif isinstance(other, AlgebraicTerm):
            new_terms = []
            for term in self.terms:
                if isinstance(term, AbsoluteValue):
                    return FractionExpression(self, AlgebraicExpression([other]))
                else:
                    new_terms.append(term / other)
            return AlgebraicExpression(new_terms)
        elif isinstance(other, AlgebraicExpression):
            if len(other.terms) == 1 and isinstance(other.terms[0], AlgebraicTerm) and other.terms[0].is_constant():
                const = other.terms[0].coeff
                return self / const
            else:
                return FractionExpression(self, other)
        elif isinstance(other, AbsoluteValue):
            return FractionExpression(self, AlgebraicExpression([other]))
        return NotImplemented

    def __pow__(self, exp):
        if not isinstance(exp, int):
            raise TypeError("指数必须是整数")
        if exp == 0:
            return AlgebraicExpression([AlgebraicTerm(Fraction(1, 1))])
        if exp == 1:
            return self
        if exp == 2:
            return self * self
        result = self
        for _ in range(abs(exp) - 1):
            result = result * self
        if exp < 0:
            return FractionExpression(
                AlgebraicExpression([AlgebraicTerm(Fraction(1, 1))]),
                result
            )
        return result

    def is_constant(self):
        return len(self.terms) == 1 and isinstance(self.terms[0], AlgebraicTerm) and self.terms[0].is_constant()

    def contains_absolute_value(self):
        for term in self.terms:
            if isinstance(term, AbsoluteValue):
                return True
        return False

    def substitute(self, var, expr, debug_callback=None):
        if debug_callback:
            debug_callback(f"Substituting {var} with {expr} in {self}", level=3)

        def substitute_term(term, debug_callback=None):
            if isinstance(term, AlgebraicTerm):
                if var in term.vars:
                    exp = term.vars[var]
                    other_vars = {k: v for k, v in term.vars.items() if k != var}
                    pow_expr = expr ** exp
                    base_term = AlgebraicTerm(term.coeff, other_vars)
                    substituted = base_term * pow_expr
                    return substituted.terms
                else:
                    return [deepcopy(term)]
            elif isinstance(term, AbsoluteValue):
                new_inner = term.inner_expr.substitute(var, expr, debug_callback)
                return [AbsoluteValue(new_inner)]
            elif isinstance(term, SqrtExpression):
                new_inner = term.inner_expr.substitute(var, expr, debug_callback)
                return [SqrtExpression(new_inner)]
            elif isinstance(term, TermWithSqrt):
                substituted = term.substitute(var, expr, debug_callback)
                if isinstance(substituted, AlgebraicExpression):
                    return substituted.terms
                elif isinstance(substituted, (AlgebraicTerm, AbsoluteValue, SqrtExpression, TermWithSqrt)):
                    return [substituted]
                elif substituted is None:
                    return []
                else:
                    return [substituted]
            elif isinstance(term, FractionExpression):
                new_num = term.numerator.substitute(var, expr, debug_callback)
                new_den = term.denominator.substitute(var, expr, debug_callback)
                return [FractionExpression(new_num, new_den)]
            else:
                return [deepcopy(term)]

        from copy import deepcopy
        new_terms = []
        for term in self.terms:
            new_terms.extend(substitute_term(term, debug_callback))
        return AlgebraicExpression(new_terms).simplify(debug_callback)

    def is_zero(self):
        if not self.terms:
            return True
        for term in self.terms:
            if isinstance(term, AlgebraicTerm):
                if term.coeff.numerator != 0:
                    return False
            elif hasattr(term, 'is_zero'):
                if not term.is_zero():
                    return False
            else:
                return False
        return True

    def rationalize_denominator(self, debug_callback=None):
        if debug_callback:
            debug_callback(f"开始分母有理化: {self}", level=1)
        sqrt_terms = [term for term in self.terms if isinstance(term, SqrtExpression)]
        if not sqrt_terms:
            return self
        if len(self.terms) == 1 and isinstance(self.terms[0], SqrtExpression):
            sqrt_term = self.terms[0]
            return sqrt_term.rationalize_denominator(self, debug_callback)
        if debug_callback:
            debug_callback("分母包含多个项，需要使用共轭有理化", level=2)
        return self


# ========== 分式表达式 FractionExpression ==========

class FractionExpression:
    """表示分式表达式，支持分母有理化"""

    def __init__(self, numerator, denominator):
        self.numerator = numerator
        self.denominator = denominator
        self.rationalized = False
        self.terms = [self]

    def __eq__(self, other):
        if not isinstance(other, FractionExpression):
            return False
        return self.numerator == other.numerator and self.denominator == other.denominator

    def __mul__(self, other):
        if isinstance(other, (int, Fraction)):
            new_numerator = self.numerator * other
            return FractionExpression(new_numerator, self.denominator)
        elif isinstance(other, AlgebraicTerm):
            new_numerator = self.numerator * other
            return FractionExpression(new_numerator, self.denominator)
        elif isinstance(other, AlgebraicExpression):
            new_numerator = self.numerator * other
            return FractionExpression(new_numerator, self.denominator)
        elif isinstance(other, FractionExpression):
            new_numerator = self.numerator * other.numerator
            new_denominator = self.denominator * other.denominator
            return FractionExpression(new_numerator, new_denominator)
        elif isinstance(other, AbsoluteValue):
            new_numerator = self.numerator * other
            return FractionExpression(new_numerator, self.denominator)
        elif isinstance(other, SqrtExpression):
            new_numerator = self.numerator * other
            return FractionExpression(new_numerator, self.denominator)
        return NotImplemented

    def __rmul__(self, other):
        return self.__mul__(other)

    def rationalize(self, debug_callback=None):
        rationalizer = DenominatorRationalizer()
        rationalized = rationalizer.rationalize(self, debug_callback)
        rationalized.rationalized = True
        return rationalized

    def __add__(self, other):
        if isinstance(other, (int, Fraction)):
            other = FractionExpression(
                AlgebraicExpression([AlgebraicTerm(Fraction(other, 1))]),
                AlgebraicExpression([AlgebraicTerm(Fraction(1, 1))])
            )
        elif isinstance(other, AlgebraicTerm):
            other = FractionExpression(
                AlgebraicExpression([other]),
                AlgebraicExpression([AlgebraicTerm(Fraction(1, 1))])
            )
        elif isinstance(other, AlgebraicExpression):
            other = FractionExpression(
                other,
                AlgebraicExpression([AlgebraicTerm(Fraction(1, 1))])
            )
        elif isinstance(other, (AbsoluteValue, SqrtExpression)):
            other = FractionExpression(
                AlgebraicExpression([other]),
                AlgebraicExpression([AlgebraicTerm(Fraction(1, 1))])
            )
        if isinstance(other, FractionExpression):
            if self.denominator == other.denominator:
                new_numerator = self.numerator + other.numerator
                new_denominator = self.denominator
                return FractionExpression(new_numerator, new_denominator)
            a = self.numerator
            b = self.denominator
            c = other.numerator
            d = other.denominator
            new_numerator = (a * d) + (c * b)
            new_denominator = b * d
            return FractionExpression(new_numerator, new_denominator)
        return NotImplemented

    def __radd__(self, other):
        return self.__add__(other)

    def __neg__(self):
        return FractionExpression(-self.numerator, self.denominator)

    def __sub__(self, other):
        if isinstance(other, (int, Fraction, AlgebraicTerm, AlgebraicExpression, AbsoluteValue, SqrtExpression, FractionExpression)):
            return self + (-other)
        return NotImplemented

    def __rsub__(self, other):
        if isinstance(other, (int, Fraction, AlgebraicTerm, AlgebraicExpression, AbsoluteValue, SqrtExpression)):
            return -(self - other)
        return NotImplemented

    def __str__(self):
        num_str = str(self.numerator)
        den_str = str(self.denominator)
        if any(op in num_str for op in '+-'):
            num_str = f"({num_str})"
        if any(op in den_str for op in '+-'):
            den_str = f"({den_str})"
        return f"{num_str}/{den_str}"

    def _contains_sqrt(self, expr):
        if isinstance(expr, SqrtExpression):
            return True
        elif isinstance(expr, AlgebraicExpression):
            for term in expr.terms:
                if isinstance(term, (SqrtExpression, TermWithSqrt)):
                    return True
        return False

    def is_zero(self):
        num = self.numerator
        if hasattr(num, 'simplify'):
            num = num.simplify()
        if isinstance(num, AlgebraicExpression):
            return num.is_zero()
        elif isinstance(num, (int, Fraction)):
            return num == 0
        elif hasattr(num, 'is_zero'):
            return num.is_zero()
        else:
            return False

    def is_constant(self):
        num = self.numerator
        den = self.denominator
        if hasattr(num, 'simplify'):
            num = num.simplify()
        if hasattr(den, 'simplify'):
            den = den.simplify()
        return (hasattr(num, 'is_constant') and num.is_constant() and
                hasattr(den, 'is_constant') and den.is_constant())

    def canonicalize_sign(self):
        if isinstance(self.denominator, AlgebraicExpression) and self.denominator.is_constant():
            const = self.denominator.terms[0].coeff
            if const == Fraction(1, 1):
                return self
        num = self.numerator
        den = self.denominator
        def term_sort_key(term):
            if isinstance(term, AlgebraicTerm):
                var_str = ''.join(sorted([f"{var}^{exp}" for var, exp in term.vars.items()]))
                priority = 1 if not term.vars else 0
                return (priority, var_str)
            else:
                return (2, str(term))
        def sorted_terms(expr):
            if not isinstance(expr, AlgebraicExpression):
                return expr.terms if hasattr(expr, 'terms') else [expr]
            return sorted(expr.terms, key=term_sort_key)
        den_terms = sorted_terms(den)
        first_den = den_terms[0] if den_terms else None
        neg_one = AlgebraicExpression([AlgebraicTerm(Fraction(-1, 1))])
        den_neg = (den * neg_one).simplify()
        num_neg = (num * neg_one).simplify()
        den_neg_terms = sorted_terms(den_neg)
        first_neg = den_neg_terms[0] if den_neg_terms else None
        def is_preferred(first):
            if isinstance(first, AlgebraicTerm):
                if first.vars and first.coeff.numerator > 0:
                    return True
            return False
        prefer_original = is_preferred(first_den)
        prefer_neg = is_preferred(first_neg)
        if prefer_neg and not prefer_original:
            return FractionExpression(num_neg, den_neg).canonicalize_sign()
        elif not prefer_neg and prefer_original:
            return self
        else:
            if first_den and isinstance(first_den, AlgebraicTerm) and not first_den.vars:
                if first_den.coeff.numerator > 0:
                    return self
            if first_neg and isinstance(first_neg, AlgebraicTerm) and not first_neg.vars:
                if first_neg.coeff.numerator > 0:
                    return FractionExpression(num_neg, den_neg).canonicalize_sign()
            return self

    def substitute(self, var, expr, debug_callback=None):
        new_num = self.numerator.substitute(var, expr, debug_callback)
        new_den = self.denominator.substitute(var, expr, debug_callback)
        return FractionExpression(new_num, new_den)

    def __pow__(self, other):
        if isinstance(other, int):
            if other >= 0:
                return FractionExpression(self.numerator ** other, self.denominator ** other)
            else:
                return FractionExpression(self.denominator ** (-other), self.numerator ** (-other))
        raise TypeError("指数必须是整数")

    def simplify(self, debug_callback=None):
        try:
            if debug_callback:
                debug_callback(f"【FractionExpression.simplify】开始化简: {self}", level=1)
            if self._contains_sqrt(self.numerator) or self._contains_sqrt(self.denominator):
                if debug_callback:
                    debug_callback("分子或分母包含根号，跳过化简", level=2)
                return self
            if hasattr(self, '_simplify_depth'):
                depth = self._simplify_depth
                if depth > 5:
                    if debug_callback:
                        debug_callback(f"达到最大递归深度 {depth}，停止化简", level=2)
                    return self
            else:
                depth = 0
            self._simplify_depth = depth + 1
            if hasattr(self.numerator, 'simplify'):
                simplified_num = self.numerator.simplify(debug_callback)
            else:
                simplified_num = self.numerator
            if hasattr(self.denominator, 'simplify'):
                simplified_den = self.denominator.simplify(debug_callback)
            else:
                simplified_den = self.denominator

            def has_neg_exp(expr):
                if isinstance(expr, AlgebraicExpression):
                    for term in expr.terms:
                        if isinstance(term, AlgebraicTerm):
                            for exp in term.vars.values():
                                if exp < 0:
                                    return True
                return False

            if has_neg_exp(simplified_den):
                if debug_callback:
                    debug_callback(f"分母 {simplified_den} 含有负指数，尝试消除", level=2)
                neg_vars = {}
                for term in simplified_den.terms:
                    if isinstance(term, AlgebraicTerm):
                        for var, exp in term.vars.items():
                            if exp < 0:
                                if var in neg_vars:
                                    neg_vars[var] = min(neg_vars[var], exp)
                                else:
                                    neg_vars[var] = exp
                if neg_vars:
                    factor_dict = {var: -exp for var, exp in neg_vars.items()}
                    multiplier_term = AlgebraicTerm(Fraction(1, 1), factor_dict)
                    multiplier_expr = AlgebraicExpression([multiplier_term])
                    new_num = (simplified_num * multiplier_expr).simplify(debug_callback)
                    new_den = (simplified_den * multiplier_expr).simplify(debug_callback)
                    if debug_callback:
                        debug_callback(f"乘以因子 {multiplier_expr} 后得到: {new_num}/{new_den}", level=3)
                    new_frac = FractionExpression(new_num, new_den)
                    simplified_result = new_frac.simplify(debug_callback)
                    if hasattr(simplified_result, '_simplify_depth'):
                        del simplified_result._simplify_depth
                    if simplified_result is None:
                        if debug_callback:
                            debug_callback("警告：FractionExpression.simplify 返回 None，使用零表达式", level=1)
                        return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])
                    return simplified_result

            num_str = str(simplified_num).replace(' ', '')
            den_str = str(simplified_den).replace(' ', '')
            if debug_callback:
                debug_callback(f"分子化简后: {num_str}", level=3)
                debug_callback(f"分母化简后: {den_str}", level=3)
            if num_str == den_str:
                if debug_callback:
                    debug_callback(f"分子分母相同，约分为1", level=2)
                return AlgebraicExpression([AlgebraicTerm(Fraction(1, 1))])
            try:
                if isinstance(simplified_den, AlgebraicExpression) and len(simplified_den.terms) == 1:
                    if isinstance(simplified_den.terms[0], (AlgebraicTerm, TermWithSqrt)):
                        denominator_term = simplified_den.terms[0]
                        if isinstance(simplified_num, AlgebraicExpression):
                            all_terms_divisible = True
                            quotient_terms = []
                            for term in simplified_num.terms:
                                if isinstance(term, (AlgebraicTerm, TermWithSqrt)):
                                    try:
                                        quotient = term / denominator_term
                                        quotient_terms.append(quotient)
                                    except:
                                        all_terms_divisible = False
                                        break
                                else:
                                    all_terms_divisible = False
                                    break
                            if all_terms_divisible and quotient_terms:
                                result_expr = AlgebraicExpression(quotient_terms)
                                simplified_result = result_expr.simplify(debug_callback)
                                if debug_callback:
                                    debug_callback(f"分子能被分母整除，结果为: {simplified_result}", level=2)
                                if simplified_result is None:
                                    if debug_callback:
                                        debug_callback("警告：FractionExpression.simplify 返回 None，使用零表达式", level=1)
                                    return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])
                                return simplified_result
            except Exception as e:
                if debug_callback:
                    debug_callback(f"尝试约分时出错: {str(e)}", level=3)

            if isinstance(simplified_den, AlgebraicExpression) and simplified_den.is_constant():
                const = simplified_den.terms[0].coeff
                if const != Fraction(1, 1):
                    if isinstance(simplified_num, AlgebraicExpression):
                        new_terms = []
                        all_terms_are_terms = True
                        for term in simplified_num.terms:
                            if isinstance(term, (AlgebraicTerm, TermWithSqrt)):
                                try:
                                    new_term = term / const
                                    new_terms.append(new_term)
                                except:
                                    all_terms_are_terms = False
                                    break
                            else:
                                all_terms_are_terms = False
                                break
                        if all_terms_are_terms and new_terms:
                            result_expr = AlgebraicExpression(new_terms)
                            simplified_result = result_expr.simplify(debug_callback)
                            if debug_callback:
                                debug_callback(f"分母为常数，将分子各项除以 {const} 得: {simplified_result}", level=2)
                            if simplified_result is None:
                                if debug_callback:
                                    debug_callback("警告：FractionExpression.simplify 返回 None，使用零表达式", level=1)
                                return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])
                            return simplified_result
                    elif isinstance(simplified_num, (AlgebraicTerm, TermWithSqrt)):
                        try:
                            result = simplified_num / const
                            if hasattr(result, 'simplify'):
                                result = result.simplify(debug_callback)
                            if debug_callback:
                                debug_callback(f"分母为常数，分子单项式除以常数得: {result}", level=2)
                            if result is None:
                                if debug_callback:
                                    debug_callback("警告：FractionExpression.simplify 返回 None，使用零表达式", level=1)
                                return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])
                            return result
                        except Exception as e:
                            if debug_callback:
                                debug_callback(f"除以常数时出错: {e}，保留分式形式", level=2)

            if isinstance(simplified_den, AlgebraicExpression) and simplified_den.is_constant():
                const = simplified_den.terms[0].coeff
                if const == Fraction(1, 1):
                    if debug_callback:
                        debug_callback("分母为1，返回分子", level=2)
                    if simplified_num is None:
                        if debug_callback:
                            debug_callback("警告：FractionExpression.simplify 返回 None，使用零表达式", level=1)
                        return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])
                    return simplified_num
            if isinstance(simplified_num, AlgebraicExpression) and simplified_num.is_constant():
                const = simplified_num.terms[0].coeff
                if const.numerator == 0:
                    if debug_callback:
                        debug_callback("分子为0，返回0", level=2)
                    return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])
            if str(self.numerator).replace(' ', '') == str(self.denominator).replace(' ', ''):
                if debug_callback:
                    debug_callback("分子分母相同，返回1", level=2)
                return AlgebraicExpression([AlgebraicTerm(Fraction(1, 1))])
            contains_sqrt = False
            if isinstance(self.denominator, SqrtExpression):
                contains_sqrt = True
            elif isinstance(self.denominator, AlgebraicExpression):
                for term in self.denominator.terms:
                    if isinstance(term, SqrtExpression):
                        contains_sqrt = True
                        break
            if contains_sqrt:
                if debug_callback:
                    debug_callback("分母包含根号，保持分式形式", level=2)
                return self
            try:
                if hasattr(self.numerator, 'simplify'):
                    simplified_num = self.numerator.simplify(debug_callback)
                else:
                    simplified_num = self.numerator
                if hasattr(self.denominator, 'simplify'):
                    simplified_den = self.denominator.simplify(debug_callback)
                else:
                    simplified_den = self.denominator
            except RecursionError:
                if debug_callback:
                    debug_callback("递归深度过大，返回原始分式", level=2)
                return self
            result = FractionExpression(simplified_num, simplified_den)
            if hasattr(simplified_den, 'is_constant') and simplified_den.is_constant():
                const = simplified_den.terms[0].coeff
                if const == Fraction(1, 1):
                    if debug_callback:
                        debug_callback("分母为1，返回分子", level=2)
                    if simplified_num is None:
                        if debug_callback:
                            debug_callback("警告：FractionExpression.simplify 返回 None，使用零表达式", level=1)
                        return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])
                    return simplified_num
            if hasattr(result, '_simplify_depth'):
                del result._simplify_depth
            if result is None:
                if debug_callback:
                    debug_callback("警告：FractionExpression.simplify 返回 None，使用零表达式", level=1)
                return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])
            return result
        except AttributeError as e:
            if debug_callback:
                debug_callback(f"在 FractionExpression.simplify 中捕获 AttributeError: {e}，返回原分式", level=1)
            return self


# ========== 分母有理化器 DenominatorRationalizer ==========

class DenominatorRationalizer:
    @staticmethod
    def rationalize(fraction_expr, debug_callback=None):
        numerator = fraction_expr.numerator
        denominator = fraction_expr.denominator
        if debug_callback:
            debug_callback(f"开始分母有理化: {numerator} / {denominator}", level=1)
        if isinstance(denominator, AlgebraicExpression) and denominator.is_constant():
            const = denominator.terms[0].coeff
            if const == Fraction(1, 1):
                if debug_callback:
                    debug_callback("分母为1，无需有理化", level=3)
                return fraction_expr
        if isinstance(denominator, SqrtExpression):
            if debug_callback:
                debug_callback(f"检测到分母为SqrtExpression: √({denominator.inner_expr})", level=2)
            return DenominatorRationalizer._rationalize_single_sqrt(
                numerator, denominator, debug_callback
            )
        if isinstance(denominator, AlgebraicExpression):
            sqrt_count = 0
            sqrt_term = None
            for term in denominator.terms:
                if isinstance(term, SqrtExpression):
                    sqrt_count += 1
                    sqrt_term = term
            if sqrt_count == 1 and len(denominator.terms) == 1:
                if debug_callback:
                    debug_callback(f"检测到分母为单个根号项: √({sqrt_term.inner_expr})", level=2)
                return DenominatorRationalizer._rationalize_single_sqrt(
                    numerator, sqrt_term, debug_callback
                )
            elif sqrt_count > 0:
                if debug_callback:
                    debug_callback("分母包含多个项，需要使用共轭有理化", level=2)
                return fraction_expr
        if debug_callback:
            debug_callback("分母不包含根号，无需有理化", level=3)
        return fraction_expr

    @staticmethod
    def _rationalize_single_sqrt(numerator, sqrt_term, debug_callback):
        if isinstance(numerator, AlgebraicExpression):
            if numerator.is_constant() and numerator.terms[0].coeff == Fraction(1, 1):
                new_numerator = sqrt_term
                new_denominator = sqrt_term.inner_expr
                if debug_callback:
                    debug_callback(f"分子为1，直接返回: {new_numerator} / {new_denominator}", level=2)
                return FractionExpression(new_numerator, new_denominator)
        new_numerator = numerator * sqrt_term
        new_denominator = sqrt_term.inner_expr
        if debug_callback:
            debug_callback(f"通用有理化: {new_numerator} / {new_denominator}", level=2)
        if hasattr(new_numerator, 'simplify'):
            simplified_num = new_numerator.simplify(debug_callback)
        else:
            simplified_num = new_numerator
        if hasattr(new_denominator, 'simplify'):
            simplified_den = new_denominator.simplify(debug_callback)
        else:
            simplified_den = new_denominator
        if isinstance(simplified_den, AlgebraicExpression) and simplified_den.is_constant():
            const = simplified_den.terms[0].coeff
            if const == Fraction(1, 1):
                return simplified_num
        return FractionExpression(simplified_num, simplified_den)