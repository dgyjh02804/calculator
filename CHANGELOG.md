# 更新说明 (2026.6.12) — 深度测试与 Bug 修复

## 🐛 Bug 修复 (16项)

### 计算错误修复 (5项)

| # | 问题 | 修复前 | 修复后 | 根因 |
|---|------|--------|--------|------|
| 1 | `√(x)=0` 解方程错误 | `x = 1` | `x = 0` | `from_string` 对中文返回 1 + `seen` 集合字符串碰撞 |
| 2 | `|x|-|x|` 不抵消 | `|(-x)|+|x|` | `0` | `AbsoluteValue.__mul__` 将负号吸入内部，simplify 未检测相反数抵消 |
| 3 | `(-1)*|x|` 错误输出 0 | `0` | `|(-x)|` | 规范化 key 查找失败导致项丢失 |
| 4 | `|x|*|x|` 嵌套绝对值 | `||x²||` | `|x²|` | `AbsoluteValue.__mul__` 未处理两个绝对值相乘 |
| 5 | `x^(1/2)*x^(1/2)` 错误输出 0 | `0` | `x` | `no_paren_pattern` 正则误匹配 `*` 运算符 |

### 解析器修复 (4项)

| # | 问题 | 修复前 | 修复后 | 根因 |
|---|------|--------|--------|------|
| 6 | `e/e` 不约分 | `e` | `1` | `_parse_term` 中 `is_constant()` 对数学常数 e 的短路错误 |
| 7 | `--x` 双负号不消去 | `-x` | `x` | `_parse_add_sub` 连续负号未翻转符号 |
| 8 | `1/(2x)` 解析为 `(1/2)x` | `(1/2)x` | `1/(2x)` | `_handle_parentheses` 移除了隐式乘法所需的括号 |
| 9 | `2x(x+2)` 解析失败 | 崩溃 | `4x+2x²` | `_insert_implicit_multiplication` 中 `c.isalpha()+next_c=='('` 被错误放在独立 elif 分支 |

### 化简与求解器修复 (4项)

| # | 问题 | 修复前 | 修复后 | 根因 |
|---|------|--------|--------|------|
| 10 | `1/x+1/y` 不合并 | 不合并 | `(x+y)/xy` | `FractionExpression.simplify` 过度展开产生负指数分式 |
| 11 | `0*|x|` 输出 `|0|` | `|0|` | `0` | `AlgebraicTerm.__mul__` 零系数时保留变量导致 `is_constant` 失败 |
| 12 | `xy=6;x+y=5` 分数不简化 | `6/3, 6/2` | `2, 3` | `_substitute_solution` 中 simplify 被注释掉 |
| 13 | `|x/y+y/x|=2;x+y=4` 无解 | 无解 | `x=2, y=2` | `_eliminate` 单方程单变量缺 abs 检查；`AlgebraicTerm(count,1)` 类型错误 |

### 测试系统修复 (3项)

| # | 问题 | 修复前 | 修复后 | 根因 |
|---|------|--------|--------|------|
| 14 | 测试运行卡死 | sympy 超时 | 秒级完成 | 移除 sympy 依赖，改用计算器自身归一化比较 |
| 15 | 结果相同仍报错 | 误报 | 正确匹配 | 只归一化期望值（不重解析实际结果） |
| 16 | `AlgebraicExpression.__init__` 包装错误 | 崩溃 | 正常工作 | `FractionExpression` 等类型未在 `__init__` 中处理 |

## ✨ 新功能

- **防卡死心跳检测**：每 2 秒检查测试线程；卡住超 5 秒在进度窗口显示红色警告和卡住的测试名
- **慢测试警告**：超 3 秒的测试自动输出 warning 到 debug 日志
- **计算器归一化比较**：`_are_solutions_equivalent` 完全移除 sympy，用计算器自身的 `parse → simplify` 统一表示形式后比较字符串
- **零系数消除**：`0*x`、`0*|x|` 等自动返回 `0`，不再保留残余变量

## 🧪 测试系统

- **测试用例从 229 增长到 252**（+23 个回归测试）
- **新增 "6.12 回归测试" 分类**，覆盖所有修复 bug
- **全部 252 测试通过，0 错误，0 差异**

## 🔧 关键代码变更

