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
            # MODIFIED: 移除指数为0的变量
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

    def has_negative_exponents(self):
        """检查是否存在负指数变量"""
        for exp in self.vars.values():
            if exp < 0:
                return True
        return False

    def __str__(self):
        # 系数为0
        if self.coeff.numerator == 0:
            return "0"

        # 如果没有负指数，使用原来的字符串表示（保持原有格式）
        if not self.has_negative_exponents():
            # 构建系数部分
            coeff_str = str(self.coeff)
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
                if exp == 0:
                    continue
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
                return "1"

        # ========== 存在负指数，使用分数表示 ==========
        # 分离正指数和负指数（负指数存储为正指数，用于分母）
        pos_vars = {}
        neg_vars = {}
        for var, exp in self.vars.items():
            if exp > 0:
                pos_vars[var] = exp
            elif exp < 0:
                neg_vars[var] = -exp  # 转为正指数

        coeff_num = self.coeff.numerator
        coeff_den = self.coeff.denominator
        sign = 1 if coeff_num >= 0 else -1
        coeff_num = abs(coeff_num)

        # 构建分子部分：系数分子 + 正指数变量
        num_parts = []
        # 如果分子整数部分不为1，或者分子整数为1但没有正指数变量，则添加数字
        if coeff_num != 1 or (coeff_num == 1 and not pos_vars):
            num_parts.append(str(coeff_num))
        for var in sorted(pos_vars.keys()):
            exp = pos_vars[var]
            if exp == 1:
                num_parts.append(var)
            else:
                num_parts.append(f"{var}^{exp}")

        # 构建分母部分：系数分母 + 负指数变量（正指数）
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
        # 如果分母包含多个因子，用括号括起来（例如 2x → (2x)）
        if len(den_parts) > 1:
            den_str = "(" + "".join(den_parts) + ")"
        else:
            den_str = "".join(den_parts) if den_parts else "1"

        # 如果分母为1（理论上不会进入此分支，因为存在负指数），直接返回分子
        if den_str == "1":
            if sign == -1:
                return f"-{num_str}"
            else:
                return num_str

        # 分子为1且无正指数变量，返回 1/分母（例如 1/(2x)）
        if num_str == "1" and not pos_vars:
            if sign == -1:
                return f"-1/{den_str}"
            else:
                return f"1/{den_str}"

        # 一般情况：分子/分母
        if sign == -1:
            return f"-{num_str}/{den_str}"
        else:
            return f"{num_str}/{den_str}"

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
            matches = re.findall(r'([a-zA-Z])(?:\^(\d+))?', var_part)
            for var, exp_str in matches:
                exp = int(exp_str) if exp_str else 1
                vars_dict[var] = vars_dict.get(var, 0) + exp

        # MODIFIED: 移除指数为0的变量
        vars_dict = {k: v for k, v in vars_dict.items() if v != 0}
        return AlgebraicTerm(coeff, vars_dict)

    def __pow__(self, exp):
        """代数项的幂运算"""
        if isinstance(exp, int) and exp >= 0:
            new_coeff = self.coeff ** exp
            new_vars = {}
            for var, var_exp in self.vars.items():
                new_vars[var] = var_exp * exp
            # MODIFIED: 移除指数为0的变量
            new_vars = {k: v for k, v in new_vars.items() if v != 0}
            return AlgebraicTerm(new_coeff, new_vars)
        else:
            return AlgebraicExpression([self]) ** exp

    def substitute(self, var, expr, debug_callback=None):
        """
        将项中出现的变量 var 替换为表达式 expr，返回新的表达式（可能是多项）。
        """
        if var not in self.vars:
            # 如果项中不包含该变量，直接返回自身（深拷贝）
            from copy import deepcopy
            return AlgebraicExpression([deepcopy(self)])

        exp = self.vars[var]
        # 构造不含 var 的部分
        other_vars = {k: v for k, v in self.vars.items() if k != var}
        base_term = AlgebraicTerm(self.coeff, other_vars)
        # expr^exp 可能产生多项，需展开
        pow_expr = expr ** exp   # expr 是 AlgebraicExpression，其 __pow__ 返回 AlgebraicExpression
        # 相乘得到表达式
        result = base_term * pow_expr
        return result   # base_term * pow_expr 已经返回 AlgebraicExpression


class AbsoluteValue:
    """表示绝对值表达式，如 |x|, |x+y| 等"""

    def __init__(self, inner_expr):
        self.inner_expr = inner_expr
        self.expr_type = ExpressionType.ABSOLUTE_VALUE

    def simplify(self, debug_callback=None):
        """简化绝对值表达式"""
        if debug_callback:
            debug_callback(f"开始简化绝对值表达式: |{self.inner_expr}|", level=1)
            debug_callback(f"内部表达式类型: {type(self.inner_expr)}", level=3)

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
                    debug_callback(f"常数绝对值: |{const}| = {result}", level=2)

                return AlgebraicExpression([AlgebraicTerm(result)])

        # 简化内部表达式
        simplified_inner = self.inner_expr.simplify(debug_callback)
        if simplified_inner != self.inner_expr:
            if debug_callback:
                debug_callback(f"内部表达式已简化: {self.inner_expr} -> {simplified_inner}", level=2)
            return AbsoluteValue(simplified_inner)

        # 无法进一步简化，返回自身
        if debug_callback:
            debug_callback(f"无法进一步简化绝对值表达式", level=3)
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
        elif isinstance(other, FractionExpression):
            # 绝对值乘以分式
            new_numerator = self * other.numerator
            return FractionExpression(new_numerator, other.denominator)
        elif isinstance(other, SqrtExpression):
            # 绝对值乘以根号
            return AlgebraicExpression([self, other])
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

    def __neg__(self):
        """返回绝对值的相反数"""
        return self * Fraction(-1, 1)

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
            debug_callback(f"开始展开绝对值表达式: |{self.inner_expr}|", level=1)
            debug_callback(f"内部表达式类型: {type(self.inner_expr)}", level=3)

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
                    debug_callback(f"单变量绝对值: |{var_name}|", level=2)

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
            debug_callback(f"绝对值展开结果: {result}", level=2)

        return result

    def is_zero(self):
        """绝对值表达式为零当且仅当内部表达式为零"""
        inner = self.inner_expr
        if hasattr(inner, 'simplify'):
            inner = inner.simplify()
        return hasattr(inner, 'is_zero') and inner.is_zero()

    def substitute(self, var, expr, debug_callback=None):
        new_inner = self.inner_expr.substitute(var, expr, debug_callback)
        return AbsoluteValue(new_inner)

    def __pow__(self, exp):
        """绝对值的幂运算，返回表达式"""
        return AlgebraicExpression([self]) ** exp


class SqrtExpression:
    """表示平方根表达式，如 √(x), √(x+y) 等"""

    def __init__(self, inner_expr):
        self.inner_expr = inner_expr
        self.expr_type = ExpressionType.SQRT

    def __eq__(self, other):
        """比较两个平方根表达式是否相等"""
        if not isinstance(other, SqrtExpression):
            return False
        return self.inner_expr == other.inner_expr

    def simplify(self, debug_callback=None):
        """化简根号表达式"""
        if debug_callback:
            debug_callback(f"开始化简根号表达式: √({self.inner_expr})", level=1)
            debug_callback(f"内部表达式类型: {type(self.inner_expr)}", level=3)

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
                    debug_callback(f"常数完全平方根: √({const}) = {result}", level=2)
                return AlgebraicExpression([AlgebraicTerm(result)])
            elif debug_callback:
                debug_callback(f"常数 {const} 不是完全平方数，保留根号形式", level=3)

        # 提取平方因子
        return self._extract_square_factors(simplified_inner, debug_callback)

    def _is_perfect_square(self, n):
        """检查是否为完全平方数"""
        if n < 0:
            return None
        root = int(math.isqrt(n))
        return root if root * root == n else None

    def _max_square_factor(self, n):
        """找到最大的平方因子"""
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
        """提取平方因子，如 √(8x³) = 2x√(2x)"""
        if debug_callback:
            debug_callback(f"开始提取平方因子: √({expr})", level=2)
            debug_callback(f"表达式类型: {type(expr)}", level=3)

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
                # MODIFIED: 提取的系数始终为正，符号保留在剩余部分
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
        """分母有理化"""
        if debug_callback:
            debug_callback(f"开始分母有理化: 1/√({self.inner_expr})", level=1)
            debug_callback(f"分母类型: {type(denominator)}", level=3)

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
        """返回根号的相反数"""
        return self * Fraction(-1, 1)

    def __truediv__(self, other):
        """重载除法运算符，正确处理根号除以常数的情况"""
        if isinstance(other, (int, Fraction)):
            # 将常数除法转化为系数乘法：√a / k = (1/k) * √a
            if isinstance(other, int):
                other = Fraction(other, 1)
            coeff = Fraction(1, 1) / other
            TermWithSqrt = globals().get('TermWithSqrt')
            if TermWithSqrt is None:
                # 如果 TermWithSqrt 类尚未定义，返回表达式形式
                return AlgebraicExpression([AlgebraicTerm(coeff), self])
            # 返回 TermWithSqrt 对象，系数为 1/other
            return TermWithSqrt(AlgebraicTerm(coeff), self)
        elif isinstance(other, SqrtExpression):
            # 根号除以根号：√a / √b = √(a/b)
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
        """基于内部表达式字符串的哈希，保证相同内容的根号具有相同哈希值"""
        return hash(('sqrt', str(self.inner_expr)))

    def is_zero(self):
        """平方根表达式为零当且仅当内部表达式为零"""
        inner = self.inner_expr
        if hasattr(inner, 'simplify'):
            inner = inner.simplify()
        return hasattr(inner, 'is_zero') and inner.is_zero()

    def substitute(self, var, expr, debug_callback=None):
        new_inner = self.inner_expr.substitute(var, expr, debug_callback)
        return SqrtExpression(new_inner)


