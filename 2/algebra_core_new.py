import re
import math
from collections import defaultdict
from enum import Enum


class ExpressionType(Enum):
    """表达式类型枚举"""
    TERM = "term"  # 代数项
    ABSOLUTE_VALUE = "absolute_value"  # 绝对值表达式
    SQRT = "sqrt"  # 根号表达式


class Fraction:
    """分数类，用于精确表示有理数"""

    def __init__(self, numerator=0, denominator=1):
        self.numerator = numerator
        self.denominator = denominator
        self.normalize()

    def __abs__(self):
        """返回分数的绝对值"""
        return Fraction(abs(self.numerator), self.denominator)

    def normalize(self):
        """规范化分数（约分，确保分母为正）"""
        if self.denominator == 0:
            raise ValueError("分母不能为零")

        # 约分
        gcd_val = math.gcd(abs(self.numerator), abs(self.denominator))
        if gcd_val > 0:
            self.numerator //= gcd_val
            self.denominator //= gcd_val

        # 确保分母为正
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
        elif isinstance(other, AlgebraicTerm) or isinstance(other, AlgebraicExpression) or isinstance(other,
                                                                                                      AbsoluteValue):
            # 分数与代数项或表达式相乘
            return other * self  # 这会调用相应类的 __mul__ 方法
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
        """从字符串创建分数，支持整数、小数、分数格式"""
        s = s.strip()
        if '/' in s:
            num, den = s.split('/')
            return Fraction(int(num), int(den))
        elif '.' in s:
            # 将小数转换为分数
            integer_part, decimal_part = s.split('.')
            denominator = 10 ** len(decimal_part)
            numerator = int(integer_part) * denominator + int(decimal_part)
            if integer_part.startswith('-'):
                numerator = -abs(numerator)
            return Fraction(numerator, denominator)
        else:
            return Fraction(int(s), 1)


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
            return AlgebraicTerm(new_coeff, new_vars)
        elif isinstance(other, AbsoluteValue):
            return AbsoluteValue(self * other.inner_expr)
        elif isinstance(other, SqrtExpression):
            # 代数项乘以根号
            # 返回代数表达式，包含两个项：代数项和根号项
            # 注意：这里需要构建乘法表达式，而不是加法
            return AlgebraicExpression([self, other])
        return NotImplemented

    def __truediv__(self, other):
        if isinstance(other, (int, Fraction)):
            return AlgebraicTerm(self.coeff / other, self.vars.copy())
        elif isinstance(other, AlgebraicTerm):
            new_coeff = self.coeff / other.coeff
            new_vars = self.vars.copy()
            for var, exp in other.vars.items():
                new_vars[var] = new_vars.get(var, 0) - exp
            # 移除指数为0的变量
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
        """检查是否为同类项"""
        return self.vars == other.vars

    def is_constant(self):
        """是否为常数项"""
        return len(self.vars) == 0

    def contains_var(self, var):
        """检查是否包含指定变量"""
        return var in self.vars

    def get_coefficient_for_var(self, var):
        """获取指定变量的系数（如果该项只包含该变量）"""
        if len(self.vars) == 1 and var in self.vars and self.vars[var] == 1:
            return self.coeff
        elif var in self.vars and self.vars[var] >= 1:
            # 如果变量有指数，我们暂时只处理指数为1的情况
            if self.vars[var] == 1:
                # 复制变量字典，移除该变量
                new_vars = self.vars.copy()
                del new_vars[var]
                return AlgebraicTerm(self.coeff, new_vars)
            else:
                return None
        else:
            return None

    def __str__(self):
        # 系数为0
        if self.coeff.numerator == 0:
            return "0"

        # 构建系数部分
        coeff_str = str(self.coeff)

        # 系数为1或-1且存在变量时，省略系数
        if self.coeff == Fraction(1, 1) and self.vars:
            coeff_str = ""
        elif self.coeff == Fraction(-1, 1) and self.vars:
            coeff_str = "-"
        elif self.coeff.denominator != 1 and self.vars:
            coeff_str = f"({coeff_str})"

        # 构建变量部分
        var_parts = []
        for var in sorted(self.vars.keys()):
            exp = self.vars[var]
            if exp == 1:
                var_parts.append(var)
            else:
                var_parts.append(f"{var}^{exp}")

        var_str = "".join(var_parts) if var_parts else ""

        # 组合
        if coeff_str and var_str:
            return f"{coeff_str}{var_str}"
        elif coeff_str:
            return coeff_str
        elif var_str:
            return var_str
        else:
            return "1"  # 系数和变量都为空的情况

    @staticmethod
    def from_string(s):
        """从字符串创建代数项"""
        s = s.strip()
        if not s:
            return AlgebraicTerm(Fraction(0, 1))

        # 处理负号
        sign = 1
        if s[0] == '-':
            sign = -1
            s = s[1:]

        # 分离系数和变量
        coeff_str = ""
        var_part = ""

        i = 0
        while i < len(s) and (s[i].isdigit() or s[i] in './'):
            coeff_str += s[i]
            i += 1

        var_part = s[i:]

        # 解析系数
        if coeff_str:
            coeff = Fraction.from_string(coeff_str)
        else:
            coeff = Fraction(1, 1)

        coeff = coeff * sign

        # 解析变量
        vars_dict = {}
        if var_part:
            # 解析变量和指数，如 x, x^2, xy, x^2y^3
            matches = re.findall(r'([a-zA-Z])(?:\^(\d+))?', var_part)
            for var, exp_str in matches:
                exp = int(exp_str) if exp_str else 1
                vars_dict[var] = vars_dict.get(var, 0) + exp

        return AlgebraicTerm(coeff, vars_dict)

    def __pow__(self, exp):
        """代数项的幂运算"""
        if isinstance(exp, int) and exp >= 0:
            # 整数次幂
            new_coeff = self.coeff ** exp
            new_vars = {}
            for var, var_exp in self.vars.items():
                new_vars[var] = var_exp * exp
            return AlgebraicTerm(new_coeff, new_vars)
        else:
            # 非整数指数或负指数，返回一个包含幂运算的表达式
            return AlgebraicExpression([self]) ** exp


class AbsoluteValue:
    """表示绝对值表达式，如 |x|, |x+y| 等"""

    def __init__(self, inner_expr):
        self.inner_expr = inner_expr
        self.expr_type = ExpressionType.ABSOLUTE_VALUE

    def simplify(self, debug_callback=None):
        """简化绝对值表达式"""
        if debug_callback:
            debug_callback(f"简化绝对值表达式: |{self.inner_expr}|")

        # 如果内部表达式是常数，直接计算绝对值
        if isinstance(self.inner_expr, AlgebraicExpression):
            if self.inner_expr.is_constant():
                # 获取常数值
                const = self.inner_expr.terms[0].coeff
                # 计算绝对值
                if const.numerator >= 0:
                    result = const
                else:
                    result = Fraction(-const.numerator, const.denominator)

                if debug_callback:
                    debug_callback(f"常数绝对值: |{const}| = {result}")

                return AlgebraicExpression([AlgebraicTerm(result)])

        # 简化内部表达式
        simplified_inner = self.inner_expr.simplify(debug_callback)
        if simplified_inner != self.inner_expr:
            return AbsoluteValue(simplified_inner)

        # 无法进一步简化，返回自身
        return self

    def __str__(self):
        inner_str = str(self.inner_expr)
        # 如果内部表达式包含运算符，需要加括号
        if any(op in inner_str for op in '+-'):
            return f"|({inner_str})|"
        else:
            return f"|{inner_str}|"

    def __mul__(self, other):
        if isinstance(other, (int, Fraction)):
            # 绝对值乘以常数
            return AbsoluteValue(self.inner_expr * other)
        elif isinstance(other, AlgebraicTerm):
            # 绝对值乘以代数项
            return AbsoluteValue(self.inner_expr * other)
        elif isinstance(other, AlgebraicExpression):
            # 绝对值乘以代数表达式
            return AbsoluteValue(self.inner_expr * other)
        elif isinstance(other, AbsoluteValue):
            # 绝对值乘以绝对值：|a| * |b| = |a*b|
            return AbsoluteValue(self.inner_expr * other.inner_expr)
        return NotImplemented

    def __rmul__(self, other):
        """支持右侧乘法，如 2 * |x|"""
        if isinstance(other, (int, Fraction)):
            return self * other
        return NotImplemented

    def __add__(self, other):
        # 绝对值加法通常不能简化，除非内部表达式相同
        if isinstance(other, AbsoluteValue):
            if self.inner_expr == other.inner_expr:
                # |a| + |a| = 2|a|
                return AbsoluteValue(AlgebraicExpression([AlgebraicTerm(Fraction(2, 1))]) * self.inner_expr)

        # 其他情况，返回表达式形式
        return AlgebraicExpression([self]) + other

    def __sub__(self, other):
        # 类似加法处理
        if isinstance(other, AbsoluteValue):
            if self.inner_expr == other.inner_expr:
                # |a| - |a| = 0
                return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])

        # 其他情况，返回表达式形式
        return AlgebraicExpression([self]) - other

    def __eq__(self, other):
        if isinstance(other, AbsoluteValue):
            return self.inner_expr == other.inner_expr
        return False

    def contains_var(self, var):
        """检查是否包含指定变量"""
        if isinstance(self.inner_expr, AlgebraicExpression):
            for term in self.inner_expr.terms:
                if term.contains_var(var):
                    return True
        elif isinstance(self.inner_expr, AlgebraicTerm):
            return self.inner_expr.contains_var(var)
        return False

    def expand_with_cases(self, debug_callback=None):
        """展开绝对值，返回分类讨论的结果"""
        if debug_callback:
            debug_callback(f"展开绝对值表达式: |{self.inner_expr}|")

        # 检查内部表达式是否是线性表达式
        if isinstance(self.inner_expr, AlgebraicExpression):
            # 获取所有变量
            all_vars = set()
            for term in self.inner_expr.terms:
                for var in term.vars:
                    all_vars.add(var)

            if len(all_vars) == 1:
                # 单个变量，可以分类讨论
                var_name = list(all_vars)[0]
                if debug_callback:
                    debug_callback(f"单变量绝对值: |{var_name}|")

                # 创建分类讨论的结果
                result = f"|{var_name}| = {{\n"
                result += f"  {var_name}, 当 {var_name} ≥ 0\n"
                result += f"  -{var_name}, 当 {var_name} < 0\n"
                result += "}"
                return result

        # 对于复杂的表达式，返回通用的分类讨论
        inner_str = str(self.inner_expr)
        result = f"|{inner_str}| = {{\n"
        result += f"  {inner_str}, 当 {inner_str} ≥ 0\n"
        result += f"  -({inner_str}), 当 {inner_str} < 0\n"
        result += "}"

        if debug_callback:
            debug_callback(f"绝对值展开结果: {result}")

        return result


