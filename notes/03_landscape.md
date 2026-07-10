# 03 · ARC-AGI 主流方法路径（必读清单 + 框架汇总）

> 更新日期：2026-07-08
> 目的：在正式动手之前，摸清楚这个赛道过去被走过的路，看相关的优劣。

---

## 一、必读论文 / 报告（5 篇，按顺序读）

| # | 论文 / 报告 | 为什么必读 | 链接 |
|---|-------------|------------|------|
| 1 | Chollet, F. *On the Measure of Intelligence*. arXiv:1911.01547 (2019) | 立论文，定义 ARC。已经精读过。 | https://arxiv.org/abs/1911.01547 |
| 2 | Chollet et al. *ARC Prize 2024: Technical Report*. arXiv:2412.04604 (2024) | 官方复盘 2024 竞赛，所有 top 方案的思路、消融、失败模式都在这一篇里；比读 5 篇零散论文效率高。 | https://arxiv.org/abs/2412.04604 |
| 3 | Greenblatt, R. *Getting 50% on ARC-AGI with GPT-4o* (2024, blog + code) | 用大模型 + 大规模程序采样 + Python 执行验证，第一次把 LLM 路线推到 50%+。定义了「LLM as program generator」范式。 | https://redwoodresearch.substack.com/p/getting-50-sota-on-arc-agi-with-gpt |
| 4 | Akyürek et al. *The Surprising Effectiveness of Test-Time Training for Abstract Reasoning*. arXiv:2411.07279 (2024) | MIT 组，把 test-time training (TTT) 这一路线写清楚了。2024 ARC Prize 私榜第一（55.5%）就是 TTT 方案。 | https://arxiv.org/abs/2411.07279 |
| 5 | Ellis, K. et al. *DreamCoder: Growing generalizable, interpretable knowledge with wake-sleep Bayesian program learning*. Philos. Trans. R. Soc. A (2023, 原 arXiv:2006.08381, 2020) | 程序合成路线的巅峰之作，虽然本身不是 ARC 论文，但要理解「为什么大家一开始都试 program synthesis」，必读这篇的 DSL + wake-sleep 框架。 | https://arxiv.org/abs/2006.08381 |

**读法建议**：1 已完成 → 2 是主线（一定精读）→ 3、4 只需读关键 section（method + 结果 + 局限）→ 5 泛读，理解思想即可。

---

## 二、方法路径框架汇总（自制）

ARC 6 年里被反复尝试的路子，可以整理成四条主线。每条主线包含：**核心思想 / 代表工作 / 打到多少分 / 为什么卡住**。

### 路线 A：Program Synthesis（DSL + 搜索）

- **核心思想**：手工设计一个 DSL（含 rotate、fill、count、pattern-match 等原语），对每个任务在 DSL 里搜索能同时解释所有 demo pair 的最短程序。
- **代表工作**：icecuber 的 2020 Kaggle 冠军方案（20%）；DreamCoder；Hodel 的手写 DSL。
- **优势**：可解释、无幻觉；命中即 100% 正确。
- **卡点**：DSL 覆盖不到的抽象（如「找出唯一不对称的物体」这类语义先验）就完全无解；组合爆炸；DSL 的边界即模型的边界。
- **2024 后地位**：单独作为主策略基本被淘汰，但被吸收进混合方案的「验证器」。

### 路线 B：Neuro-symbolic / Neural-guided Search

- **核心思想**：神经网络学一个「策略」来剪枝 DSL 搜索空间，或直接生成候选程序，再用符号执行验证。
- **代表工作**：DreamCoder（wake-sleep）；CodeIt (2024)；Hypothesis Search (2023)。
- **优势**：结合了神经的模式识别 + 符号的严格性。
- **卡点**：训练数据稀缺——ARC training set 只有 400 题，撑不起一个大网络；需要合成任务扩充数据，但合成数据分布和真实测试差距大。
- **2024 后地位**：仍是活跃研究方向，尤其和 LLM 结合后，成为主流之一。

