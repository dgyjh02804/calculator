import math
from algebra_base import Fraction
from algebra_expression import (
    AlgebraicTerm, AbsoluteValue, SqrtExpression,
    TermWithSqrt, AlgebraicExpression, FractionExpression,
    DenominatorRationalizer
)


class UnsolvableEquationError(Exception):
    """当方程无法求解时抛出的异常"""
    def __init__(self, equation):
        self.equation = equation
        super().__init__(f"无法求解方程，已化简为：{equation}")


def solve_equation(expr, var, debug_callback=None):
    """
    求解方程 expr = 0 关于变量 var 的解。
    返回解字符串（可能包含多个解，用“或”分隔）。
    """
    if debug_callback:
        debug_callback(f"开始求解变量 {var}: {expr} = 0", level=1)
        debug_callback(f"方程项数: {len(expr.terms)}", level=3)

    if expr.contains_absolute_value():
        if debug_callback:
            debug_callback(f"方程包含绝对值，无法直接求解", level=2)
        return f"目前不支持求解这类方程，已化简：{str(expr)}"

    coeffs = {}
    for term in expr.terms:
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
                if debug_callback:
                    debug_callback(f"遇到不支持的项类型: {type(term)}，无法求解", level=1)
                return f"目前不支持求解这类方程，已化简：{str(expr)}"
            else:
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
            return f"目前不支持求解这类方程，已化简：{str(expr)}"

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
            debug_callback(f"方程含有负指数，最小指数 {min_exp}，乘以 {var}^{ -min_exp} 化为多项式", level=2)
        k = -min_exp
        multiplier_term = AlgebraicTerm(Fraction(1, 1), {var: k})
        multiplier_expr = AlgebraicExpression([multiplier_term])
        new_expr = (expr * multiplier_expr).simplify(debug_callback)
        return solve_equation(new_expr, var, debug_callback)

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
        if hasattr(solution, 'canonicalize_sign'):
            solution = solution.canonicalize_sign()
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

        # 计算 -b 和 2a
        neg_b = (b * Fraction(-1, 1)).simplify(debug_callback)
        two_a = (a * Fraction(2, 1)).simplify(debug_callback)

        # 规范化分母的符号（避免分母为负）
        if two_a.is_constant() and two_a.terms[0].coeff.numerator < 0:
            neg_b = (neg_b * Fraction(-1, 1)).simplify(debug_callback)
            two_a = (two_a * Fraction(-1, 1)).simplify(debug_callback)

        # 处理判别式
        if delta.is_constant():
            delta_const = delta.terms[0].coeff
            if delta_const.numerator < 0:
                return "无实数解"
            if delta_const.denominator == 1:
                num = abs(delta_const.numerator)
                root = int(math.isqrt(num))
                if root * root == num:
                    # 完全平方数
                    sqrt_val = Fraction(root, 1) * (Fraction(1, 1) if delta_const.numerator >= 0 else Fraction(-1, 1))
                    # 构造解表达式
                    sol1 = (neg_b + AlgebraicExpression([AlgebraicTerm(sqrt_val)])) / two_a
                    sol2 = (neg_b - AlgebraicExpression([AlgebraicTerm(sqrt_val)])) / two_a
                    sol1 = sol1.simplify(debug_callback)
                    sol2 = sol2.simplify(debug_callback)
                    sol1_str = str(sol1).replace('+-', '-').replace('--', '+')
                    sol2_str = str(sol2).replace('+-', '-').replace('--', '+')
                    if sol1_str == sol2_str:
                        return sol1_str
                    else:
                        return f"{sol1_str} 或 {sol2_str}"

        # 判别式不是完全平方数，保留根号形式，直接返回字符串以避免内部简化错误
        neg_b_str = str(neg_b)
        delta_str = str(delta)
        two_a_str = str(two_a)
        # 简化字符串，去除可能的括号
        if neg_b_str.startswith('(') and neg_b_str.endswith(')'):
            neg_b_str = neg_b_str[1:-1]
        if two_a_str.startswith('(') and two_a_str.endswith(')'):
            two_a_str = two_a_str[1:-1]
        sol1_str = f"({neg_b_str}+√({delta_str}))/({two_a_str})"
        sol2_str = f"({neg_b_str}-√({delta_str}))/({two_a_str})"
        sol1_str = sol1_str.replace('+-', '-').replace('--', '+')
        sol2_str = sol2_str.replace('+-', '-').replace('--', '+')
        if sol1_str == sol2_str:
            return sol1_str
        else:
            return f"{sol1_str} 或 {sol2_str}"
    else:
        return f"目前不支持求解这类方程，已化简：{str(expr)}"