class SqrtExpression:
    """表示平方根表达式，如 √(x), √(x+y) 等"""

    def __init__(self, inner_expr):
        self.inner_expr = inner_expr
        self.expr_type = ExpressionType.SQRT

    def simplify(self, debug_callback=None):
        """化简根号表达式"""
        if debug_callback:
            debug_callback(f"化简根号表达式: √({self.inner_expr})")

        # 先化简内部表达式
        if hasattr(self.inner_expr, 'simplify'):
            simplified_inner = self.inner_expr.simplify(debug_callback)
        else:
            simplified_inner = self.inner_expr

        # 如果内部是常数，计算数值平方根（只处理精确平方数）
        if isinstance(simplified_inner, AlgebraicExpression) and simplified_inner.is_constant():
            const = simplified_inner.terms[0].coeff
            # 检查常数是否为平方数
            num = const.numerator
            den = const.denominator
            num_sqrt = self._is_perfect_square(num)
            den_sqrt = self._is_perfect_square(den)

            if num_sqrt and den_sqrt:
                # 完全平方数
                result = Fraction(num_sqrt, den_sqrt)
                if debug_callback:
                    debug_callback(f"常数完全平方根: √({const}) = {result}")
                return AlgebraicExpression([AlgebraicTerm(result)])
            elif debug_callback:
                debug_callback(f"常数 {const} 不是完全平方数")

        # 提取平方因子
        return self._extract_square_factors(simplified_inner, debug_callback)

    def _is_perfect_square(self, n):
        """检查是否为完全平方数"""
        if n < 0:
            return None
        root = int(math.isqrt(n))
        return root if root * root == n else None

    def _extract_square_factors(self, expr, debug_callback=None):
        """提取平方因子，如 √(8x³) = 2x√(2x)"""
        if debug_callback:
            debug_callback(f"提取平方因子: √({expr})")
            debug_callback(f"expr 类型: {type(expr)}")
            if isinstance(expr, AlgebraicExpression):
                debug_callback(f"expr.terms 长度: {len(expr.terms)}")
                for i, term in enumerate(expr.terms):
                    debug_callback(f"  项 {i}: {term}, 类型: {type(term)}")

        # 如果表达式是代数表达式
        if isinstance(expr, AlgebraicExpression):
            # 检查表达式是否只有一个项
            if len(expr.terms) == 1:
                term = expr.terms[0]
                if isinstance(term, AlgebraicTerm):
                    # 提取系数的平方因子
                    coeff = term.coeff

                    # 确保 coeff 是 Fraction 类型
                    if not isinstance(coeff, Fraction):
                        try:
                            coeff = Fraction(coeff, 1) if not isinstance(coeff, Fraction) else coeff
                        except Exception as e:
                            if debug_callback:
                                debug_callback(f"无法处理系数 {coeff}: {e}")
                            return self

                    # 获取分子和分母的绝对值
                    try:
                        num = abs(coeff.numerator)
                        den = coeff.denominator
                    except Exception as e:
                        if debug_callback:
                            debug_callback(f"获取分子分母失败: {e}")
                        return self

                    if debug_callback:
                        debug_callback(f"处理项: {term}, 系数: {coeff}, 分子: {num}, 分母: {den}")

                    # 计算系数的平方因子
                    num_sqrt = self._max_square_factor(num)
                    den_sqrt = self._max_square_factor(den)

                    if debug_callback:
                        debug_callback(f"分子最大平方因子: {num_sqrt}, 分母最大平方因子: {den_sqrt}")

                    # 提取出来的系数平方根
                    extracted_num = num_sqrt
                    extracted_den = den_sqrt

                    # 剩余部分
                    remaining_num = num // (num_sqrt * num_sqrt) if num_sqrt != 0 else num
                    remaining_den = den // (den_sqrt * den_sqrt) if den_sqrt != 0 else den

                    # 构建系数
                    sign = 1 if coeff.numerator >= 0 else -1
                    extracted_coeff = Fraction(sign * extracted_num, extracted_den)
                    remaining_coeff = Fraction(remaining_num, remaining_den)

                    # 提取变量的平方因子
                    var_factors = {}
                    var_remainders = {}

                    for var, exp in term.vars.items():
                        factor_exp = exp // 2
                        remainder_exp = exp % 2
                        if factor_exp > 0:
                            var_factors[var] = factor_exp
                        if remainder_exp > 0:
                            var_remainders[var] = remainder_exp

                    # 构建表达式
                    extracted_term = AlgebraicTerm(extracted_coeff, var_factors)
                    remaining_term = AlgebraicTerm(remaining_coeff, var_remainders)

                    if debug_callback:
                        debug_callback(f"提取因子: {extracted_term}, 剩余: {remaining_term}")

                    # 检查是否需要保留根号
                    if (remaining_term.coeff == Fraction(1, 1) and not remaining_term.vars) or \
                            (remaining_term.coeff == Fraction(0, 1)):
                        # 完全平方，直接返回提取的因子
                        return AlgebraicExpression([extracted_term])
                    else:
                        # 有剩余部分，返回 提取因子 * √(剩余部分)
                        remaining_expr = AlgebraicExpression([remaining_term])
                        sqrt_remaining = SqrtExpression(remaining_expr)

                        # 如果提取的因子是1，只返回根号
                        if extracted_term.coeff == Fraction(1, 1) and not extracted_term.vars:
                            return AlgebraicExpression([sqrt_remaining])
                        else:
                            # 返回乘法表达式
                            return AlgebraicExpression([extracted_term, sqrt_remaining])
                else:
                    # 如果不是代数项，可能是其他类型的表达式
                    if debug_callback:
                        debug_callback(f"根号内不是代数项，无法提取平方因子: {type(term)}")
                    return self
            else:
                # 多个项，无法提取平方因子
                if debug_callback:
                    debug_callback(f"根号内有多个项，无法提取平方因子: {len(expr.terms)}个项")
                    for i, term in enumerate(expr.terms):
                        debug_callback(f"  项 {i}: {term}, 类型: {type(term)}")
                return self
        else:
            # 不是代数表达式，无法提取平方因子
            if debug_callback:
                debug_callback(f"根号内不是代数表达式: {type(expr)}")
            return self

    def _max_square_factor(self, n):
        """找到最大的平方因子"""
        # 确保 n 是整数
        if isinstance(n, Fraction):
            # 对于分数，我们只取分子（假设分母已被单独处理）
            n = n.numerator

        if not isinstance(n, int):
            # 如果不是整数，返回 1（无平方因子可提取）
            return 1

        if n <= 1:
            return 1

        max_factor = 1
        i = 2
        while i * i <= n:
            count = 0
            while n % (i * i) == 0:
                n //= (i * i)
                count += 1
            if count > 0:
                max_factor *= (i ** count)
            i += 1

        return max_factor

    def rationalize_denominator(self, denominator, debug_callback=None):
        """分母有理化"""
        if debug_callback:
            debug_callback(f"分母有理化: 1/√({self.inner_expr})")

        # 分子分母同乘以根号
        numerator = AlgebraicExpression([AlgebraicTerm(Fraction(1, 1))])
        new_numerator = numerator * self
        new_denominator = self.inner_expr

        return FractionExpression(new_numerator, new_denominator)

    def __str__(self):
        inner_str = str(self.inner_expr)
        # 如果内部表达式包含运算符，需要加括号
        if any(op in inner_str for op in '+-'):
            return f"√({inner_str})"
        else:
            return f"√{inner_str}"

    def __mul__(self, other):
        if isinstance(other, SqrtExpression):
            # √a * √b = √(a*b)
            return SqrtExpression(self.inner_expr * other.inner_expr)
        elif isinstance(other, (int, Fraction)):
            # 常数乘以根号：k * √a = √(k² * a) 或者保持为 k√a
            # 为了简化，我们返回一个包含常数的代数表达式
            if other == 1:
                return self
            return AlgebraicExpression([AlgebraicTerm(Fraction(other, 1)), self])
        elif isinstance(other, AlgebraicTerm):
            # 代数项乘以根号
            if other.coeff == Fraction(1, 1) and not other.vars:
                return self
            return AlgebraicExpression([other, self])
        elif isinstance(other, AlgebraicExpression):
            # 表达式乘以根号
            new_terms = []
            for term in other.terms:
                if isinstance(term, (AlgebraicTerm, int, Fraction)):
                    new_terms.append(term * self)
                elif isinstance(term, AbsoluteValue):
                    new_terms.append(term * self)
                elif isinstance(term, SqrtExpression):
                    new_terms.append(term * self)
            return AlgebraicExpression(new_terms)
        return NotImplemented

    def __rmul__(self, other):
        """支持右侧乘法，如 2 * √x"""
        return self.__mul__(other)

    def __truediv__(self, other):
        if isinstance(other, (int, Fraction)):
            return SqrtExpression(self.inner_expr / other)
        elif isinstance(other, SqrtExpression):
            # √a / √b = √(a/b)
            return SqrtExpression(self.inner_expr / other.inner_expr)
        else:
            return NotImplemented

    def __pow__(self, exp):
        if exp == 2:
            return self.inner_expr
        else:
            return AlgebraicExpression([self]) ** exp

    def contains_var(self, var):
        """检查是否包含指定变量"""
        if hasattr(self.inner_expr, 'contains_var'):
            return self.inner_expr.contains_var(var)
        elif isinstance(self.inner_expr, AlgebraicExpression):
            for term in self.inner_expr.terms:
                if hasattr(term, 'contains_var') and term.contains_var(var):
                    return True
        return False


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
        """化简表达式"""
        if debug_callback:
            debug_callback(f"开始化简表达式: {self}")

        if not self.terms:
            return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])

        # 显示原始项
        if debug_callback:
            term_strs = []
            for term in self.terms:
                term_strs.append(str(term))
            debug_callback(f"原始项: {' + '.join(term_strs) if term_strs else '空'}")

        # 检查是否有分式项
        fraction_terms = [term for term in self.terms if isinstance(term, FractionExpression)]

        # 如果有分式项，处理它们
        if len(fraction_terms) > 0:
            if debug_callback:
                debug_callback(f"发现分式项: {len(fraction_terms)}个")

            # 如果只有一个分式项且没有其他项，直接返回该分式
            if len(fraction_terms) == 1 and len(self.terms) == 1:
                return fraction_terms[0]

            # 如果有多个分式项或混合项，使用简化的方法处理
            if debug_callback:
                debug_callback(f"发现{len(fraction_terms)}个分式项和{len(self.terms) - len(fraction_terms)}个非分式项")

            # 方法1: 将所有项转换为分式然后相加
            # 创建一个基础分式，然后逐个添加其他项
            all_fractions = []

            for term in self.terms:
                if isinstance(term, FractionExpression):
                    all_fractions.append(term)
                elif isinstance(term, AlgebraicTerm):
                    # 将代数项转换为分式
                    term_fraction = FractionExpression(
                        AlgebraicExpression([term]),
                        AlgebraicExpression([AlgebraicTerm(Fraction(1, 1))])
                    )
                    all_fractions.append(term_fraction)
                elif isinstance(term, (AbsoluteValue, SqrtExpression)):
                    # 将其他类型的项转换为分式
                    term_fraction = FractionExpression(
                        AlgebraicExpression([term]),
                        AlgebraicExpression([AlgebraicTerm(Fraction(1, 1))])
                    )
                    all_fractions.append(term_fraction)

            if debug_callback:
                debug_callback(f"将所有项转换为分式，共{len(all_fractions)}个")

            # 从第一个分式开始合并
            if not all_fractions:
                return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])

            combined_fraction = all_fractions[0]
            for i in range(1, len(all_fractions)):
                if debug_callback:
                    debug_callback(f"合并分式 {i + 1}/{len(all_fractions)}: {combined_fraction} + {all_fractions[i]}")

                # 简化的合并方法，避免递归
                combined_fraction = self._safe_fraction_add(combined_fraction, all_fractions[i], debug_callback)

                if debug_callback:
                    debug_callback(f"合并后结果: {combined_fraction}")

            # 返回合并后的分式，不进行深层化简
            return combined_fraction

        # 如果没有分式项，继续原来的处理流程
        # 分离不同类型的项
        regular_terms = []
        abs_terms = []
        sqrt_terms = []

        for term in self.terms:
            if isinstance(term, AbsoluteValue):
                # 简化绝对值表达式
                simplified_abs = term.simplify(debug_callback)
                if isinstance(simplified_abs, AlgebraicExpression):
                    # 如果绝对值简化为常数表达式，递归处理
                    for t in simplified_abs.terms:
                        if isinstance(t, AlgebraicTerm) and t.coeff.numerator == 0:
                            continue
                        regular_terms.append(t)
                else:
                    abs_terms.append(simplified_abs)
            elif isinstance(term, SqrtExpression):
                # 简化根号表达式
                simplified_sqrt = term.simplify(debug_callback)
                if isinstance(simplified_sqrt, AlgebraicExpression):
                    # 如果根号简化为常数表达式，递归处理
                    for t in simplified_sqrt.terms:
                        if isinstance(t, AlgebraicTerm) and t.coeff.numerator == 0:
                            continue
                        regular_terms.append(t)
                else:
                    sqrt_terms.append(simplified_sqrt)
            else:
                # 普通代数项
                if isinstance(term, AlgebraicTerm) and term.coeff.numerator == 0:
                    continue
                regular_terms.append(term)

        # 合并普通项中的同类项
        term_dict = {}
        for term in regular_terms:
            if isinstance(term, AlgebraicTerm):
                # 创建变量的元组作为键
                var_key = tuple(sorted(term.vars.items()))
                if var_key in term_dict:
                    if debug_callback:
                        debug_callback(f"合并同类项: {term_dict[var_key]} + {term}")
                    term_dict[var_key] = term_dict[var_key] + term
                    if debug_callback:
                        debug_callback(f"合并结果: {term_dict[var_key]}")
                else:
                    term_dict[var_key] = term
            else:
                # 如果不是代数项，直接添加到特殊项列表
                if isinstance(term, SqrtExpression):
                    sqrt_terms.append(term)
                elif isinstance(term, AbsoluteValue):
                    abs_terms.append(term)
                else:
                    regular_terms.append(term)

        # 移除系数为0的项
        simplified_regular_terms = []
        for term in term_dict.values():
            if isinstance(term, AlgebraicTerm) and term.coeff.numerator != 0:
                simplified_regular_terms.append(term)
            elif debug_callback:
                debug_callback(f"移除系数为0的项: {term}")

        # 组合所有项
        all_terms = simplified_regular_terms + abs_terms + sqrt_terms

        # 如果没有项，返回0
        if not all_terms:
            if debug_callback:
                debug_callback("所有项系数为0，返回0")
            return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])

        # 如果只有一个项，直接返回该项
        if len(all_terms) == 1:
            return AlgebraicExpression(all_terms)

        # 显示化简后的项
        if debug_callback:
            term_strs = []
            for term in all_terms:
                term_strs.append(str(term))
            debug_callback(f"化简后的项: {' + '.join(term_strs) if term_strs else '空'}")

        return AlgebraicExpression(all_terms)

    def _safe_fraction_add(self, frac1, frac2, debug_callback=None):
        """安全的分数加法，避免递归"""
        if debug_callback:
            debug_callback(f"安全分数加法: {frac1} + {frac2}")

        # 直接使用通分公式，避免调用 FractionExpression.__add__ 的复杂逻辑
        # a/b + c/d = (ad + bc)/(bd)
        a = frac1.numerator
        b = frac1.denominator
        c = frac2.numerator
        d = frac2.denominator

        # 计算新分子和新分母
        ad = a * d
        bc = c * b
        bd = b * d

        new_numerator = ad + bc
        new_denominator = bd

        # 创建新的分式
        result = FractionExpression(new_numerator, new_denominator)

        # 只进行基本化简，避免递归
        return self._basic_fraction_simplify(result, debug_callback)

    def _basic_fraction_simplify(self, fraction, debug_callback=None):
        """基本的分式化简，避免递归"""
        if debug_callback:
            debug_callback(f"基本分式化简: {fraction}")

        numerator = fraction.numerator
        denominator = fraction.denominator

        # 检查分子是否为0
        if (isinstance(numerator, AlgebraicExpression) and
                numerator.is_constant() and
                numerator.terms[0].coeff.numerator == 0):
            return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])

        # 检查分母是否为1
        if isinstance(denominator, AlgebraicExpression) and denominator.is_constant():
            const = denominator.terms[0].coeff
            if const == Fraction(1, 1):
                return numerator

        # 检查分子分母是否相同（简单字符串比较）
        num_str = str(numerator).replace(' ', '')
        den_str = str(denominator).replace(' ', '')

        if num_str == den_str:
            return AlgebraicExpression([AlgebraicTerm(Fraction(1, 1))])

        # 检查分子和分母是否互为相反数（简单形式）
        if num_str.startswith('-') and num_str[1:] == den_str:
            return AlgebraicExpression([AlgebraicTerm(Fraction(-1, 1))])

        if den_str.startswith('-') and den_str[1:] == num_str:
            return AlgebraicExpression([AlgebraicTerm(Fraction(-1, 1))])

        # 检查分母是否为-1
        if isinstance(denominator, AlgebraicExpression) and denominator.is_constant():
            const = denominator.terms[0].coeff
            if const == Fraction(-1, 1):
                return numerator * Fraction(-1, 1)

        # 如果无法进一步化简，返回原分式
        return fraction

    def simple_equals(self, other):
        """简单的等价性检查，避免递归"""
        if not isinstance(other, AlgebraicExpression):
            return False

        # 如果都是常数，直接比较
        if self.is_constant() and other.is_constant():
            return self.terms[0].coeff == other.terms[0].coeff

        # 简单的字符串比较
        return str(self).replace(' ', '') == str(other).replace(' ', '')

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
            # 如果当前表达式是分数表达式，则调用分数的加法
            if isinstance(self, FractionExpression):
                return self + other
            # 否则，将当前表达式转换为分式，然后相加
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
        elif not isinstance(other, AlgebraicExpression):
            return NotImplemented

        # 将other的所有项取负
        neg_terms = []
        for term in other.terms:
            if isinstance(term, AbsoluteValue):
                # 绝对值取负：-|a| = -|a|
                neg_terms.append(AbsoluteValue(AlgebraicExpression([AlgebraicTerm(Fraction(-1, 1))]) * term.inner_expr))
            elif term.coeff.numerator == 0:
                continue
            else:
                neg_terms.append(term * Fraction(-1, 1))

        new_terms = self.terms + neg_terms
        return AlgebraicExpression(new_terms)

    def __mul__(self, other):
        if isinstance(other, (int, Fraction)):
            new_terms = []
            for term in self.terms:
                if isinstance(term, AbsoluteValue):
                    new_terms.append(term * other)
                elif isinstance(term, SqrtExpression):
                    new_terms.append(term * other)
                else:
                    new_terms.append(term * other)
            return AlgebraicExpression(new_terms)
        elif isinstance(other, AlgebraicTerm):
            new_terms = []
            for term in self.terms:
                if isinstance(term, AbsoluteValue):
                    new_terms.append(term * other)
                elif isinstance(term, SqrtExpression):
                    new_terms.append(term * other)
                else:
                    new_terms.append(term * other)
            return AlgebraicExpression(new_terms)
        elif isinstance(other, AlgebraicExpression):
            # 括号乘法：将self的每一项乘入other的每一项
            new_terms = []
            for t1 in self.terms:
                for t2 in other.terms:
                    if isinstance(t1, AbsoluteValue):
                        if isinstance(t2, AbsoluteValue):
                            new_terms.append(t1 * t2)
                        else:
                            new_terms.append(t1 * t2)
                    elif isinstance(t1, SqrtExpression):
                        new_terms.append(t1 * t2)
                    else:
                        if isinstance(t2, AbsoluteValue):
                            new_terms.append(t2 * t1)
                        elif isinstance(t2, SqrtExpression):
                            new_terms.append(t2 * t1)
                        else:
                            new_terms.append(t1 * t2)
            return AlgebraicExpression(new_terms)
        elif isinstance(other, AbsoluteValue):
            # 表达式乘以绝对值
            return other * self
        elif isinstance(other, SqrtExpression):
            # 表达式乘以根号
            new_terms = []
            for term in self.terms:
                new_terms.append(term * other)
            return AlgebraicExpression(new_terms)
        return NotImplemented

    def __rmul__(self, other):
        """支持右侧乘法，如 2 * x"""
        if isinstance(other, (int, Fraction)):
            return self * other
        return NotImplemented

    def __truediv__(self, other):
        if isinstance(other, (int, Fraction)):
            new_terms = []
            for term in self.terms:
                if isinstance(term, AbsoluteValue):
                    # 绝对值除以常数：|a|/c = |a/c|
                    new_terms.append(AbsoluteValue(term.inner_expr / other))
                else:
                    new_terms.append(term / other)
            return AlgebraicExpression(new_terms)
        elif isinstance(other, AlgebraicTerm):
            new_terms = []
            for term in self.terms:
                if isinstance(term, AbsoluteValue):
                    # 绝对值除以代数项：|a|/b，不能简化
                    return FractionExpression(self, AlgebraicExpression([other]))
                else:
                    new_terms.append(term / other)
            return AlgebraicExpression(new_terms)
        elif isinstance(other, AlgebraicExpression):
            # 对于表达式除以表达式，只有当分母是常数时才处理
            if len(other.terms) == 1 and isinstance(other.terms[0], AlgebraicTerm) and other.terms[0].is_constant():
                const = other.terms[0].coeff
                return self / const
            else:
                # 其他情况返回分式形式
                return FractionExpression(self, other)
        elif isinstance(other, AbsoluteValue):
            # 表达式除以绝对值：a/|b|，不能简化
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
            # 平方运算，展开
            return self * self

        # 对于其他整数指数，使用连乘
        result = self
        for _ in range(abs(exp) - 1):
            result = result * self

        if exp < 0:
            # 负指数，返回分式
            return FractionExpression(
                AlgebraicExpression([AlgebraicTerm(Fraction(1, 1))]),
                result
            )

        return result

    def __str__(self):
        if not self.terms:
            return "0"

        # 对项进行排序，确保一致的输出
        def term_sort_key(term):
            if isinstance(term, AlgebraicTerm):
                # 对于代数项，按变量字符串排序
                var_str = ''.join(sorted([f"{var}^{exp}" for var, exp in term.vars.items()]))
                return (0, var_str)  # 0表示代数项
            elif isinstance(term, AbsoluteValue):
                return (1, str(term))  # 1表示绝对值
            elif isinstance(term, SqrtExpression):
                return (2, str(term))  # 2表示根号
            elif isinstance(term, FractionExpression):
                return (3, str(term))  # 3表示分式
            else:
                return (4, str(term))  # 其他

        sorted_terms = sorted(self.terms, key=term_sort_key)

        # 构建字符串
        terms_str = []
        for i, term in enumerate(sorted_terms):
            term_str = str(term)

            if term_str == "0":
                continue

            if i == 0:
                terms_str.append(term_str)
            else:
                # 检查系数是否为负
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
        # 清理多余空格
        result = result.replace(" ", "")
        return result

    def is_constant(self):
        """是否为常数表达式"""
        return len(self.terms) == 1 and isinstance(self.terms[0], AlgebraicTerm) and self.terms[0].is_constant()

    def contains_absolute_value(self):
        """是否包含绝对值表达式"""
        for term in self.terms:
            if isinstance(term, AbsoluteValue):
                return True
        return False

    def solve_for_variable(self, var, debug_callback=None):
        """解方程，假设表达式等于0，求解变量var"""
        if debug_callback:
            debug_callback(f"开始求解变量 {var}: {self} = 0")

        # 检查是否包含绝对值
        if self.contains_absolute_value():
            if debug_callback:
                debug_callback("表达式中包含绝对值，需要分类讨论")

            # 对于包含绝对值的方程，返回分类讨论的结果
            result = "方程包含绝对值，需要分类讨论:\n\n"

            # 收集所有绝对值项
            abs_terms = [term for term in self.terms if isinstance(term, AbsoluteValue)]

            for i, abs_term in enumerate(abs_terms):
                result += f"情况 {i + 1}: {abs_term.expand_with_cases(debug_callback)}\n\n"

            result += "将上述情况分别代入原方程求解。"
            return result

        # 原代码继续...
        # 将表达式重新排列为 a*var + b = 0 的形式
        # 其中a是包含var的项的系数，b是不包含var的常数项

        a_terms = []  # 包含var的项的系数（不含var）
        b_terms = []  # 不包含var的项

        for term in self.terms:
            if isinstance(term, AlgebraicTerm):
                if term.contains_var(var):
                    coeff = term.get_coefficient_for_var(var)
                    if coeff is not None:
                        if isinstance(coeff, AlgebraicTerm):
                            a_terms.append(coeff)
                        else:
                            a_terms.append(AlgebraicTerm(coeff))
                        if debug_callback:
                            debug_callback(f"项 {term} 包含变量 {var}，系数为 {coeff}")
                    else:
                        # 变量有指数或与其他变量混合，无法直接求解
                        raise ValueError(f"无法求解包含 {var} 的高次项或混合项")
                else:
                    b_terms.append(term)
                    if debug_callback:
                        debug_callback(f"项 {term} 不包含变量 {var}")

        if not a_terms:
            # 表达式不包含该变量
            if debug_callback:
                debug_callback("表达式中不包含变量 " + var)
            if self.is_zero():
                return "恒等式（对任何值都成立）"
            else:
                return "无解"

        # 构建a和b表达式
        a_expr = AlgebraicExpression(a_terms).simplify(debug_callback)
        b_expr = AlgebraicExpression(b_terms).simplify(debug_callback)

        if debug_callback:
            debug_callback(f"系数 a (包含 {var} 的系数): {a_expr}")
            debug_callback(f"常数项 b (不包含 {var} 的项): {b_expr}")
            debug_callback(f"方程形式: {a_expr}*{var} + {b_expr} = 0")

        # 方程形式：a*var + b = 0
        # 解：var = -b / a

        # 处理特殊情况
        if a_expr.is_constant() and a_expr.terms[0].coeff == 0:
            if debug_callback:
                debug_callback("系数 a 为 0")
            if b_expr.is_constant() and b_expr.terms[0].coeff == 0:
                if debug_callback:
                    debug_callback("常数项 b 也为 0，无穷多解")
                return "无穷多解"
            else:
                if debug_callback:
                    debug_callback("常数项 b 不为 0，无解")
                return "无解"

        # 计算 -b
        neg_b = b_expr * Fraction(-1, 1)
        if debug_callback:
            debug_callback(f"-b = {neg_b}")

        # 计算 -b / a
        # 如果a和b都是常数，直接计算分数值
        if a_expr.is_constant() and neg_b.is_constant():
            a_coeff = a_expr.terms[0].coeff
            b_coeff = neg_b.terms[0].coeff
            result_fraction = b_coeff / a_coeff

            if debug_callback:
                debug_callback(f"a = {a_coeff}, -b = {b_coeff}")
                debug_callback(f"解: {var} = {b_coeff} / {a_coeff} = {result_fraction}")

            # 简化分数
            if result_fraction.denominator == 1:
                return str(result_fraction.numerator)
            else:
                return str(result_fraction)
        else:
            # 包含其他变量，返回表达式形式
            if debug_callback:
                debug_callback(f"计算: {var} = {neg_b} / {a_expr}")
            solution = neg_b / a_expr
            # 如果结果是代数表达式，进一步化简
            if isinstance(solution, AlgebraicExpression):
                simplified = solution.simplify(debug_callback)
                result_str = str(simplified)
                # 清理结果字符串
                result_str = result_str.replace('+-', '-').replace('--', '+')
                result_str = result_str.replace('+0', '').replace('-0', '')
                result_str = result_str.replace('1*', '').replace('*1', '')
                if debug_callback:
                    debug_callback(f"最终解: {var} = {result_str}")
                return result_str
            else:
                if debug_callback:
                    debug_callback(f"最终解: {var} = {solution}")
                return str(solution)

    def is_zero(self):
        """检查表达式是否为0"""
        if not self.terms:
            return True

        for term in self.terms:
            if isinstance(term, AlgebraicTerm):
                if term.coeff.numerator != 0:
                    return False
            elif isinstance(term, AbsoluteValue):
                # 绝对值表达式通常不为0，除非内部为0
                # 这里简化处理，认为绝对值表达式不为0
                return False
        return True

    def rationalize_denominator(self, debug_callback=None):
        """分母有理化"""
        if debug_callback:
            debug_callback(f"分母有理化: {self}")

        # 检查分母是否包含根号
        sqrt_terms = [term for term in self.terms if isinstance(term, SqrtExpression)]

        if not sqrt_terms:
            return self

        # 简单情况：分母只有根号
        if len(self.terms) == 1 and isinstance(self.terms[0], SqrtExpression):
            sqrt_term = self.terms[0]
            return sqrt_term.rationalize_denominator(self, debug_callback)

        # 复杂情况：分母有多个项，使用共轭
        # 这里简化处理，只显示提示信息
        if debug_callback:
            debug_callback("分母包含多个项，需要使用共轭有理化")

        return self


