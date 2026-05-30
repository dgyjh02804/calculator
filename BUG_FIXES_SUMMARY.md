# 代数计算器 Bug 修复总结

**修复日期:** 2026-05-30
**触发场景:** 测试类别 3.7（方程组）出现多项 bug，包括错误结果、界面卡死

---

## 修复概览

| # | Bug | 严重度 | 文件 | 状态 |
|---|-----|--------|------|------|
| 1 | `Fraction.__mul__` 对 int 入参返回 None | Critical | `algebra_base.py` | ✅ |
| 2 | `x^N/M` 被错误解析为 `x^(N/M)` | Critical | `algebra_solver.py` | ✅ |
| 3 | 消元法不优先选择低次方程 | Critical | `algebra_solver.py` | ✅ |
| 4 | `from_string` catch-all 吞掉复杂表达式 | Critical | `algebra_solver.py` | ✅ |
| 5 | 测试对比无法识别数学等价解 | High | `algebra_gui.py` | ✅ |
| 6 | Debug 队列无上限导致 UI 卡死 | High | `algebra_gui.py` | ✅ |
| 7 | 根式验证不处理 FractionExpression | Medium | `algebra_solver.py` | ✅ |

---

## Bug 1: `Fraction.__mul__` 缺少 return 语句

**文件:** `algebra_base.py` 第 51-59 行
**根因:** `__mul__` 方法使用 `if-elif-else` 结构，当 `other` 为 `int` 时只将其转换为 `Fraction`，但没有 `return`，函数隐式返回 `None`。后续 `AlgebraicTerm.__init__` 调用 `Fraction(None, 1)`，`normalize()` 中 `abs(None)` 抛出 `TypeError: bad operand type for abs(): 'NoneType'`。

**修复前:**
```python
def __mul__(self, other):
    if isinstance(other, int):
        other = Fraction(other, 1)          # 无 return!
    elif isinstance(other, Fraction):
        ...
```

**修复后:**
```python
def __mul__(self, other):
    if isinstance(other, int):
        other = Fraction(other, 1)
    if isinstance(other, Fraction):         # 独立 if，承接 int 转换后的 Fraction
        new_numerator = self.numerator * other.numerator
        new_denominator = self.denominator * other.denominator
        return Fraction(new_numerator, new_denominator)
    return NotImplemented
```

**影响链:**
```
AlgebraicTerm.from_string → coeff * sign (int)
  → Fraction.__mul__ → None
    → Fraction(None, 1) → abs(None) → TypeError
```

---

## Bug 2: `_parse_factor` 中 `x^N/M` 解析错误

**文件:** `algebra_solver.py` `_parse_factor` 方法
**根因:** `^` 的指数解析贪婪地取全部右侧内容为指数。`x^2/4` 中，`exp_str = "2/4"`。`2/4` 不是 `1/2`（sqrt），也不是整数指数，代码 fallback 返回常数 `1`，`/4` 除法被完全丢失。
**后果:** `x^2/4+y^2=1; y=x` 被解析为 `1+y^2=1` → `y=0, x=0`（完全错误）。

**修复:** 在取 `exp_str` 后添加检查：若指数字符串中存在顶层（非括号内）的 `*` 或 `/` 运算符，抛出 `ValueError`，让 `_parse_term` 按运算符拆分，正确处理除法。同时将分数指数约分后再判断（如 `2/4` → `1/2` 识别为 sqrt）。

**修复要点:**
```python
exp_str = factor_str[i + 1:]
# 新增：检查指数后是否有 */ 运算符
bkt = 0
for j, c in enumerate(exp_str):
    if c == '(': bkt += 1
    elif c == ')': bkt -= 1
    elif c in '*/' and bkt == 0:
        raise ValueError(f"指数后存在运算符 '{c}'，需在term层级处理")
```

---

## Bug 3: 消元法不优先选择低次方程

**文件:** `algebra_solver.py` `_eliminate` 方法第 1296-1302 行
**根因:** 消元时选择第一个包含目标变量的方程，不考虑次数。对 `x^2+y^2=9; x=y-1`，二次方程 `x^2+y^2-9` 被选中，线性方程 `x-y+1` 被跳过。解二次方程产生根式表达式，代入验证时因 FractionExpression 处理不完整而失败，最终返回"无解"。

**修复:** 改为选择目标变量次数最低的方程（线性优于二次）：
```python
best_degree = float('inf')
for i, eq in enumerate(equations):
    max_deg = 0
    for term in eq.terms:
        if term.contains_var(var):
            if isinstance(term, AlgebraicTerm):
                deg = term.vars.get(var, 0)
                max_deg = max(max_deg, deg)
            else:
                max_deg = max(max_deg, 1)
    if max_deg > 0 and max_deg < best_degree:
        best_degree = max_deg
        eq_index = i
```

---

## Bug 4: `AlgebraicTerm.from_string` catch-all 吞掉复杂表达式

