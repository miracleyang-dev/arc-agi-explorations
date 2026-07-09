# 04 · Meeting Outline · 2026-07-10 15:00 with Prof. Chen

> **Format.** 白板 + 现场讲。此文件是**讲稿骨架 + 白板要写的东西**，不是幻灯片。
> **Time budget.** 约 45–60 min 讲 + 讨论。前 25 min 讲，后面留讨论。
> **Materials to have open on laptop.**
> - `notes/02_task_taxonomy.md`（尤其 §2 coverage matrix 和 3.11 `6e02f1e3` / 3.15 `ded97339`）
> - ARC Prize 官网 `https://arcprize.org/play` 备用（现场解一题）
> - 本文件（提词）

---

## 0 · 一句话开场（30 秒）

> 「过去 4 天我从零开始接触 ARC-AGI，我打算先跟您对齐一下**ARC 是什么、为什么难、社区做到哪、以及我下一步的两条候选方向**，然后一起讨论。」

---

## 1 · What is ARC?（3 min, 白板画一张 task）

**白板画**：一个 task = 2–3 组 `input grid → output grid`（3×3 到 10×10）+ 1 个 test input（? output）。

- 数据规模：ARC-AGI-1 = 400 train + 400 eval；ARC-AGI-2 = 1000 train + 120 eval（更抽象）。
- 每 task 只给 **3-5 个 demo**，模型必须从中提炼规则并对 test input 预测。
- 允许 **pass@2**（提交 2 个答案，任一正确算过）。
- 人类 solve rate ≥ 80%；SOTA 机器 ~ 55% (ARC-1) / ~10% (ARC-2)。

**关键差异**（对比 ImageNet/GLUE）：**不允许同分布 fine-tune**——每个 test task 的抽象结构在 train 里都没见过。

---

## 2 · Why hard?（8 min, 白板举 2 题）

**核心原因**：所有 mainstream benchmark 都可以用 "大数据 + 大模型 + 同分布训练" 攻破，ARC 掐死了这条路——**demo 极少 + 抽象方式未见过**。

### 2.1 例题 A · `6e02f1e3`（**我认为最难的一题**）
- 白板画 3×3 → 3×3 的一组 demo。
- 规则：数输入里不同颜色的种数 k，根据 k 决定输出的 3×3 pattern。
- **难在哪**：这是**两阶段**任务——先 count（P3），再 lookup pattern。神经网络一步 forward 学不到"先统计再决定"的中介变量；LLM 直推容易糊掉；DSL 需要显式暴露"计数"这个原语。

### 2.2 例题 B · `ded97339`（**次难**）
- 规则：同一行/列上成对蓝点之间画蓝线。
- **难在哪**：需要**"配对 + 判断共线 + 沿轴画线"**三个步骤的组合。搜索空间在 pixel level 极大，但在 object/geometry level 又极小——这个 abstraction gap 是 ARC 的核心难点。

**归纳**：**ARC 难 = few-shot + 抽象层次高 + 组合搜索空间大 + 无同分布数据可 leverage**。

---

## 3 · Chollet 的核心 framework（5 min, 白板写公式 + 4 priors）

**智能公式**（笔记 01 §三）：
$$
I = \frac{\text{达标的任务数（按难度加权）}}{\text{经验 } E + \text{先验 } P}
$$
- 一句话：**用越少数据、越少先验、越能解决新任务 = 智能**。
- 意义：这个定义**否定了纯 scale**，也否定了 test-set fine-tuning。

**四类 Core Knowledge Priors**：
1. Objectness（物体、边界、运动、包含）
2. Agentness / goal-directedness（意图、朝向、避让）
3. Numbers（计数、比较、少量算术）
4. Geometry / topology（对称、连通、内外）

> ARC 的每一题**理论上**只需要这四类先验就能解——这也是"排除文化和语言"、"公平测抽象"的手段。

---

## 4 · Task Taxonomy（5 min, 白板画 coverage matrix）

**白板画**（简化版）：
```
        T1 sym  T2 grav  T3 recolor  T4 crop  T5 fill  T6 count  T7 tile  T8 draw
P1 obj                   ✓                                       ✓
P2 goal          ✓
P3 num                   ✓                              ✓
P4 geom  ✓                                    ✓                          ✓
```

- 我从 400 训练题里挑了 **15 seed**，按 `prior × transformation` 二维分类（详见 `notes/02_task_taxonomy.md`）。
- **诊断价值**：空的 cell 反映现有 method 族的盲区；比如 **P3 × T2（数量决定移动距离）** 全空，是 count-then-act 高阶变体，值得后期专攻。
- 关于**为什么我把 Chollet 的 4 priors 合并成 2 组**（objectness+physics 合并、agentness+goal-directedness 合并）：见笔记 02 §1.3；实证观察上 ARC 里这两对总是耦合出现，独立分类会稀释诊断价值。

---

## 5 · Current Landscape（5 min, 白板列 4 条 baseline）

四条主线方法（详见 `notes/03_landscape.md`）：