class FractionExpression:
    """表示分式表达式，支持分母有理化"""

    def __init__(self, numerator, denominator):
        self.numerator = numerator
        self.denominator = denominator
        self.rationalized = False
        # 添加terms属性，使其与AlgebraicExpression兼容
        # 这是一个包装器，将分式包装为单个"项"
        self.terms = [self]

    def rationalize(self, debug_callback=None):
        """分母有理化"""
        rationalizer = DenominatorRationalizer()
        rationalized = rationalizer.rationalize(self, debug_callback)
        rationalized.rationalized = True
        return rationalized

    def __add__(self, other):
        """分式加法：a/b + c/d = (ad + bc)/(bd)"""
        # 如果other是整数或分数，转换为分式
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

        # 如果是两个分式相加
        if isinstance(other, FractionExpression):
            # 简化的等价性检查：比较字符串表示
            self_den_str = str(self.denominator).replace(' ', '')
            other_den_str = str(other.denominator).replace(' ', '')

            if self_den_str == other_den_str:
                # 分母相同，直接合并分子
                new_numerator = self.numerator + other.numerator
                new_denominator = self.denominator

                return FractionExpression(new_numerator, new_denominator)

            # 否则使用通分公式
            a = self.numerator
            b = self.denominator
            c = other.numerator
            d = other.denominator

            new_numerator = (a * d) + (c * b)
            new_denominator = b * d

            return FractionExpression(new_numerator, new_denominator)

        return NotImplemented

    def __radd__(self, other):
        """右侧加法，如 1 + 1/(x+1)"""
        return self.__add__(other)

    def __str__(self):
        num_str = str(self.numerator)
        den_str = str(self.denominator)

        # 如果分子或分母包含运算符，需要加括号
        if any(op in num_str for op in '+-'):
            num_str = f"({num_str})"
        if any(op in den_str for op in '+-'):
            den_str = f"({den_str})"

        return f"{num_str}/{den_str}"

    def simplify(self, debug_callback=None):
        """化简分式"""
        if debug_callback:
            debug_callback(f"化简分式: {self}")

        # 化简分子和分母
        if hasattr(self.numerator, 'simplify'):
            simplified_num = self.numerator.simplify(debug_callback)
        else:
            simplified_num = self.numerator

        if hasattr(self.denominator, 'simplify'):
            simplified_den = self.denominator.simplify(debug_callback)
        else:
            simplified_den = self.denominator

        # 检查分子是否为0
        if (isinstance(simplified_num, AlgebraicExpression) and
                simplified_num.is_constant() and
                simplified_num.terms[0].coeff.numerator == 0):
            return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])

        # 检查分母是否为1
        if isinstance(simplified_den, AlgebraicExpression) and simplified_den.is_constant():
            const = simplified_den.terms[0].coeff
            if const == Fraction(1, 1):
                return simplified_num

        # 标准化分子和分母的字符串表示
        # 对代数表达式中的项进行排序，使 x+1 和 1+x 有相同的表示
        def normalize_expression(expr):
            if isinstance(expr, AlgebraicExpression):
                # 对项进行排序
                sorted_terms = sorted(expr.terms, key=lambda term: str(term))
                return AlgebraicExpression(sorted_terms)
            return expr

        # 尝试标准化分子和分母
        normalized_num = normalize_expression(simplified_num)
        normalized_den = normalize_expression(simplified_den)

        # 检查标准化后的分子分母是否相等
        if str(normalized_num) == str(normalized_den):
            return AlgebraicExpression([AlgebraicTerm(Fraction(1, 1))])

        # 检查分子和分母是否互为相反数
        if isinstance(normalized_num, AlgebraicExpression) and isinstance(normalized_den, AlgebraicExpression):
            # 如果分子是负的分母，结果为-1
            neg_den = normalized_den * Fraction(-1, 1)
            if str(normalized_num) == str(neg_den.simplify()):
                return AlgebraicExpression([AlgebraicTerm(Fraction(-1, 1))])

        # 返回化简后的分式
        return FractionExpression(simplified_num, simplified_den)


