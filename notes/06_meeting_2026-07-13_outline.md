# 06 · Meeting Outline · 2026-07-13 10:00

> 时间从 7/10 15:00 改到 7/13 10:00（陈老师有事）。
> 多出的 7/11-12 用来跑 minimum viable solver + 出 baseline 数字，见 §8。

带：`notes/02` + arcprize.org/play + baseline 结果（若已跑出）

## 0 · 开场
一周从零起步（7/6 至今）。今天讲：ARC / why hard / landscape / 我的方向 / 已有的 baseline 数字。

## 1 · What is ARC
- Task = few input→output demo + test input
- ARC-1 400/400，ARC-2 1000/120
- 3-5 demo，pass@2；人类 ≥80%，SOTA：ARC-1 55.5%（Kaggle 2024）/ ARC-2 24%（Kaggle 2025）
- 掐死同分布 fine-tune

## 2 · Why hard（举 2 题）
- `6e02f1e3`：count k → lookup pattern，两阶段中介变量
- `ded97339`：配对+共线+画线，object-level abstraction gap
- few-shot + 高抽象 + 组合搜索

## 3 · Chollet
- $I = \frac{\text{达标任务}}{E + P}$
- 4 priors: Objectness / Agentness / Numbers / Geometry

## 4 · Taxonomy
```
        T1  T2  T3  T4  T5  T6  T7  T8
P1                              ✓
P2      ✓
P3          ✓           ✓
P4  ✓               ✓           ✓
```
- 15 seed 已分类
- 空 cell = 方法族盲区

## 5 · Landscape
- Program synthesis (Icecuber, Hodel)
- Neuro-symbolic (DreamCoder)
- LLM 直推 (Greenblatt ~50%)
- **TTT (Akyürek, SOTA ~55%)**
- 共同盲区：中介变量、object-level 组合

## 6 · 方向（重点）
**A · ARC as few-shot discrete operator learning**
接老师"operator learning"，empirical，风险中

**B · Differentiable proxy for $S/(E+P)$**
PAC-Bayes / meta-learning，理论无 debug，风险高

**倾向**：A 主 + B 挂 discussion

## 6.5 · Baseline（7/11 已跑三版）

手写 DSL + 暴力 depth≤2 搜索，同一 harness 跑三版：

| 版本 | Primitives | Solved / 400 | Solve rate | 耗时 |
|------|-----------|-------------|-----------|------|
| v1 | 63  | 10 | 2.5%   | 27s |
| v2 | 170 | 19 | 4.75%  | 204s |
| **v3** | **197** | **43** | **10.75%** | 326s |

- 一键复现：`python -m solver.runner --split training --max-tasks -1 --depth 2 --budget 5`
- 详细 changelog 与每版原语清单：`notes/05_dsl_changelog.md`
- **每版严格支配前一版**（0 退化）；depth-2 到 v3 才开始有实质贡献（18/43）

**关键 talking points**：
1. **不是要打分数**，是**建立可复现测量框架** —— 后续 Direction A 的每个改动都要在同一个 harness 上跑，回归看得见。
2. **结构化算子 ROI 远大于参数展开**：v3 加 27 个结构化 (+2.3×)，v2 加 107 个参数化 (+1.9×) —— 教训直接指向"手写 DSL 不 scalable"，Direction A 的立论。
3. **10.75% 就是这条路的天花板**：ARC-1 剩下的 357 题需要 counting / pattern-generation / test-input-conditioned rules，纯 Grid→Grid 吃不到。**继续扩 DSL 是死路，转 operator learning 才有出路**。

## 7 · Target
- **ARC Prize 2026 Paper Track**，deadline **11-09**
- 同工作：arXiv + NeurIPS/ICLR workshop + AGI-2 顺提
- 顶会一作定位 = 博一目标

## 8 · 时间线

**Meeting 前（7/11-12，本周末）**：
- 7/11 上午：requirements + fetch_data + solver 骨架 + smoke test（已完成）
- 7/11 下午：跑满 ARC-1 training 400 题，记录 baseline
- 7/12：Akyürek TTT 精读笔记 → `notes/07_akyurek_ttt.md`
- 7/13 早：把数字填回 §6.5，准备 meeting

**Meeting 后（7/14-）**：
- 7/14-15：Li 2024 induction⊕transduction 精读
- 7/16-20：Direction A 架构蓝图 → `notes/08_direction_A_blueprint.md`
- 7/21+：DSL 扩到 Hodel-level，开始跑消融

## 9 · 问陈老师
1. A / B 方向反应？
2. discrete operator framing 靠谱吗？
3. 期望 deliverable？
4. Group meeting / 师兄推荐？
5. H800 算力权限？