class TermWithSqrt:
    """表示系数乘以平方根的项，如 2x√(y)"""
    def __init__(self, coeff, sqrt_expr):
        # 将系数统一为 AlgebraicTerm
        if isinstance(coeff, AlgebraicTerm):
            self.coeff = coeff
        else:
            # 假设 coeff 是 Fraction 或 int
            self.coeff = AlgebraicTerm(coeff if isinstance(coeff, Fraction) else Fraction(coeff, 1))
        self.sqrt_expr = sqrt_expr

    def __eq__(self, other):
        """比较两个带平方根的项是否相等"""
        if not isinstance(other, TermWithSqrt):
            return False
        return self.coeff == other.coeff and self.sqrt_expr == other.sqrt_expr

    def __str__(self):
        coeff_str = str(self.coeff)
        sqrt_str = str(self.sqrt_expr)
        # 系数为1且没有变量时省略系数
        if self.coeff.coeff == Fraction(1, 1) and not self.coeff.vars:
            return sqrt_str
        # 系数为-1且没有变量时显示负号
        if self.coeff.coeff == Fraction(-1, 1) and not self.coeff.vars:
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
            return AlgebraicExpression([new_coeff, new_sqrt])
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
        """支持除以常数或常数项"""
        if isinstance(other, (int, Fraction)):
            return TermWithSqrt(self.coeff / other, self.sqrt_expr)
        elif isinstance(other, AlgebraicTerm) and other.is_constant():
            return TermWithSqrt(self.coeff / other.coeff, self.sqrt_expr)
        else:
            return NotImplemented

    def __add__(self, other):
        if isinstance(other, TermWithSqrt) and self.sqrt_expr == other.sqrt_expr:
            new_coeff = self.coeff + other.coeff
            if isinstance(new_coeff, AlgebraicTerm):
                return TermWithSqrt(new_coeff, self.sqrt_expr)
            # 如果相加后不是代数项（例如不同变量），则返回表达式
            return AlgebraicExpression([self, other])
        return AlgebraicExpression([self]) + other

    def __sub__(self, other):
        return self + (-other)

    def __neg__(self):
        return TermWithSqrt(-self.coeff, self.sqrt_expr)

    def __eq__(self, other):
        if not isinstance(other, TermWithSqrt):
            return False
        return self.coeff == other.coeff and self.sqrt_expr == other.sqrt_expr

    def contains_var(self, var):
        return self.coeff.contains_var(var) or self.sqrt_expr.contains_var(var)

    def simplify(self, debug_callback=None):
        """简化 TermWithSqrt 对象"""
        if debug_callback:
            debug_callback(f"开始简化 TermWithSqrt: {self}", level=2)

        # 简化系数和内部的平方根
        simplified_coeff = self.coeff.simplify(debug_callback) if hasattr(self.coeff, 'simplify') else self.coeff
        simplified_sqrt = self.sqrt_expr.simplify(debug_callback)

        if simplified_coeff != self.coeff or simplified_sqrt != self.sqrt_expr:
            result = TermWithSqrt(simplified_coeff, simplified_sqrt)
            if debug_callback:
                debug_callback(f"简化 TermWithSqrt 结果: {result}", level=2)
            return result

        if debug_callback:
            debug_callback(f"TermWithSqrt 无需进一步简化", level=3)
        return self

    def is_zero(self):
        """带根号的项为零当且仅当系数为零（因为根号部分非负）"""
        return self.coeff.coeff.numerator == 0

    def substitute(self, var, expr, debug_callback=None):
        """将系数和根号部分中的变量替换"""
        new_coeff = self.coeff.substitute(var, expr, debug_callback)
        new_sqrt = self.sqrt_expr.substitute(var, expr, debug_callback)
        return TermWithSqrt(new_coeff, new_sqrt)


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
        if debug_callback:
            debug_callback(f"开始化简代数表达式: {self}", level=1)
            debug_callback(f"原始项数: {len(self.terms)}", level=3)

        if not self.terms:
            return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])

        simplified_terms = []
        for term in self.terms:
            if debug_callback:
                debug_callback(f"处理项 {term} (类型: {type(term)})", level=3)

            if hasattr(term, 'simplify'):
                simplified_term = term.simplify(debug_callback)
                if isinstance(simplified_term, AlgebraicExpression):
                    simplified_terms.extend(simplified_term.terms)
                else:
                    simplified_terms.append(simplified_term)
            else:
                simplified_terms.append(term)

        fraction_terms = [term for term in simplified_terms if isinstance(term, FractionExpression)]
        non_fraction_terms = [term for term in simplified_terms if not isinstance(term, FractionExpression)]

        if debug_callback:
            debug_callback(f"分式项数量: {len(fraction_terms)}", level=3)
            debug_callback(f"非分式项数量: {len(non_fraction_terms)}", level=3)

        if not fraction_terms:
            # 没有分式项，合并同类项（包括 TermWithSqrt）
            regular_terms = []
            abs_terms = []
            sqrt_terms = []
            term_with_sqrt_terms = []

            for term in non_fraction_terms:
                if isinstance(term, AbsoluteValue):
                    abs_terms.append(term)
                elif isinstance(term, SqrtExpression):
                    sqrt_terms.append(term)
                elif isinstance(term, TermWithSqrt):
                    term_with_sqrt_terms.append(term)
                else:
                    if isinstance(term, AlgebraicTerm) and term.coeff.numerator == 0:
                        continue
                    regular_terms.append(term)

            if debug_callback:
                debug_callback(f"常规项: {len(regular_terms)}", level=3)
                debug_callback(f"绝对值项: {len(abs_terms)}", level=3)
                debug_callback(f"根号项: {len(sqrt_terms)}", level=3)
                debug_callback(f"根号乘积项: {len(term_with_sqrt_terms)}", level=3)

            # 合并常规代数项
            term_dict = {}
            for term in regular_terms:
                if isinstance(term, AlgebraicTerm):
                    # 优化点：使用 frozenset 代替 tuple(sorted(...))，避免排序开销
                    var_key = frozenset(term.vars.items())
                    if var_key in term_dict:
                        term_dict[var_key] = term_dict[var_key] + term
                    else:
                        term_dict[var_key] = term
                else:
                    # 理论上这里不应有其他类型，但保留
                    if isinstance(term, SqrtExpression):
                        sqrt_terms.append(term)
                    elif isinstance(term, AbsoluteValue):
                        abs_terms.append(term)
                    elif isinstance(term, TermWithSqrt):
                        term_with_sqrt_terms.append(term)
                    else:
                        regular_terms.append(term)

            simplified_regular_terms = []
            for var_key, term in term_dict.items():
                if debug_callback:
                    debug_callback(f"合并变量组 {var_key}: {term}", level=3)

                if isinstance(term, AlgebraicTerm) and term.coeff.numerator != 0:
                    simplified_regular_terms.append(term)

            # 合并 TermWithSqrt 项
            term_with_sqrt_dict = {}
            for term in term_with_sqrt_terms:
                key = term.sqrt_expr
                if key in term_with_sqrt_dict:
                    combined = term_with_sqrt_dict[key] + term
                    if isinstance(combined, TermWithSqrt):
                        term_with_sqrt_dict[key] = combined
                    else:
                        term_with_sqrt_dict[key] = term  # 保留第一个
                else:
                    term_with_sqrt_dict[key] = term

            simplified_term_with_sqrt_terms = []
            for term in term_with_sqrt_dict.values():
                if isinstance(term, TermWithSqrt) and term.coeff.coeff.numerator != 0:
                    simplified_term_with_sqrt_terms.append(term)

            all_terms = simplified_regular_terms + abs_terms + sqrt_terms + simplified_term_with_sqrt_terms

            if debug_callback:
                debug_callback(f"合并后总项数: {len(all_terms)}", level=3)

            if not all_terms:
                return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])

            if len(all_terms) == 1:
                if debug_callback:
                    debug_callback(f"化简为单项式: {all_terms[0]}", level=2)
                return AlgebraicExpression(all_terms)

            if debug_callback:
                debug_callback(f"化简完成，结果项数: {len(all_terms)}", level=2)
            return AlgebraicExpression(all_terms)

        else:
            # 存在分式项，合并所有项到一个分式（原代码保持不变）
            # ... 此处省略分式处理部分，原样保留 ...
            if debug_callback:
                debug_callback(f"发现分式项，开始处理分式合并", level=2)

            combined_fraction = None
            for i, fraction in enumerate(fraction_terms):
                if debug_callback:
                    debug_callback(f"处理第 {i + 1} 个分式: {fraction}", level=3)

                if combined_fraction is None:
                    combined_fraction = fraction
                else:
                    a = combined_fraction.numerator
                    b = combined_fraction.denominator
                    c = fraction.numerator
                    d = fraction.denominator

                    new_numerator = (a * d) + (c * b)
                    new_denominator = b * d

                    combined_fraction = FractionExpression(new_numerator, new_denominator)

            for non_fraction in non_fraction_terms:
                if isinstance(non_fraction, AlgebraicTerm):
                    term_fraction = FractionExpression(
                        AlgebraicExpression([non_fraction]),
                        AlgebraicExpression([AlgebraicTerm(Fraction(1, 1))])
                    )
                elif isinstance(non_fraction, (AbsoluteValue, SqrtExpression)):
                    term_fraction = FractionExpression(
                        AlgebraicExpression([non_fraction]),
                        AlgebraicExpression([AlgebraicTerm(Fraction(1, 1))])
                    )
                elif isinstance(non_fraction, AlgebraicExpression):
                    term_fraction = FractionExpression(
                        non_fraction,
                        AlgebraicExpression([AlgebraicTerm(Fraction(1, 1))])
                    )
                elif isinstance(non_fraction, TermWithSqrt):
                    term_fraction = FractionExpression(
                        AlgebraicExpression([non_fraction]),
                        AlgebraicExpression([AlgebraicTerm(Fraction(1, 1))])
                    )
                else:
                    continue

                if combined_fraction is None:
                    combined_fraction = term_fraction
                else:
                    a = combined_fraction.numerator
                    b = combined_fraction.denominator
                    c = term_fraction.numerator
                    d = term_fraction.denominator

                    new_numerator = (a * d) + (c * b)
                    new_denominator = b * d

                    combined_fraction = FractionExpression(new_numerator, new_denominator)

            if combined_fraction is None:
                return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])

            simplified_fraction = combined_fraction.simplify(debug_callback)

            if isinstance(simplified_fraction, AlgebraicExpression):
                return simplified_fraction
            else:
                return simplified_fraction

    def __str__(self):
        if not self.terms:
            return "0"

        def term_sort_key(term):
            """排序键：常数项优先级高（排在后面），变量项优先级低（排在前面）"""
            if isinstance(term, AlgebraicTerm):
                var_str = ''.join(sorted([f"{var}^{exp}" for var, exp in term.vars.items()]))
                # 常数项（无变量）优先级为1，变量项优先级为0
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
            other = AlgebraicExpression([other])  # 将根号包装为表达式
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
            other = AlgebraicExpression([other])  # 将根号包装为表达式
        elif not isinstance(other, AlgebraicExpression):
            return NotImplemented

        neg_terms = []
        for term in other.terms:
            if isinstance(term, AbsoluteValue):
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
        elif isinstance(other, FractionExpression):
            # 代数表达式乘以分式
            new_numerator = self * other.numerator
            return FractionExpression(new_numerator, other.denominator)
        return NotImplemented

    def __rmul__(self, other):
        if isinstance(other, (int, Fraction)):
            return self * other
        return NotImplemented

    def __neg__(self):
        """返回表达式的相反数"""
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

    def solve_for_variable(self, var, debug_callback=None):
        if debug_callback:
            debug_callback(f"开始求解变量 {var}: {self} = 0", level=1)
            debug_callback(f"方程项数: {len(self.terms)}", level=3)

        if self.contains_absolute_value():
            if debug_callback:
                debug_callback(f"方程包含绝对值，无法直接求解", level=2)
            return f"目前不支持求解这类方程，已化简：{str(self)}"

        coeffs = {}
        for term in self.terms:
            if isinstance(term, AlgebraicTerm):
                if var in term.vars:
                    exp = term.vars[var]
                    new_vars = term.vars.copy()
                    del new_vars[var]
                    coeff_term = AlgebraicTerm(term.coeff, new_vars)
                else:
                    exp = 0
                    coeff_term = term

                coeff_expr = AlgebraicExpression([coeff_term])

                if exp in coeffs:
                    coeffs[exp] = (coeffs[exp] + coeff_expr).simplify(debug_callback)
                else:
                    coeffs[exp] = coeff_expr

            elif isinstance(term, TermWithSqrt):
                if term.contains_var(var):
                    # 根号部分或系数中包含变量，无法处理
                    if debug_callback:
                        debug_callback(f"遇到不支持的项类型: {type(term)}，无法求解", level=1)
                    return f"目前不支持求解这类方程，已化简：{str(self)}"
                else:
                    # 不含变量，视为常数项
                    coeff_expr = AlgebraicExpression([term])
                    exp = 0
                    if exp in coeffs:
                        coeffs[exp] = (coeffs[exp] + coeff_expr).simplify(debug_callback)
                    else:
                        coeffs[exp] = coeff_expr
                    continue

            else:
                if debug_callback:
                    debug_callback(f"遇到不支持的项类型: {type(term)}，无法求解", level=1)
                return f"目前不支持求解这类方程，已化简：{str(self)}"

        for exp in coeffs:
            coeffs[exp] = coeffs[exp].simplify(debug_callback)

        if debug_callback:
            debug_callback(f"系数收集完成: { {exp: str(coeffs[exp]) for exp in coeffs} }", level=3)

        exponents = sorted(coeffs.keys(), reverse=True)
        if not exponents:
            return "无变量项"

        max_exp = exponents[0]
        min_exp = exponents[-1]

        if min_exp < 0:
            if debug_callback:
                debug_callback(f"方程含有负指数，最小指数 {min_exp}，乘以 {var}^{-min_exp} 化为多项式", level=2)
            k = -min_exp
            multiplier_term = AlgebraicTerm(Fraction(1, 1), {var: k})
            multiplier_expr = AlgebraicExpression([multiplier_term])
            new_expr = self * multiplier_expr
            new_expr = new_expr.simplify(debug_callback)
            return new_expr.solve_for_variable(var, debug_callback)

        if max_exp == 0:
            const_expr = coeffs[0]
            if const_expr.is_zero():
                return "恒等式（对任何值都成立）"
            else:
                return "矛盾方程（无解）"

        elif max_exp == 1:
            a = coeffs.get(1, AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))]))
            b = coeffs.get(0, AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))]))

            if a.is_zero():
                if b.is_zero():
                    return "无穷多解"
                else:
                    return "无解"

            solution = (b * Fraction(-1, 1)) / a
            if hasattr(solution, 'simplify'):
                solution = solution.simplify(debug_callback)

            # ========== 添加符号规范化 ==========
            if hasattr(solution, 'canonicalize_sign'):
                solution = solution.canonicalize_sign()
            # ========== 添加结束 ==========

            sol_str = str(solution)
            sol_str = sol_str.replace('+-', '-').replace('--', '+')
            sol_str = sol_str.replace('+0', '').replace('-0', '')
            sol_str = sol_str.replace('1*', '').replace('*1', '')
            if sol_str.startswith('+'):
                sol_str = sol_str[1:]

            return sol_str

        elif max_exp == 2:
            a = coeffs.get(2, AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))]))
            b = coeffs.get(1, AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))]))
            c = coeffs.get(0, AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))]))

            if debug_callback:
                debug_callback(f"二次方程: a={a}, b={b}, c={c}", level=2)

            if a.is_zero():
                if b.is_zero():
                    return "无穷多解" if c.is_zero() else "无解"
                solution = (c * Fraction(-1, 1)) / b
                sol_str = str(solution.simplify(debug_callback))
                return sol_str

            if b.is_zero():
                rhs = (c * Fraction(-1, 1)) / a
                rhs_simplified = rhs.simplify(debug_callback)
                if rhs_simplified.is_zero():
                    return "0"
                # 检查 rhs 是否为负数
                if rhs_simplified.is_constant():
                    const = rhs_simplified.terms[0].coeff
                    if const.numerator < 0:
                        if debug_callback:
                            debug_callback(f"右边为负数 {const}，无实数解", level=2)
                        return "无实数解"
                rhs_str = str(rhs_simplified).replace('+-', '-').replace('--', '+')
                return f"√({rhs_str}) 或 -√({rhs_str})"

            b_sq = (b * b).simplify(debug_callback)
            ac = (a * c).simplify(debug_callback)
            delta = (b_sq - (ac * Fraction(4, 1))).simplify(debug_callback)

            if debug_callback:
                debug_callback(f"判别式 delta = {delta}", level=2)

            # 处理负常数判别式
            if delta.is_constant():
                delta_const = delta.terms[0].coeff
                if delta_const.numerator < 0:
                    return "无实数解"
                if delta_const.denominator == 1:
                    num = abs(delta_const.numerator)
                    root = int(math.isqrt(num))
                    if root * root == num:
                        sqrt_val = Fraction(root, 1) * (Fraction(1, 1) if delta_const.numerator >= 0 else Fraction(-1, 1))
                        neg_b = (b * Fraction(-1, 1)).simplify(debug_callback)
                        two_a = (a * Fraction(2, 1)).simplify(debug_callback)

                        sol1 = (neg_b + AlgebraicTerm(sqrt_val)) / two_a
                        sol2 = (neg_b - AlgebraicTerm(sqrt_val)) / two_a
                        sol1 = sol1.simplify(debug_callback)
                        sol2 = sol2.simplify(debug_callback)

                        sol1_str = str(sol1).replace('+-', '-').replace('--', '+')
                        sol2_str = str(sol2).replace('+-', '-').replace('--', '+')
                        if sol1_str == sol2_str:
                            return sol1_str
                        else:
                            return f"{sol1_str} 或 {sol2_str}"

            sqrt_delta = SqrtExpression(delta)
            sqrt_delta_expr = AlgebraicExpression([sqrt_delta]).simplify(debug_callback)
            neg_b = (b * Fraction(-1, 1)).simplify(debug_callback)
            two_a = (a * Fraction(2, 1)).simplify(debug_callback)

            # 规范化分母中的负指数
            if len(two_a.terms) == 1 and isinstance(two_a.terms[0], AlgebraicTerm):
                term = two_a.terms[0]
                neg_vars = {var: exp for var, exp in term.vars.items() if exp < 0}
                if neg_vars:
                    if debug_callback:
                        debug_callback(f"分母 {two_a} 包含负指数变量 {neg_vars}，准备乘以因子消除负指数", level=2)
                    factor_dict = {var: -exp for var, exp in neg_vars.items()}
                    factor_term = AlgebraicTerm(Fraction(1, 1), factor_dict)
                    factor_expr = AlgebraicExpression([factor_term])
                    if debug_callback:
                        debug_callback(f"乘以因子 {factor_expr}", level=3)
                    neg_b = (neg_b * factor_expr).simplify(debug_callback)
                    two_a = (two_a * factor_expr).simplify(debug_callback)
                    if debug_callback:
                        debug_callback(f"规范化后: 分子={neg_b}, 分母={two_a}", level=2)

            # 检查分母符号，如果 two_a 是负数，则乘以 -1 使分母为正
            adjust_sign = False
            if two_a.is_constant():
                const = two_a.terms[0].coeff
                if const.numerator < 0:
                    adjust_sign = True

            if adjust_sign:
                neg_b = (neg_b * Fraction(-1, 1)).simplify(debug_callback)
                two_a = (two_a * Fraction(-1, 1)).simplify(debug_callback)

            # 添加解化简逻辑
            def _simplify_sqrt_fraction(num_expr, sqrt_expr, den_expr):
                TermWithSqrt = globals().get('TermWithSqrt')
                if TermWithSqrt is None:
                    return None

                def is_constant_term(expr):
                    if not isinstance(expr, AlgebraicExpression):
                        return False
                    if len(expr.terms) != 1:
                        return False
                    term = expr.terms[0]
                    if not isinstance(term, AlgebraicTerm):
                        return False
                    if term.vars:
                        return False
                    return True

                if not (is_constant_term(num_expr) and is_constant_term(den_expr)):
                    return None

                num_coeff = num_expr.terms[0].coeff
                den_coeff = den_expr.terms[0].coeff

                sqrt_coeff = Fraction(1, 1)
                inner_sqrt = None
                if isinstance(sqrt_expr, AlgebraicExpression) and len(sqrt_expr.terms) == 1:
                    term = sqrt_expr.terms[0]
                    if isinstance(term, TermWithSqrt):
                        sqrt_coeff = term.coeff.coeff
                        inner_sqrt = term.sqrt_expr
                    elif isinstance(term, SqrtExpression):
                        inner_sqrt = term
                    else:
                        return None
                else:
                    return None

                import math
                nums = [num_coeff.numerator, sqrt_coeff.numerator, den_coeff.numerator]
                dens = [num_coeff.denominator, sqrt_coeff.denominator, den_coeff.denominator]
                lcm_den = 1
                for d in dens:
                    lcm_den = lcm_den * d // math.gcd(lcm_den, d)
                int_nums = [n * lcm_den // d for n, d in zip(nums, dens)]
                gcd_val = 0
                for val in int_nums:
                    gcd_val = math.gcd(gcd_val, val)
                    if gcd_val == 1:
                        break
                if gcd_val <= 1:
                    return None

                new_num_coeff = Fraction(int_nums[0] // gcd_val, lcm_den)
                new_sqrt_coeff = Fraction(int_nums[1] // gcd_val, lcm_den)
                new_den_coeff = Fraction(int_nums[2] // gcd_val, lcm_den)

                terms = []
                if new_num_coeff != Fraction(0, 1):
                    terms.append(AlgebraicTerm(new_num_coeff))
                if new_sqrt_coeff != Fraction(0, 1):
                    if new_sqrt_coeff == Fraction(1, 1):
                        sqrt_term = inner_sqrt
                    elif new_sqrt_coeff == Fraction(-1, 1):
                        sqrt_term = -inner_sqrt
                    else:
                        sqrt_term = TermWithSqrt(AlgebraicTerm(new_sqrt_coeff), inner_sqrt)
                    terms.append(sqrt_term)

                numerator_expr = AlgebraicExpression(terms)
                if new_den_coeff == Fraction(1, 1):
                    return numerator_expr
                else:
                    return FractionExpression(numerator_expr, AlgebraicExpression([AlgebraicTerm(new_den_coeff)]))

            # 尝试化简两个解
            simplified_sol1 = _simplify_sqrt_fraction(neg_b, sqrt_delta_expr, two_a)
            simplified_sol2 = _simplify_sqrt_fraction(neg_b, -sqrt_delta_expr, two_a)

            if simplified_sol1 is not None and simplified_sol2 is not None:
                # ========== 添加符号规范化 ==========
                if hasattr(simplified_sol1, 'canonicalize_sign'):
                    simplified_sol1 = simplified_sol1.canonicalize_sign()
                if hasattr(simplified_sol2, 'canonicalize_sign'):
                    simplified_sol2 = simplified_sol2.canonicalize_sign()
                # ========== 添加结束 ==========
                sol1_str = str(simplified_sol1)
                sol2_str = str(simplified_sol2)
            else:
                sol1_str = f"({neg_b}+{sqrt_delta_expr})/({two_a})"
                sol2_str = f"({neg_b}-{sqrt_delta_expr})/({two_a})"

            sol1_str = sol1_str.replace('+-', '-').replace('--', '+')
            sol2_str = sol2_str.replace('+-', '-').replace('--', '+')

            if sol1_str.startswith('(') and sol1_str.endswith(')'):
                inner = sol1_str[1:-1]
                if not any(op in inner for op in '+-'):
                    sol1_str = inner
            if sol2_str.startswith('(') and sol2_str.endswith(')'):
                inner = sol2_str[1:-1]
                if not any(op in inner for op in '+-'):
                    sol2_str = inner

            return f"{sol1_str} 或 {sol2_str}"
        else:
            return f"目前不支持求解这类方程，已化简：{str(self)}"

    def substitute(self, var, expr, debug_callback=None):
        """
        将表达式中所有出现的变量 var 替换为表达式 expr，返回新的表达式。
        expr 应为 AlgebraicExpression 对象。
        debug_callback: 可选，用于输出调试信息。
        """
        if debug_callback:
            debug_callback(f"Substituting {var} with {expr} in {self}", level=3)

        def substitute_term(term, debug_callback=None):
            if isinstance(term, AlgebraicTerm):
                if var in term.vars:
                    exp = term.vars[var]
                    other_vars = {k: v for k, v in term.vars.items() if k != var}
                    pow_expr = expr ** exp   # expr^exp 返回 AlgebraicExpression
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
                new_coeff = term.coeff.substitute(var, expr, debug_callback)
                new_sqrt = term.sqrt_expr.substitute(var, expr, debug_callback)
                # 尝试化简根号部分
                if hasattr(new_sqrt, 'simplify'):
                    new_sqrt = new_sqrt.simplify(debug_callback)
                # 检查系数是否可保留为单项式
                if isinstance(new_coeff, AlgebraicExpression) and len(new_coeff.terms) == 1:
                    only_term = new_coeff.terms[0]
                    if isinstance(only_term, AlgebraicTerm):
                        if only_term.coeff.numerator == 0:
                            return []  # 系数为零，该项消失
                        return [TermWithSqrt(only_term, new_sqrt)]
                # 否则，将系数与根号部分相乘，展开为普通项
                product = new_coeff * new_sqrt
                if isinstance(product, AlgebraicExpression):
                    return product.terms
                else:
                    return [product]
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
        """判断代数表达式是否为零"""
        if not self.terms:
            return True
        for term in self.terms:
            # 如果是代数项，检查系数
            if isinstance(term, AlgebraicTerm):
                if term.coeff.numerator != 0:
                    return False
            # 如果项有 is_zero 方法，调用它
            elif hasattr(term, 'is_zero'):
                if not term.is_zero():
                    return False
            else:
                # 未知类型，假设非零（安全起见返回 False）
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


class FractionExpression:
    """表示分式表达式，支持分母有理化"""

    def __init__(self, numerator, denominator):
        self.numerator = numerator
        self.denominator = denominator
        self.rationalized = False
        self.terms = [self]

    def __eq__(self, other):
        """比较两个分式是否相等（分子分母分别相等）"""
        if not isinstance(other, FractionExpression):
            return False
        return self.numerator == other.numerator and self.denominator == other.denominator

    def __mul__(self, other):
        """分式乘以其他表达式"""
        if isinstance(other, (int, Fraction)):
            # 分式乘以常数：分子乘以常数
            new_numerator = self.numerator * other
            return FractionExpression(new_numerator, self.denominator)
        elif isinstance(other, AlgebraicTerm):
            # 分式乘以代数项：分子乘以代数项
            new_numerator = self.numerator * other
            return FractionExpression(new_numerator, self.denominator)
        elif isinstance(other, AlgebraicExpression):
            # 分式乘以代数表达式：分子乘以表达式
            new_numerator = self.numerator * other
            return FractionExpression(new_numerator, self.denominator)
        elif isinstance(other, FractionExpression):
            # 分式乘以分式：(a/b) * (c/d) = (a*c)/(b*d)
            new_numerator = self.numerator * other.numerator
            new_denominator = self.denominator * other.denominator
            return FractionExpression(new_numerator, new_denominator)
        elif isinstance(other, AbsoluteValue):
            # 分式乘以绝对值：分子乘以绝对值
            new_numerator = self.numerator * other
            return FractionExpression(new_numerator, self.denominator)
        elif isinstance(other, SqrtExpression):
            # 分式乘以根号：分子乘以根号
            new_numerator = self.numerator * other
            return FractionExpression(new_numerator, self.denominator)
        return NotImplemented

    def __rmul__(self, other):
        """支持右侧乘法"""
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
            # 替换点：原代码使用字符串比较，现改为直接对象比较
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
        """返回分式的相反数"""
        return FractionExpression(-self.numerator, self.denominator)

    def __sub__(self, other):
        """分式减去其他表达式"""
        # 将减法转化为加法：self - other = self + (-other)
        if isinstance(other, (int, Fraction, AlgebraicTerm, AlgebraicExpression, AbsoluteValue, SqrtExpression, FractionExpression)):
            return self + (-other)
        return NotImplemented

    def __rsub__(self, other):
        """其他表达式减去分式：other - self = - (self - other)"""
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
        """检查表达式是否包含平方根"""
        if isinstance(expr, SqrtExpression):
            return True
        elif isinstance(expr, AlgebraicExpression):
            for term in expr.terms:
                if isinstance(term, (SqrtExpression, TermWithSqrt)):
                    return True
        return False

    def is_zero(self):
        """判断分式是否为零（即分子为零）"""
        # 简化分子
        num = self.numerator
        if hasattr(num, 'simplify'):
            num = num.simplify()
        # 判断分子是否为零
        if isinstance(num, AlgebraicExpression):
            return num.is_zero()
        elif isinstance(num, (int, Fraction)):
            return num == 0
        elif hasattr(num, 'is_zero'):
            return num.is_zero()
        else:
            # 无法判断，返回 False
            return False

    def is_constant(self):
        """判断分式是否常数（即分子分母均不含变量）"""
        # 简化分子和分母
        num = self.numerator
        den = self.denominator
        if hasattr(num, 'simplify'):
            num = num.simplify()
        if hasattr(den, 'simplify'):
            den = den.simplify()
        # 检查分子分母是否都是常数表达式
        return (hasattr(num, 'is_constant') and num.is_constant() and
                hasattr(den, 'is_constant') and den.is_constant())

    def canonicalize_sign(self):
        """
        对分式的符号进行规范化，使得分母的项按变量优先、常数在后的顺序排列，
        并且第一个变量项（如果有）的系数为正，否则常数项系数为正。
        例如：(-y)/(1-y) 转换为 y/(y-1)。
        返回规范化后的表达式对象（可能是 FractionExpression 或 AlgebraicExpression）。
        """
        # 如果分母是1，直接返回自身
        if isinstance(self.denominator, AlgebraicExpression) and self.denominator.is_constant():
            const = self.denominator.terms[0].coeff
            if const == Fraction(1, 1):
                return self

        num = self.numerator
        den = self.denominator

        # 定义排序函数，与 AlgebraicExpression.__str__ 一致
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
            terms = sorted(expr.terms, key=term_sort_key)
            return terms

        # 获取原分母排序后的第一项
        den_terms = sorted_terms(den)
        first_den = den_terms[0] if den_terms else None

        # 尝试乘以-1
        neg_one = AlgebraicExpression([AlgebraicTerm(Fraction(-1, 1))])
        den_neg = (den * neg_one).simplify()
        num_neg = (num * neg_one).simplify()
        den_neg_terms = sorted_terms(den_neg)
        first_neg = den_neg_terms[0] if den_neg_terms else None

        # 判断哪个更友好：优先选第一项是变量且系数为正的
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
            # 平局，选择常数项系数为正的
            if first_den and isinstance(first_den, AlgebraicTerm) and not first_den.vars:
                if first_den.coeff.numerator > 0:
                    return self
            if first_neg and isinstance(first_neg, AlgebraicTerm) and not first_neg.vars:
                if first_neg.coeff.numerator > 0:
                    return FractionExpression(num_neg, den_neg).canonicalize_sign()
            # 否则保持原样
            return self

    def substitute(self, var, expr, debug_callback=None):
        """将分子和分母中的变量替换"""
        new_num = self.numerator.substitute(var, expr, debug_callback)
        new_den = self.denominator.substitute(var, expr, debug_callback)
        return FractionExpression(new_num, new_den)

    def __pow__(self, other):
        """分式的整数次幂"""
        if isinstance(other, int):
            if other >= 0:
                return FractionExpression(self.numerator ** other, self.denominator ** other)
            else:
                # 负指数：取倒数
                return FractionExpression(self.denominator ** (-other), self.numerator ** (-other))
        raise TypeError("指数必须是整数")

    def simplify(self, debug_callback=None):
        try:
            if debug_callback:
                debug_callback(f"【FractionExpression.simplify】开始化简: {self}", level=1)
                debug_callback(f"分子类型: {type(self.numerator)}, 分母类型: {type(self.denominator)}", level=2)
                debug_callback(f"分子字符串: {self.numerator}", level=2)
                debug_callback(f"分母字符串: {self.denominator}", level=2)

            # 如果分子或分母包含根号，直接返回自身
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

            # 先简化分子和分母
            if hasattr(self.numerator, 'simplify'):
                simplified_num = self.numerator.simplify(debug_callback)
            else:
                simplified_num = self.numerator

            if hasattr(self.denominator, 'simplify'):
                simplified_den = self.denominator.simplify(debug_callback)
            else:
                simplified_den = self.denominator

            # ========== 新增：处理分母中的负指数 ==========
            # 定义一个辅助函数检查是否存在负指数
            def has_neg_exp(expr):
                if isinstance(expr, AlgebraicExpression):
                    for term in expr.terms:
                        if isinstance(term, AlgebraicTerm):
                            for exp in term.vars.values():
                                if exp < 0:
                                    return True
                return False

            # 如果分母有负指数，尝试乘以因子消除负指数
            if has_neg_exp(simplified_den):
                if debug_callback:
                    debug_callback(f"分母 {simplified_den} 含有负指数，尝试消除", level=2)

                # 收集分母中所有负指数变量及其最小指数（最负的）
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
                    # 构造乘数因子：每个变量取 -min_exp 次幂
                    factor_dict = {var: -exp for var, exp in neg_vars.items()}
                    multiplier_term = AlgebraicTerm(Fraction(1, 1), factor_dict)
                    multiplier_expr = AlgebraicExpression([multiplier_term])

                    # 分子分母同时乘以该因子
                    new_num = (simplified_num * multiplier_expr).simplify(debug_callback)
                    new_den = (simplified_den * multiplier_expr).simplify(debug_callback)

                    if debug_callback:
                        debug_callback(f"乘以因子 {multiplier_expr} 后得到: {new_num}/{new_den}", level=3)

                    # 递归简化新的分式
                    new_frac = FractionExpression(new_num, new_den)
                    simplified_result = new_frac.simplify(debug_callback)
                    if hasattr(simplified_result, '_simplify_depth'):
                        del simplified_result._simplify_depth
                    return simplified_result
            # ========== 新增结束 ==========

            # 检查分子和分母是否相同
            num_str = str(simplified_num).replace(' ', '')
            den_str = str(simplified_den).replace(' ', '')

            if debug_callback:
                debug_callback(f"分子化简后: {num_str}", level=3)
                debug_callback(f"分母化简后: {den_str}", level=3)

            # 如果分子和分母相同，返回1
            if num_str == den_str:
                if debug_callback:
                    debug_callback(f"分子分母相同，约分为1", level=2)
                return AlgebraicExpression([AlgebraicTerm(Fraction(1, 1))])

            # 检查分子是否包含分母作为因子（简单情况）
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

                                return simplified_result
            except Exception as e:
                if debug_callback:
                    debug_callback(f"尝试约分时出错: {str(e)}", level=3)

            # 如果分母是1，返回分子
            if isinstance(simplified_den, AlgebraicExpression) and simplified_den.is_constant():
                const = simplified_den.terms[0].coeff
                if const == Fraction(1, 1):
                    if debug_callback:
                        debug_callback("分母为1，返回分子", level=2)
                    return simplified_num

            # 如果分子是0，返回0
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

            # 如果分母为1，直接返回分子
            if hasattr(simplified_den, 'is_constant') and simplified_den.is_constant():
                const = simplified_den.terms[0].coeff
                if const == Fraction(1, 1):
                    if debug_callback:
                        debug_callback("分母为1，返回分子", level=2)
                    return simplified_num

            if hasattr(result, '_simplify_depth'):
                del result._simplify_depth

            return result
        except AttributeError as e:
            if debug_callback:
                debug_callback(f"在 FractionExpression.simplify 中捕获 AttributeError: {e}，返回原分式", level=1)
            return self

class AlgebraicCalculator:
    def __init__(self):
        # 原有初始化代码（如果有其他属性，请保留）
        self._parse_cache = {}  # 新增：解析结果缓存，键为预处理后的表达式字符串

    def parse_expression(self, expr, debug_callback=None):
        """
        解析表达式字符串，返回 AlgebraicExpression 对象。
        引入缓存避免重复解析相同表达式（仅在无调试回调时启用缓存）。
        """
        if debug_callback:
            debug_callback(f"开始解析表达式: {expr}", level=1)

        # ========== 预处理步骤（确定性的转换） ==========
        processed_expr = expr.replace(' ', '').replace('**', '^')

        import re
        # 将 (something)^(1/2) 或 (something)^1/2 转换为 √(something)
        pattern = r'\(([^)]+)\)\^\(?1/2\)?'
        while True:
            match = re.search(pattern, processed_expr)
            if not match:
                break
            full_match = match.group(0)
            inner_expr = match.group(1)
            if debug_callback:
                debug_callback(f"将 {full_match} 转换为 √({inner_expr})", level=3)
            processed_expr = processed_expr.replace(full_match, f'√({inner_expr})', 1)

        no_paren_pattern = r'([a-zA-Z0-9*\^]+)\^\(?1/2\)?'
        processed_expr = re.sub(no_paren_pattern, r'√(\1)', processed_expr)

        # 处理绝对值函数 abs(...)
        processed_expr = self._handle_absolute_value(processed_expr, debug_callback)
        # 处理平方根函数 sqrt(...)
        processed_expr = self._handle_sqrt_function(processed_expr, debug_callback)
        # 插入隐式乘法
        processed_expr = self._insert_implicit_multiplication(processed_expr, debug_callback)

        if debug_callback:
            debug_callback(f"处理根号后: {processed_expr}", level=3)

        processed_expr = self._insert_implicit_multiplication(processed_expr, debug_callback)

        if debug_callback:
            debug_callback(f"插入隐式乘法后: {processed_expr}", level=3)

        # ========== 缓存处理 ==========
        # 当有调试回调时，为了完整输出调试信息，不启用缓存
        if debug_callback is None:
            cache_key = processed_expr
            if cache_key in self._parse_cache:
                import copy
                cached_result = self._parse_cache[cache_key]
                # 深拷贝返回，避免后续修改污染缓存
                result = copy.deepcopy(cached_result)
                if debug_callback:  # 实际上此时 debug_callback 为 None，但为代码完整性保留
                    debug_callback(f"缓存命中，返回缓存的解析结果", level=3)
                return result

        # 解析预处理后的表达式
        result = self._parse_expr(processed_expr, debug_callback)

        # 存入缓存（同样仅在无调试回调时）
        if debug_callback is None:
            import copy
            self._parse_cache[cache_key] = copy.deepcopy(result)
            # 限制缓存大小，避免无限增长
            if len(self._parse_cache) > 100:
                # 移除最早的一项（简单策略）
                self._parse_cache.pop(next(iter(self._parse_cache)))

        return result

    def _auto_parenthesize_sqrt(self, expr_str, debug_callback=None):
        if debug_callback:
            debug_callback(f"自动为根号添加括号，原始表达式: {expr_str}", level=3)

        result = []
        i = 0
        n = len(expr_str)

        while i < n:
            char = expr_str[i]
            result.append(char)

            if char == '√':
                if i + 1 < n and expr_str[i + 1] != '(':
                    j = i + 1
                    bracket_count = 0
                    in_abs = False
                    abs_depth = 0

                    while j < n:
                        next_char = expr_str[j]

                        if next_char == '|':
                            if in_abs:
                                abs_depth -= 1
                                if abs_depth == 0:
                                    in_abs = False
                            else:
                                in_abs = True
                                abs_depth = 1

                        if not in_abs:
                            if next_char == '(':
                                bracket_count += 1
                            elif next_char == ')':
                                bracket_count -= 1
                                if bracket_count < 0:
                                    break

                        if bracket_count == 0 and not in_abs:
                            if next_char in '+-' and j > 0:
                                prev_char = expr_str[j - 1]
                                if not (next_char == '-' and prev_char in '(+-*/^'):
                                    break

                        j += 1

                    if j > i + 1:
                        result.append('(')

                        for k in range(i + 1, j):
                            result.append(expr_str[k])

                        result.append(')')

                        i = j - 1

                        if debug_callback:
                            debug_callback(f"为根号添加括号: √{expr_str[i + 1:j]} -> √({expr_str[i + 1:j]})", level=3)

            i += 1

        new_expr = ''.join(result)

        if debug_callback:
            debug_callback(f"自动添加括号后表达式: {new_expr}", level=3)

        return new_expr

    def _insert_implicit_multiplication(self, expr, debug_callback=None):
        if not expr:
            return expr

        result = []
        i = 0
        n = len(expr)

        # 标记是否在除法后面
        after_division = False
        # 括号深度
        bracket_depth = 0

        while i < n:
            c = expr[i]
            result.append(c)

            # 更新括号深度
            if c == '(':
                bracket_depth += 1
            elif c == ')':
                bracket_depth -= 1

            # 遇到除法符号时标记
            if c == '/' and bracket_depth == 0:
                after_division = True
            # 重置除法标记
            elif after_division and bracket_depth == 0 and c in '+-*/^':
                after_division = False

            # 检查是否需要插入乘号
            if i + 1 < n:
                next_c = expr[i + 1]

                # 除法后面（且括号深度为0）时不插入任何隐式乘号
                if after_division and bracket_depth == 0:
                    pass
                # 仅当当前字符是英文字母（ASCII）时才考虑插入乘号
                elif c.isalpha() and c.isascii():
                    if next_c.isalpha() and next_c.isascii():
                        result.append('*')
                    elif next_c.isdigit():
                        result.append('*')
                    elif next_c == '√':
                        result.append('*')
                # 数字后面跟英文字母或括号时插入乘号
                elif c.isdigit():
                    if next_c == '(' or (next_c.isalpha() and next_c.isascii()):
                        if i > 0 and expr[i - 1] == '/':
                            pass
                        else:
                            result.append('*')
                    elif next_c == '√':
                        result.append('*')
                # 英文字母后面跟括号，排除函数名
                elif c.isalpha() and c.isascii() and next_c == '(':
                    func_start = i
                    while func_start > 0 and expr[func_start - 1].isalpha():
                        func_start -= 1
                    func_name = expr[func_start:i + 1]
                    if func_name not in ['abs', 'sqrt']:
                        result.append('*')
                # 右括号后面跟左括号、数字或英文字母
                elif c == ')':
                    if next_c == '(' or next_c.isdigit() or (next_c.isalpha() and next_c.isascii()):
                        if next_c == '(' or (i + 1 < n and expr[i + 1] != '^'):
                            result.append('*')
                    elif next_c == '√':
                        result.append('*')

            i += 1

        return ''.join(result)

    def _parse_expr(self, expr, debug_callback=None):
        if debug_callback:
            debug_callback(f"解析表达式: {expr}", level=2)

        expr = self._handle_absolute_value(expr, debug_callback)
        expr = self._handle_sqrt_function(expr, debug_callback)
        expr = self._handle_parentheses(expr, debug_callback)

        if debug_callback:
            debug_callback(f"处理括号后: {expr}", level=3)

        if not expr:
            return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])

        bracket_count = 0
        plus_minus_positions = []

        for i, char in enumerate(expr):
            if char == '(':
                bracket_count += 1
            elif char == ')':
                bracket_count -= 1
            elif bracket_count == 0 and char in '+-' and (i == 0 or expr[i - 1] not in '*/^'):
                plus_minus_positions.append((i, char))

        if plus_minus_positions:
            if debug_callback:
                debug_callback(f"表达式包含顶层加减法，调用 _parse_add_sub", level=3)
            return self._parse_add_sub(expr, debug_callback)
        else:
            if debug_callback:
                debug_callback(f"表达式不包含顶层加减法，直接当作项处理", level=3)
            return self._parse_term(expr, debug_callback)

    def _handle_absolute_value(self, expr, debug_callback=None):
        if debug_callback:
            debug_callback(f"处理绝对值函数: {expr}", level=3)

        import re
        result = expr
        while 'abs(' in result:
            start = result.find('abs(')
            if start == -1:
                break

            bracket_count = 0
            i = start + 3

            while i < len(result):
                if result[i] == '(':
                    bracket_count += 1
                elif result[i] == ')':
                    bracket_count -= 1
                    if bracket_count == 0:
                        break
                i += 1

            if i >= len(result):
                break

            inner_start = start + 4
            inner_expr = result[inner_start:i]

            if debug_callback:
                debug_callback(f"找到绝对值函数: abs({inner_expr})", level=3)

            inner_result = self._parse_expr(inner_expr, debug_callback)
            abs_expr = f"|{inner_expr}|"
            result = result[:start] + abs_expr + result[i + 1:]

            if debug_callback:
                debug_callback(f"替换后表达式: {result}", level=3)

        return result

    def _handle_parentheses(self, expr, debug_callback=None):
        if debug_callback:
            debug_callback(f"处理括号: {expr}", level=3)

        # 检查括号匹配
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

        if '(' not in expr:
            return expr

        result = []
        i = 0
        n = len(expr)

        while i < n:
            if expr[i] == '(':
                # 找到匹配的右括号
                count = 1
                j = i + 1
                while j < n and count > 0:
                    if expr[j] == '(':
                        count += 1
                    elif expr[j] == ')':
                        count -= 1
                    j += 1
                if count > 0:
                    raise ValueError(f"括号不匹配: 位置 {i} 处的左括号未闭合")

                inner_expr = expr[i + 1:j - 1]  # 括号内的原始内容
                is_after_sqrt = (i > 0 and expr[i - 1] == '√')

                # 检查括号后面是否有指数 ^
                has_exponent = (j < n and expr[j] == '^')

                if has_exponent:
                    # 处理括号后的指数
                    exp_start = j + 1
                    # 指数可能是数字、变量或括号表达式
                    if exp_start < n and expr[exp_start] == '(':
                        # 指数是括号表达式，如 ^(1/2)
                        exp_count = 1
                        k = exp_start + 1
                        while k < n and exp_count > 0:
                            if expr[k] == '(':
                                exp_count += 1
                            elif expr[k] == ')':
                                exp_count -= 1
                            k += 1
                        if exp_count > 0:
                            raise ValueError("指数括号不匹配")
                        exp_str = expr[exp_start:k]  # 包含括号，如 "(1/2)"
                        # 递归处理指数内部的括号（可能还有嵌套）
                        exp_processed = self._handle_parentheses(exp_str, debug_callback)
                        # 递归处理括号内部表达式（可能含有运算符）
                        inner_processed = self._handle_parentheses(inner_expr, debug_callback)
                        inner_result = self._parse_expr(inner_processed, debug_callback)
                        inner_str = str(inner_result)
                        # 确保内部表达式在指数前用括号包裹
                        result.append(f"({inner_str})^{exp_processed}")
                        i = k  # 跳过整个指数部分
                    else:
                        # 指数是数字/变量（如 ^2 或 ^x）
                        k = exp_start
                        while k < n and (expr[k].isalnum() or expr[k] == '.'):
                            k += 1
                        exp_str = expr[exp_start:k]
                        # 递归处理括号内部表达式
                        inner_processed = self._handle_parentheses(inner_expr, debug_callback)
                        inner_result = self._parse_expr(inner_processed, debug_callback)
                        inner_str = str(inner_result)
                        result.append(f"({inner_str})^{exp_str}")
                        i = k  # 跳过指数部分
                else:
                    # 没有指数，按原有逻辑处理括号
                    if debug_callback:
                        debug_callback(
                            f"处理括号对: 位置 {i}-{j - 1}, 内部表达式: {inner_expr}, 在根号后: {is_after_sqrt}",
                            level=3
                        )
                    if i > 0 and expr[i - 1] == '^':
                        # 括号前面是指数符号，保留括号结构
                        result.append(f"({inner_expr})")
                    elif is_after_sqrt:
                        # 根号后的括号，直接保留
                        result.append(f"({inner_expr})")
                    else:
                        # 普通括号，展开内部表达式
                        inner_processed = self._handle_parentheses(inner_expr, debug_callback)
                        inner_result = self._parse_expr(inner_processed, debug_callback)
                        inner_str = str(inner_result)
                        # 修改点：只检查加减运算符，不再检查乘除和幂
                        if any(op in inner_str for op in '+-'):  # 只检查加减运算符
                            result.append(f"({inner_str})")
                        else:
                            result.append(inner_str)
                    i = j
            else:
                # 非括号字符直接添加
                result.append(expr[i])
                i += 1

        final_expr = ''.join(result)
        if debug_callback:
            debug_callback(f"括号处理后最终表达式: {final_expr}", level=3)
        return final_expr

    def _parse_add_sub(self, expr, debug_callback=None):
        if debug_callback:
            debug_callback(f"解析加减法表达式: {expr}", level=2)

        if not expr:
            return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])

        terms = []
        current = ''
        sign = 1

        i = 0
        bracket_count = 0
        abs_count = 0

        while i < len(expr):
            char = expr[i]

            if char == '(':
                bracket_count += 1
                current += char
            elif char == ')':
                bracket_count -= 1
                current += char
            elif char == '|':
                abs_count = 1 - abs_count
                current += char
            elif bracket_count == 0 and abs_count == 0:
                if char == '+' and (i == 0 or expr[i - 1] not in '*/^'):
                    if current:
                        term_expr = self._parse_term(current, debug_callback)
                        if sign == -1:
                            term_expr = term_expr * Fraction(-1, 1)
                        terms.extend(term_expr.terms)
                    current = ''
                    sign = 1
                elif char == '-' and (i == 0 or expr[i - 1] not in '*/^'):
                    if current:
                        term_expr = self._parse_term(current, debug_callback)
                        if sign == -1:
                            term_expr = term_expr * Fraction(-1, 1)
                        terms.extend(term_expr.terms)
                    current = ''
                    sign = -1
                else:
                    current += char
            else:
                current += char

            i += 1

        if current:
            term_expr = self._parse_term(current, debug_callback)
            if sign == -1:
                term_expr = term_expr * Fraction(-1, 1)
            terms.extend(term_expr.terms)

        expr_obj = AlgebraicExpression(terms)
        return expr_obj.simplify(debug_callback)

    def _parse_term(self, term_str, debug_callback=None):
        """
        解析项（由乘除连接的部分），返回 AlgebraicExpression 或 FractionExpression。
        采用左结合处理乘除。
        """
        if debug_callback:
            debug_callback(f"解析单项式: {term_str}", level=3)

        term_str = term_str.strip()
        if not term_str:
            return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])

        # 处理绝对值表达式作为一个整体
        if term_str.startswith('|') and term_str.endswith('|'):
            inner = term_str[1:-1]
            if debug_callback:
                debug_callback(f"解析绝对值表达式: |{inner}|", level=3)
            inner_expr = self._parse_expr(inner, debug_callback)
            return AlgebraicExpression([AbsoluteValue(inner_expr)])

        # 扫描不在括号和绝对值内的乘除操作符
        bracket_count = 0
        abs_count = 0
        operators = []  # 每个元素为 (position, operator_char)

        for i, char in enumerate(term_str):
            if char == '(':
                bracket_count += 1
            elif char == ')':
                bracket_count -= 1
            elif char == '|':
                abs_count = 1 - abs_count
            elif bracket_count == 0 and abs_count == 0:
                if char in '*/':
                    operators.append((i, char))

        if not operators:
            # 没有乘除操作符，作为单个因子处理
            return self._parse_factor(term_str, debug_callback)

        # 从左到右依次处理乘除
        # 第一个因子从开始到第一个操作符
        first_part = term_str[:operators[0][0]]
        result = self._parse_factor(first_part, debug_callback)

        for idx, (pos, op) in enumerate(operators):
            # 确定下一个因子的结束位置
            start = pos + 1
            end = operators[idx + 1][0] if idx + 1 < len(operators) else len(term_str)
            next_part = term_str[start:end]
            factor = self._parse_factor(next_part, debug_callback)

            if op == '*':
                result = result * factor
            else:  # '/'
                # 处理除法，如果除数是常数，直接进行除法运算
                if isinstance(factor, AlgebraicExpression) and factor.is_constant():
                    const = factor.terms[0].coeff
                    result = result / const
                else:
                    # 否则创建分式表达式
                    result = FractionExpression(result, factor)

        return result

    def _parse_factor(self, factor_str, debug_callback=None):
        if debug_callback:
            debug_callback(f"解析因子: {factor_str}", level=3)

        factor_str = factor_str.strip()

        if not factor_str:
            return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])

        # 处理负号
        if factor_str.startswith('-') and len(factor_str) > 1:
            inner = factor_str[1:]
            inner_expr = self._parse_factor(inner, debug_callback)
            return inner_expr * Fraction(-1, 1)

        # 处理根号
        if factor_str.startswith('√'):
            if len(factor_str) <= 1 or factor_str[1] != '(':
                raise ValueError("根号表达式必须写作 √(…) 的形式，例如 √(2x)")
            bracket_count = 1
            i = 2
            while i < len(factor_str) and bracket_count > 0:
                if factor_str[i] == '(':
                    bracket_count += 1
                elif factor_str[i] == ')':
                    bracket_count -= 1
                i += 1
            if bracket_count != 0:
                raise ValueError("根号括号不匹配")
            inner = factor_str[2:i - 1]
            if debug_callback:
                debug_callback(f"解析根号内部表达式: {inner}", level=3)
            inner_expr = self._parse_expr(inner, debug_callback)
            return AlgebraicExpression([SqrtExpression(inner_expr)])

        # 处理绝对值
        if factor_str.startswith('|') and factor_str.endswith('|'):
            inner = factor_str[1:-1]
            if debug_callback:
                debug_callback(f"解析绝对值因子: |{inner}|", level=3)
            inner_expr = self._parse_expr(inner, debug_callback)
            return AlgebraicExpression([AbsoluteValue(inner_expr)])

        # 处理纯数字
        if re.match(r'^[-+]?\d*\.?\d*(?:/\d*\.?\d*)?$', factor_str) and factor_str not in ['', '-', '+']:
            if factor_str.replace('-', '').replace('+', '').replace('.', '').replace('/', '').isdigit():
                if debug_callback:
                    debug_callback(f"解析数字: {factor_str}", level=3)
                try:
                    coeff = Fraction.from_string(factor_str)
                    return AlgebraicExpression([AlgebraicTerm(coeff)])
                except Exception as e:
                    if debug_callback:
                        debug_callback(f"解析数字失败: {str(e)}", level=3)

        # 处理单个变量（如 x, x^2）
        var_pattern = r'^[a-zA-Z](\^\d+)?$'
        if re.match(var_pattern, factor_str):
            if '^' in factor_str:
                var_name, exp_str = factor_str.split('^')
                exp = int(exp_str)
            else:
                var_name = factor_str
                exp = 1
            if debug_callback:
                debug_callback(f"解析变量: {var_name}^{exp}", level=3)
            vars_dict = {var_name: exp}
            return AlgebraicExpression([AlgebraicTerm(Fraction(1, 1), vars_dict)])

        # 处理带系数的单个变量，如 4x, 4x^2, 5/3x, -2x^2
        match = re.match(r'^([-+]?\d*\.?\d*/?\d*\.?\d*)([a-zA-Z](\^\d+)?)$', factor_str)
        if match:
            coeff_str = match.group(1)
            var_part = match.group(2)
            if not coeff_str or coeff_str in ['+', '-']:
                coeff_str += '1'
            try:
                coeff = Fraction.from_string(coeff_str)
                if debug_callback:
                    debug_callback(f"解析带系数变量: 系数={coeff_str} -> {coeff}, 变量部分={var_part}", level=3)
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
                    debug_callback(f"解析带系数变量失败: {str(e)}", level=3)

        # 新增分支：处理多个连续变量，如 4ac, 3/4xy, -2a^2b
        coeff_match = re.match(r'^([+-]?\d*\.?\d*(?:/\d*\.?\d*)?)([a-zA-Z](?:[a-zA-Z]|\^\d+)*)$', factor_str)
        if coeff_match:
            coeff_str = coeff_match.group(1)
            var_str = coeff_match.group(2)
            if not coeff_str or coeff_str in ['+', '-']:
                coeff = Fraction(1, 1)
                if coeff_str == '-':
                    coeff = Fraction(-1, 1)
            else:
                try:
                    coeff = Fraction.from_string(coeff_str)
                except Exception as e:
                    coeff = None
                    if debug_callback:
                        debug_callback(f"解析多个连续变量时系数解析失败: {e}", level=3)
            if coeff is not None:
                vars_dict = {}
                var_pattern = re.compile(r'([a-zA-Z])(?:\^(\d+))?')
                for var, exp_str in var_pattern.findall(var_str):
                    exp = int(exp_str) if exp_str else 1
                    vars_dict[var] = vars_dict.get(var, 0) + exp
                if vars_dict:
                    if debug_callback:
                        debug_callback(f"解析多个连续变量: 系数={coeff}, 变量={vars_dict}", level=3)
                    return AlgebraicExpression([AlgebraicTerm(coeff, vars_dict)])

        # 处理幂运算（从右向左找第一个不在括号内的 ^）
        bracket_count = 0
        for i in range(len(factor_str) - 1, -1, -1):
            char = factor_str[i]
            if char == ')':
                bracket_count += 1
            elif char == '(':
                bracket_count -= 1
            elif char == '^' and bracket_count == 0:
                base_str = factor_str[:i]
                exp_str = factor_str[i + 1:]
                if debug_callback:
                    debug_callback(f"处理幂运算: {base_str}^{exp_str}", level=3)
                base = self._parse_factor(base_str, debug_callback)
                clean_exp_str = exp_str.strip()
                if clean_exp_str in ['1/2', '(1/2)']:
                    if hasattr(base, 'simplify'):
                        base = base.simplify(debug_callback)
                    return AlgebraicExpression([SqrtExpression(base)])
                else:
                    try:
                        if clean_exp_str.startswith('(') and clean_exp_str.endswith(')'):
                            clean_exp_str = clean_exp_str[1:-1]
                        if '/' in clean_exp_str:
                            num_str, den_str = clean_exp_str.split('/')
                            num = int(num_str.strip())
                            den = int(den_str.strip())
                            if num == 1 and den == 2:
                                return AlgebraicExpression([SqrtExpression(base)])
                            elif den == 1:
                                return base ** num
                            else:
                                return AlgebraicExpression([
                                    AlgebraicTerm(Fraction(1, 1), {})
                                ])
                        else:
                            exp = int(clean_exp_str)
                            return base ** exp
                    except ValueError as e:
                        power_expr = f"{base_str}^{exp_str}"
                        return AlgebraicExpression([
                            AlgebraicTerm.from_string(power_expr) if power_expr else
                            AlgebraicTerm(Fraction(1, 1), {})
                        ])

        # 处理括号表达式
        if factor_str.startswith('(') and factor_str.endswith(')'):
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
                    debug_callback(f"解析括号表达式: {inner_expr}", level=3)
                if inner_expr.strip():
                    return self._parse_expr(inner_expr, debug_callback)
                else:
                    return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])

        # 最后尝试作为代数项解析
        try:
            term = AlgebraicTerm.from_string(factor_str)
            if debug_callback:
                debug_callback(f"成功解析为代数项: {term}", level=3)
            return AlgebraicExpression([term])
        except Exception as e:
            if debug_callback:
                debug_callback(f"解析为代数项失败: {str(e)}", level=3)

        # ========== 修复点：如果所有解析都失败，不再递归，而是抛出异常 ==========
        if debug_callback:
            debug_callback(f"无法解析因子: {factor_str}，抛出异常", level=3)
        raise ValueError(f"无法识别的表达式: {factor_str}")

    def simplify_expression(self, expr, debug_callback=None):
        try:
            if debug_callback:
                debug_callback(f"开始化简表达式: {expr}", level=1)

            # 新增：检测联立方程组（分号分隔）
            if ';' in expr:
                # 注意：solve_system 内部可能抛出异常，由外层统一处理
                return self.solve_system(expr, debug_callback=debug_callback)

            if '=' in expr:
                return self._solve_equation(expr, debug_callback)

            if debug_callback:
                debug_callback(f"开始化简表达式: {expr}", level=2)

            expr_obj = self.parse_expression(expr, debug_callback)

            if debug_callback:
                debug_callback(f"解析结果类型: {type(expr_obj)}", level=3)

            if hasattr(expr_obj, 'simplify'):
                simplified = expr_obj.simplify(debug_callback)
            else:
                simplified = expr_obj

            if isinstance(simplified, FractionExpression):
                if self._contains_sqrt(simplified.denominator):
                    if debug_callback:
                        debug_callback("检测到分母包含根号，进行有理化...", level=2)
                    rationalizer = DenominatorRationalizer()
                    simplified = rationalizer.rationalize(simplified, debug_callback)

                    if hasattr(simplified, 'simplify'):
                        simplified = simplified.simplify(debug_callback)

            result = str(simplified)

            if debug_callback:
                debug_callback(f"化简后结果: {result}", level=1)

            result = result.replace('+-', '-').replace('--', '+')
            result = result.replace('+0', '').replace('-0', '')
            result = result.replace('1*', '').replace('*1', '')

            if result.startswith('+'):
                result = result[1:]

            if not result or result == '':
                result = '0'

            if debug_callback:
                debug_callback(f"最终结果: {result}", level=2)

            return result
        except Exception as e:
            if debug_callback:
                import traceback
                debug_callback(f"错误: {str(e)}", level=1)
                debug_callback("详细堆栈信息:\n" + traceback.format_exc(), level=1)
            raise e

    def _solve_equation(self, equation, debug_callback=None):
        if debug_callback:
            debug_callback(f"开始解方程: {equation}", level=1)

        parts = equation.split('=')
        if len(parts) != 2:
            raise ValueError("无效的方程格式，应包含一个等号")

        left_str, right_str = parts[0].strip(), parts[1].strip()

        left_expr = self.parse_expression(left_str, debug_callback)
        right_expr = self.parse_expression(right_str, debug_callback)

        equation_expr = left_expr - right_expr

        simplified_eq = equation_expr.simplify(debug_callback)

        # ========== 处理分式方程 ==========
        if isinstance(simplified_eq, FractionExpression):
            numerator = simplified_eq.numerator
            denominator = simplified_eq.denominator

            while isinstance(numerator, FractionExpression):
                numerator = numerator.numerator
            if not isinstance(numerator, AlgebraicExpression):
                numerator = AlgebraicExpression([numerator])

            while isinstance(denominator, FractionExpression):
                denominator = denominator.numerator
            if not isinstance(denominator, AlgebraicExpression):
                denominator = AlgebraicExpression([denominator])

            vars_in_expr = set()
            for term in numerator.terms:
                if isinstance(term, AlgebraicTerm):
                    for var in term.vars:
                        vars_in_expr.add(var)
            for term in denominator.terms:
                if isinstance(term, AlgebraicTerm):
                    for var in term.vars:
                        vars_in_expr.add(var)

            if not vars_in_expr:
                num_const = numerator.simplify()
                if num_const.is_zero():
                    return "分式方程恒成立（需排除使分母为零的点）"
                else:
                    return "矛盾方程（无解）"

            if len(vars_in_expr) > 1:
                vars_in_numerator = set()
                for term in numerator.terms:
                    if isinstance(term, AlgebraicTerm):
                        for var in term.vars:
                            vars_in_numerator.add(var)

                if not vars_in_numerator:
                    num_const = numerator.simplify()
                    if num_const.is_zero():
                        return "分式方程恒成立（需排除使分母为零的点）"
                    else:
                        return "矛盾方程（无解）"

                solutions = []
                # MODIFIED: 定义特殊结果集合
                SPECIAL_SOLUTIONS = {"无实数解", "无解", "矛盾方程（无解）", "无穷多解", "恒等式（对任何值都成立）"}

                for var in sorted(vars_in_numerator):
                    sol_str = numerator.solve_for_variable(var, debug_callback)

                    if sol_str in ["无解", "矛盾方程（无解）"]:
                        return "无解"
                    elif sol_str == "无穷多解":
                        solutions.append(f"  {var} 为任意值（需排除使分母为零的点）")
                        continue

                    if "或" in sol_str:
                        raw_parts = [s.strip() for s in sol_str.split(" 或 ")]
                        simplified_parts = []
                        for p in raw_parts:
                            # MODIFIED: 跳过特殊结果字符串
                            if p in SPECIAL_SOLUTIONS:
                                simplified_parts.append(p)
                                continue
                            try:
                                p_expr = self.parse_expression(p)
                                simplified = self._simplify_rational(p_expr)
                                simplified_parts.append(str(simplified))
                            except Exception as e:
                                if debug_callback:
                                    debug_callback(f"化简解 {p} 时出错: {e}，保留原样", level=3)
                                simplified_parts.append(p)
                        sol_display = ' 或 '.join(simplified_parts)
                    else:
                        # MODIFIED: 跳过特殊结果字符串
                        if sol_str.strip() in SPECIAL_SOLUTIONS:
                            sol_display = sol_str.strip()
                        else:
                            try:
                                sol_expr = self.parse_expression(sol_str.strip())
                                simplified = self._simplify_rational(sol_expr)
                                sol_display = str(simplified)
                            except Exception as e:
                                if debug_callback:
                                    debug_callback(f"化简解 {sol_str} 时出错: {e}，保留原样", level=3)
                                sol_display = sol_str.strip()

                    solutions.append(f"  {var} = {sol_display}")

                if not solutions:
                    return "无解"
                solutions.sort()
                result_str = "多变量方程的解:\n" + "\n".join(solutions)
                return result_str

            var = list(vars_in_expr)[0]

            numerator_has_var = False
            for term in numerator.terms:
                if isinstance(term, AlgebraicTerm) and term.contains_var(var):
                    numerator_has_var = True
                    break

            if not numerator_has_var:
                num_const_expr = numerator.simplify()
                if num_const_expr.is_zero():
                    return "分式方程恒成立（需排除使分母为零的点）"
                else:
                    return "矛盾方程（无解）"

            min_exp = 0
            for term in numerator.terms:
                if isinstance(term, AlgebraicTerm) and var in term.vars:
                    exp = term.vars[var]
                    if exp < min_exp:
                        min_exp = exp
            if min_exp < 0:
                k = -min_exp
                if debug_callback:
                    debug_callback(f"分子含有负指数，乘以 {var}^{k} 化为多项式", level=2)
                multiplier = AlgebraicTerm(Fraction(1, 1), {var: k})
                numerator = (numerator * multiplier).simplify(debug_callback)

            sol_str = numerator.solve_for_variable(var, debug_callback)

            # MODIFIED: 定义特殊结果集合
            SPECIAL_SOLUTIONS = {"无实数解", "无解", "矛盾方程（无解）", "无穷多解", "恒等式（对任何值都成立）"}

            if "或" in sol_str:
                raw_solutions = [s.strip() for s in sol_str.split(" 或 ")]
            else:
                raw_solutions = [sol_str.strip()]

            simplified_solutions = []
            for sol in raw_solutions:
                # MODIFIED: 跳过特殊结果字符串
                if sol in SPECIAL_SOLUTIONS:
                    simplified_solutions.append(sol)
                    continue
                try:
                    sol_expr = self.parse_expression(sol)
                    simplified = self._simplify_rational(sol_expr)
                    simplified_solutions.append(str(simplified))
                except Exception as e:
                    if debug_callback:
                        debug_callback(f"化简解 {sol} 时出错: {e}，保留原样", level=3)
                    simplified_solutions.append(sol)
            raw_solutions = simplified_solutions

            valid_solutions = []
            for sol in raw_solutions:
                if not sol:
                    continue
                if self._check_denominator_zero(denominator, var, sol, debug_callback):
                    if debug_callback:
                        debug_callback(f"解 {sol} 使分母为零，舍去", level=2)
                else:
                    valid_solutions.append(sol)

            if not valid_solutions:
                return "无解"
            elif len(valid_solutions) == 1:
                return f"{var} = {valid_solutions[0]}"
            else:
                return f"{var} = {' 或 '.join(valid_solutions)}"

        # ========== 原有处理（非分式） ==========
        vars_in_expr = set()
        for term in simplified_eq.terms:
            if isinstance(term, AlgebraicTerm):
                for var in term.vars:
                    vars_in_expr.add(var)
            elif isinstance(term, AbsoluteValue):
                vars_in_expr.add('|')

        if not vars_in_expr:
            if simplified_eq.is_zero():
                return "恒等式（对任何值都成立）"
            else:
                return "矛盾方程（无解）"

        if '|' in vars_in_expr:
            result = "方程中包含绝对值表达式，需要分类讨论:\n\n"
            abs_terms = [term for term in simplified_eq.terms if isinstance(term, AbsoluteValue)]
            if abs_terms:
                for i, abs_term in enumerate(abs_terms):
                    result += f"情况 {i + 1}: {abs_term.expand_with_cases(debug_callback)}\n\n"
                result += "将上述情况分别代入原方程求解。"
            else:
                result = "方程化简后不包含绝对值项，请检查输入。"
            return result

        results = {}
        for var in sorted(vars_in_expr):
            try:
                solution = simplified_eq.solve_for_variable(var, debug_callback)
                results[var] = solution
            except Exception as e:
                results[var] = f"无法求解: {str(e)}"

        if len(results) == 1:
            var, solution = list(results.items())[0]
            if solution.startswith("目前不支持求解这类方程"):
                return solution.strip()
            if solution.replace(' ', '').endswith('=0'):
                return solution.strip()
            else:
                return f"{var} = {solution.strip()}"
        else:
            result_str = "多变量方程的解:\n"
            for var, solution in results.items():
                if solution.replace(' ', '').endswith('=0'):
                    result_str += f"  {solution.strip()}\n"
                else:
                    result_str += f"  {var} = {solution.strip()}\n"
            result_str = result_str.strip()
            return result_str

    def _solve_one_equation(self, expr, var, debug_callback=None):
        """
        求解单个方程 expr = 0 关于变量 var 的解。
        返回 AlgebraicExpression 列表（每个元素是一个解表达式），
        若无解返回空列表，若为恒等式返回 [AlgebraicExpression([AlgebraicTerm(1, {var:1})])] 表示变量自由。
        若方程无法求解，抛出 UnsolvableEquationError 异常。
        """
        simplified = expr.simplify(debug_callback)

        # 如果是分式表达式，转化为分子方程（递归求解）
        if isinstance(simplified, FractionExpression):
            numerator = simplified.numerator
            return self._solve_one_equation(numerator, var, debug_callback)

        if simplified.is_zero():
            # 恒等式，变量自由
            return [AlgebraicExpression([AlgebraicTerm(1, {var:1})])]

        # 调用现有的 solve_for_variable（返回字符串）
        sol_str = simplified.solve_for_variable(var, debug_callback)

        # 检测特定无法求解的提示（不再检测所有中文）
        if "目前不支持求解这类方程" in sol_str or "方程中包含绝对值表达式" in sol_str:
            raise self.UnsolvableEquationError(simplified)

        if sol_str in ("无解", "矛盾方程（无解）"):
            return []
        if sol_str == "无穷多解":
            # 当作变量自由处理
            return [AlgebraicExpression([AlgebraicTerm(1, {var:1})])]

        # 处理“或”分割
        if " 或 " in sol_str:
            parts = sol_str.split(" 或 ")
        else:
            parts = [sol_str]

        solutions = []
        for p in parts:
            p = p.strip()
            if not p:
                continue
            # 不再检查中文，直接尝试解析（多变量方程的解可能包含其他变量，是正常的）
            try:
                sol_expr = self.parse_expression(p, debug_callback)
                sol_expr = sol_expr.simplify(debug_callback)
                solutions.append(sol_expr)
            except Exception:
                pass
        return solutions

    def _eliminate(self, equations, variables, debug_callback=None):
        """
        递归消元求解方程组。
        equations: list of AlgebraicExpression，每个表示方程=0
        variables: list of str，待求解的变量列表
        返回 list of dict，每个 dict 映射变量名 -> AlgebraicExpression（解表达式）
        若某个方程无法求解，抛出 UnsolvableEquationError。
        """
        if not equations:
            return [{}]
        if not variables:
            for eq in equations:
                if not eq.is_zero():
                    return []
            return [{}]

        if len(equations) == 1 and len(variables) == 1:
            var = variables[0]
            try:
                sols = self._solve_one_equation(equations[0], var, debug_callback)
            except self.UnsolvableEquationError as e:
                raise e
            result = []
            for sol in sols:
                if isinstance(sol, AlgebraicExpression) and len(sol.terms) == 1:
                    term = sol.terms[0]
                    if isinstance(term, AlgebraicTerm) and term.vars == {var: 1} and term.coeff == Fraction(1, 1):
                        result.append({var: AlgebraicExpression([AlgebraicTerm(1, {var:1})])})
                    else:
                        result.append({var: sol})
                else:
                    result.append({var: sol})
            return result

        var = variables[0]
        eq = equations[0].simplify(debug_callback)

        if eq.is_zero():
            # 第一个方程为恒等式，跳过它，继续求解剩余方程（变量列表不变）
            sub_solutions = self._eliminate(equations[1:], variables, debug_callback)
            full_solutions = []
            for sub in sub_solutions:
                full = {var: AlgebraicExpression([AlgebraicTerm(1, {var:1})])}
                full.update(sub)
                full_solutions.append(full)
            return full_solutions

        try:
            sols_for_var = self._solve_one_equation(eq, var, debug_callback)
        except self.UnsolvableEquationError as e:
            raise e

        if not sols_for_var:
            return []

        result = []
        for sol_expr in sols_for_var:
            new_equations = []
            for i in range(1, len(equations)):
                new_eq = equations[i].substitute(var, sol_expr, debug_callback)
                new_equations.append(new_eq.simplify(debug_callback))
            try:
                sub_solutions = self._eliminate(new_equations, variables[1:], debug_callback)
            except self.UnsolvableEquationError as e:
                raise e
            for sub in sub_solutions:
                full = {var: sol_expr}
                full.update(sub)
                result.append(full)
        return result

    def _substitute_solution(self, sol_dict, debug_callback=None):
        sol = sol_dict.copy()
        changed = True
        max_iter = 100
        iter_count = 0
        while changed and iter_count < max_iter:
            iter_count += 1
            changed = False
            for var, expr in list(sol.items()):
                if isinstance(expr, AlgebraicExpression) and len(expr.terms) == 1:
                    term = expr.terms[0]
                    if isinstance(term, AlgebraicTerm) and term.vars == {var: 1} and term.coeff == Fraction(1, 1):
                        continue
                new_expr = expr
                for other_var, other_expr in sol.items():
                    if other_var != var:
                        new_expr = new_expr.substitute(other_var, other_expr, debug_callback)
                # 使用字符串比较，避免对象不同导致的误判
                if str(new_expr) != str(expr):
                    sol[var] = new_expr
                    changed = True
        if debug_callback and iter_count >= max_iter:
            debug_callback(f"Warning: _substitute_solution reached max iterations for {sol_dict}", level=1)

        for var, expr in sol.items():
            if hasattr(expr, 'simplify'):
                sol[var] = expr.simplify(debug_callback)
        return sol

    def solve_system(self, equations_str, solve_vars=None, debug_callback=None):
        """
        求解联立方程组。
        equations_str: 用分号分隔的方程字符串，如 "x+y=5; x-y=1"
        solve_vars: 可选，指定要解的变量列表（用于欠定方程组）
        返回格式化后的结果字符串。
        """
        eq_strings = [e.strip() for e in equations_str.split(';') if e.strip()]
        if not eq_strings:
            return ""

        equations = []
        all_vars = set()
        for eq_str in eq_strings:
            if '=' not in eq_str:
                raise ValueError(f"方程 '{eq_str}' 不含等号")
            left, right = eq_str.split('=', 1)
            left_expr = self.parse_expression(left.strip(), debug_callback)
            right_expr = self.parse_expression(right.strip(), debug_callback)
            eq_expr = (left_expr - right_expr).simplify(debug_callback)
            equations.append(eq_expr)
            for term in eq_expr.terms:
                if isinstance(term, AlgebraicTerm):
                    all_vars.update(term.vars.keys())
        all_vars = sorted(all_vars)

        if solve_vars is None:
            solve_vars = all_vars
        else:
            solve_vars = [v for v in solve_vars if v in all_vars]

        try:
            solutions = self._eliminate(equations, solve_vars, debug_callback)
        except self.UnsolvableEquationError as e:
            # 无法求解，返回化简后的方程信息
            return f"无法求解，化简后的方程为：{e.equation}"

        if not solutions:
            return "无解"
        if len(solutions) == 1:
            sol = self._substitute_solution(solutions[0], debug_callback)
            return self._format_solution(sol, all_vars)
        else:
            sol_strs = []
            for sol in solutions:
                sol = self._substitute_solution(sol, debug_callback)
                sol_strs.append(self._format_solution(sol, all_vars))
            return " 或 ".join(sol_strs)

    def _format_solution(self, solution_dict, all_vars):
        """
        将单个解字典格式化为字符串，按变量字典序排列。
        solution_dict: {var: expr}
        all_vars: 所有变量列表（用于确定哪些是自由变量）
        """
        parts = []
        for var in sorted(solution_dict.keys()):
            expr = solution_dict[var]
            expr_str = str(expr)
            # 如果表达式就是变量自身，可简化显示（但保留原样）
            parts.append(f"{var} = {expr_str}")
        # 对于没有出现在解中的变量（自由参数），它们会出现在表达式中，不需要单独列出
        return ", ".join(parts)

    def _check_denominator_zero(self, den_expr, var, sol_str, debug_callback=None, depth=0):
        """检查解 sol_str 是否使分母 den_expr 为零，增加深度限制并捕获递归错误"""
        if depth > 5:
            if debug_callback:
                debug_callback(f"验根递归深度过大，假设解 {sol_str} 使分母不为零", level=2)
            return False

        import re
        den_str = str(den_expr)
        # 使用正则匹配独立的变量（前后不是字母）
        pattern = r'(?<![a-zA-Z])' + re.escape(var) + r'(?![a-zA-Z])'
        new_str = re.sub(pattern, f'({sol_str})', den_str)

        try:
            # 注意：避免递归调用 debug_callback 造成循环，传入 None
            result = self.simplify_expression(new_str, debug_callback=None)
            return result == '0'
        except RecursionError:
            if debug_callback:
                debug_callback(f"验根时递归出错，假设解 {sol_str} 使分母不为零", level=2)
            return False
        except Exception as e:
            if debug_callback:
                debug_callback(f"验根时出错: {e}", level=3)
            return False

    def _handle_sqrt_function(self, expr, debug_callback=None):
        if debug_callback:
            debug_callback(f"处理平方根函数: {expr}", level=3)

        import re

        result = expr
        while 'sqrt(' in result:
            start = result.find('sqrt(')
            if start == -1:
                break

            bracket_count = 0
            i = start + 4

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

            inner_start = start + 5
            inner_expr = result[inner_start:i]

            if debug_callback:
                debug_callback(f"找到平方根函数: sqrt({inner_expr})", level=3)

            inner_result = self._parse_expr(inner_expr, debug_callback)
            sqrt_expr = f"√({inner_expr})"
            result = result[:start] + sqrt_expr + result[i + 1:]

            if debug_callback:
                debug_callback(f"替换后表达式: {result}", level=3)

        return result

    def _contains_sqrt(self, expr):
        if isinstance(expr, SqrtExpression):
            return True
        elif isinstance(expr, AlgebraicExpression):
            for term in expr.terms:
                if isinstance(term, SqrtExpression):
                    return True
        return False

    def _simplify_rational(self, expr):
        """
        将表达式中的负指数消除，并化简分式为更简洁的形式。
        主要处理形如 (-1)/(-1+y^-1) → y/(y-1) 的情况。
        """
        if not isinstance(expr, FractionExpression):
            return expr

        numerator = expr.numerator
        denominator = expr.denominator

        # 辅助函数：检查表达式是否包含负指数
        def has_neg_exp(e):
            if isinstance(e, AlgebraicExpression):
                for term in e.terms:
                    if isinstance(term, AlgebraicTerm):
                        for exp in term.vars.values():
                            if exp < 0:
                                return True
            return False

        # 如果分母没有负指数，直接返回
        if not has_neg_exp(denominator):
            return expr

        # 收集分母中的所有负指数变量及其最小指数（最负的）
        neg_vars = {}
        for term in denominator.terms:
            if isinstance(term, AlgebraicTerm):
                for var, exp in term.vars.items():
                    if exp < 0:
                        if var in neg_vars:
                            neg_vars[var] = min(neg_vars[var], exp)
                        else:
                            neg_vars[var] = exp

        if not neg_vars:
            return expr

        # 构造乘数因子：每个变量取 -min_exp 次幂
        factor_dict = {var: -exp for var, exp in neg_vars.items()}
        multiplier_term = AlgebraicTerm(Fraction(1, 1), factor_dict)
        multiplier_expr = AlgebraicExpression([multiplier_term])

        # 分子分母同时乘以该因子
        new_num = (numerator * multiplier_expr).simplify()
        new_den = (denominator * multiplier_expr).simplify()

        # 构建新的分式
        new_frac = FractionExpression(new_num, new_den)

        # 进一步化简：处理分子分母中的符号，使分母中的变量项在前，且系数为正
        def is_preferred_form(frac):
            """判断分式是否更符合期望的形式：分母以变量字母开头"""
            den_str = str(frac.denominator)
            # 去掉外层括号
            if den_str.startswith('(') and den_str.endswith(')'):
                den_str = den_str[1:-1]
            # 检查第一个字符是否为字母
            return den_str and den_str[0].isalpha()

        # 尝试翻转符号
        if isinstance(new_num, AlgebraicExpression) and len(new_num.terms) == 1:
            num_term = new_num.terms[0]
            if isinstance(num_term, AlgebraicTerm) and num_term.coeff.numerator < 0:
                if isinstance(new_den, AlgebraicExpression):
                    neg_one = AlgebraicTerm(Fraction(-1, 1))
                    neg_expr = AlgebraicExpression([neg_one])
                    new_num2 = (new_num * neg_expr).simplify()
                    new_den2 = (new_den * neg_expr).simplify()
                    new_frac2 = FractionExpression(new_num2, new_den2)
                    # 优先选择更标准的形式
                    if is_preferred_form(new_frac2) and not is_preferred_form(new_frac):
                        new_frac = new_frac2
                    elif not is_preferred_form(new_frac2) and is_preferred_form(new_frac):
                        pass  # 保留原形式
                    else:
                        # 如果两者一样标准，选长度短的
                        if len(str(new_frac2)) < len(str(new_frac)):
                            new_frac = new_frac2

        return new_frac.simplify()


    class UnsolvableEquationError(Exception):
        def __init__(self, equation):
            self.equation = equation
            super().__init__(f"无法求解方程，已化简为：{equation}")

class DenominatorRationalizer:
    @staticmethod
    def rationalize(fraction_expr, debug_callback=None):
        numerator = fraction_expr.numerator
        denominator = fraction_expr.denominator

        if debug_callback:
            debug_callback(f"开始分母有理化: {numerator} / {denominator}", level=1)
            debug_callback(f"分子类型: {type(numerator)}, 分母类型: {type(denominator)}", level=3)

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