class AlgebraicCalculator:
    def __init__(self):
        pass

    def parse_expression(self, expr, debug_callback=None):
        """解析代数表达式"""
        if debug_callback:
            debug_callback(f"解析表达式: {expr}")

        expr = expr.replace(' ', '').replace('**', '^')

        # 预处理：将 (expr)^(1/2) 转换为 √(expr)
        import re

        # 匹配 (表达式)^(1/2) 或 (表达式)^1/2
        pattern = r'\(([^)]+)\)\^\(?1/2\)?'
        while True:
            match = re.search(pattern, expr)
            if not match:
                break

            full_match = match.group(0)
            inner_expr = match.group(1)

            if debug_callback:
                debug_callback(f"将 {full_match} 转换为 √({inner_expr})")

            # 替换为根号形式
            expr = expr.replace(full_match, f'√({inner_expr})', 1)

        # 处理不带括号的表达式的幂运算，如 8x^3^(1/2)
        # 匹配 expr^1/2 或 expr^(1/2) 格式
        no_paren_pattern = r'([a-zA-Z0-9*\^]+)\^\(?1/2\)?'
        expr = re.sub(no_paren_pattern, r'√(\1)', expr)

        # 插入隐式乘法符号
        expr = self._insert_implicit_multiplication(expr, debug_callback)

        if debug_callback:
            debug_callback(f"插入隐式乘法后: {expr}")

        # 将表达式转换为代数表达式对象
        return self._parse_expr(expr, debug_callback)

    def _insert_implicit_multiplication(self, expr, debug_callback=None):
        """插入隐式乘法符号，处理括号乘法如 (a+b)(c+d)"""
        if not expr:
            return expr

        result = []
        i = 0
        n = len(expr)

        while i < n:
            c = expr[i]
            result.append(c)

            # 检查是否需要插入乘法符号
            if i + 1 < n:
                next_c = expr[i + 1]

                # 跳过幂运算部分
                if c == '^':
                    # 幂运算符号后面不插入乘号
                    # 直接跳过指数部分
                    pass
                elif i > 0 and expr[i - 1] == '^':
                    # 指数部分不插入乘号
                    pass
                # 情况1: 数字后面跟着括号或变量
                elif c.isdigit() and (next_c == '(' or next_c.isalpha()):
                    # 但不要在处理除法时插入，如 1/(x+y)
                    # 检查前面是否有除号
                    if i > 0 and expr[i - 1] == '/':
                        # 不要插入乘号
                        pass
                    else:
                        result.append('*')
                        if debug_callback:
                            debug_callback(f"在 '{c}' 和 '{next_c}' 之间插入 '*'")

                # 情况2: 变量后面跟着括号，但要排除函数名
                elif c.isalpha() and next_c == '(':
                    # 检查当前字母是否是函数名的一部分
                    # 向前查找完整的函数名
                    func_start = i
                    while func_start > 0 and expr[func_start - 1].isalpha():
                        func_start -= 1

                    func_name = expr[func_start:i + 1]  # 包括当前字符

                    # 如果是函数名，不插入乘号
                    if func_name in ['abs', 'sqrt']:
                        if debug_callback:
                            debug_callback(f"函数名 '{func_name}' 后面跟着括号，不插入 '*'")
                    else:
                        result.append('*')
                        if debug_callback:
                            debug_callback(f"在 '{c}' 和 '{next_c}' 之间插入 '*'")

                # 情况3: 括号后面跟着括号、数字或变量
                elif c == ')' and (next_c == '(' or next_c.isdigit() or next_c.isalpha()):
                    # 需要检查下一个字符是否是^，如果是，则不插入乘号，因为可能是表达式的幂运算
                    if next_c == '(' or (i + 1 < n and expr[i + 1] != '^'):
                        result.append('*')
                        if debug_callback:
                            debug_callback(f"在 '{c}' 和 '{next_c}' 之间插入 '*'")

                # 情况4: 数字后面跟着分数形式的系数
                elif c.isdigit() and next_c == '/':
                    # 检查是否形如 "2/3x" 或 "2/3(x+y)"
                    j = i + 2
                    while j < n and (expr[j].isdigit() or expr[j] == '/'):
                        j += 1
                    if j < n and (expr[j] == '(' or expr[j].isalpha()):
                        # 在分数和后面的内容之间插入 *
                        # 但不要插入，因为这是分数形式的一部分
                        if debug_callback:
                            debug_callback(f"发现分数形式: {expr[i:j]} 后面跟着 {expr[j]}")

            i += 1

        return ''.join(result)

    def _parse_expr(self, expr, debug_callback=None):
        """解析表达式的主要函数"""
        if debug_callback:
            debug_callback(f"解析表达式: {expr}")

        # 处理绝对值函数
        expr = self._handle_absolute_value(expr, debug_callback)

        # 处理平方根函数
        expr = self._handle_sqrt_function(expr, debug_callback)

        # 处理括号
        expr = self._handle_parentheses(expr, debug_callback)

        if debug_callback:
            debug_callback(f"处理括号后: {expr}")

        # 检查表达式是否为空
        if not expr:
            return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])

        # 首先检查表达式是否包含加减法（顶层）
        # 我们需要确保只在顶层处理加减法，不在括号内处理
        # 查找不在括号内的加减号
        bracket_count = 0
        plus_minus_positions = []

        for i, char in enumerate(expr):
            if char == '(':
                bracket_count += 1
            elif char == ')':
                bracket_count -= 1
            elif bracket_count == 0 and char in '+-' and (i == 0 or expr[i - 1] not in '*/^'):
                # 不在括号内，且不是指数的一部分
                plus_minus_positions.append((i, char))

        if plus_minus_positions:
            # 表达式包含顶层加减法，调用 _parse_add_sub
            if debug_callback:
                debug_callback(f"表达式包含顶层加减法，调用 _parse_add_sub")
            return self._parse_add_sub(expr, debug_callback)
        else:
            # 表达式不包含顶层加减法，直接当作项处理
            if debug_callback:
                debug_callback(f"表达式不包含顶层加减法，直接当作项处理")
            return self._parse_term(expr, debug_callback)

    def _handle_absolute_value(self, expr, debug_callback=None):
        """处理绝对值函数"""
        if debug_callback:
            debug_callback(f"处理绝对值函数: {expr}")

        # 查找所有abs函数
        import re

        # 改进的正则表达式，可以处理嵌套括号
        # 但正则表达式处理嵌套括号比较困难，所以我们用循环
        result = expr
        while 'abs(' in result:
            # 找到第一个'abs('
            start = result.find('abs(')
            if start == -1:
                break

            # 找到匹配的右括号
            bracket_count = 0
            i = start + 3  # 'abs('的长度是4，start是'a'的位置

            while i < len(result):
                if result[i] == '(':
                    bracket_count += 1
                elif result[i] == ')':
                    bracket_count -= 1
                    if bracket_count == 0:
                        break
                i += 1

            if i >= len(result):
                # 没有找到匹配的右括号
                break

            # 提取内部表达式
            inner_start = start + 4  # 跳过'abs('
            inner_expr = result[inner_start:i]

            if debug_callback:
                debug_callback(f"找到绝对值函数: abs({inner_expr})")

            # 解析内部表达式
            inner_result = self._parse_expr(inner_expr, debug_callback)

            # 创建绝对值表达式字符串
            abs_expr = f"|{inner_expr}|"

            # 替换
            result = result[:start] + abs_expr + result[i + 1:]

            if debug_callback:
                debug_callback(f"替换后表达式: {result}")

        return result

    def _handle_parentheses(self, expr, debug_callback=None):
        """处理括号，递归解析内部表达式"""
        if debug_callback:
            debug_callback(f"处理括号: {expr}")

        # 检查括号是否匹配
        bracket_count = 0
        for char in expr:
            if char == '(':
                bracket_count += 1
            elif char == ')':
                bracket_count -= 1
                if bracket_count < 0:
                    raise ValueError("括号不匹配: 多余的右括号")

        if bracket_count > 0:
            raise ValueError("括号不匹配: 未闭合的左括号")

        # 如果没有括号，直接返回
        if '(' not in expr:
            return expr

        # 使用栈来匹配括号
        result = []
        i = 0

        while i < len(expr):
            if expr[i] == '(':
                # 找到匹配的右括号
                count = 1
                j = i + 1
                while j < len(expr) and count > 0:
                    if expr[j] == '(':
                        count += 1
                    elif expr[j] == ')':
                        count -= 1
                    j += 1

                if count > 0:
                    raise ValueError(f"括号不匹配: 位置 {i} 处的左括号未闭合")

                # 提取括号内的表达式（不包括两端的括号）
                inner_expr = expr[i + 1:j - 1]
                if debug_callback:
                    debug_callback(f"处理括号对: 位置 {i}-{j - 1}, 内部表达式: {inner_expr}")

                # 检查是否是幂运算的一部分
                if i > 0 and expr[i - 1] == '^':
                    # 这是指数部分，保持原样，不要单独解析
                    result.append(f"({inner_expr})")
                else:
                    # 递归处理括号内的表达式
                    inner_processed = self._handle_parentheses(inner_expr, debug_callback)

                    # 解析括号内的表达式
                    inner_result = self._parse_expr(inner_processed, debug_callback)

                    # 获取结果的字符串表示
                    inner_str = str(inner_result)

                    # 如果内部表达式是简单项，不需要括号
                    if any(op in inner_str for op in '+-'):
                        result.append(f"({inner_str})")
                    else:
                        result.append(inner_str)

                i = j
            else:
                result.append(expr[i])
                i += 1

        final_expr = ''.join(result)
        if debug_callback:
            debug_callback(f"括号处理后最终表达式: {final_expr}")

        return final_expr

    def _parse_add_sub(self, expr, debug_callback=None):
        """解析加减法表达式"""
        if debug_callback:
            debug_callback(f"解析加减法表达式: {expr}")

        if not expr:
            return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])

        # 按+或-拆分，但要考虑负号和表达式中的符号，同时要忽略括号内的加减号
        terms = []
        current = ''
        sign = 1

        i = 0
        bracket_count = 0  # 跟踪括号深度
        abs_count = 0  # 跟踪绝对值符号深度

        while i < len(expr):
            char = expr[i]

            # 更新括号计数
            if char == '(':
                bracket_count += 1
                current += char
            elif char == ')':
                bracket_count -= 1
                current += char
            elif char == '|':
                # 绝对值符号
                abs_count = 1 - abs_count  # 切换0/1
                current += char
            elif bracket_count == 0 and abs_count == 0:  # 只在顶层括号且不在绝对值内处理加减号
                if char == '+' and (i == 0 or expr[i - 1] not in '*/^'):
                    if current:
                        term_expr = self._parse_term(current, debug_callback)
                        if sign == -1:
                            term_expr = term_expr * Fraction(-1, 1)
                        terms.extend(term_expr.terms)
                        if debug_callback:
                            debug_callback(f"解析项: {current}, 符号: {sign}, 结果: {term_expr}")
                    current = ''
                    sign = 1
                elif char == '-' and (i == 0 or expr[i - 1] not in '*/^'):
                    if current:
                        term_expr = self._parse_term(current, debug_callback)
                        if sign == -1:
                            term_expr = term_expr * Fraction(-1, 1)
                        terms.extend(term_expr.terms)
                        if debug_callback:
                            debug_callback(f"解析项: {current}, 符号: {sign}, 结果: {term_expr}")
                    current = ''
                    sign = -1
                else:
                    current += char
            else:
                # 在括号内或绝对值内，直接添加到当前项
                current += char

            i += 1

        if current:
            term_expr = self._parse_term(current, debug_callback)
            if sign == -1:
                term_expr = term_expr * Fraction(-1, 1)
            terms.extend(term_expr.terms)
            if debug_callback:
                debug_callback(f"解析最后一项: {current}, 符号: {sign}, 结果: {term_expr}")

        # 创建表达式并化简
        expr_obj = AlgebraicExpression(terms)
        return expr_obj.simplify(debug_callback)

    def _parse_term(self, term_str, debug_callback=None):
        """解析单项式，可能包含乘除法"""
        if debug_callback:
            debug_callback(f"解析单项式: {term_str}")

        # 处理绝对值表达式
        if term_str.startswith('|') and term_str.endswith('|'):
            # 去掉绝对值符号
            inner = term_str[1:-1]
            if debug_callback:
                debug_callback(f"解析绝对值表达式: |{inner}|")

            # 解析内部表达式
            inner_expr = self._parse_expr(inner, debug_callback)

            # 创建绝对值对象
            return AlgebraicExpression([AbsoluteValue(inner_expr)])

        # 处理除法优先
        # 但要注意检查除法符号不在括号内
        bracket_count = 0
        abs_count = 0
        division_positions = []

        for i, char in enumerate(term_str):
            if char == '(':
                bracket_count += 1
            elif char == ')':
                bracket_count -= 1
            elif char == '|':
                abs_count = 1 - abs_count
            elif char == '/' and bracket_count == 0 and abs_count == 0:
                division_positions.append(i)

        if division_positions:
            if debug_callback:
                debug_callback(f"处理除法，位置: {division_positions}")

            # 从第一个除号处拆分
            first_div = division_positions[0]
            numerator_str = term_str[:first_div]
            denominator_str = term_str[first_div + 1:]

            if debug_callback:
                debug_callback(f"分子: {numerator_str}, 分母: {denominator_str}")

            # 解析分子和分母
            numerator = self._parse_factor(numerator_str, debug_callback)
            denominator = self._parse_factor(denominator_str, debug_callback)

            # 检查分母是否为常数表达式
            if isinstance(denominator, AlgebraicExpression) and denominator.is_constant():
                # 分母是常数，直接除法
                const = denominator.terms[0].coeff
                return numerator / const
            else:
                # 分母包含变量或绝对值，返回分式表达式
                return FractionExpression(numerator, denominator)

        # 如果没有除法，处理乘法
        # 按乘号拆分，但要考虑括号乘法
        parts = []
        current = ''
        bracket_count = 0
        abs_count = 0

        for char in term_str:
            if char == '(':
                bracket_count += 1
                current += char
            elif char == ')':
                bracket_count -= 1
                current += char
            elif char == '|':
                abs_count = 1 - abs_count
                current += char
            elif char == '*' and bracket_count == 0 and abs_count == 0:
                parts.append(current)
                current = ''
            else:
                current += char

        if current:
            parts.append(current)

        if debug_callback:
            debug_callback(f"乘法拆分结果: {parts}")

        if len(parts) == 1:
            # 没有乘法，直接解析
            return self._parse_factor(parts[0], debug_callback)

        # 处理乘法
        result = self._parse_factor(parts[0], debug_callback)
        for part in parts[1:]:
            factor = self._parse_factor(part, debug_callback)

            # 检查是否是括号乘法
            if (isinstance(result, AlgebraicExpression) and
                    isinstance(factor, AlgebraicExpression)):
                # 两个都是代数表达式，需要展开
                if debug_callback:
                    debug_callback(f"展开括号乘法: {result} * {factor}")

                result = result * factor
            else:
                result = result * factor

            if debug_callback:
                debug_callback(f"乘以 {factor}: {result}")

        return result

    def _parse_factor(self, factor_str, debug_callback=None):
        """解析因子：数字、变量、括号表达式、幂运算"""
        if debug_callback:
            debug_callback(f"解析因子: {factor_str}")

        factor_str = factor_str.strip()

        if not factor_str:
            return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])

        # 处理负数情况
        if factor_str.startswith('-') and len(factor_str) > 1:
            inner = factor_str[1:]
            inner_expr = self._parse_factor(inner, debug_callback)
            return inner_expr * Fraction(-1, 1)

        # 处理平方根符号
        if factor_str.startswith('√'):
            # 提取根号内的表达式
            if len(factor_str) > 1 and factor_str[1] == '(':
                # 带括号的根号：√(...)
                # 找到匹配的右括号
                bracket_count = 1
                i = 2
                while i < len(factor_str) and bracket_count > 0:
                    if factor_str[i] == '(':
                        bracket_count += 1
                    elif factor_str[i] == ')':
                        bracket_count -= 1
                    i += 1

                if bracket_count == 0:
                    inner = factor_str[2:i - 1]
                else:
                    inner = factor_str[2:]
            else:
                # 不带括号的根号，尝试提取直到遇到运算符或结束
                inner = ""
                for j in range(1, len(factor_str)):
                    char = factor_str[j]
                    if char in '+-*/^':
                        break
                    inner += char

            if debug_callback:
                debug_callback(f"解析根号表达式: √{inner}")

            inner_expr = self._parse_expr(inner, debug_callback)
            return AlgebraicExpression([SqrtExpression(inner_expr)])

        # 处理绝对值表达式
        if factor_str.startswith('|') and factor_str.endswith('|'):
            inner = factor_str[1:-1]
            if debug_callback:
                debug_callback(f"解析绝对值因子: |{inner}|")

            inner_expr = self._parse_expr(inner, debug_callback)
            return AlgebraicExpression([AbsoluteValue(inner_expr)])

        # 首先检查幂运算 - 需要找到不在括号内的 ^ 符号
        # 从右向左查找，以正确处理右结合性
        bracket_count = 0
        for i in range(len(factor_str) - 1, -1, -1):
            char = factor_str[i]
            if char == ')':
                bracket_count += 1
            elif char == '(':
                bracket_count -= 1
            elif char == '^' and bracket_count == 0:
                # 找到顶层幂运算
                base_str = factor_str[:i]
                exp_str = factor_str[i + 1:]

                if debug_callback:
                    debug_callback(f"处理幂运算: {base_str}^{exp_str}")

                # 解析底数
                base = self._parse_factor(base_str, debug_callback)

                # 检查指数是否为 1/2
                clean_exp_str = exp_str.strip()
                if clean_exp_str in ['1/2', '(1/2)']:
                    # 转换为根号
                    if debug_callback:
                        debug_callback(f"分数指数 1/2，转换为根号")
                    # 先化简底数
                    if hasattr(base, 'simplify'):
                        base = base.simplify(debug_callback)
                    return AlgebraicExpression([SqrtExpression(base)])
                else:
                    try:
                        # 尝试解析为整数或分数指数
                        # 处理括号
                        if clean_exp_str.startswith('(') and clean_exp_str.endswith(')'):
                            clean_exp_str = clean_exp_str[1:-1]

                        # 尝试解析为分数
                        if '/' in clean_exp_str:
                            # 分数指数
                            num_str, den_str = clean_exp_str.split('/')
                            num = int(num_str.strip())
                            den = int(den_str.strip())

                            if num == 1 and den == 2:
                                # 1/2 指数，转换为根号
                                return AlgebraicExpression([SqrtExpression(base)])
                            elif den == 1:
                                # 整数指数
                                return base ** num
                            else:
                                # 其他分数指数，目前不支持简化，返回代数表达式形式
                                if debug_callback:
                                    debug_callback(f"复杂分数指数 {num}/{den}，保持原样")
                                # 创建幂运算表达式
                                return AlgebraicExpression([
                                    AlgebraicTerm(Fraction(1, 1), {})
                                ])
                        else:
                            # 整数指数
                            exp = int(clean_exp_str)
                            return base ** exp
                    except ValueError as e:
                        if debug_callback:
                            debug_callback(f"无法解析指数 '{exp_str}': {str(e)}")
                        # 保持原样，返回幂运算形式
                        # 创建幂运算表达式
                        power_expr = f"{base_str}^{exp_str}"
                        return AlgebraicExpression([
                            AlgebraicTerm.from_string(power_expr) if power_expr else
                            AlgebraicTerm(Fraction(1, 1), {})
                        ])

        # 处理数字
        if re.match(r'^[-+]?\d*\.?\d*(?:/\d*\.?\d*)?$', factor_str) and factor_str not in ['', '-', '+']:
            if factor_str.replace('-', '').replace('+', '').replace('.', '').replace('/', '').isdigit():
                if debug_callback:
                    debug_callback(f"解析数字: {factor_str}")
                try:
                    coeff = Fraction.from_string(factor_str)
                    return AlgebraicExpression([AlgebraicTerm(coeff)])
                except Exception as e:
                    if debug_callback:
                        debug_callback(f"解析数字失败: {str(e)}")

        # 处理变量 - 包括带指数的变量
        # 匹配类似 x, x^3, xy, x^2y^3 等形式
        var_pattern = r'^[a-zA-Z](\^\d+)?$'
        if re.match(var_pattern, factor_str):
            if '^' in factor_str:
                var_name, exp_str = factor_str.split('^')
                exp = int(exp_str)
            else:
                var_name = factor_str
                exp = 1

            if debug_callback:
                debug_callback(f"解析变量: {var_name}^{exp}")

            vars_dict = {var_name: exp}
            return AlgebraicExpression([AlgebraicTerm(Fraction(1, 1), vars_dict)])

        # 处理带系数的变量 - 简化处理
        # 使用正则表达式匹配类似 "2x", "-3y^2", "1/2a^3" 等形式
        # 改进的正则表达式，匹配更广泛
        match = re.match(r'^([-+]?\d*\.?\d*/?\d*\.?\d*)([a-zA-Z](\^\d+)?)$', factor_str)
        if match:
            coeff_str = match.group(1)
            var_part = match.group(2)

            if not coeff_str or coeff_str in ['+', '-']:
                coeff_str += '1'

            try:
                coeff = Fraction.from_string(coeff_str)
                if debug_callback:
                    debug_callback(f"解析带系数变量: 系数={coeff_str} -> {coeff}, 变量部分={var_part}")

                # 解析变量部分
                if '^' in var_part:
                    var_name, exp_str = var_part.split('^')
                    exp = int(exp_str)
                else:
                    var_name = var_part
                    exp = 1

                vars_dict = {var_name: exp}
                return AlgebraicExpression([AlgebraicTerm(coeff, vars_dict)])
            except Exception as e:
                if debug_callback:
                    debug_callback(f"解析带系数变量失败: {str(e)}")

        # 可能是括号表达式
        if factor_str.startswith('(') and factor_str.endswith(')'):
            # 检查是否是最外层括号
            bracket_count = 0
            is_outermost = True
            for i, char in enumerate(factor_str):
                if char == '(':
                    bracket_count += 1
                elif char == ')':
                    bracket_count -= 1
                    if bracket_count == 0 and i < len(factor_str) - 1:
                        is_outermost = False
                        break

            if is_outermost:
                inner_expr = factor_str[1:-1]
                if debug_callback:
                    debug_callback(f"解析括号表达式: {inner_expr}")
                if inner_expr.strip():
                    return self._parse_expr(inner_expr, debug_callback)
                else:
                    return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])

        # 尝试解析为代数项
        try:
            # 尝试直接解析为代数项
            term = AlgebraicTerm.from_string(factor_str)
            if debug_callback:
                debug_callback(f"成功解析为代数项: {term}")
            return AlgebraicExpression([term])
        except Exception as e:
            if debug_callback:
                debug_callback(f"解析为代数项失败: {str(e)}")

        # 尝试作为复杂表达式解析
        if debug_callback:
            debug_callback(f"尝试作为完整表达式解析: {factor_str}")
        return self._parse_expr(factor_str, debug_callback)

    def simplify_expression(self, expr, debug_callback=None):
        """化简表达式的主要接口"""
        try:
            # 清空调试日志
            if debug_callback:
                debug_callback.clear()

            # 检查是否为等式
            if '=' in expr:
                return self._solve_equation(expr, debug_callback)

            if debug_callback:
                debug_callback(f"开始化简表达式: {expr}")

            expr_obj = self.parse_expression(expr, debug_callback)

            if debug_callback:
                debug_callback(f"解析结果类型: {type(expr_obj)}")

            # 简化表达式
            if hasattr(expr_obj, 'simplify'):
                simplified = expr_obj.simplify(debug_callback)
            else:
                simplified = expr_obj

            # 检查结果是否是分式且分母包含根号，进行有理化
            if isinstance(simplified, FractionExpression):
                # 检查分母是否包含根号
                if self._contains_sqrt(simplified.denominator):
                    if debug_callback:
                        debug_callback("检测到分母包含根号，进行有理化...")
                    # 使用DenominatorRationalizer进行有理化
                    rationalizer = DenominatorRationalizer()
                    simplified = rationalizer.rationalize(simplified, debug_callback)

                    # 有理化后再次化简
                    if hasattr(simplified, 'simplify'):
                        simplified = simplified.simplify(debug_callback)

            result = str(simplified)

            if debug_callback:
                debug_callback(f"化简后结果: {result}")

            # 最终清理
            result = result.replace('+-', '-').replace('--', '+')
            result = result.replace('+0', '').replace('-0', '')
            result = result.replace('1*', '').replace('*1', '')

            # 移除开头的+号
            if result.startswith('+'):
                result = result[1:]

            # 处理空结果
            if not result or result == '':
                result = '0'

            if debug_callback:
                debug_callback(f"最终结果: {result}")

            return result
        except Exception as e:
            if debug_callback:
                debug_callback(f"错误: {str(e)}")
            raise e

    def _simplify_fraction_string(self, fraction_str, debug_callback=None):
        """简化分式字符串，如 (x+2)/(x+1) 保持原样"""
        # 目前只做基本清理，未来可以添加更多化简逻辑
        if '/' not in fraction_str:
            return fraction_str

        # 分割分子和分母
        parts = fraction_str.split('/')
        if len(parts) != 2:
            return fraction_str

        numerator, denominator = parts

        # 如果分子分母相同，返回1
        if numerator == denominator:
            return "1"

        # 如果分母是1，返回分子
        if denominator == "1":
            return numerator

        # 其他情况保持原样
        return f"{numerator}/{denominator}"

    def _solve_equation(self, equation, debug_callback=None):
        """解方程"""
        if debug_callback:
            debug_callback(f"开始解方程: {equation}")

        # 分离等号两边
        parts = equation.split('=')
        if len(parts) != 2:
            raise ValueError("无效的方程格式，应包含一个等号")

        left_str, right_str = parts[0].strip(), parts[1].strip()

        if debug_callback:
            debug_callback(f"方程左边: {left_str}")
            debug_callback(f"方程右边: {right_str}")

        # 解析左右两边
        left_expr = self.parse_expression(left_str, debug_callback)
        right_expr = self.parse_expression(right_str, debug_callback)

        if debug_callback:
            debug_callback(f"左边表达式: {left_expr}")
            debug_callback(f"右边表达式: {right_expr}")

        # 移项：左边 - 右边 = 0
        equation_expr = left_expr - right_expr

        if debug_callback:
            debug_callback(f"移项后: {equation_expr} = 0")

        # 简化方程
        simplified_eq = equation_expr.simplify(debug_callback)

        if debug_callback:
            debug_callback(f"化简后方程: {simplified_eq} = 0")

        # 提取未知数（假设只有一个未知数，取第一个出现的字母）
        vars_in_expr = set()
        for term in simplified_eq.terms:
            if isinstance(term, AlgebraicTerm):
                for var in term.vars:
                    vars_in_expr.add(var)
            elif isinstance(term, AbsoluteValue):
                # 绝对值表达式中可能包含变量
                if term.contains_var:
                    # 这里简化处理，假设绝对值表达式包含至少一个变量
                    vars_in_expr.add('|')

        if not vars_in_expr:
            # 没有变量，检查是否为恒等式
            if simplified_eq.is_zero():
                if debug_callback:
                    debug_callback("方程不含变量且为0，是恒等式")
                return "恒等式（对任何值都成立）"
            else:
                if debug_callback:
                    debug_callback("方程不含变量且不为0，是矛盾方程")
                return "矛盾方程（无解）"

        if debug_callback:
            debug_callback(f"方程中的变量: {', '.join(sorted(vars_in_expr))}")

        # 如果有绝对值符号，返回分类讨论
        if '|' in vars_in_expr:
            # 方程中包含绝对值，需要分类讨论
            result = "方程中包含绝对值表达式，需要分类讨论:\n\n"

            # 找出所有绝对值项
            abs_terms = [term for term in simplified_eq.terms if isinstance(term, AbsoluteValue)]

            if abs_terms:
                for i, abs_term in enumerate(abs_terms):
                    result += f"情况 {i + 1}: {abs_term.expand_with_cases(debug_callback)}\n\n"

                result += "将上述情况分别代入原方程求解。"
            else:
                result = "方程化简后不包含绝对值项，请检查输入。"

            return result

        # 如果没有多个变量，让用户选择要求解的变量
        # 这里我们返回一个包含所有可能求解结果的字典
        results = {}
        for var in sorted(vars_in_expr):
            try:
                if debug_callback:
                    debug_callback(f"求解变量 {var}")
                solution = simplified_eq.solve_for_variable(var, debug_callback)
                results[var] = solution
            except Exception as e:
                results[var] = f"无法求解: {str(e)}"
                if debug_callback:
                    debug_callback(f"求解变量 {var} 时出错: {str(e)}")

        # 构建结果字符串
        if len(results) == 1:
            var, solution = list(results.items())[0]
            result_str = f"{var} = {solution}"
            if debug_callback:
                debug_callback(f"最终解: {result_str}")
            return result_str
        else:
            result_str = "多变量方程的解:\n"
            for var, solution in results.items():
                result_str += f"  {var} = {solution}\n"
            result_str = result_str.strip()
            if debug_callback:
                debug_callback(f"最终解: {result_str}")
            return result_str

    def _handle_sqrt_function(self, expr, debug_callback=None):
        """处理平方根函数"""
        if debug_callback:
            debug_callback(f"处理平方根函数: {expr}")

        import re

        result = expr
        while 'sqrt(' in result:
            start = result.find('sqrt(')
            if start == -1:
                break

            # 找到匹配的右括号
            bracket_count = 0
            i = start + 4  # 'sqrt(' 的长度是5，start是's'的位置

            while i < len(result):
                if result[i] == '(':
                    bracket_count += 1
                elif result[i] == ')':
                    if bracket_count == 0:
                        break
                    bracket_count -= 1
                i += 1

            if i >= len(result):
                break

            # 提取内部表达式
            inner_start = start + 5  # 跳过'sqrt('
            inner_expr = result[inner_start:i]

            if debug_callback:
                debug_callback(f"找到平方根函数: sqrt({inner_expr})")

            # 解析内部表达式
            inner_result = self._parse_expr(inner_expr, debug_callback)

            # 创建根号表达式
            sqrt_expr = f"√({inner_expr})"

            # 替换
            result = result[:start] + sqrt_expr + result[i + 1:]

            if debug_callback:
                debug_callback(f"替换后表达式: {result}")

        return result

    def _contains_sqrt(self, expr):
        """检查表达式中是否包含根号"""
        if isinstance(expr, SqrtExpression):
            return True
        elif isinstance(expr, AlgebraicExpression):
            for term in expr.terms:
                if isinstance(term, SqrtExpression):
                    return True
        return False