**文件:** `algebra_solver.py` `_parse_factor` 方法第 880-888 行
**根因:** Bug 1 修复后，`AlgebraicTerm.from_string` 不再抛 NoneType 异常。对于 `(1-√(17))/2` 等复杂表达式，`from_string` "成功"返回了常数 `1`（因为 `(` 不是数字，while 循环不执行，coeff 默认 1，var_part 不匹配任何变量名，最终返回常数项 `1`）。`_parse_factor` 拿到这个结果就返回了，绕过了 `_parse_term` 的运算符拆分。

**修复:** 在 catch-all 调用前添加守卫，检测字符串是否含括号或运算符：
```python
_has_paren = '(' in factor_str or ')' in factor_str
_has_top_op = bool(re.search(r'(?<!\^)[+\-*/]', re.sub(r'^[+-]', '', factor_str)))
if _has_paren or _has_top_op:
    raise ValueError(f"表达式包含括号或运算符，需在上层处理: {factor_str}")
```

---

## Bug 5: 测试对比函数无法识别数学等价解

**文件:** `algebra_gui.py` `_are_solutions_equivalent` 方法第 1798-1872 行
**根因:** 原函数仅做简单字符串正则替换（如 `√(N)/D → (1/D)√(N)`）后逐字比较。无法处理：
- `3/√(2)` vs `3√(1/2)`（`/√` 模式未覆盖）
- `(1+√(17))/2` vs `1/2+(√(17))/2`（分布律展开）

**修复:** 重写为使用 sympy 进行数学等价性判断。核心逻辑：
1. 将 `√(...)` 转换为 `sqrt(...)`，`^` 转换为 `**`
2. 使用 `sympy.sympify` 解析表达式
3. 使用 `sympy.simplify(expr1 - expr2) == 0` 判断等价
4. 按 `或` 分割多组解，对每组进行顺序无关匹配
5. 支持多变量单行解（如 `x = a, y = b`）的逐变量比较

---

## Bug 6: Debug 输出队列无限制导致 UI 卡死

**文件:** `algebra_gui.py` `DebugCallback` 类
**根因:** 后台测试线程向 `message_queue` 无限制写入（一个根式方程产生 11,166 条调试消息），主线程 `process_queue` 一次性全量处理，每条 `insert` + `see` 到 tkinter ScrolledText 需要 ~10ms，总计 ~110 秒 UI 冻结。

**修复 (三处):**
1. `__init__` 添加 `self.max_queue_size = 2000`
2. `__call__` 中队列超过上限时丢弃旧消息（FIFO 弹出）
3. `process_queue` 每次最多处理 100 条消息（而非全量）

---

## Bug 7: 根式验证不处理 FractionExpression

**文件:** `algebra_solver.py` `_solve_radical_equation` 验证部分
**根因:** 候选解代入根式方程后，代入结果可能是 `FractionExpression`（如 `(2+√68)/4`），但验证代码仅检查 `isinstance(substituted, AlgebraicExpression)`。`FractionExpression` 被跳过，sqrt 合并逻辑未执行，导致有效候选解被错误拒绝。

**修复:** 在 `is_zero` 判断中添加 `FractionExpression` 分支：
```python
elif isinstance(substituted, FractionExpression):
    num_simplified = substituted.numerator.simplify(debug_callback)
    if hasattr(num_simplified, 'is_zero') and num_simplified.is_zero():
        is_zero = True
    elif self.contains_radical(num_simplified):
        if _zero_after_squaring(num_simplified):
            is_zero = True
```

---

## 额外修复

**`algebra_gui.py` 第 767 行:** 为测试用例 `x^2+y^2=r^2; x+y=0` 添加 `solve_vars=['x', 'y']` 参数，明确求解 x 和 y（保持 r 为自由变量），与期望输出格式一致。

---

## 验证结果

### 3.7 测试（全部 9 个用例）

| # | 表达式 | 结果 |
|---|--------|------|
| 1 | `x^2+y^2=r^2; x+y=0` | ✅ PASS |
| 2 | `|x+y|=4; x^2+y^2=9` | ✅ PASS |
| 3 | `x^2+y^2-4x=9; x=y-1` | ✅ PASS |
| 4 | `x^2+y^2+4x-4y=0; x^2+y^2+2x-12=0` | ✅ PASS |
| 5 | `x^2/4+y^2=1; y=x` | ✅ PASS |
| 6 | `√(x^2+1) + √(x^2+1) = 2` | ✅ PASS |
| 7 | `x^2+y^2=9; x=y` | ✅ PASS |
| 8 | `x^2+y^2=9; x=y-2` | ✅ PASS |
| 9 | `x^2+y^2=9; x=y-1` | ✅ PASS |

### 回归测试

- 16 个覆盖表达式/方程/方程组的冒烟测试全部通过
- 所有曾触发 `bad operand type for abs(): 'NoneType'` 的表达式均正常解析
- UI 卡死问题已根除（队列批处理 + 上限控制）
