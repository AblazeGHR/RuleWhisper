# Wiki 可视化 — 数据审查工具

## 目标

把所有结构化数据（武器/怪物/法术/技能/规则）渲染为 HTML wiki 页面，便于人眼审查数据质量。

只需要静态 HTML，零依赖，浏览器直接打开。

## 数据源

| 数据 | 文件 |
|------|------|
| 武器 | `data/weapons.json` |
| 怪物 | `data/monsters.json` |
| 法术 | `data/spells.json` |
| 技能 | `data/skills.json` |
| 规则 | `data/rules.json` |
| 分章规则 | `data/rules/*.json` |

## 输出

```
docs/wiki/
├── index.html           ← 首页导航
├── weapons.html         ← 武器表（按分类折叠）
├── monsters.html        ← 怪物卡（按分类分组）
├── spells.html          ← 法术列表
├── skills.html          ← 技能表
├── rules.html           ← 规则索引（按模块分组）
└── rules/
    ├── combat.html
    ├── sanity.html
    └── ...              ← 每模块一页
```

## 技术要求

- 纯静态 HTML，单文件自包含（CSS/JS 内联）
- 使用 Python 脚本生成（读取 JSON → 模板 → HTML）
- 不引入前端框架，手写 HTML table
- 表格支持：武器分类折叠、怪物属性卡片、规则标签检索
- 生成脚本：`docs/wiki/build.py`，一个文件

## 实现步骤

1. 创建 `docs/wiki/` 目录
2. 编写 `build.py`（~200 行）：读取各 JSON → 生成 HTML
3. 运行 `python docs/wiki/build.py`
4. 浏览器打开 `docs/wiki/index.html` 验证
5. commit

## 输出预览

**weapons.html 大致效果：**
```
手枪 (18)
│ 名称              │ 伤害     │ 射程  │ 价格        │
│ .38/9mm左轮手枪   │ 1D10     │ 15码  │ $25/$200    │
│ ...

霰弹枪 (10)
│ 20号双管霰弹枪    │ 2D6/...  │ 10码  │ $35/稀有    │
```

**monsters.html 大致效果：**
```
拜亚基，星骏                        [神话生物]

属性  STR 90  CON 50  SIZ 90  DEX 67  INT 50  POW 50
HP 14  伤害加值 1D6  体格 2  移动 5/16 飞行
格斗 55% (1D6+DB)  闪避 33%
护甲 2 毛发与坚韧兽皮
理智损失 1/1D6
```

**rules.html 大致效果：**
```
[第八章 理智] 29条
  sanity_check_basic     | 理智检定 ≤ 当前理智值为成功
  sanity_loss_format     | 损失格式 SAN X/Y
  ...
```

## 注意事项

- 如果某数据文件不存在（如 monsters.json 可能未完成），跳过该页面
- 所有 HTML 文件加入 `.gitignore`（生成物），只提交 `build.py`
- 在主页 `index.html` 标注数据更新时间