class DenominatorRationalizer:
    """分母有理化处理器"""

    @staticmethod
    def rationalize(fraction_expr, debug_callback=None):
        """对分式进行分母有理化"""
        numerator = fraction_expr.numerator
        denominator = fraction_expr.denominator

        if debug_callback:
            debug_callback(f"开始分母有理化: {numerator} / {denominator}")

        # 情况1：分母是SqrtExpression对象
        if isinstance(denominator, SqrtExpression):
            if debug_callback:
                debug_callback(f"检测到分母为SqrtExpression: √({denominator.inner_expr})")
            return DenominatorRationalizer._rationalize_single_sqrt(
                numerator, denominator, debug_callback
            )

        # 情况2：分母是代数表达式且包含根号项
        sqrt_terms = DenominatorRationalizer._extract_sqrt_terms(denominator)
        if sqrt_terms:
            if debug_callback:
                debug_callback(f"检测到分母包含根号项: {len(sqrt_terms)}个")
            return DenominatorRationalizer._rationalize_with_conjugate(
                numerator, denominator, sqrt_terms, debug_callback
            )

        # 情况3：分母是单个根号项（包裹在AlgebraicExpression中）
        if isinstance(denominator, AlgebraicExpression) and len(denominator.terms) == 1:
            term = denominator.terms[0]
            if isinstance(term, SqrtExpression):
                if debug_callback:
                    debug_callback(f"检测到分母为单个根号项: √({term.inner_expr})")
                return DenominatorRationalizer._rationalize_single_sqrt(
                    numerator, term, debug_callback
                )

        # 无需有理化
        if debug_callback:
            debug_callback("分母不包含根号，无需有理化")
        return fraction_expr

    @staticmethod
    def _rationalize_single_sqrt(numerator, sqrt_term, debug_callback):
        """单个根号在分母的有理化"""
        if debug_callback:
            debug_callback(f"单个根号有理化: 分子乘以√(...)")

        # 如果分子是常数1，特殊处理
        if isinstance(numerator, AlgebraicExpression):
            if numerator.is_constant() and numerator.terms[0].coeff == Fraction(1, 1):
                # 分子为1时，有理化结果为 √(inner) / inner
                new_numerator = sqrt_term
                new_denominator = sqrt_term.inner_expr

                if debug_callback:
                    debug_callback(f"分子为1，直接返回: {new_numerator} / {new_denominator}")

                return FractionExpression(new_numerator, new_denominator)

        # 通用情况：分子分母同乘以根号
        new_numerator = numerator * sqrt_term
        new_denominator = sqrt_term.inner_expr

        if debug_callback:
            debug_callback(f"通用有理化: {new_numerator} / {new_denominator}")

        # 化简分子
        if hasattr(new_numerator, 'simplify'):
            simplified_num = new_numerator.simplify(debug_callback)
        else:
            simplified_num = new_numerator

        # 化简分母
        if hasattr(new_denominator, 'simplify'):
            simplified_den = new_denominator.simplify(debug_callback)
        else:
            simplified_den = new_denominator

        # 如果分母是1，直接返回分子
        if isinstance(simplified_den, AlgebraicExpression) and simplified_den.is_constant():
            const = simplified_den.terms[0].coeff
            if const == Fraction(1, 1):
                return simplified_num

        return FractionExpression(simplified_num, simplified_den)

    @staticmethod
    def _extract_sqrt_terms(expr):
        """从表达式中提取根号项"""
        sqrt_terms = []
        if isinstance(expr, AlgebraicExpression):
            for term in expr.terms:
                if isinstance(term, SqrtExpression):
                    sqrt_terms.append(term)
        return sqrt_terms

    @staticmethod
    def _rationalize_with_conjugate(numerator, denominator, sqrt_terms, debug_callback):
        """使用共轭进行分母有理化"""
        if debug_callback:
            debug_callback(f"使用共轭有理化，共轭表达式构建中...")

        # 构建共轭表达式（将根号项的符号取反）
        conjugate_terms = []
        for term in denominator.terms:
            if isinstance(term, SqrtExpression):
                # 根号项取负
                conjugate_terms.append(AlgebraicExpression([AlgebraicTerm(Fraction(-1, 1))]) * term)
            else:
                conjugate_terms.append(term)

        conjugate = AlgebraicExpression(conjugate_terms).simplify(debug_callback)

        # 分子分母同乘以共轭
        new_numerator = numerator * conjugate
        new_denominator = denominator * conjugate

        # 化简
        simplified_num = new_numerator.simplify(debug_callback)
        simplified_den = new_denominator.simplify(debug_callback)

        if debug_callback:
            debug_callback(f"有理化结果: {simplified_num} / {simplified_den}")

        return FractionExpression(simplified_num, simplified_den)