| 方法族 | 代表工作 | 现在到哪 | 短板 |
|--------|----------|----------|------|
| **Program synthesis / DSL search** | Icecuber (Kaggle 2020, 21%), Hodel DSL | 需要人手写 DSL；组合爆炸 | 不能泛化到 DSL 外的 transformation |
| **Neuro-symbolic hybrid** | DreamCoder (Ellis et al.) | 学 primitive + 搜索 | 训练重 |
| **LLM direct** | Greenblatt GPT-4o (~50%) | prompt engineering + revision | 昂贵、慢，且 ARC-2 崩盘 |
| **Test-Time Training (TTT)** | Akyürek 2024 (arXiv:2411.07279) | **当前 SOTA** ~55% (ARC-1) | 每个 test 都重训、算力贵 |

**共同盲区**（我看下来）：
- 都缺 "**先抽象出中间变量，再做二次决策**" 的能力（e.g. `6e02f1e3` 的两阶段结构）。
- 都缺"**在 object level 而非 pixel level 组合规则**"的机制（e.g. `ded97339` 的配对+画线）。

---

## 6 · 我的两个候选研究方向（10 min, 讨论重点）

**共同点**：都基于"Chollet 的公式没法作为 loss 优化——只是事后打分"这个观察。

### Direction A · Learning ARC as few-shot discrete operator learning
- **一句话**：把每个 ARC task 看作一个 discrete operator $f: X \to Y$，从 3-5 个 demo 中 few-shot 学出 $f$，架构受 neural operators 启发。
- **与陈老师工作接口**：这直接对应老师"learning operators from data"的方向；把连续 operator 换成 discrete 的、把数据规模换成 few-shot。
- **产出预期**：ARC-1 上一个能报的数（哪怕不是 SOTA）+ 一个 architecture ablation。
- **风险**：中等；主要靠工程，不确定性在"discrete operator 的 embedding 怎么设计"。

### Direction B · A differentiable proxy for skill-acquisition efficiency
- **一句话**：给 Chollet 的 $\dfrac{S}{E+P}$ 造一个可微上界（用 KL divergence 代理 $E$、参数量/预训练 loss 代理 $P$），塞进 loss 训 ARC solver。
- **理论味道**：可以挂 PAC-Bayes / meta-learning sample complexity 的线，讨论章节写一小段推导。
- **产出预期**：一个新 objective + ARC-1 上跟标准 loss 的对比。
- **风险**：较高；理论那一步组内没人 debug，需要自己啃 Amit-Meir 2018 一类的论文。

**我的倾向**：**A 为主，B 作为 discussion 里的"future work"**——即：主要做 A 的工程，在最后半页讨论里挂 B 的想法。这样：
- 保底可发（A 是纯 empirical，跟老师方向接得上）。
- 上限还在（B 的种子留着，博士期可以再展开）。
- 不孤军作战（A 老师能给指导）。

---

## 7 · 下周计划（3 min, 白板列 3 条）

- **7/11-7/13**：（如果去打 Kaggle NeuroGolf 就在这几天）；否则读 ARC Prize 2024 Tech Report + Akyürek TTT paper，把 `notes/03` 补厚。
- **7/14-7/17**：写 minimum viable ARC solver（一个 CNN + task-conditioning，用 3-5 demo few-shot 训）→ 用它跑 baseline 数字。
- **7/18 之前**：确定 Direction A 的 architecture 蓝图，交下一次 meeting 讨论。

---

## 8 · 问陈老师的问题（讨论区，5 min）

1. **您对我提的两条方向有什么反应？** 是想让我先做 A、B 分头试，还是直接砍掉一条？
2. **您觉得"把 ARC task 看作 discrete operator learning"这个 framing 靠不靠谱？** 有没有踩到您之前工作中已经知道的坑？
3. **产出形式**：您希望这段暑研的最终 deliverable 是 (a) 一份 report、(b) arXiv preprint、(c) 一个能跑的 codebase + demo notebook？
4. **有没有 group meeting / reading group** 我可以参加，或者一起讨论 ARC 的师兄师姐推荐？
5. **算力**：我目前假设可以用组内 H800，如果不行请告诉我预算/权限怎么走。

---

## 附 · 如果时间不够，砍这些

- §5 landscape 只讲表头，不展开各方法细节
- §6 只讲 Direction A，B 塞到 §8 讨论里问
- §7 只留一句"下周先跑通 baseline"

## 附 · 如果被问到但没准备的问题（诚实版应答）

- "ARC-2 你看过题目了吗？"→ 「还没系统看，本周只解了 ARC-1 的 15 题；ARC-2 计划下周开始跟 tech report 一起看」
- "TTT 的具体机制？"→ 「Akyürek paper 我还没精读，只看了 blog。核心是每个 test task 上做几百步 gradient update，用 demo 造增强数据。下次可以带 detailed writeup」
- "你的 15 题 taxonomy 有没有 formal metric？"→ 「目前是我人肉标注的，还没量化；下一步想加 estimated DSL length 和 human solve time 两个 metric」