### 路线 C：LLM 直接推理（Prompt / CoT / Program Emission）

- **核心思想**：把 grid 序列化成文本 / 图像塞给 LLM，让它输出预测网格，或输出一段 Python 程序去解题。
- **代表工作**：
  - Greenblatt 2024（GPT-4o + 大规模 Python program sampling + execute-and-verify，达到 ~50%）。
  - Anthropic Claude 3.5 直接推理（~14%，不做程序生成）。
  - o3 (2024 年 12 月 OpenAI 官宣) 在 semi-private 上达到 75.7%（low compute）/ 87.5%（high compute）——但 high compute 单题成本 ~$3400，被 ARC Prize 判为不满足 efficiency 约束。
- **优势**：直接吃 LLM 的世界知识；工程简单。
- **卡点**：token 化后颜色 / 坐标信息损失；推理不稳定，需要几十上百次采样投票；成本极高。
- **2024 后地位**：SOTA 主力之一，但被 efficiency 指标反噬。

### 路线 D：Test-Time Training（TTT）

- **核心思想**：拿到一个测试任务的 demo pair 后，**临时对预训练模型做几步梯度更新**（LoRA / 全参数微调都可以），然后再预测。相当于把「in-context learning」变成「in-context fine-tuning」。
- **代表工作**：
  - Akyürek et al. 2024（arXiv:2411.07279）：8B 模型 + TTT，ARC-AGI-1 private set 达到 61.9%。
  - MindsAI 团队 2024 Kaggle 冠军方案（55.5%）本质是 TTT + augmentation ensembling。
- **优势**：在有限先验下，每个测试任务都得到「定制化」的模型；对小样本抽象特别有效。
- **卡点**：每题都要重训，计算贵；augmentation 策略（旋转、颜色置换、转置）是黑魔法，泛化性存疑；Chollet 本人质疑这在概念上是否违反「efficiency」约束。
- **2024 后地位**：当前 ARC-AGI-1 上性价比最高的路线，2024 ARC Prize 冠军就是这类。

---

## 三、混合方案与前沿趋势（写这篇时的观察）

- **ARC-AGI-2 (2025 发布)**：为了阻挡 LLM+TTT，新任务显著变难，SOTA 快速回落到 5% 附近（人类仍 ~60%）。TTT 单打独斗不够用了。
- **趋势 1：LLM + program synthesis 混合**——LLM 出候选程序，符号执行器筛选。（Greenblatt 是这套的原型。）
- **趋势 2：Meta-learning on augmented tasks**——用 procedural task generator 造几十万题预训练，再在测试时 TTT。
- **趋势 3：多模态 grid 表示**——把 grid 转成图片 + 文本双输入，缓解 token 化的信息损失。
- **趋势 4：把 skill-acquisition efficiency 这个理论量搬进优化目标**——目前几乎没人做，可能是能出 novelty 的方向。

---

## 四、阅读顺序建议（对齐我的时间盘）

| 时间 | 任务 |
|------|------|
| 7/8（今晚） | 读 arXiv:2412.04604（ARC Prize 2024 Tech Report），做本 note 的迭代补充 |
| 7/9 | 读 Greenblatt blog + Akyürek TTT 论文的 method section |
| 7/9 晚 | 写 `notes/02_task_taxonomy.md`（10 个手解任务的先验分类）|
| 7/10 见导师前 | 泛读 DreamCoder 简介，能讲清 4 条路线区别即可 |

---

## 五、待考证 / 有疑问的点

- Akyürek 2024 的 61.9% 是 semi-private 还是 public？两个数字都在流传，需要看原论文附录确认。
- o3 的成本是否可以线性外推 ARC-AGI-2？现有报告没给。
- 「skill-acquisition efficiency 可微化」是否已有前置工作？需要找 meta-learning sample complexity 的最新综述。