def are_expressions_equivalent(expr1, expr2, debug_callback=None):
    """
    检查两个代数表达式是否代数等价

    参数:
        expr1: 第一个表达式
        expr2: 第二个表达式
        debug_callback: 调试回调函数

    返回:
        bool: 如果表达式等价返回True，否则返回False
    """
    if debug_callback:
        debug_callback(f"检查表达式等价性: {expr1} 和 {expr2}")

    # 如果类型不同，直接返回False（除了特殊情况）
    if type(expr1) != type(expr2):
        # 特殊处理：一个可能是代数项，另一个是包含该代数项的代数表达式
        if isinstance(expr1, AlgebraicTerm) and isinstance(expr2, AlgebraicExpression):
            if len(expr2.terms) == 1 and isinstance(expr2.terms[0], AlgebraicTerm):
                return are_expressions_equivalent(expr1, expr2.terms[0], debug_callback)
        elif isinstance(expr2, AlgebraicTerm) and isinstance(expr1, AlgebraicExpression):
            if len(expr1.terms) == 1 and isinstance(expr1.terms[0], AlgebraicTerm):
                return are_expressions_equivalent(expr1.terms[0], expr2, debug_callback)
        return False

    # 如果是代数表达式
    if isinstance(expr1, AlgebraicExpression):
        # 简化两个表达式
        simplified1 = expr1.simplify(debug_callback)
        simplified2 = expr2.simplify(debug_callback)

        # 获取字符串表示并标准化
        str1 = str(simplified1).replace(' ', '').replace('+-', '-').replace('--', '+')
        str2 = str(simplified2).replace(' ', '').replace('+-', '-').replace('--', '+')

        # 如果字符串相等，直接返回True
        if str1 == str2:
            if debug_callback:
                debug_callback(f"表达式字符串相等: {str1}")
            return True

        # 检查项的数量是否相同
        if len(simplified1.terms) != len(simplified2.terms):
            if debug_callback:
                debug_callback(f"项的数量不同: {len(simplified1.terms)} != {len(simplified2.terms)}")
            return False

        # 尝试重新排序项进行匹配
        # 对于加法，项的顺序不影响结果
        # 收集所有项
        terms1 = simplified1.terms[:]
        terms2 = simplified2.terms[:]

        # 为每个项寻找匹配
        matched_indices = set()
        for i, term1 in enumerate(terms1):
            found_match = False
            for j, term2 in enumerate(terms2):
                if j in matched_indices:
                    continue
                if are_terms_equivalent(term1, term2, debug_callback):
                    matched_indices.add(j)
                    found_match = True
                    break
            if not found_match:
                if debug_callback:
                    debug_callback(f"在第二个表达式中未找到匹配项: {term1}")
                return False

        if debug_callback:
            debug_callback(f"所有项都匹配，表达式等价")
        return True

    # 如果是分数表达式
    elif isinstance(expr1, FractionExpression):
        # 检查分子分母是否分别等价
        num_eq = are_expressions_equivalent(expr1.numerator, expr2.numerator, debug_callback)
        den_eq = are_expressions_equivalent(expr1.denominator, expr2.denominator, debug_callback)
        result = num_eq and den_eq
        if debug_callback:
            debug_callback(f"分式等价性检查结果: 分子{num_eq}, 分母{den_eq}, 总体{result}")
        return result

    # 如果是代数项
    elif isinstance(expr1, AlgebraicTerm):
        return are_terms_equivalent(expr1, expr2, debug_callback)

    # 如果是绝对值表达式
    elif isinstance(expr1, AbsoluteValue):
        # 检查内部表达式是否等价
        return are_expressions_equivalent(expr1.inner_expr, expr2.inner_expr, debug_callback)

    # 如果是根号表达式
    elif isinstance(expr1, SqrtExpression):
        # 检查内部表达式是否等价
        return are_expressions_equivalent(expr1.inner_expr, expr2.inner_expr, debug_callback)

    # 其他情况，检查字符串表示
    str1 = str(expr1).replace(' ', '')
    str2 = str(expr2).replace(' ', '')
    result = str1 == str2
    if debug_callback:
        debug_callback(f"其他类型等价性检查: {str1} == {str2} => {result}")
    return result