class AlgebraicCalculator:
    def __init__(self):
        self._parse_cache = {}

    def parse_expression(self, expr, debug_callback=None):
        if debug_callback:
            debug_callback(f"开始解析表达式: {expr}", level=1)
        processed_expr = expr.replace(' ', '').replace('**', '^')
        import re
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
        processed_expr = self._handle_absolute_value(processed_expr, debug_callback)
        processed_expr = self._handle_sqrt_function(processed_expr, debug_callback)
        processed_expr = self._insert_implicit_multiplication(processed_expr, debug_callback)
        if debug_callback:
            debug_callback(f"处理根号后: {processed_expr}", level=3)
        processed_expr = self._insert_implicit_multiplication(processed_expr, debug_callback)
        if debug_callback:
            debug_callback(f"插入隐式乘法后: {processed_expr}", level=3)
        if debug_callback is None:
            cache_key = processed_expr
            if cache_key in self._parse_cache:
                import copy
                cached_result = self._parse_cache[cache_key]
                if cached_result is None:
                    if debug_callback:
                        debug_callback(f"缓存中的结果为 None，重新解析", level=3)
                else:
                    result = copy.deepcopy(cached_result)
                    if debug_callback:
                        debug_callback(f"缓存命中，返回缓存的解析结果", level=3)
                    return result
        result = self._parse_expr(processed_expr, debug_callback)
        if result is None:
            if debug_callback:
                debug_callback(f"警告: _parse_expr('{processed_expr}') 返回 None，使用零表达式", level=1)
            result = AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])
        if debug_callback is None:
            import copy
            self._parse_cache[cache_key] = copy.deepcopy(result)
            if len(self._parse_cache) > 100:
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
        after_division = False
        bracket_depth = 0
        while i < n:
            c = expr[i]
            result.append(c)
            if c == '(':
                bracket_depth += 1
            elif c == ')':
                bracket_depth -= 1
            if c == '/' and bracket_depth == 0:
                after_division = True
            elif after_division and bracket_depth == 0 and c in '+-*/^':
                after_division = False
            if i + 1 < n:
                next_c = expr[i + 1]
                if after_division and bracket_depth == 0:
                    pass
                elif c.isalpha() and c.isascii():
                    if next_c.isalpha() and next_c.isascii():
                        result.append('*')
                    elif next_c.isdigit():
                        result.append('*')
                    elif next_c == '√':
                        result.append('*')
                elif c.isdigit():
                    if next_c == '(' or (next_c.isalpha() and next_c.isascii()):
                        if i > 0 and expr[i - 1] == '/':
                            pass
                        else:
                            result.append('*')
                    elif next_c == '√':
                        result.append('*')
                elif c.isalpha() and c.isascii() and next_c == '(':
                    func_start = i
                    while func_start > 0 and expr[func_start - 1].isalpha():
                        func_start -= 1
                    func_name = expr[func_start:i + 1]
                    if func_name not in ['abs', 'sqrt']:
                        result.append('*')
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
                inner_expr = expr[i + 1:j - 1]
                is_after_sqrt = (i > 0 and expr[i - 1] == '√')
                has_exponent = (j < n and expr[j] == '^')
                if has_exponent:
                    exp_start = j + 1
                    if exp_start < n and expr[exp_start] == '(':
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
                        exp_str = expr[exp_start:k]
                        exp_processed = self._handle_parentheses(exp_str, debug_callback)
                        inner_processed = self._handle_parentheses(inner_expr, debug_callback)
                        inner_result = self._parse_expr(inner_processed, debug_callback)
                        inner_str = str(inner_result)
                        result.append(f"({inner_str})^{exp_processed}")
                        i = k
                    else:
                        k = exp_start
                        while k < n and (expr[k].isalnum() or expr[k] == '.'):
                            k += 1
                        exp_str = expr[exp_start:k]
                        inner_processed = self._handle_parentheses(inner_expr, debug_callback)
                        inner_result = self._parse_expr(inner_processed, debug_callback)
                        inner_str = str(inner_result)
                        result.append(f"({inner_str})^{exp_str}")
                        i = k
                else:
                    if debug_callback:
                        debug_callback(
                            f"处理括号对: 位置 {i}-{j - 1}, 内部表达式: {inner_expr}, 在根号后: {is_after_sqrt}",
                            level=3
                        )
                    if i > 0 and expr[i - 1] == '^':
                        result.append(f"({inner_expr})")
                    elif is_after_sqrt:
                        result.append(f"({inner_expr})")
                    else:
                        inner_processed = self._handle_parentheses(inner_expr, debug_callback)
                        inner_result = self._parse_expr(inner_processed, debug_callback)
                        inner_str = str(inner_result)
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
                        if term_expr is None:
                            raise ValueError(f"解析项 '{current}' 失败，返回 None")
                        if sign == -1:
                            term_expr = term_expr * Fraction(-1, 1)
                        terms.extend(term_expr.terms)
                    current = ''
                    sign = 1
                elif char == '-' and (i == 0 or expr[i - 1] not in '*/^'):
                    if current:
                        term_expr = self._parse_term(current, debug_callback)
                        if term_expr is None:
                            raise ValueError(f"解析项 '{current}' 失败，返回 None")
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
            if term_expr is None:
                raise ValueError(f"解析项 '{current}' 失败，返回 None")
            if sign == -1:
                term_expr = term_expr * Fraction(-1, 1)
            terms.extend(term_expr.terms)
        expr_obj = AlgebraicExpression(terms)
        return expr_obj.simplify(debug_callback)

    def _parse_term(self, term_str, debug_callback=None):
        if debug_callback:
            debug_callback(f"解析单项式: {term_str}", level=3)
        term_str = term_str.strip()
        if not term_str:
            return AlgebraicExpression([AlgebraicTerm(Fraction(0, 1))])

        # 优先尝试将整个字符串解析为因子
        try:
            result = self._parse_factor(term_str, debug_callback)
            if result is not None:
                if isinstance(result, AlgebraicExpression) and len(result.terms) == 1:
                    if debug_callback:
                        debug_callback(f"整个字符串解析为单项式: {result}", level=3)
                    return result
                if not isinstance(result, AlgebraicExpression):
                    result = AlgebraicExpression([result])
                if debug_callback:
                    debug_callback(f"整个字符串解析为表达式: {result}", level=3)
                return result
        except Exception as e:
            if debug_callback:
                debug_callback(f"整体解析失败: {e}，继续按运算符拆分", level=3)
            pass

        # 查找顶层运算符
        bracket_count = 0
        abs_count = 0
        operators = []
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
            result = self._parse_factor(term_str, debug_callback)
            if result is None:
                raise ValueError(f"解析因子 '{term_str}' 失败，返回 None")
            if not isinstance(result, AlgebraicExpression):
                result = AlgebraicExpression([result])
            return result

        first_part = term_str[:operators[0][0]]
        result = self._parse_factor(first_part, debug_callback)
        if result is None:
            raise ValueError(f"解析因子 '{first_part}' 失败，返回 None")
        if not isinstance(result, AlgebraicExpression):
            result = AlgebraicExpression([result])

        for idx, (pos, op) in enumerate(operators):
            start = pos + 1
            end = operators[idx + 1][0] if idx + 1 < len(operators) else len(term_str)
            next_part = term_str[start:end]
            factor = self._parse_factor(next_part, debug_callback)
            if factor is None:
                raise ValueError(f"解析因子 '{next_part}' 失败，返回 None")
            if not isinstance(factor, AlgebraicExpression):
                factor = AlgebraicExpression([factor])

            if op == '*':
                result = result * factor
            else:  # 除法
                if factor.is_constant():
                    const = factor.terms[0].coeff
                    result = result / const
                else:
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

        # ========== 新增：处理隐式乘法，如 2x, 3xy^2 等 ==========
        import re
        coeff_var_pattern = r'^(\d+(?:/\d+)?)([a-zA-Z]+(?:\^\d+)?)$'
        match = re.match(coeff_var_pattern, factor_str)
        if match:
            coeff_str, var_part = match.groups()
            coeff = Fraction.from_string(coeff_str)
            # 解析变量部分（支持多个变量和指数）
            vars_dict = {}
            var_matches = re.findall(r'([a-zA-Z])(?:\^(\d+))?', var_part)
            for var, exp_str in var_matches:
                exp = int(exp_str) if exp_str else 1
                vars_dict[var] = vars_dict.get(var, 0) + exp
            term = AlgebraicTerm(coeff, vars_dict)
            if debug_callback:
                debug_callback(f"解析为系数乘变量: {term}", level=3)
            return AlgebraicExpression([term])
        # ========== 结束新增 ==========

        # 解析系数 + 根号形式
        import re
        # 匹配模式1: 括号系数√(内部) 例如 (1/2)√(2)
        match = re.match(r'^\(([^)]+)\)√\(([^)]+)\)$', factor_str)
        if match:
            coeff_part, inner_part = match.groups()
            try:
                coeff_expr = self._parse_expr(coeff_part, debug_callback)
                if hasattr(coeff_expr, 'is_constant') and coeff_expr.is_constant():
                    coeff = coeff_expr.terms[0].coeff
                    inner_expr = self._parse_expr(inner_part, debug_callback)
                    sqrt_expr = SqrtExpression(inner_expr)
                    term = TermWithSqrt(AlgebraicTerm(coeff), sqrt_expr)
                    return AlgebraicExpression([term])
            except Exception as e:
                if debug_callback:
                    debug_callback(f"解析括号系数根号失败: {e}", level=3)
                pass

        # 匹配模式2: 简单系数√(内部) 例如 2√(2) 或 -3√(5)
        match = re.match(r'^([+-]?\d*\.?\d*(?:/\d*\.?\d*)?)√\(([^)]+)\)$', factor_str)
        if match:
            coeff_str, inner_part = match.groups()
            if coeff_str and coeff_str not in ['+', '-']:
                try:
                    coeff = Fraction.from_string(coeff_str)
                except:
                    coeff = None
            else:
                coeff = Fraction(1, 1) if coeff_str != '-' else Fraction(-1, 1)
            if coeff is not None:
                inner_expr = self._parse_expr(inner_part, debug_callback)
                sqrt_expr = SqrtExpression(inner_expr)
                term = TermWithSqrt(AlgebraicTerm(coeff), sqrt_expr)
                return AlgebraicExpression([term])

        # 幂运算处理（从右向左扫描）
        bracket_count = 0
        for i in range(len(factor_str) - 1, -1, -1):
            char = factor_str[i]
            if char == ')':
                bracket_count += 1
            elif char == '(':
                bracket_count -= 1
            elif char == '^' and bracket_count == 0:
                try:
                    start, end = self._get_left_factor(factor_str, i)
                except ValueError as e:
                    if debug_callback:
                        debug_callback(f"获取底数失败: {e}", level=3)
                    continue
                base_str = factor_str[start:end]
                exp_str = factor_str[i + 1:]
                left_part = factor_str[:start]

                # 检查指数后面是否有 */ 运算符（不在括号内），这些应在 term 层级处理
                # 例如 x^2/4 应解析为 (x^2)/4 而非 x^(2/4)
                bkt = 0
                for j, c in enumerate(exp_str):
                    if c == '(':
                        bkt += 1
                    elif c == ')':
                        bkt -= 1
                    elif c in '*/' and bkt == 0:
                        raise ValueError(f"指数后存在运算符 '{c}'，需在term层级处理")

                if debug_callback:
                    debug_callback(f"处理幂运算: {base_str}^{exp_str}", level=3)
                base = self._parse_factor(base_str, debug_callback)
                clean_exp_str = exp_str.strip()
                if clean_exp_str in ['1/2', '(1/2)']:
                    if hasattr(base, 'simplify'):
                        base = base.simplify(debug_callback)
                    pow_expr = AlgebraicExpression([SqrtExpression(base)])
                else:
                    try:
                        if clean_exp_str.startswith('(') and clean_exp_str.endswith(')'):
                            clean_exp_str = clean_exp_str[1:-1]
                        if '/' in clean_exp_str:
                            num_str, den_str = clean_exp_str.split('/')
                            num = int(num_str.strip())
                            den = int(den_str.strip())
                            # 约分后判断是否等于 1/2 (sqrt)
                            frac = Fraction(num, den)
                            if frac.numerator == 1 and frac.denominator == 2:
                                pow_expr = AlgebraicExpression([SqrtExpression(base)])
                            elif frac.denominator == 1:
                                pow_expr = base ** frac.numerator
                            else:
                                pow_expr = AlgebraicExpression([AlgebraicTerm(Fraction(1, 1), {})])
                        else:
                            exp = int(clean_exp_str)
                            pow_expr = base ** exp
                    except ValueError as e:
                        power_expr = f"{base_str}^{exp_str}"
                        pow_expr = AlgebraicExpression([
                            AlgebraicTerm.from_string(power_expr) if power_expr else
                            AlgebraicTerm(Fraction(1, 1), {})
                        ])
                if left_part:
                    left_expr = self._parse_factor(left_part, debug_callback)
                    result = left_expr * pow_expr
                else:
                    result = pow_expr
                return result

        # 处理括号系数变量形式（如 (-1/2)a）
        match = re.match(r'^\(([^()]+)\)([a-zA-Z][a-zA-Z0-9\^]*)$', factor_str)
        if match:
            coeff_inner, var_part = match.groups()
            try:
                coeff_expr = self._parse_expr(coeff_inner, debug_callback)
                if hasattr(coeff_expr, 'is_constant') and coeff_expr.is_constant():
                    coeff = coeff_expr.terms[0].coeff
                    vars_dict = {}
                    var_matches = re.findall(r'([a-zA-Z])(?:\^(\d+))?', var_part)
                    for var, exp_str in var_matches:
                        exp = int(exp_str) if exp_str else 1
                        vars_dict[var] = vars_dict.get(var, 0) + exp
                    if vars_dict:
                        if debug_callback:
                            debug_callback(f"解析括号系数变量: 系数={coeff}, 变量={vars_dict}", level=3)
                        return AlgebraicExpression([AlgebraicTerm(coeff, vars_dict)])
            except Exception as e:
                if debug_callback:
                    debug_callback(f"尝试解析括号系数变量失败: {e}", level=3)

        # 处理最外层括号
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

        # 尝试解析为纯数字
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

        # 尝试解析为单个变量
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

        # 最后尝试使用 AlgebraicTerm.from_string
        # 但如果字符串包含括号或运算符（不在简单系数/变量范匹配内），
        # 说明应该由更上层（_parse_term / _parse_add_sub）拆分处理
        import re as _re
        _has_paren = '(' in factor_str or ')' in factor_str
        _has_top_op = bool(_re.search(r'(?<!\^)[+\-*/]', _re.sub(r'^[+-]', '', factor_str)))
        if _has_paren or _has_top_op:
            raise ValueError(f"表达式包含括号或运算符，需在上层处理: {factor_str}")
        try:
            term = AlgebraicTerm.from_string(factor_str)
            if debug_callback:
                debug_callback(f"成功解析为代数项: {term}", level=3)
            return AlgebraicExpression([term])
        except Exception as e:
            if debug_callback:
                debug_callback(f"解析为代数项失败: {str(e)}", level=3)

        raise ValueError(f"无法识别的表达式: {factor_str}")

    def simplify_expression(self, expr, debug_callback=None):
        try:
            if debug_callback:
                debug_callback(f"开始化简表达式: {expr}", level=1)
            if ';' in expr:
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

    def factor_expression(self, expr, debug_callback=None):
        """因式分解表达式：先化简，再对结果进行因式分解"""
        try:
            if ';' in expr:
                raise ValueError("因式分解不支持方程组，请使用解方程功能")
            if '=' in expr:
                raise ValueError("因式分解不支持方程，请只输入表达式")

            if debug_callback:
                debug_callback(f"开始因式分解: {expr}", level=1)

            # 第一步：化简
            expr_obj = self.parse_expression(expr, debug_callback)
            if hasattr(expr_obj, 'simplify'):
                simplified = expr_obj.simplify(debug_callback)
            else:
                simplified = expr_obj

            # 如果结果是分式且分母含根号，进行有理化
            if isinstance(simplified, FractionExpression) and self._contains_sqrt(simplified.denominator):
                from algebra_expression import DenominatorRationalizer
                rationalizer = DenominatorRationalizer()
                simplified = rationalizer.rationalize(simplified, debug_callback)
                if hasattr(simplified, 'simplify'):
                    simplified = simplified.simplify(debug_callback)

            # 第二步：转为 sympy 格式进行因式分解
            simplified_str = str(simplified).replace('+-', '-').replace('--', '+')
            sp_expr_str = self._to_sympy_string(simplified_str)

            import sympy as sp
            sp_expr = sp.sympify(sp_expr_str)
            factored = sp.factor(sp_expr)
            result = str(factored)

            # 将 sympy 格式转回计算器格式
            result = result.replace('**', '^')
            result = result.replace('sqrt', '√')
            result = result.replace('*', '')
            result = result.replace(' ', '')  # 去掉空格

            if debug_callback:
                debug_callback(f"因式分解结果: {result}", level=1)
            return result
        except ValueError:
            raise
        except Exception as e:
            if debug_callback:
                import traceback
                debug_callback(f"因式分解出错: {str(e)}", level=1)
                debug_callback("详细堆栈信息:\n" + traceback.format_exc(), level=1)
            return f"因式分解失败: {str(e)}"

    def _to_sympy_string(self, s):
        """将计算器格式的表达式字符串转为 sympy 可识别的格式"""
        import re
        s = s.replace(' ', '')
        sqrt_char = '√'
        while sqrt_char + '(' in s:
            s = re.sub(sqrt_char + r'\(([^()]+)\)', r'sqrt(\1)', s)
        # ^ → **
        s = s.replace('^', '**')
        # 隐式乘法：数字后跟字母 → 数字*字母
        s = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', s)
        # 数字后跟 ( → 数字*(
        s = re.sub(r'(\d)\(', r'\1*(', s)
        # )后跟数字或字母 → )*X
        s = re.sub(r'\)(\d)', r')*\1', s)
        s = re.sub(r'\)([a-zA-Z])', r')*\1', s)
        # 字母之间隐式乘法：仅在非 sqrt 的字母间插入 *
        # 方法：找到所有连续字母块，如果块不是 "sqrt"，则插入 *
        def _insert_letter_mul(s):
            result = []
            i = 0
            while i < len(s):
                if s[i:i+4] == 'sqrt':
                    result.append('sqrt')
                    i += 4
                elif s[i].isalpha():
                    start = i
                    while i < len(s) and s[i].isalpha():
                        i += 1
                    block = s[start:i]
                    if block != 'sqrt':
                        result.append('*'.join(block))
                    else:
                        result.append(block)
                else:
                    result.append(s[i])
                    i += 1
            return ''.join(result)
        s = _insert_letter_mul(s)
        return s

    def _collect_variables(self, expr):
        """递归收集表达式中的所有变量名"""
        vars_set = set()
        if isinstance(expr, AlgebraicExpression):
            for term in expr.terms:
                vars_set.update(self._collect_variables(term))
        elif isinstance(expr, FractionExpression):
            vars_set.update(self._collect_variables(expr.numerator))
            vars_set.update(self._collect_variables(expr.denominator))
        elif isinstance(expr, AlgebraicTerm):
            vars_set.update(expr.vars.keys())
        elif isinstance(expr, SqrtExpression):
            vars_set.update(self._collect_variables(expr.inner_expr))
        elif isinstance(expr, TermWithSqrt):
            vars_set.update(self._collect_variables(expr.coeff))
            vars_set.update(self._collect_variables(expr.sqrt_expr))
        elif isinstance(expr, AbsoluteValue):
            vars_set.update(self._collect_variables(expr.inner_expr))
        return vars_set

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
            # 收集所有变量（使用递归方法）
            vars_in_expr = self._collect_variables(numerator) | self._collect_variables(denominator)
            if not vars_in_expr:
                num_const = numerator.simplify()
                if num_const.is_zero():
                    return "分式方程恒成立（需排除使分母为零的点）"
                else:
                    return "矛盾方程（无解）"
            if len(vars_in_expr) > 1:
                vars_in_numerator = self._collect_variables(numerator)
                if not vars_in_numerator:
                    num_const = numerator.simplify()
                    if num_const.is_zero():
                        return "分式方程恒成立（需排除使分母为零的点）"
                    else:
                        return "矛盾方程（无解）"
                solutions = []
                SPECIAL_SOLUTIONS = {"无实数解", "无解", "矛盾方程（无解）", "无穷多解", "恒等式（对任何值都成立）"}
                for var in sorted(vars_in_numerator):
                    sol_str = solve_equation(numerator, var, debug_callback)
                    if sol_str in ["无解", "矛盾方程（无解）"]:
                        return "无解"
                    elif sol_str == "无穷多解":
                        solutions.append(f"  {var} 为任意值（需排除使分母为零的点）")
                        continue
                    if "或" in sol_str:
                        raw_parts = [s.strip() for s in sol_str.split(" 或 ")]
                        simplified_parts = []
                        for p in raw_parts:
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
            numerator_has_var = self._expr_contains_var(numerator, var)
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
            sol_str = solve_equation(numerator, var, debug_callback)
            SPECIAL_SOLUTIONS = {"无实数解", "无解", "矛盾方程（无解）", "无穷多解", "恒等式（对任何值都成立）"}
            if "或" in sol_str:
                raw_solutions = [s.strip() for s in sol_str.split(" 或 ")]
            else:
                raw_solutions = [sol_str.strip()]
            simplified_solutions = []
            for sol in raw_solutions:
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

        # 收集所有变量
        vars_in_expr = self._collect_variables(simplified_eq)

        # 检查是否包含绝对值
        if self.contains_abs(simplified_eq):
            if len(vars_in_expr) == 1:
                var = list(vars_in_expr)[0]
                try:
                    sol_list = self._solve_abs_equation(simplified_eq, var, debug_callback)
                    solution = self._format_solutions(var, sol_list)
                    results = {var: solution}
                except Exception as e:
                    results = {var: f"无法求解: {str(e)}"}
            else:
                # 多变量绝对值方程
                all_vars = sorted(vars_in_expr)
                try:
                    solutions_with_conds = self._solve_abs_multivar(simplified_eq, all_vars, debug_callback)
                    if not solutions_with_conds:
                        return "无解"
                    result_lines = []
                    for conds, sol_dict in solutions_with_conds:
                        # 构建条件字符串
                        cond_strs = []
                        for sign, inner_expr in conds:
                            inner_str = str(inner_expr)
                            if sign == '>=':
                                cond_strs.append(f"{inner_str} ≥ 0")
                            else:
                                cond_strs.append(f"{inner_str} < 0")
                        cond_part = " 且 ".join(cond_strs) if cond_strs else "无条件"

                        # 构建解字符串，尝试用其他变量表示自由变量
                        # 首先找出所有非平凡表达式（不是自身）
                        explicit = {}
                        for var in all_vars:
                            if var in sol_dict:
                                expr = sol_dict[var]
                                expr_str = str(expr)
                                # 判断是否为自由变量：表达式化简后等于自身？
                                # 简单判断：表达式字符串等于变量名，或者形如 "x"
                                if expr_str == var:
                                    continue
                                # 尝试化简看是否等于自身
                                try:
                                    if hasattr(expr, 'simplify'):
                                        simplified = expr.simplify()
                                        if str(simplified) == var:
                                            continue
                                except:
                                    pass
                                explicit[var] = expr

                        # 如果存在非平凡表达式，只输出它们；否则，输出所有变量（自由变量用自身表示）
                        if explicit:
                            sol_parts = []
                            for var in sorted(explicit.keys()):
                                expr = explicit[var]
                                expr_str = str(expr)
                                sol_parts.append(f"{var} = {expr_str}")
                            sol_part = ", ".join(sol_parts)
                        else:
                            # 所有变量都是自由的（无解？不应发生）
                            sol_part = ", ".join([f"{var} = {var}" for var in all_vars])

                        result_lines.append(f"当 {cond_part} 时，解为：{sol_part}")

                    # 去重
                    unique_lines = []
                    seen = set()
                    for line in result_lines:
                        if line not in seen:
                            seen.add(line)
                            unique_lines.append(line)
                    return "\n".join(unique_lines)
                except Exception as e:
                    if debug_callback:
                        import traceback
                        debug_callback(f"多变量绝对值求解出错: {e}\n{traceback.format_exc()}", level=1)
                    return f"多变量绝对值方程求解出错: {str(e)}"
        else:
            # 无绝对值，按原有逻辑求解（根式或常规）
            results = {}
            for var in sorted(vars_in_expr):
                try:
                    if self.contains_radical(simplified_eq):
                        sol_list = self._solve_radical_equation(simplified_eq, var, debug_callback)
                        solution = self._format_solutions(var, sol_list)
                    else:
                        solution = solve_equation(simplified_eq, var, debug_callback)
                    results[var] = solution
                except Exception as e:
                    results[var] = f"无法求解: {str(e)}"

        # 处理结果，确保 solution 为字符串
        if len(results) == 1:
            var, solution = list(results.items())[0]
            # 如果结果是特殊解字符串，直接返回
            SPECIAL_SOLUTIONS = {"无解", "无实数解", "矛盾方程（无解）", "无穷多解", "恒等式（对任何值都成立）"}
            sol_stripped = solution.strip()
            if sol_stripped in SPECIAL_SOLUTIONS:
                return sol_stripped
            # 如果 solution 已经以 "var = " 开头，则直接返回，避免重复
            if solution.strip().startswith(f"{var} ="):
                return solution.strip()
            if solution.startswith("目前不支持求解这类方程"):
                return solution.strip()
            if solution.replace(' ', '').endswith('=0'):
                return solution.strip()
            else:
                return f"{var} = {solution.strip()}"
        else:
            result_str = "多变量方程的解:\n"
            for var, solution in results.items():
                if not isinstance(solution, str):
                    solution = str(solution)
                if solution.replace(' ', '').endswith('=0'):
                    result_str += f"  {solution.strip()}\n"
                else:
                    result_str += f"  {var} = {solution.strip()}\n"
            result_str = result_str.strip()
            return result_str

    def _solve_one_equation(self, expr, var, debug_callback=None):
        # 如果表达式包含变量 var 相关的根号，调用根号求解器
        if self._expr_contains_var_radical(expr, var):
            return self._solve_radical_equation(expr, var, debug_callback)

        # 否则用常规方法求解（可包含常数根号）
        simplified = expr.simplify(debug_callback)
        if isinstance(simplified, FractionExpression):
            numerator = simplified.numerator
            return self._solve_one_equation(numerator, var, debug_callback)
        if simplified.is_zero():
            return [AlgebraicExpression([AlgebraicTerm(1, {var:1})])]
        sol_str = solve_equation(simplified, var, debug_callback)
        if "目前不支持求解这类方程" in sol_str or "方程中包含绝对值表达式" in sol_str:
            raise UnsolvableEquationError(simplified)
        if sol_str in ("无解", "矛盾方程（无解）"):
            return []
        if sol_str == "无穷多解":
            return [AlgebraicExpression([AlgebraicTerm(1, {var:1})])]
        if " 或 " in sol_str:
            parts = sol_str.split(" 或 ")
        else:
            parts = [sol_str]
        solutions = []
        for p in parts:
            p = p.strip()
            if not p:
                continue
            try:
                sol_expr = self.parse_expression(p, debug_callback)
                sol_expr = sol_expr.simplify(debug_callback)
                solutions.append(sol_expr)
            except Exception as e1:
                if debug_callback:
                    debug_callback(f"解析解 {p} 失败: {e1}，尝试作为单项式解析", level=3)
                try:
                    term = AlgebraicTerm.from_string(p)
                    sol_expr = AlgebraicExpression([term])
                    solutions.append(sol_expr)
                except Exception as e2:
                    if debug_callback:
                        debug_callback(f"单项式解析也失败: {e2}，忽略此解", level=3)
                    continue
        return solutions

    def _eliminate(self, equations, variables, debug_callback=None):
        """
        消元法求解方程组
        equations: 方程列表（已化为等于0的表达式）
        variables: 待求解的变量列表
        返回解字典的列表，每个字典形如 {var: 解表达式}
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
            except UnsolvableEquationError as e:
                raise e
            result = []
            for sol in sols:
                if isinstance(sol, AlgebraicExpression) and len(sol.terms) == 1:
                    term = sol.terms[0]
                    if isinstance(term, AlgebraicTerm) and term.vars == {var: 1} and term.coeff == Fraction(1, 1):
                        result.append({var: AlgebraicExpression([AlgebraicTerm(1, {var: 1})])})
                    else:
                        result.append({var: sol})
                else:
                    result.append({var: sol})
            return result

        var = variables[0]
        # 寻找包含 var 的方程，优先选择 var 次数最低的方程（线性优于二次）
        eq_index = -1
        best_degree = float('inf')
        for i, eq in enumerate(equations):
            # 计算该方程中 var 的最高次数
            max_deg = 0
            for term in eq.terms:
                if term.contains_var(var):
                    if isinstance(term, AlgebraicTerm):
                        deg = term.vars.get(var, 0)
                        max_deg = max(max_deg, deg)
                    else:
                        max_deg = max(max_deg, 1)  # TermWithSqrt 等视为1次
            if max_deg > 0 and max_deg < best_degree:
                best_degree = max_deg
                eq_index = i

        if eq_index == -1:
            # 没有方程包含 var，则 var 是自由变量
            sub_solutions = self._eliminate(equations, variables[1:], debug_callback)
            full_solutions = []
            for sub in sub_solutions:
                full = {var: AlgebraicExpression([AlgebraicTerm(1, {var: 1})])}  # 表示 var 本身
                full.update(sub)
                full_solutions.append(full)
            return full_solutions

        # 取出该方程，并从方程组中移除
        eq = equations[eq_index]
        remaining_equations = equations[:eq_index] + equations[eq_index + 1:]

        if debug_callback:
            debug_callback(f"【DEBUG】消元: 当前方程 {eq}，剩余方程 {len(remaining_equations)} 个", level=2)

        if eq.is_zero():
            # 方程恒成立，直接递归求解剩余变量
            sub_solutions = self._eliminate(remaining_equations, variables[1:], debug_callback)
            full_solutions = []
            for sub in sub_solutions:
                full = {var: AlgebraicExpression([AlgebraicTerm(1, {var: 1})])}
                full.update(sub)
                full_solutions.append(full)
            return full_solutions

        # ========== 新增：处理包含绝对值的方程 ==========
        if self.contains_abs(eq):
            if debug_callback:
                debug_callback(f"方程包含绝对值，使用多变量绝对值求解器", level=2)
            # 调用多变量绝对值求解器，返回分支解列表
            try:
                abs_solutions = self._solve_abs_multivar(eq, variables, debug_callback)
            except Exception as e:
                if debug_callback:
                    debug_callback(f"多变量绝对值求解出错: {e}，分支无解", level=2)
                return []

            if not abs_solutions:
                return []

            result = []
            for conditions, sol_dict in abs_solutions:
                if debug_callback:
                    debug_callback(f"处理绝对值分支: {sol_dict}", level=3)
                # 将当前解代入剩余方程
                new_remaining = []
                for other_eq in remaining_equations:
                    substituted = other_eq
                    for v, val in sol_dict.items():
                        substituted = substituted.substitute(v, val, debug_callback)
                    new_remaining.append(substituted.simplify(debug_callback))
                # 确定剩余变量：所有变量中除去已经在 sol_dict 中的
                remaining_vars = [v for v in variables if v not in sol_dict]
                # 对剩余变量递归求解
                try:
                    sub_solutions = self._eliminate(new_remaining, remaining_vars, debug_callback)
                except UnsolvableEquationError as e:
                    # 如果递归中遇到无法求解的方程，此分支无解
                    if debug_callback:
                        debug_callback(f"绝对值分支递归求解出错: {e}，舍弃", level=2)
                    continue
                for sub_sol in sub_solutions:
                    full_sol = sol_dict.copy()
                    full_sol.update(sub_sol)
                    result.append(full_sol)
            return result
        # ========== 结束新增 ==========

        try:
            sols_for_var = self._solve_one_equation(eq, var, debug_callback)
        except Exception as e:
            if debug_callback:
                debug_callback(f"解方程 {eq} 关于 {var} 时出错: {e}，分支无解", level=2)
            return []

        if debug_callback:
            debug_callback(f"【DEBUG】解 {var} 得到 {len(sols_for_var)} 个候选解: {[str(s) for s in sols_for_var]}",
                           level=2)

        if not sols_for_var:
            return []

        result = []
        for sol_expr in sols_for_var:
            new_equations = []
            for other_eq in remaining_equations:
                new_eq = other_eq.substitute(var, sol_expr, debug_callback)
                new_equations.append(new_eq.simplify(debug_callback))
            try:
                sub_solutions = self._eliminate(new_equations, variables[1:], debug_callback)
            except UnsolvableEquationError as e:
                raise e
            for sub in sub_solutions:
                full = {var: sol_expr}
                full.update(sub)
                result.append(full)
        return result

    def _substitute_solution(self, sol_dict, debug_callback=None):
        """将解字典中的表达式相互代入以简化，但避免不必要的化简"""
        sol = sol_dict.copy()
        changed = True
        max_iter = 100
        iter_count = 0
        while changed and iter_count < max_iter:
            iter_count += 1
            changed = False
            for var, expr in list(sol.items()):
                # 跳过形如 var = var 的恒等式
                if isinstance(expr, AlgebraicExpression) and len(expr.terms) == 1:
                    term = expr.terms[0]
                    if isinstance(term, AlgebraicTerm) and term.vars == {var: 1} and term.coeff == Fraction(1, 1):
                        continue
                new_expr = expr
                for other_var, other_expr in sol.items():
                    if other_var != var:
                        new_expr = new_expr.substitute(other_var, other_expr, debug_callback)
                if str(new_expr) != str(expr):
                    sol[var] = new_expr
                    changed = True
        if debug_callback and iter_count >= max_iter:
            debug_callback(f"Warning: _substitute_solution reached max iterations for {sol_dict}", level=1)
        # 移除不必要的简化，避免破坏分数系数
        # for var, expr in sol.items():
        #     if hasattr(expr, 'simplify'):
        #         sol[var] = expr.simplify(debug_callback)
        return sol

    def solve_system(self, equations_str, solve_vars=None, debug_callback=None):
        try:
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
                diff_expr = left_expr - right_expr
                if diff_expr is None:
                    raise ValueError(f"{left_expr} - {right_expr} 返回 None")
                eq_expr = diff_expr.simplify(debug_callback)
                if eq_expr is None:
                    raise ValueError(f"simplify 返回 None for {diff_expr}")
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
            except UnsolvableEquationError as e:
                return f"无法求解，化简后的方程为：{e.equation}"
            if not solutions:
                return "无解"

            # 验根过滤
            valid_solutions = []
            for sol_dict in solutions:
                is_valid = True
                for eq in equations:
                    substituted = eq
                    for var, val in sol_dict.items():
                        substituted = substituted.substitute(var, val, debug_callback)
                    substituted = substituted.simplify(debug_callback)
                    if self._is_zero(substituted):
                        continue
                    val_approx = self._approx_value(substituted)
                    if val_approx is not None and abs(val_approx) < 1e-10:
                        continue
                    remaining_vars = self._collect_variables(substituted)
                    if remaining_vars:
                        test_expr = substituted
                        for v in remaining_vars:
                            test_expr = test_expr.substitute(v, AlgebraicExpression([AlgebraicTerm(1)]), debug_callback)
                        test_expr = test_expr.simplify(debug_callback)
                        if self._is_zero(test_expr):
                            continue
                        val_approx2 = self._approx_value(test_expr)
                        if val_approx2 is not None and abs(val_approx2) < 1e-10:
                            continue
                    is_valid = False
                    break
                if is_valid:
                    valid_solutions.append(sol_dict)

            if not valid_solutions:
                return "无解"

            # 对每个解进行相互代入以简化表达式
            for i in range(len(valid_solutions)):
                valid_solutions[i] = self._substitute_solution(valid_solutions[i], debug_callback)

            if len(valid_solutions) == 1:
                sol = valid_solutions[0]
                # 只补充求解变量中缺失的自由变量
                for var in solve_vars:
                    if var not in sol:
                        sol[var] = AlgebraicExpression([AlgebraicTerm(1, {var: 1})])
                return self._format_solution(sol, solve_vars)
            else:
                sol_strs = []
                for sol in valid_solutions:
                    sol_strs.append(self._format_solution(sol, solve_vars))
                # 去重
                unique_strs = []
                seen = set()
                for s in sol_strs:
                    if s not in seen:
                        seen.add(s)
                        unique_strs.append(s)
                return " 或 ".join(unique_strs)
        except Exception as e:
            import traceback
            if debug_callback:
                debug_callback(f"solve_system 中发生异常: {e}", level=1)
                debug_callback(traceback.format_exc(), level=1)
            return f"方程组求解错误: {str(e)}"

    def _is_identity_expr(self, expr, var):
        """判断表达式是否就是该变量自身（系数1、次数1、无其他变量）"""
        if isinstance(expr, AlgebraicExpression) and len(expr.terms) == 1:
            term = expr.terms[0]
            if isinstance(term, AlgebraicTerm):
                return (term.coeff == Fraction(1, 1) and
                        term.vars == {var: 1})
        return False

    def _format_solution(self, solution_dict, solve_vars):
        parts = []
        for var in sorted(solve_vars):
            expr = solution_dict.get(var, AlgebraicExpression([AlgebraicTerm(1, {var: 1})]))
            # 跳过自由变量（表达式为 var = var 的恒等式）
            if self._is_identity_expr(expr, var):
                continue
            expr_str = str(expr)
            parts.append(f"{var} = {expr_str}")
        if not parts:
            return "任意解（所有变量均为自由变量）"
        return ", ".join(parts)

    def _check_denominator_zero(self, den_expr, var, sol_str, debug_callback=None, depth=0):
        if depth > 5:
            if debug_callback:
                debug_callback(f"验根递归深度过大，假设解 {sol_str} 使分母不为零", level=2)
            return False
        import re
        den_str = str(den_expr)
        pattern = r'(?<![a-zA-Z])' + re.escape(var) + r'(?![a-zA-Z])'
        new_str = re.sub(pattern, f'({sol_str})', den_str)
        try:
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
        if isinstance(expr, (SqrtExpression, TermWithSqrt)):
            return True
        elif isinstance(expr, AlgebraicExpression):
            for term in expr.terms:
                if isinstance(term, (SqrtExpression, TermWithSqrt)):
                    return True
        elif isinstance(expr, FractionExpression):
            return (self._contains_sqrt(expr.numerator) or
                    self._contains_sqrt(expr.denominator))
        return False

    def _simplify_rational(self, expr):
        if not isinstance(expr, FractionExpression):
            return expr
        numerator = expr.numerator
        denominator = expr.denominator
        def has_neg_exp(e):
            if isinstance(e, AlgebraicExpression):
                for term in e.terms:
                    if isinstance(term, AlgebraicTerm):
                        for exp in term.vars.values():
                            if exp < 0:
                                return True
            return False
        if not has_neg_exp(denominator):
            return expr
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
        factor_dict = {var: -exp for var, exp in neg_vars.items()}
        multiplier_term = AlgebraicTerm(Fraction(1, 1), factor_dict)
        multiplier_expr = AlgebraicExpression([multiplier_term])
        new_num = (numerator * multiplier_expr).simplify()
        new_den = (denominator * multiplier_expr).simplify()
        new_frac = FractionExpression(new_num, new_den)
        def is_preferred_form(frac):
            den_str = str(frac.denominator)
            if den_str.startswith('(') and den_str.endswith(')'):
                den_str = den_str[1:-1]
            return den_str and den_str[0].isalpha()
        if isinstance(new_num, AlgebraicExpression) and len(new_num.terms) == 1:
            num_term = new_num.terms[0]
            if isinstance(num_term, AlgebraicTerm) and num_term.coeff.numerator < 0:
                if isinstance(new_den, AlgebraicExpression):
                    neg_one = AlgebraicTerm(Fraction(-1, 1))
                    neg_expr = AlgebraicExpression([neg_one])
                    new_num2 = (new_num * neg_expr).simplify()
                    new_den2 = (new_den * neg_expr).simplify()
                    new_frac2 = FractionExpression(new_num2, new_den2)
                    if is_preferred_form(new_frac2) and not is_preferred_form(new_frac):
                        new_frac = new_frac2
                    elif not is_preferred_form(new_frac2) and is_preferred_form(new_frac):
                        pass
                    else:
                        if len(str(new_frac2)) < len(str(new_frac)):
                            new_frac = new_frac2
        return new_frac.simplify()

    def contains_radical(self, expr):
        """判断表达式是否包含根号（SqrtExpression 或 TermWithSqrt）"""
        if isinstance(expr, (SqrtExpression, TermWithSqrt)):
            return True
        if isinstance(expr, AlgebraicExpression):
            for term in expr.terms:
                if self.contains_radical(term):
                    return True
        if isinstance(expr, FractionExpression):
            return self.contains_radical(expr.numerator) or self.contains_radical(expr.denominator)
        return False

    def _is_radical_term(self, term):
        """判断一个项是否为根号项（SqrtExpression 或 TermWithSqrt）"""
        return isinstance(term, (SqrtExpression, TermWithSqrt))

    def _format_solutions(self, var, sol_list):
        """将解表达式列表格式化为字符串（如 x = 3 或 2）"""
        if not sol_list:
            return "无解"
        if len(sol_list) == 1:
            return f"{var} = {str(sol_list[0])}"
        else:
            sol_strs = [str(s) for s in sol_list]
            return f"{var} = {' 或 '.join(sol_strs)}"

    def _solve_radical_equation(self, expr, var, debug_callback=None, depth=0, seen=None):
        """
        递归求解含有根号的方程 expr = 0 关于变量 var
        返回解表达式列表（每个元素为 AlgebraicExpression）
        """
        MAX_DEPTH = 6
        if depth > MAX_DEPTH:
            if debug_callback:
                debug_callback(f"递归深度超限 ({MAX_DEPTH})，停止求解", level=2)
            return []

        if seen is None:
            seen = set()
        expr_str = str(expr)
        if expr_str in seen:
            if debug_callback:
                debug_callback(f"检测到重复表达式，停止递归", level=2)
            return []
        seen.add(expr_str)

        # 处理分式表达式：取分子
        if isinstance(expr, FractionExpression):
            numerator = expr.numerator
            if not self._expr_contains_var(numerator, var):
                return self._solve_one_equation(numerator, var, debug_callback)
            else:
                return self._solve_radical_equation(numerator, var, debug_callback, depth, seen)

        # 无根号则常规求解
        if not self.contains_radical(expr):
            return self._solve_one_equation(expr, var, debug_callback)

        # 分离根号项（仅包含变量 var 的根号）和其他项
        radical_terms = []
        other_terms = []
        for term in expr.terms:
            if self._is_radical_term(term) and self._term_contains_var(term, var):
                radical_terms.append(term)
            else:
                other_terms.append(term)

        if not radical_terms:
            return self._solve_one_equation(expr, var, debug_callback)

        # 选择第一个根号项孤立
        chosen = radical_terms[0]
        remaining_radicals = radical_terms[1:]
        right_expr = AlgebraicExpression(other_terms + remaining_radicals)

        # 情况1：右边为0
        if right_expr.is_zero():
            if isinstance(chosen, SqrtExpression):
                return self._solve_radical_equation(chosen.inner_expr, var, debug_callback, depth + 1, seen)
            elif isinstance(chosen, TermWithSqrt):
                coeff_expr = AlgebraicExpression([chosen.coeff])
                sol1 = self._solve_radical_equation(coeff_expr, var, debug_callback, depth + 1, seen)
                sqrt_expr = chosen.sqrt_expr
                sol2 = self._solve_radical_equation(sqrt_expr, var, debug_callback, depth + 1, seen)
                return sol1 + sol2
            else:
                return []

        # 情况2：一般形式，两边平方
        try:
            chosen_sq = (chosen * chosen).simplify(debug_callback)
            if debug_callback:
                debug_callback(f"【DEBUG】平方后的 chosen_sq = {chosen_sq}", level=2)
        except Exception as e:
            if debug_callback:
                debug_callback(f"平方 chosen 时出错: {e}", level=1)
            return []

        try:
            right_sq = (right_expr * right_expr).simplify(debug_callback)
            if debug_callback:
                debug_callback(f"【DEBUG】平方后的 right_sq = {right_sq}", level=2)
        except Exception as e:
            if debug_callback:
                debug_callback(f"平方 right_expr 时出错: {e}", level=1)
            return []

        if chosen_sq is None or right_sq is None:
            if debug_callback:
                debug_callback("错误：平方结果为空", level=1)
            return []

        try:
            new_expr = (chosen_sq - right_sq).simplify(debug_callback)
        except TypeError as e:
            if debug_callback:
                debug_callback(f"减法运算出错: {e}, chosen_sq={chosen_sq}, right_sq={right_sq}", level=1)
            return []

        # 递归求解
        candidates = self._solve_radical_equation(new_expr, var, debug_callback, depth + 1, seen)
        if candidates is None:
            candidates = []

        # ========== 增强的验根函数 ==========
        def _zero_after_squaring(e, max_depth=3):
            """递归平方判断表达式是否为零"""
            if max_depth <= 0:
                return False
            # 先尝试常规判断
            if hasattr(e, 'is_zero') and e.is_zero():
                return True
            if str(e).replace(' ', '') == '0':
                return True
            # 检查是否包含根号，若无则无法通过平方化简
            if not self.contains_radical(e):
                return False
            # 平方并递归
            try:
                squared = (e * e).simplify(debug_callback)
                if debug_callback:
                    debug_callback(f"递归平方 (深度 {max_depth}) 得到: {squared}", level=3)
                return _zero_after_squaring(squared, max_depth - 1)
            except Exception as ex:
                if debug_callback:
                    debug_callback(f"递归平方时出错: {ex}", level=3)
                return False

        # ========== 结束 ==========

        # 验根
        valid = []
        for sol in candidates:
            try:
                substituted = expr.substitute(var, sol, debug_callback).simplify(debug_callback)
                if debug_callback:
                    debug_callback(f"【DEBUG】代入解 {sol} 得到 {substituted}", level=2)

                is_zero = False
                if hasattr(substituted, 'is_zero') and substituted.is_zero():
                    is_zero = True
                elif str(substituted).replace(' ', '') == '0':
                    is_zero = True
                # 处理 FractionExpression：分式为零当且仅当分子为零
                elif isinstance(substituted, FractionExpression):
                    num_simplified = (substituted.numerator.simplify(debug_callback)
                                      if hasattr(substituted.numerator, 'simplify') else substituted.numerator)
                    if hasattr(num_simplified, 'is_zero') and num_simplified.is_zero():
                        is_zero = True
                    elif str(num_simplified).replace(' ', '') == '0':
                        is_zero = True
                    elif self.contains_radical(num_simplified):
                        if _zero_after_squaring(num_simplified):
                            is_zero = True
                else:
                    # 手动合并同类根式项
                    if isinstance(substituted, AlgebraicExpression):
                        sqrt_groups = {}
                        other_terms_list = []
                        for term in substituted.terms:
                            if isinstance(term, TermWithSqrt):
                                key = str(term.sqrt_expr)
                                sqrt_groups.setdefault(key, []).append(term)
                            else:
                                other_terms_list.append(term)
                        merged_sqrt_terms = []
                        for key, terms in sqrt_groups.items():
                            total_coeff = None
                            for t in terms:
                                if total_coeff is None:
                                    total_coeff = t.coeff
                                else:
                                    total_coeff = total_coeff + t.coeff
                            if total_coeff is not None and total_coeff.coeff.numerator != 0:
                                merged_sqrt_terms.append(TermWithSqrt(total_coeff, terms[0].sqrt_expr))
                        merged_expr = AlgebraicExpression(other_terms_list + merged_sqrt_terms)
                        if merged_expr.is_zero():
                            is_zero = True
                        else:
                            squared = (merged_expr * merged_expr).simplify(debug_callback)
                            if squared.is_zero():
                                try:
                                    test_expr = merged_expr
                                    all_vars = self._collect_variables(test_expr)
                                    if all_vars:
                                        for v in all_vars:
                                            test_expr = test_expr.substitute(v, AlgebraicExpression([AlgebraicTerm(1)]),
                                                                             debug_callback)
                                        test_val_expr = test_expr.simplify(debug_callback)
                                        if hasattr(test_val_expr, 'to_float'):
                                            if abs(test_val_expr.to_float()) < 1e-10:
                                                is_zero = True
                                        elif str(test_val_expr).replace(' ', '') == '0':
                                            is_zero = True
                                except:
                                    pass

                # ========== 新增递归平方判断 ==========
                if not is_zero:
                    if debug_callback:
                        debug_callback(f"尝试递归平方判断: {substituted}", level=2)
                    if _zero_after_squaring(substituted):
                        if debug_callback:
                            debug_callback(f"通过递归平方判断，解 {sol} 成立", level=2)
                        is_zero = True
                # ========== 结束 ==========

                if is_zero:
                    valid.append(sol)
            except Exception as e:
                if debug_callback:
                    debug_callback(f"验根时出错: {e}，舍弃解 {sol}", level=2)
        return valid

    def _term_contains_var(self, term, var):
        """判断一个项是否包含变量 var"""
        if isinstance(term, AlgebraicTerm):
            return var in term.vars
        elif isinstance(term, SqrtExpression):
            return self._expr_contains_var(term.inner_expr, var)
        elif isinstance(term, TermWithSqrt):
            return (self._term_contains_var(term.coeff, var) or
                    self._expr_contains_var(term.sqrt_expr, var))
        elif isinstance(term, AbsoluteValue):
            return self._expr_contains_var(term.inner_expr, var)
        return False

    def _expr_contains_var(self, expr, var):
        """判断表达式是否包含变量 var"""
        if isinstance(expr, AlgebraicExpression):
            for term in expr.terms:
                if self._term_contains_var(term, var):
                    return True
            return False
        elif isinstance(expr, (AlgebraicTerm, SqrtExpression, TermWithSqrt, AbsoluteValue)):
            return self._term_contains_var(expr, var)
        elif isinstance(expr, FractionExpression):
            return (self._expr_contains_var(expr.numerator, var) or
                    self._expr_contains_var(expr.denominator, var))
        else:
            return False

    def _term_contains_var_radical(self, term, var):
        """判断一个项是否包含根号，且根号内部包含变量 var"""
        if isinstance(term, AlgebraicTerm):
            return False
        elif isinstance(term, SqrtExpression):
            return self._expr_contains_var(term.inner_expr, var)
        elif isinstance(term, TermWithSqrt):
            return self._expr_contains_var(term.sqrt_expr, var) or self._term_contains_var_radical(term.coeff, var)
        elif isinstance(term, AbsoluteValue):
            return self._expr_contains_var_radical(term.inner_expr, var)
        return False

    def _expr_contains_var_radical(self, expr, var):
        """判断表达式是否包含根号，且该根号内部包含变量 var"""
        if isinstance(expr, AlgebraicExpression):
            for term in expr.terms:
                if self._term_contains_var_radical(term, var):
                    return True
            return False
        elif isinstance(expr, (AlgebraicTerm, SqrtExpression, TermWithSqrt, AbsoluteValue)):
            return self._term_contains_var_radical(expr, var)
        elif isinstance(expr, FractionExpression):
            return (self._expr_contains_var_radical(expr.numerator, var) or
                    self._expr_contains_var_radical(expr.denominator, var))
        else:
            return False

    def contains_abs(self, expr):
        """递归判断表达式是否包含绝对值项"""
        if isinstance(expr, AbsoluteValue):
            return True
        if isinstance(expr, AlgebraicExpression):
            for term in expr.terms:
                if self.contains_abs(term):
                    return True
        if isinstance(expr, FractionExpression):
            return self.contains_abs(expr.numerator) or self.contains_abs(expr.denominator)
        if isinstance(expr, TermWithSqrt):
            return self.contains_abs(expr.coeff) or self.contains_abs(expr.sqrt_expr)
        if isinstance(expr, SqrtExpression):
            return self.contains_abs(expr.inner_expr)
        return False

    def _is_zero(self, expr):
        """判断表达式是否为零（增强版，支持递归平方判断）"""
        if expr is None:
            return False

        # 递归平方判断辅助函数
        def _zero_after_squaring(e, max_depth=3):
            if max_depth <= 0:
                return False
            # 常规判断
            if hasattr(e, 'is_zero') and e.is_zero():
                return True
            s = str(e).replace(' ', '')
            if s == '0':
                return True
            if s.startswith('(') and s.endswith(')'):
                if s[1:-1] == '0':
                    return True
            # 如果不含根号，无法进一步简化
            if not self.contains_radical(e):
                return False
            # 尝试平方
            try:
                squared = (e * e).simplify()
                return _zero_after_squaring(squared, max_depth - 1)
            except Exception:
                return False

        # 优先使用对象的 is_zero 方法
        if hasattr(expr, 'is_zero') and expr.is_zero():
            return True
        # 检查数字零
        if isinstance(expr, (int, float)) and expr == 0:
            return True
        if isinstance(expr, Fraction) and expr.numerator == 0:
            return True
        # 检查字符串零
        try:
            s = str(expr).replace(' ', '')
            if s == '0':
                return True
            if s.startswith('(') and s.endswith(')'):
                if s[1:-1] == '0':
                    return True
        except:
            pass

        # 如果常规方法未判断为零，尝试递归平方
        if _zero_after_squaring(expr):
            return True

        return False

    def _solve_abs_equation(self, expr, var, debug_callback=None, depth=0, seen=None):
        """递归求解含绝对值的方程 expr = 0 关于变量 var，返回解表达式列表"""
        MAX_DEPTH = 10
        if depth > MAX_DEPTH:
            if debug_callback:
                debug_callback(f"绝对值方程递归深度超限 ({MAX_DEPTH})，停止求解", level=2)
            return []
        if seen is None:
            seen = set()
        expr_str = str(expr)
        if expr_str in seen:
            return []
        seen.add(expr_str)

        # 确保 expr 是 AlgebraicExpression 以便遍历 terms
        if not isinstance(expr, AlgebraicExpression):
            expr = AlgebraicExpression(expr)

        # 处理分式：取分子
        if isinstance(expr, FractionExpression):
            numerator = expr.numerator
            if not self._expr_contains_var(numerator, var):
                return self._solve_one_equation(numerator, var, debug_callback)
            else:
                return self._solve_abs_equation(numerator, var, debug_callback, depth, seen)

        # 如果没有绝对值项，直接调用常规求解
        if not self.contains_abs(expr):
            return self._solve_one_equation(expr, var, debug_callback)

        # 分离绝对值项（仅包含变量 var 的绝对值项）和其他项
        abs_terms = []
        other_terms = []
        for term in expr.terms:
            if isinstance(term, AbsoluteValue) and self._term_contains_var(term, var):
                abs_terms.append(term)
            else:
                other_terms.append(term)

        if not abs_terms:
            # 虽然有绝对值，但都不含变量 var，直接常规求解
            return self._solve_one_equation(expr, var, debug_callback)

        # 选择第一个绝对值项孤立
        chosen = abs_terms[0]
        rest = AlgebraicExpression(other_terms + abs_terms[1:])

        if debug_callback:
            debug_callback(f"【绝对值方程】孤立绝对值项: {chosen}，其余部分: {rest}", level=2)

        # 方程: chosen + rest = 0  => chosen = -rest
        inner = chosen.inner_expr
        # 情况1: inner ≥ 0 => chosen = inner，方程变为 inner + rest = 0
        eq1 = (inner + rest).simplify(debug_callback)
        # 情况2: inner < 0 => chosen = -inner，方程变为 -inner = -rest => inner = rest => inner - rest = 0
        eq2 = (inner - rest).simplify(debug_callback)

        if debug_callback:
            debug_callback(f"情况1 (inner≥0): {eq1} = 0", level=2)
            debug_callback(f"情况2 (inner<0): {eq2} = 0", level=2)

        # 递归求解
        sols1 = self._solve_abs_equation(eq1, var, debug_callback, depth + 1, seen.copy())
        sols2 = self._solve_abs_equation(eq2, var, debug_callback, depth + 1, seen.copy())

        # 合并候选解并去重
        candidates = sols1 + sols2
        unique = {}
        for sol in candidates:
            s_str = str(sol)
            if s_str not in unique:
                unique[s_str] = sol
        candidates = list(unique.values())

        def _zero_after_squaring(e, max_depth=3):
            if max_depth <= 0:
                return False
            # 先尝试常规判断
            if hasattr(e, 'is_zero') and e.is_zero():
                return True
            if str(e).replace(' ', '') == '0':
                return True
            # 检查是否包含根号，若无则无法通过平方化简
            if not self.contains_radical(e):
                return False
            # 平方并递归
            try:
                squared = (e * e).simplify(debug_callback)
                return _zero_after_squaring(squared, max_depth - 1)
            except Exception as ex:
                if debug_callback:
                    debug_callback(f"乘法出错: {ex}, e的类型: {type(e)}, e的内容: {e}", level=1)
                raise

        valid = []
        for sol in candidates:
            try:
                substituted = expr.substitute(var, sol, debug_callback).simplify(debug_callback)
                if debug_callback:
                    debug_callback(f"【DEBUG】代入解 {sol} 得到 {substituted}", level=2)

                is_zero = False
                if hasattr(substituted, 'is_zero') and substituted.is_zero():
                    is_zero = True
                elif str(substituted).replace(' ', '') == '0':
                    is_zero = True
                else:
                    # 手动合并同类根式项（原有逻辑，保持不变）
                    if isinstance(substituted, AlgebraicExpression):
                        sqrt_groups = {}
                        other_terms_list = []
                        for term in substituted.terms:
                            if isinstance(term, TermWithSqrt):
                                key = str(term.sqrt_expr)
                                sqrt_groups.setdefault(key, []).append(term)
                            else:
                                other_terms_list.append(term)
                        merged_sqrt_terms = []
                        for key, terms in sqrt_groups.items():
                            total_coeff = None
                            for t in terms:
                                if total_coeff is None:
                                    total_coeff = t.coeff
                                else:
                                    total_coeff = total_coeff + t.coeff
                            if total_coeff is not None and total_coeff.coeff.numerator != 0:
                                merged_sqrt_terms.append(TermWithSqrt(total_coeff, terms[0].sqrt_expr))
                        merged_expr = AlgebraicExpression(other_terms_list + merged_sqrt_terms)
                        if merged_expr.is_zero():
                            is_zero = True
                        else:
                            squared = (merged_expr * merged_expr).simplify(debug_callback)
                            if squared.is_zero():
                                try:
                                    test_expr = merged_expr
                                    all_vars = self._collect_variables(test_expr)
                                    if all_vars:
                                        for v in all_vars:
                                            test_expr = test_expr.substitute(v, AlgebraicExpression([AlgebraicTerm(1)]),
                                                                             debug_callback)
                                        test_val_expr = test_expr.simplify(debug_callback)
                                        if hasattr(test_val_expr, 'to_float'):
                                            if abs(test_val_expr.to_float()) < 1e-10:
                                                is_zero = True
                                        elif str(test_val_expr).replace(' ', '') == '0':
                                            is_zero = True
                                except:
                                    pass

                # ========== 新增：若常规判断未认定为零，则尝试递归平方判断 ==========
                if not is_zero:
                    if _zero_after_squaring(substituted):
                        if debug_callback:
                            debug_callback(f"通过递归平方判断，解 {sol} 成立", level=2)
                        is_zero = True
                # ========== 结束新增 ==========

                if is_zero:
                    valid.append(sol)
            except Exception as e:
                if debug_callback:
                    debug_callback(f"验根时出错: {e}，舍弃解 {sol}", level=2)
        return valid

    def _solve_abs_multivar(self, expr, variables, debug_callback=None, depth=0, max_depth=10, conditions=None,
                            seen=None):
        """
        求解多变量绝对值方程 expr = 0。
        返回列表，每个元素为 (conditions, solution)，
        conditions 为 (符号, 内部表达式) 列表，solution 为变量到解的字典。
        """
        if depth > max_depth:
            if debug_callback:
                debug_callback(f"绝对值方程递归深度超限 ({max_depth})，停止分支", level=2)
            return []
        if conditions is None:
            conditions = []
        if seen is None:
            seen = set()

        # 首先规范化表达式中的绝对值（例如将 |-x| 替换为 |x|）
        expr = self._normalize_abs(expr)
        if not isinstance(expr, AlgebraicExpression):
            expr = AlgebraicExpression(expr)

        expr_str = str(expr)
        if expr_str in seen:
            if debug_callback:
                debug_callback(f"检测到重复表达式 {expr_str}，停止递归", level=2)
            return []
        seen.add(expr_str)

        # 检查是否还有绝对值项
        abs_terms = [term for term in expr.terms if isinstance(term, AbsoluteValue)]
        if not abs_terms:
            # 无绝对值，对方程进行消元，选择一个变量求解
            try:
                vars_in_expr = self._collect_variables(expr)
                if not vars_in_expr:
                    # 常数方程
                    if expr.is_zero():
                        return [(conditions, {})]  # 恒成立
                    else:
                        return []  # 矛盾
                # 选择一个变量（例如第一个）
                chosen_var = sorted(vars_in_expr)[0]
                sol_list = self._solve_one_equation(expr, chosen_var, debug_callback)
                if not sol_list:
                    return []
                branches = []
                for sol in sol_list:
                    # 构建解字典，只包含 chosen_var
                    sol_dict = {chosen_var: sol}
                    # 其他变量自由，不加入字典
                    branches.append((conditions, sol_dict))
                if debug_callback:
                    debug_callback(f"分支方程 {expr} 选择变量 {chosen_var} 求解得到 {len(branches)} 个分支", level=2)
                return branches
            except Exception as e:
                if debug_callback:
                    debug_callback(f"分支方程求解出错: {e}", level=2)
                return []

        # 选择一个绝对值项，并找出所有与它内部表达式相同的项
        chosen = abs_terms[0]
        inner = chosen.inner_expr
        same_abs_terms = [term for term in abs_terms if self._abs_inner_equal(term.inner_expr, inner)]
        count = len(same_abs_terms)

        # 从表达式中移除这些项
        other_terms = [term for term in expr.terms if term not in same_abs_terms]
        rest = AlgebraicExpression(other_terms)

        # 构造 count * inner 和 -count * inner
        count_term = AlgebraicTerm(Fraction(count, 1))
        if isinstance(inner, AlgebraicExpression):
            inner_times_count = (inner * count_term).simplify(debug_callback)
            inner_times_neg_count = (inner * (count_term * Fraction(-1, 1))).simplify(debug_callback)
        else:
            # 如果 inner 是简单类型（如单变量），直接构造代数表达式
            inner_times_count = AlgebraicExpression([AlgebraicTerm(count, 1)]) * inner
            inner_times_neg_count = AlgebraicExpression([AlgebraicTerm(-count, 1)]) * inner

        # 情况1: inner ≥ 0 => 绝对值项的和 = count * inner
        eq1 = (inner_times_count + rest).simplify(debug_callback)
        eq1 = self._normalize_abs(eq1)
        cond1 = conditions + [('>=', inner)]

        # 情况2: inner < 0 => 绝对值项的和 = count * (-inner) = -count * inner
        eq2 = (inner_times_neg_count + rest).simplify(debug_callback)
        eq2 = self._normalize_abs(eq2)
        cond2 = conditions + [('<', inner)]

        if debug_callback:
            debug_callback(f"【多变量绝对值】合并 {count} 个相同绝对值项 {inner}，分支1: {eq1} = 0  条件: {inner} ≥ 0",
                           level=2)
            debug_callback(f"【多变量绝对值】分支2: {eq2} = 0  条件: {inner} < 0", level=2)

        # 递归求解，传递 seen 的副本
        results1 = self._solve_abs_multivar(eq1, variables, debug_callback, depth + 1, max_depth, cond1, seen.copy())
        results2 = self._solve_abs_multivar(eq2, variables, debug_callback, depth + 1, max_depth, cond2, seen.copy())

        return results1 + results2

    def _normalize_abs(self, expr):
        """
        规范化表达式中的绝对值项，将形如 |-x| 的项替换为 |x|。
        递归处理整个表达式。
        """
        if isinstance(expr, AbsoluteValue):
            inner = expr.inner_expr
            # 如果内部表达式是 -var 的形式
            if isinstance(inner, AlgebraicTerm) and len(inner.vars) == 1 and inner.coeff == Fraction(-1, 1):
                var = list(inner.vars.keys())[0]
                return AbsoluteValue(AlgebraicTerm(1, {var: 1}))
            # 对于更复杂的内部表达式，暂时不做处理
            return expr
        elif isinstance(expr, AlgebraicExpression):
            new_terms = []
            for term in expr.terms:
                if isinstance(term, AbsoluteValue):
                    new_terms.append(self._normalize_abs(term))
                else:
                    new_terms.append(term)
            return AlgebraicExpression(new_terms)
        elif isinstance(expr, FractionExpression):
            return FractionExpression(self._normalize_abs(expr.numerator), self._normalize_abs(expr.denominator))
        else:
            return expr

    def _abs_inner_equal(self, expr1, expr2):
        """比较两个绝对值内部表达式是否相等（先归一化）"""
        expr1_norm = self._normalize_abs(expr1)
        expr2_norm = self._normalize_abs(expr2)
        return str(expr1_norm) == str(expr2_norm)

    def _approx_term_value(self, term):
        """计算单个项（AlgebraicTerm, TermWithSqrt, SqrtExpression, AbsoluteValue）的数值近似"""
        if isinstance(term, AlgebraicTerm):
            if term.is_constant():
                return term.coeff.numerator / term.coeff.denominator
            else:
                return None
        elif isinstance(term, TermWithSqrt):
            coeff_val = self._approx_value(term.coeff)
            sqrt_val = self._approx_value(term.sqrt_expr)
            if coeff_val is None or sqrt_val is None:
                return None
            return coeff_val * sqrt_val
        elif isinstance(term, SqrtExpression):
            inner_val = self._approx_value(term.inner_expr)
            if inner_val is None or inner_val < 0:
                return None
            return math.sqrt(inner_val)
        elif isinstance(term, AbsoluteValue):
            inner_val = self._approx_value(term.inner_expr)
            if inner_val is None:
                return None
            return abs(inner_val)
        else:
            return None

    def _approx_value(self, expr):
        """计算表达式 expr 的浮点近似值，若含有变量或无法计算则返回 None"""
        if expr is None:
            return None
        if isinstance(expr, (int, float)):
            return float(expr)
        if isinstance(expr, Fraction):
            return expr.numerator / expr.denominator
        if isinstance(expr, AlgebraicExpression):
            total = 0.0
            for term in expr.terms:
                term_val = self._approx_term_value(term)
                if term_val is None:
                    return None
                total += term_val
            return total
        return self._approx_term_value(expr)

    def _get_left_factor(self, s, pos):
        """
        从字符串 s 中，在位置 pos（'^' 的位置）向左提取一个因子。
        返回因子的起始索引（包含）和结束索引（不包含），即 s[start:pos] 是因子。
        """
        i = pos - 1
        if i < 0:
            raise ValueError("缺少底数")
        # 处理括号
        if s[i] == ')':
            bracket_count = 1
            j = i - 1
            while j >= 0 and bracket_count > 0:
                if s[j] == ')':
                    bracket_count += 1
                elif s[j] == '(':
                    bracket_count -= 1
                j -= 1
            if bracket_count != 0:
                raise ValueError("括号不匹配")
            start = j + 1
            return start, i + 1
        # 处理数字
        if s[i].isdigit():
            while i >= 0 and s[i].isdigit():
                i -= 1
            start = i + 1
            return start, pos
        # 处理字母（变量）
        if s[i].isalpha():
            while i >= 0 and s[i].isalpha():
                i -= 1
            start = i + 1
            return start, pos
        raise ValueError("无效的底数")
