# 05 · Meeting Outline · 2026-07-13 10:00

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

## 6.5 · Baseline（7/11-12 已跑）
- 手写 DSL 63 原语（geometric / color-swap / fill / crop / tile）+ 暴力 depth≤2 搜索
- `solver/` 骨架 + smoke test 已过；`python -m solver.runner --split training --max-tasks -1` 一键复现
- **预期数字**：ARC-1 training 上 solve rate ~10-15%（对齐 icecuber 2020 的 depth-2 部分）
- **实际数字**：TODO 填入（跑完后更新）
- **意图**：不是要打分数，是**建立可复现测量框架** —— 后续 Direction A 的每个改动都要在同一个 harness 上跑，回归看得见

## 7 · Target
- **ARC Prize 2026 Paper Track**，deadline **11-09**
- 同工作：arXiv + NeurIPS/ICLR workshop + AGI-2 顺提
- 顶会一作定位 = 博一目标

## 8 · 时间线

**Meeting 前（7/11-12，本周末）**：
- 7/11 上午：requirements + fetch_data + solver 骨架 + smoke test（已完成）
- 7/11 下午：跑满 ARC-1 training 400 题，记录 baseline
- 7/12：Akyürek TTT 精读笔记 → `notes/06_akyurek_ttt.md`
- 7/13 早：把数字填回 §6.5，准备 meeting

**Meeting 后（7/14-）**：
- 7/14-15：Li 2024 induction⊕transduction 精读
- 7/16-20：Direction A 架构蓝图 → `notes/07_direction_A_blueprint.md`
- 7/21+：DSL 扩到 Hodel-level，开始跑消融

## 9 · 问陈老师
1. A / B 方向反应？
2. discrete operator framing 靠谱吗？
3. 期望 deliverable？
4. Group meeting / 师兄推荐？
5. H800 算力权限？
