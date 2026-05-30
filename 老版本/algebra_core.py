import re
import math
from collections import defaultdict


class Fraction:
    """分数类，用于精确表示有理数"""

    def __init__(self, numerator=0, denominator=1):
        self.numerator = numerator
        self.denominator = denominator
        self.normalize()

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
        elif not isinstance(other, Fraction):
            raise TypeError("只能与分数或整数相乘")

        new_numerator = self.numerator * other.numerator
        new_denominator = self.denominator * other.denominator
        return Fraction(new_numerator, new_denominator)

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


class AlgebraicExpression:
    """表示代数表达式，如 2x + 3y - 5"""

    def __init__(self, terms=None):
        self.terms = terms if terms is not None else []

    def simplify(self):
        """化简表达式"""
        if not self.terms:
            return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])

        # 合并同类项
        term_dict = {}
        for term in self.terms:
            # 创建变量的元组作为键
            var_key = tuple(sorted(term.vars.items()))
            if var_key in term_dict:
                term_dict[var_key] = term_dict[var_key] + term
            else:
                term_dict[var_key] = term

        # 移除系数为0的项
        simplified_terms = [term for term in term_dict.values() if term.coeff.numerator != 0]

        # 如果没有项，返回0
        if not simplified_terms:
            simplified_terms = [AlgebraicTerm(Fraction(0, 1))]

        return AlgebraicExpression(simplified_terms)

    def __add__(self, other):
        if isinstance(other, (int, Fraction)):
            other = AlgebraicExpression([AlgebraicTerm(Fraction(other, 1))])
        elif isinstance(other, AlgebraicTerm):
            other = AlgebraicExpression([other])
        elif not isinstance(other, AlgebraicExpression):
            return NotImplemented

        new_terms = self.terms + other.terms
        return AlgebraicExpression(new_terms).simplify()

    def __sub__(self, other):
        if isinstance(other, (int, Fraction)):
            other = AlgebraicExpression([AlgebraicTerm(Fraction(other, 1))])
        elif isinstance(other, AlgebraicTerm):
            other = AlgebraicExpression([other])
        elif not isinstance(other, AlgebraicExpression):
            return NotImplemented

        # 将other的所有项取负
        neg_terms = []
        for term in other.terms:
            if term.coeff.numerator == 0:
                continue
            neg_terms.append(term * Fraction(-1, 1))

        new_terms = self.terms + neg_terms
        return AlgebraicExpression(new_terms).simplify()

    def __mul__(self, other):
        if isinstance(other, (int, Fraction)):
            new_terms = [term * other for term in self.terms]
            return AlgebraicExpression(new_terms).simplify()
        elif isinstance(other, AlgebraicTerm):
            new_terms = [term * other for term in self.terms]
            return AlgebraicExpression(new_terms).simplify()
        elif isinstance(other, AlgebraicExpression):
            new_terms = []
            for t1 in self.terms:
                for t2 in other.terms:
                    new_terms.append(t1 * t2)
            return AlgebraicExpression(new_terms).simplify()
        return NotImplemented

    def __truediv__(self, other):
        if isinstance(other, (int, Fraction)):
            new_terms = [term / other for term in self.terms]
            return AlgebraicExpression(new_terms).simplify()
        elif isinstance(other, AlgebraicTerm):
            new_terms = [term / other for term in self.terms]
            return AlgebraicExpression(new_terms).simplify()
        elif isinstance(other, AlgebraicExpression):
            # 对于表达式除以表达式，只有当分母是常数时才处理
            if len(other.terms) == 1 and other.terms[0].is_constant():
                const = other.terms[0].coeff
                new_terms = [term / const for term in self.terms]
                return AlgebraicExpression(new_terms).simplify()
            else:
                # 其他情况返回分式形式
                return FractionExpression(self, other)
        return NotImplemented

    def __pow__(self, exp):
        if not isinstance(exp, int):
            raise TypeError("指数必须是整数")

        if exp == 0:
            return AlgebraicExpression([AlgebraicTerm(Fraction(1, 1))])

        result = self
        for _ in range(exp - 1):
            result = result * self
        return result.simplify()

    def __str__(self):
        if not self.terms:
            return "0"

        terms_str = []
        for i, term in enumerate(self.terms):
            term_str = str(term)
            if term_str == "0":
                continue

            if i == 0:
                terms_str.append(term_str)
            else:
                # 检查系数是否为负
                if term.coeff.numerator < 0:
                    neg_term = term * Fraction(-1, 1)
                    terms_str.append(f" - {str(neg_term)}")
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
        return len(self.terms) == 1 and self.terms[0].is_constant()


