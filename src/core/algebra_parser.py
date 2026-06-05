"""代数表达式解析器 — 将字符串解析为表达式树"""
import re
from core.base import Fraction, KNOWN_MATH_CONSTANTS
from core.expression import (
    AlgebraicTerm, AbsoluteValue, SqrtExpression,
    TermWithSqrt, AlgebraicExpression, FractionExpression,
    DenominatorRationalizer, LogExpression, PowerTerm
)


class AlgebraicParser:
    """表达式解析器，负责将用户输入的字符串解析为内部表达式对象"""

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
        processed_expr = self._handle_log_function(processed_expr, debug_callback)
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
                        # 检查是否属于 log, abs, sqrt 等关键词
                        func_start = i
                        while func_start > 0 and expr[func_start - 1].isalpha():
                            func_start -= 1
                        func_end = i + 1
                        while func_end < n and expr[func_end].isalpha():
                            func_end += 1
                        block = expr[func_start:func_end]
                        if block not in ['log', 'abs', 'sqrt']:
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
                    if func_name not in ['abs', 'sqrt', 'log']:
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
        # 括号处理后重新插入隐式乘法（因为字符串化可能丢失 *，如 e*x → ex）
        expr = self._insert_implicit_multiplication(expr, debug_callback)
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
                is_after_log = (i >= 3 and expr[i - 3:i] == 'log')
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
                    elif is_after_sqrt or is_after_log:
                        result.append(f"({inner_expr})")
                    else:
                        inner_processed = self._handle_parentheses(inner_expr, debug_callback)
                        inner_result = self._parse_expr(inner_processed, debug_callback)
                        inner_str = str(inner_result)
                        # Keep parens if inner contains any operator that would change precedence
                        if any(op in inner_str for op in '+-*/'):
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
            # 检查根号后面是否还有内容（如 /2），如果有则需在上层处理运算符
            if i < len(factor_str):
                raise ValueError(f"根号表达式后还有内容，需在上层处理: {factor_str[i:]}")
            if debug_callback:
                debug_callback(f"解析根号内部表达式: {inner}", level=3)
            inner_expr = self._parse_expr(inner, debug_callback)
            return AlgebraicExpression([SqrtExpression(inner_expr)])

        # 处理对数 log(base, arg)
        if factor_str.startswith('log('):
            if debug_callback:
                debug_callback(f"解析对数表达式: {factor_str}", level=3)
            # 找到匹配的右括号（log( 的开括号已消费，bracket 初始为 1）
            bracket_count = 1
            i = 4
            while i < len(factor_str):
                if factor_str[i] == '(':
                    bracket_count += 1
                elif factor_str[i] == ')':
                    bracket_count -= 1
                    if bracket_count == 0:
                        break
                i += 1
            if bracket_count != 0:
                raise ValueError("对数括号不匹配")
            inner = factor_str[4:i]  # 提取 base,arg 部分
            # 找到顶层逗号（分割底数和真数）
            comma_pos = -1
            bkt = 0
            for j, c in enumerate(inner):
                if c == '(':
                    bkt += 1
                elif c == ')':
                    bkt -= 1
                elif c == ',' and bkt == 0:
                    comma_pos = j
                    break
            if comma_pos == -1:
                raise ValueError("对数需要两个参数: log(底数, 真数)")
            base_str = inner[:comma_pos]
            arg_str = inner[comma_pos + 1:]
            from core.expression import LogExpression
            base_expr = self._parse_expr(base_str, debug_callback)
            arg_expr = self._parse_expr(arg_str, debug_callback)
            # 检查 log(...) 后面是否还有内容（如运算符）
            if i + 1 < len(factor_str):
                raise ValueError(f"对数表达式后还有内容，需在上层处理: {factor_str[i+1:]}")
            return AlgebraicExpression([LogExpression(base_expr, arg_expr)])

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
                        # 指数包含变量或为表达式，解析并创建 PowerTerm
                        if debug_callback:
                            debug_callback(f"指数 '{clean_exp_str}' 包含变量，创建符号幂表达式", level=3)
                        try:
                            # 尝试解析指数表达式
                            from core.expression import PowerTerm
                            exp_expr = self._parse_expr(clean_exp_str, debug_callback)
                            # 先尝试用 __pow__（可能返回 PowerTerm）
                            pow_expr = base ** exp_expr
                            if isinstance(pow_expr, AlgebraicExpression) and len(pow_expr.terms) == 1:
                                pow_expr = pow_expr  # 保持为表达式
                        except Exception as e2:
                            if debug_callback:
                                debug_callback(f"创建符号幂表达式失败: {e2}，使用原始形式", level=3)
                            # 保留原字符串形式
                            power_expr = f"{base_str}^{exp_str}"
                            pow_expr = AlgebraicExpression([PowerTerm(
                                AlgebraicExpression([AlgebraicTerm.from_string(base_str)]),
                                AlgebraicExpression([AlgebraicTerm.from_string(exp_str)])
                            )])
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




    def _handle_sqrt_function(self, expr, debug_callback=None):
        if debug_callback:
            debug_callback(f"处理平方根函数: {expr}", level=3)
        import re
        result = expr
        while 'sqrt(' in result:
            start = result.find('sqrt(')
            if start == -1:
                break
            bracket_count = 1  # 从1开始，因为sqrt(的开括号已经消费
            i = start + 5  # 从sqrt(的内部分开始
            while i < len(result) and bracket_count > 0:
                if result[i] == '(':
                    bracket_count += 1
                elif result[i] == ')':
                    bracket_count -= 1
                i += 1
            if bracket_count != 0:
                break
            inner_start = start + 5
            inner_expr = result[inner_start:i - 1]
            # 隐式乘法：处理 √(3)x 中的 )x → )*x
            inner_expr = self._insert_implicit_multiplication(inner_expr, debug_callback)
            if debug_callback:
                debug_callback(f"找到平方根函数: sqrt({inner_expr})", level=3)
            inner_result = self._parse_expr(inner_expr, debug_callback)
            sqrt_expr = f"√({inner_expr})"
            result = result[:start] + sqrt_expr + result[i:]
            # 处理替换后可能产生的隐式乘法 如 ...√(...)x
            result = self._insert_implicit_multiplication(result, debug_callback)
            if debug_callback:
                debug_callback(f"替换后表达式: {result}", level=3)
        return result

    def _handle_log_function(self, expr, debug_callback=None):
        """预处理 log(base, arg)：不做格式转换，保持原样。
        实际解析在 _parse_factor 中通过检测 'log(' 前缀完成。
        """
        return expr  # 保持原样，逗号由 _parse_factor 特殊处理

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