def are_terms_equivalent(term1, term2, debug_callback=None):
    """
    检查两个代数项是否等价

    参数:
        term1: 第一个项
        term2: 第二个项
        debug_callback: 调试回调函数

    返回:
        bool: 如果项等价返回True，否则返回False
    """
    if debug_callback:
        debug_callback(f"检查项等价性: {term1} 和 {term2}")

    if not isinstance(term1, AlgebraicTerm) or not isinstance(term2, AlgebraicTerm):
        # 如果有一个不是代数项，可能要进行类型转换
        if isinstance(term1, AlgebraicTerm) and isinstance(term2, (int, Fraction)):
            # 将数字转换为代数项
            term2 = AlgebraicTerm(Fraction(term2, 1) if isinstance(term2, int) else term2)
        elif isinstance(term2, AlgebraicTerm) and isinstance(term1, (int, Fraction)):
            # 将数字转换为代数项
            term1 = AlgebraicTerm(Fraction(term1, 1) if isinstance(term1, int) else term1)
        else:
            return False

    # 系数相等
    if term1.coeff != term2.coeff:
        if debug_callback:
            debug_callback(f"系数不相等: {term1.coeff} != {term2.coeff}")
        return False

    # 变量相同
    if len(term1.vars) != len(term2.vars):
        if debug_callback:
            debug_callback(f"变量数量不同: {len(term1.vars)} != {len(term2.vars)}")
        return False

    # 检查每个变量及其指数
    for var, exp in term1.vars.items():
        if var not in term2.vars or term2.vars[var] != exp:
            if debug_callback:
                debug_callback(f"变量 {var}^{exp} 不匹配")
            return False

    if debug_callback:
        debug_callback(f"项等价: {term1} == {term2}")
    return True


def normalize_expression_string(expr_str):
    """
    规范化表达式字符串，确保一致的表示

    参数:
        expr_str: 表达式字符串

    返回:
        str: 规范化的表达式字符串
    """
    if not expr_str:
        return expr_str

    # 移除所有空格
    result = expr_str.replace(' ', '')

    # 标准化符号
    while '+-' in result:
        result = result.replace('+-', '-')
    while '--' in result:
        result = result.replace('--', '+')

    # 确保开头没有+号
    if result.startswith('+'):
        result = result[1:]

    # 处理特殊情况：空字符串或单个0
    if not result:
        result = '0'

    return result