class FractionExpression:
    """表示分式表达式，如 (x+y)/(a+b)"""

    def __init__(self, numerator, denominator):
        self.numerator = numerator
        self.denominator = denominator

    def __str__(self):
        num_str = str(self.numerator)
        den_str = str(self.denominator)

        # 如果分子或分母包含运算符，需要加括号
        if any(op in num_str for op in '+-'):
            num_str = f"({num_str})"
        if any(op in den_str for op in '+-'):
            den_str = f"({den_str})"

        return f"{num_str}/{den_str}"


class AlgebraicCalculator:
    def __init__(self):
        pass

    def parse_expression(self, expr):
        """解析代数表达式"""
        expr = expr.replace(' ', '').replace('**', '^')
        # 插入隐式乘法符号
        expr = self._insert_implicit_multiplication(expr)
        # 将表达式转换为代数表达式对象
        return self._parse_expr(expr)

    def _insert_implicit_multiplication(self, expr):
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

                # 情况1: 数字后面跟着括号或变量
                if c.isdigit() and (next_c == '(' or next_c.isalpha()):
                    result.append('*')

                # 情况2: 变量后面跟着括号
                elif c.isalpha() and next_c == '(':
                    result.append('*')

                # 情况3: 括号后面跟着括号、数字或变量
                elif c == ')' and (next_c == '(' or next_c.isdigit() or next_c.isalpha()):
                    result.append('*')

                # 情况4: 数字后面跟着分数形式的系数
                elif c.isdigit() and next_c == '/':
                    # 检查是否形如 "2/3x" 或 "2/3(x+y)"
                    j = i + 2
                    while j < n and (expr[j].isdigit() or expr[j] == '/'):
                        j += 1
                    if j < n and (expr[j] == '(' or expr[j].isalpha()):
                        # 在分数和后面的内容之间插入 *
                        result.append('*')

            i += 1

        return ''.join(result)

    def _parse_expr(self, expr):
        """解析表达式的主要函数"""
        # 处理括号
        expr = self._handle_parentheses(expr)
        # 处理加减法
        return self._parse_add_sub(expr)

    def _handle_parentheses(self, expr):
        """处理括号，递归解析内部表达式"""
        # 先找到所有括号对
        stack = []
        pairs = []
        for i, ch in enumerate(expr):
            if ch == '(':
                stack.append(i)
            elif ch == ')':
                if stack:
                    start = stack.pop()
                    pairs.append((start, i))

        # 如果没有括号，直接返回
        if not pairs:
            return expr

        # 从最内层开始处理括号
        pairs.sort(key=lambda x: x[1] - x[0])

        result = list(expr)
        for start, end in pairs:
            inner_expr = expr[start + 1:end]
            inner_result = self._parse_expr(inner_expr)
            inner_str = str(inner_result)

            # 如果内部结果包含加减号，需要加括号
            if any(op in inner_str for op in '+-'):
                result[start:end + 1] = f'({inner_str})'
            else:
                result[start:end + 1] = inner_str

        return ''.join(result)

    def _parse_add_sub(self, expr):
        """解析加减法表达式"""
        if not expr:
            return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])

        # 按+或-拆分，但要考虑负号和表达式中的符号
        terms = []
        current = ''
        sign = 1

        i = 0
        while i < len(expr):
            char = expr[i]

            if char == '+' and (i == 0 or expr[i - 1] not in '*/^'):
                if current:
                    term_expr = self._parse_term(current)
                    if sign == -1:
                        term_expr = term_expr * Fraction(-1, 1)
                    terms.extend(term_expr.terms)
                current = ''
                sign = 1
            elif char == '-' and (i == 0 or expr[i - 1] not in '*/^'):
                if current:
                    term_expr = self._parse_term(current)
                    if sign == -1:
                        term_expr = term_expr * Fraction(-1, 1)
                    terms.extend(term_expr.terms)
                current = ''
                sign = -1
            else:
                current += char

            i += 1

        if current:
            term_expr = self._parse_term(current)
            if sign == -1:
                term_expr = term_expr * Fraction(-1, 1)
            terms.extend(term_expr.terms)

        # 创建表达式并化简
        expr_obj = AlgebraicExpression(terms)
        return expr_obj.simplify()

    def _parse_term(self, term_str):
        """解析单项式，可能包含乘除法"""
        # 处理除法优先
        if '/' in term_str:
            parts = term_str.split('/')
            if len(parts) >= 2:
                result = self._parse_factor(parts[0])
                for part in parts[1:]:
                    denominator = self._parse_factor(part)
                    result = result / denominator
                return result

        # 按乘号拆分
        parts = term_str.split('*')

        if len(parts) == 1:
            # 没有乘法，直接解析
            return self._parse_factor(parts[0])

        # 处理乘法
        result = self._parse_factor(parts[0])
        for part in parts[1:]:
            result = result * self._parse_factor(part)

        return result

    def _parse_factor(self, factor_str):
        """解析因子：数字、变量、括号表达式、幂运算"""
        # 处理幂运算
        if '^' in factor_str:
            parts = factor_str.split('^')
            if len(parts) == 2:
                base = self._parse_factor(parts[0])
                try:
                    exp = int(parts[1])
                    return base ** exp
                except ValueError:
                    raise ValueError(f"无效的指数: {parts[1]}")

        # 处理数字
        if factor_str.replace('.', '').replace('-', '').isdigit() or \
                (factor_str.startswith('-') and factor_str[1:].replace('.', '').isdigit()):
            return AlgebraicExpression([AlgebraicTerm(Fraction.from_string(factor_str))])

        # 处理变量
        if factor_str.isalpha():
            vars_dict = {factor_str: 1}
            return AlgebraicExpression([AlgebraicTerm(Fraction(1, 1), vars_dict)])
        elif factor_str == '-x' or factor_str == '-y' or factor_str == '-z' or \
                factor_str == '-a' or factor_str == '-b' or factor_str == '-c':
            # 处理 -x, -y 等特殊情况
            var_name = factor_str[1:]
            vars_dict = {var_name: 1}
            return AlgebraicExpression([AlgebraicTerm(Fraction(-1, 1), vars_dict)])

        # 处理带系数的变量
        match = re.match(r'^([-+]?\d*\.?\d*/?\d*\.?\d*)([a-zA-Z].*)$', factor_str)
        if match:
            coeff_str = match.group(1)
            var_part = match.group(2)

            if not coeff_str or coeff_str == '+' or coeff_str == '-':
                coeff_str += '1'

            coeff = Fraction.from_string(coeff_str)

            # 解析变量部分
            vars_dict = {}
            var_matches = re.findall(r'([a-zA-Z])(?:\^(\d+))?', var_part)
            for var, exp_str in var_matches:
                exp = int(exp_str) if exp_str else 1
                vars_dict[var] = vars_dict.get(var, 0) + exp

            return AlgebraicExpression([AlgebraicTerm(coeff, vars_dict)])

        # 可能是括号表达式
        if factor_str.startswith('(') and factor_str.endswith(')'):
            inner_expr = factor_str[1:-1]
            # 检查内部是否为空
            if inner_expr.strip():
                return self._parse_expr(inner_expr)
            else:
                return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])

        # 尝试解析为代数项
        try:
            term = AlgebraicTerm.from_string(factor_str)
            return AlgebraicExpression([term])
        except:
            # 默认情况
            return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])

    def simplify_expression(self, expr):
        """化简表达式的主要接口"""
        try:
            expr_obj = self.parse_expression(expr)
            # 检查是否为FractionExpression
            if isinstance(expr_obj, FractionExpression):
                return str(expr_obj)

            simplified = expr_obj.splify()
            result = str(simplified)

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

            return result
        except Exception as e:
            raise e  # 重新抛出异常，让GUI处理

# GUI将导入此模块，不需要独立的main函数