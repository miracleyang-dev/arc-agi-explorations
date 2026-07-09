# 04 · Meeting Outline · 2026-07-10 15:00 with Prof. Chen

白板 + 现场讲。25 min 讲 + 讨论。
带：`notes/02` (coverage matrix + 3.11 `6e02f1e3` + 3.15 `ded97339`)、arcprize.org/play。

---

## 0 · 开场
过去 4 天从零起步，讲：ARC 是什么、为什么难、社区做到哪、我的方向。

## 1 · What is ARC
- Task = 2-3 组 input→output grid + test input
- ARC-1: 400/400；ARC-2: 1000/120（更抽象）
- 3-5 demo，pass@2；人类 ≥80%，SOTA ~55% (ARC-1) / ~10% (ARC-2)
- 掐死同分布 fine-tune

## 2 · Why hard（白板举 2 题）
- **`6e02f1e3`**：数颜色种数 k → 决定 3×3 pattern。两阶段（count 再 lookup）。神网学不到中介变量。
- **`ded97339`**：同行/列成对蓝点连线。配对+共线+画线三步组合，pixel/object level abstraction gap。
- 归纳：few-shot + 高抽象层 + 组合搜索空间大

## 3 · Chollet framework
- $I = \dfrac{\text{达标任务}}{E + P}$：少数据少先验 = 智能
- 4 core priors: Objectness / Agentness / Numbers / Geometry

## 4 · Taxonomy（白板画简化 matrix）
```
        T1 sym  T2 grav  T3 recolor  T4 crop  T5 fill  T6 count  T7 tile  T8 draw
P1 obj                   ✓                                       ✓
P2 goal          ✓
P3 num                   ✓                              ✓
P4 geom  ✓                                    ✓                          ✓
```
- 15 seed 已分类（`notes/02`）
- 空 cell = 现有方法盲区（P3×T2 全空）
- 4 prior 合并成 2 组的理由：ARC 里两两耦合出现，见 `notes/02 §1.3`

## 5 · Landscape
| 族 | 代表 | 短板 |
|---|---|---|
| Program synthesis / DSL | Icecuber, Hodel | 组合爆炸 |
| Neuro-symbolic | DreamCoder | 训练重 |
| LLM 直推 | Greenblatt GPT-4o ~50% | 昂贵、ARC-2 崩 |
| **TTT (SOTA)** | Akyürek 2024 | 每 test 重训 |

共同盲区：中介变量缺失；pixel level ≠ object level 组合。

## 6 · 方向（讨论重点）
**A · ARC as few-shot discrete operator learning**
- Task 看作 discrete operator，few-shot 学 $f: X \to Y$，架构参考 neural operators
- 对接老师"learning operators from data"
- 主要靠 empirical，风险中

**B · Differentiable proxy for skill-acquisition efficiency**
- 给 $\dfrac{S}{E+P}$ 造可微上界，塞进 loss
- 挂 PAC-Bayes / meta-learning，discussion 里推半页
- 理论那步无 debug 支持，风险高

**倾向**：A 主 + B 挂讨论（future work）

## 7 · 时间线 & 目标产出
- **ARC Prize 2026 Paper Track** deadline **2026-11-09**（主目标）
- 同一份工作：arXiv preprint + 一个 NeurIPS/ICLR workshop（备选）+ ARC-AGI-2 主赛顺手提
- 顶会一作定位为博士第一年目标，不 over-promise

## 8 · 下周
- 7/11-7/13：读 ARC Prize 2024 Tech Report + Akyürek TTT paper
- 7/14-7/17：跑 minimum viable ARC solver
- 7/18：Direction A 架构蓝图 → 下次 meeting

## 9 · 问陈老师
1. A / B 方向反应？先都试还是砍一条？
2. "Task as discrete operator" framing 有坑吗？
3. 期望 deliverable：report / arXiv / codebase？
4. Group meeting / reading group / 可讨论 ARC 的师兄？
5. H800 算力权限怎么走？

---

**时间不够砍**：§5 只讲表头；§6 只讲 A。
**没准备的问题**：ARC-2 还没系统看；TTT 只读 blog；taxonomy 无 formal metric（下步加 DSL length + human solve time）。
