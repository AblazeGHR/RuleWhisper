# COC 全能跑团助手

模块化的 COC 7th 跑团全能助手。兼具**极速规则查询**、**自动化骰子机制**和**AI 辅助创作**能力。最终通过 NapCat/QQ Bot 接入 QQ 群，成为守秘人和玩家的桌面级工具。

## 使用方式

```bash
# 环境配置
source .venv/Scripts/activate
pip install -r requirements.txt

# 规则查询 (P1)
python src/cli.py rule "霰弹枪伤害"
python src/cli.py rule "理智值归零"
python src/cli.py rule "追逐"

# 结构化查询 (P2)
python src/cli.py weapon ".38 左轮"
python src/cli.py monster "深潜者"

# 骰子机制 (P3)
python src/cli.py dice ".rc 侦查 55"
python src/cli.py dice ".r 3d6"
python src/cli.py dice ".sc 0/1d3"
```

## 项目结构

```
ai_coc/
├── data/                    # 数据层
│   ├── 守秘人规则书.txt      # 规则书 txt (1.5MB, 400页)
│   ├── 快速开始规则.txt      # 快速开始 txt (76KB)
│   ├── weapons.json          # [P2] 武器结构化数据
│   ├── monsters.json         # [P2] 怪物结构化数据
│   └── spells.json           # [P2] 法术结构化数据
├── src/
│   ├── cli.py                # CLI 主入口
│   ├── engine/               # 引擎模块
│   │   ├── rule_search.py    # [P1] 关键词搜索
│   │   ├── indexer.py        # [P1] 倒排索引构建
│   │   ├── structured_query.py # [P2] 结构化查询
│   │   ├── embeddings.py     # [P4] 向量化
│   │   ├── rag.py            # [P4] RAG 检索
│   │   └── router.py         # 调度层
│   ├── dice/
│   │   ├── parser.py         # [P3] 骰子命令解析
│   │   └── resolver.py       # [P3] 骰子机制引擎
│   ├── extractor/            # [P2] 数据提取
│   └── bot/                  # [P5] QQ Bot
├── docs/
├── requirements.txt
└── .venv/
```

## 路线图

| Phase | 功能 | 状态 |
|-------|------|------|
| P1 | 关键词搜索 + CLI | 🔨 进行中 |
| P2 | 结构化数据提取 (武器/怪物/法术 → JSON) | ⬜ |
| P3 | 骰子与机制引擎 (.rc .ra .sc .dam) | ⬜ |
| P4 | 语义检索 RAG (chromadb) | ⬜ |
| P5 | NapCat QQ Bot 接入 | ⬜ |
| P6+ | 生成器引擎 (NPC/遭遇/线索) | ⬜ |

## 技术栈

| 组件 | 选型 | 理由 |
|------|------|------|
| 分词 | jieba | 中文断词，轻量零配置 |
| PDF 提取 | pypdfium2 | Chrome 引擎，CJK 完美支持 |
| 表格识别 | pdfplumber | 规则引擎识别武器/怪物表 |
| 向量库 | chromadb | pip 安装即用 |
| 中文 embedding | BAAI/bge-small-zh-v1.5 | 本地运行 |
| QQ Bot | NapCat HTTP API | 解耦接入 |

## 版权声明

本译文仅做学习交流之用，禁止用于商业用途。规则书版权归 Chaosium Inc. 所有。
