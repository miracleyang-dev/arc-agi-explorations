# 04 · Meeting Outline · 2026-07-10 15:00

带：`notes/02` + arcprize.org/play

## 0 · 开场
4 天从零起步。今天讲：ARC / why hard / landscape / 我的方向。

## 1 · What is ARC
- Task = few input→output demo + test input
- ARC-1 400/400，ARC-2 1000/120
- 3-5 demo，pass@2；人类 ≥80%，SOTA ~55%/~10%
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
- 4→2 合并见 `notes/02 §1.3`

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

## 7 · Target
- **ARC Prize 2026 Paper Track**，deadline **11-09**
- 同工作：arXiv + NeurIPS/ICLR workshop + AGI-2 顺提
- 顶会一作定位 = 博一目标

## 8 · 下周
- 7/11-13：ARC Prize 2024 Tech Report + Akyürek TTT
- 7/14-17：minimum viable ARC solver
- 7/18：Direction A 架构蓝图

## 9 · 问陈老师
1. A / B 方向反应？
2. discrete operator framing 靠谱吗？
3. 期望 deliverable？
4. Group meeting / 师兄推荐？
5. H800 算力权限？
