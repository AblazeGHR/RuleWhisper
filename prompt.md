# P5 — 骰子引擎

## 目标

实现 COC 7th 完整骰子机制，纯 Python 标准库，兼容塔骰/豹骰命令格式。

## 产出文件

```
src/dice/parser.py       ← 命令解析器
src/dice/resolver.py     ← 骰子机制引擎
```

## 命令对照表

| 命令 | 功能 | 示例 | 输出要求 |
|------|------|------|---------|
| `.r NdS` | 基础掷骰 | `.r 3d6` | `3D6 = 5+3+6 = 14` |
| `.r NdS+K` | 取最高 K 个 | `.r 4d6k3` | `4D6k3 = [5,3,6,2] → 14` |
| `.rc skill val` | 技能检定 | `.rc 侦查 55` | `[22/55] 困难成功！` |
| `.rc skill` | 技能检定（查角色卡） | `.rc 侦查` | `哈维 侦查55 → [22/55] 困难成功！` |
| `.ra attr val` | 属性检定 | `.ra 力量 65` | `[81/65] 失败` |
| `.rb skill val` | 奖励骰 | `.rb 侦查 55` | `[22(18,22)/55] 困难成功（奖励骰取优）` |
| `.rp skill val` | 惩罚骰 | `.rp 侦查 55` | `[89(71,89)/55] 失败（惩罚骰取劣）` |
| `.rs N#skill val` | 多次检定 | `.rs 3#侦查 55` | `#1 [22/55] 困难成功 / #2 [81/55] 失败 / #3 [45/55] 成功` |
| `.sc cur/max` | 理智检定 | `.sc 0/1d6` | `SAN检定 [45/60] 成功，损失 0` |
| `.sc max` | 理智检定（查卡） | `.sc 1/1d10` | `SAN检定 [81/60] 失败，掷1D10=6，损失6` |
| `.st attr val` | 设定属性 | `.st 力量 65` | `哈维 力量 → 65` |
| `.dam expr` | 伤害掷骰 | `.dam 1d8+1d4` | `1D8+1D4 = 5+3 = 8` |

## COC 7th 成功等级判定

所有检定自动判定成功等级：

```
大成功    ≤ skill/50 且 ≤96   (出01)
极难成功  ≤ skill/5          (≤ 1/5)
困难成功  ≤ skill/2          (≤ 1/2)
常规成功  ≤ skill
失败      > skill 且 ≤ 95
大失败    ≥ 96
```

## parser.py 设计

```python
class DiceCommand:
    type: str           # "rc" | "ra" | "rb" | "rp" | "rs" | "sc" | "r" | "dam" | "st"
    skill_name: str     # 侦查
    skill_value: int    # 55
    extra_dice: int     # 奖励骰 / 惩罚骰参数

def parse(input: str) -> DiceCommand:
    """解析用户输入的命令字符串"""

# 也支持自然语言输入
def parse_natural(input: str) -> DiceCommand:
    """解析自然语言输入，如 '侦查 55'、'投个 3d6'、'力量检定'"""
```

## resolver.py 设计

```python
def resolve(cmd: DiceCommand) -> DiceResult:
    """执行检定并返回结果"""

class DiceResult:
    dice_roll: int       # 实际掷出值
    success_level: str   # "极难成功" | "困难成功" | "常规成功" | "失败" | "大失败"
    display: str         # 格式化输出
    extra_info: dict     # 奖励骰/惩罚骰的额外骰值等
```

## 注意

- 纯标准库，不引入额外依赖
- 先做 `.rc`/`.ra`/`.r`/`.dam` 四个核心命令
- 奖励骰/惩罚骰 `.rb`/`.rp` 次优先
- 理智检定 `.sc` 和多次检定 `.rs` 最后做
- 每完成一个命令就测试并 commit
- commit 格式：`feat(dice): support .rc command`