| 文件 | 变更 |
|------|------|
| `core/expression.py` | `from_string` 输入验证、`__init__` 包装所有表达式类型、`__truediv__` 修复、绝对值互消检测、分式展开防负指数、嵌套分式处理、零系数消除 |
| `core/algebra_parser.py` | 连续负号翻转、`_insert_implicit_multiplication` 逻辑修复、`_handle_parentheses` 隐式乘括号保留、`no_paren_pattern` 正则修复 |
| `core/solver.py` | `_solve_one_equation` 无解检测、`seen` 防碰撞、`_eliminate` 单变量 abs/radical 委托、`_substitute_solution` 启用 simplify、`_solve_abs_multivar` 类型修复 |
| `gui/app.py` | 移除 sympy 比较、计算器归一化比较、防卡死心跳、慢测试警告 |
| `gui/widgets.py` | `show_freeze_warning` 防卡死进度显示 |
| `gui/test_data.py` | 新增 23 个回归测试、更新 5 个期望值 |

## 🚀 运行方式

```bash
cd src
pip install sympy   # 仅因式分解和高次方程求根需要
python run.py
```


# 更新说明 (2025.6.5)(ai写的)

## 🐛 Bug 修复 (12项)

| # | 问题 | 修复 |
|---|------|------|
| 1 | `a/x-2x-2+a=0` 结果未化简 | √(a²+4a+4) 自动检测为完全平方三项式 → \|a+2\| |
| 2 | 部分解方程没化简结果 | 多项改善（根号有理化、因式分解约分） |
| 3 | 三次方程有实数解但不显示 | 修复 casus irreducibilis 过滤逻辑 |
| 4 | `√(2/3)` 未化简 | 根号内分母自动有理化：√(2/3) → √6/3 |
| 5 | `x²+y²-2x+6y+2=0; x²+y²+4x-2y-4=0` 计算错误+死机 | 新增方程相减降次策略，正确求解 |
| 6 | `y=kx-√3k; y=√2x` 无法求解 | TermWithSqrt 变量在系数中时正确提取 |
| 7 | 不同分辨率页面显示异常 | 窗口自适应屏幕 + 所有按钮行等比缩放 + 设置弹窗整合控件 |
| 8 | `(1+x)*eˣ=1` 将 e 误认为变量 | **新增 `e` 为自然常数识别**，新增 PowerTerm 支持 eˣ |
| 9 | 用户界面有重复的 ^ 按钮 | 移除重复按钮 |
| 10 | `(x+1)(ex²-1)/x` 将 e 当变量计算 | e 作为数学常数，结果：ex+ex²-1/x-1 |
| 11 | 因式分解中 e 被误认为变量 | 修复 `contains_var` 跳过数学常数 |
| 12 | 测试全部运行时卡死 | 新增智能匹配：计算器自动规范化表达式后比较，消除格式差异 |

## ✨ 新功能

- **`e` 自然常数支持**：`e`、`e^x`、`ex²` 等表达式自动识别欧拉数
- **幂表达式 (PowerTerm)**：支持符号幂如 `e^x`，保留指数结构
- **完全平方三项式检测**：`√(a²+4a+4)` → `|a+2|`
- **根号内分母有理化**：`√(2/3)` → `(√6)/3`，`3√(1/2)` → `(3√2)/2`
- **方程相减降次**：方程组自动尝试消去高次项
- **⚙ 设置弹窗**：Debug 级别、速度、历史过滤整合到一个弹窗
- **分辨率自适应**：窗口随屏幕等比缩放，按钮行使用 grid 等宽布局

## 🧪 测试系统

- **79 个测试用例**，全部通过
- **智能匹配**：`_are_solutions_equivalent` 通过计算器自身的解析→化简规范化表达式，自动处理格式差异
- **新增模式注解**：测试支持 `"simplify"`、`"factor"`、`["x","y"]` 三种模式
- **新增 "6.5" + "3.7" 测试分类**，覆盖所有修复 bug
- **新增 "化简匹配测试"**，验证不同格式的数学等价匹配

## 🏗 代码重构

### 文件拆分（4→10个文件）

```
src/
├── run.py                     # 启动入口
├── core/
│   ├── base.py                # Fraction, 数学常数
│   ├── expression.py          # 表达式系统 (AlgebraicTerm/AbsoluteValue/SqrtExpression/PowerTerm/...)
│   ├── algebra_parser.py      # 字符串解析器 (AlgebraicParser)
│   └── solver.py              # 方程求解器 (AlgebraicCalculator)
└── gui/
    ├── config.py              # 配置/日志/Debug 回调
    ├── widgets.py             # 弹窗控件
    ├── test_data.py           # 测试用例数据
    └── app.py                 # 主界面
```

### 关键改动

- `AlgebraicCalculator` 继承 `AlgebraicParser` 获得解析能力
- GUI 三层分离：core（配置/日志）→ widgets（控件）→ app（主界面）
- 测试数据独立于主界面代码
- 修复 `parser.py` 与 Python 内置模块冲突（→ `algebra_parser.py`）
- 备份整理至 `老版本/6.5半稳定/`

## 🚀 运行方式

```bash
cd src
pip install sympy
python run.py
```
