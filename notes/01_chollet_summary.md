# 01 · On the Measure of Intelligence (Chollet, 2019) 精读笔记

> Chollet, F. (2019). *On the Measure of Intelligence*. arXiv:1911.01547
> 精读日期：2026-07-08

---

## 一、这篇论文到底在解决什么问题

深度学习基准（ImageNet、Atari、GLUE）的共同特点是：**给模型足够多的同分布训练数据 + 足够大的算力，就能刷分**。作者认为这类基准无法区分「学到了能力」和「记住了模式」——一个足够大的模型可以在完全不理解任务的情况下拿到 SOTA。

于是 Chollet 想为「智能」下一个**可操作的定义**，并配套一个**能真正测量它的基准**。ARC（Abstraction and Reasoning Corpus）就是这个定义的实例化。

论文分两部分：

1. **前半（Section I–II）**：批判现有 AI 评价体系，提出智能的形式化定义。
2. **后半（Section III）**：把定义翻译成基准 ARC 的设计原则与实现。

---

## 二、核心哲学立场

Chollet 反复强调一句话：

> **Intelligence is skill-acquisition efficiency**，不是 skill 本身。

含义拆开看：

- 会下国际象棋（skill）≠ 智能。深蓝会下棋不代表深蓝有智能，它只是被塞了大量领域知识 + 搜索算力。
- 智能是「面对**从未见过**的任务，用**尽量少的先验和经验**，尽量快地获得解决该任务的技能」的能力。
- 因此测量智能要控制三个变量：**先验（priors）**、**经验（experience）**、**技能泛化范围（generalization scope）**。

这里作者反对两种流派：

| 流派 | Chollet 的态度 |
|------|----------------|
| 图灵测试 / 类人智能（Turing, Legg-Hutter） | 太主观，无法测量 |
| 「通用性能」压缩派（Solomonoff / AIXI） | 数学漂亮但不可实现，且忽略先验 |

他要走的是**中间路径**：承认智能一定依附于某组先验（人类的核心知识），但要在**任务的多样性、先验的显性化、经验的有限性**上做严格约束。

---

## 三、关键公式（本文最重要的内容）

对某个智能系统 $IS$，在任务空间 $\text{scope}$ 上的智能定义为：

$$
I_{IS}^{\text{scope}} = \mathbb{E}_{T \sim \text{scope}} \left[ \omega_T \cdot \theta_T \cdot \frac{\sum_{\text{curr}} P_C \cdot [S_{\min}(\text{curr}) > \theta_T]}{\sum_{\text{curr}} P_C \cdot (E_{IS,T,C} + P_{IS,T})} \right]
$$

**符号定义**（Chollet 2019 §II.3）：
- $IS$：被评估的智能系统本身
- $\text{scope}$：任务空间（ARC 里 = 所有满足 core-priors 约束的 grid task）；$T$ = 从中采样的单个任务
- $\omega_T$：任务权重（相对重要性）；$\theta_T$：技能阈值，超过它才算"会做"（ARC 实操 = pass@2 正确）
- $\text{curr}$ (curriculum)：一段学习经历，即 IS 在解题前接收的样本序列；$P_C$ = 该 curriculum 出现的概率
- $S_{\min}(\text{curr})$：训练该 curriculum 后 IS 在 $T$ 上取得的**最低**技能水平；$[\cdot]$ 是 Iverson 括号（真=1 假=0）
- $E_{IS,T,C}$：**经验成本**——消化 $C$ 所耗样本/算力；$P_{IS,T}$：**先验成本**——开始前已内嵌的相关先验（预训练、归纳偏置）

看不下去公式的话，只记住**分子分母的直觉**：

- **分子**：模型在任务 $T$ 上达到的技能水平（超过阈值 $\theta_T$ 才算数），并按任务难度加权。
- **分母**：为达到该技能，系统消耗的**经验 $E$**（训练样本数、试错次数）+ 携带的**先验 $P$**（预训练知识、内置归纳偏置）。

**结论**：智能 = 技能 ÷（先验 + 经验）。少给数据少给先验还能解决新任务，才叫智能。

这就直接解释了 ARC 的两条设计规则：

1. 每个任务只给 3–5 个 demonstration pair（**极小样本**）。
2. 所有任务只依赖「人类核心知识先验」，不需要文化知识（**先验可枚举**）。

---

## 四、Core Knowledge Priors（人类核心先验）

Chollet 借鉴发展心理学（Spelke, Dehaene），列出**每个 ARC 任务都可以只用这四类先验解决**：

1. **Objectness**：世界由离散、持续存在的物体组成；物体有边界、可移动、可粘连、可包含。
2. **Basic agentness / goal-directedness**：识别「意图」——比如某个物体在朝某个方向移动、或在对齐、或在避开另一个物体。
3. **Numbers & counting**：小整数、比较大小、计数、加减。
4. **Basic geometry & topology**：形状、对称、旋转、镜像、缩放、路径、内外、连通性。

**为什么显性化先验很重要**：如果一个基准需要「阅读理解」或「常识」，你根本分不清模型是靠智能解决的，还是靠训练语料里刚好有相似内容。ARC 把先验列清楚了，任何超出这四类的知识都不允许被利用——这也是它至今难以被 LLM 攻破的核心原因。

---

## 五、Developer-aware Generalization（关键概念）

作者区分四种泛化：

| 层级 | 含义 | 例子 |
|------|------|------|
| No generalization | 记忆 | 查表 |
| Local generalization | 同分布插值 | ImageNet 分类 |
| Broad generalization | 分布外但相似任务族 | 迁移学习 |
| **Extreme / developer-aware generalization** | 面对**开发者本人也未预见**的任务 | ARC |

第四层是 ARC 的目标。测试集里的每个任务，**其抽象方式在训练集里没有出现过**——这就掐死了「暴力枚举 DSL / 靠训练集穷举」的路子。

---

## 六、ARC 基准的具体设计

- **800 个任务**：400 training + 400 evaluation（ARC-AGI-1；ARC-AGI-2 已扩到 1000/120）。
- 每个任务是几个 input→output 的 grid pair（1×1 到 30×30，10 种颜色）。
- 人类求解率 ≥ 80%；2019 年提交时最好机器仅 20%（现在 SOTA 因 LLM+TTT 已推高，但仍远未饱和）。
- **私有测试集**：防止过拟合，评价永远在从未公开的任务上跑。

Chollet 认为一个通过 ARC 的系统必须具备：**program synthesis 能力 + 对 core priors 的显性建模 + 从极少样本中提炼抽象规则的能力**。

---

## 七、批注

1. **智能定义里的 $\omega_T$ 和 $\theta_T$ 怎么定？** 论文并未给出公认的加权方案，实际上后续所有 ARC 榜单都用「pass@k」代替这个理论公式——这是理论与实践的第一个 gap。
2. **Core priors 的完备性**存疑。人类除四类核心先验外还有语言、社会、时间等，为什么这些能在 ARC 里被安全排除？部分任务事实上仍需要「因果」直觉。
3. **Extreme generalization 是否可测**？如果测试任务来自开发者未预见的分布，如何构造？现实中 ARC-AGI-2 靠**人工作坊 + 私有集** 逼近这一点。
4. **和当前 LLM+TTT 路线的张力**：现在的最强方案本质是「在测试时对少量 demo 做梯度更新」，这算不算「消耗经验」？如果算，如何在评分里扣除？——这是我读完最想深挖的一点，可能是下一步阅读方向。
5. **对我自己**：如果做研究的话，最有意思的角度是**把 skill-acquisition efficiency 公式化到可微框架里**——目前它更像哲学声明而非可优化目标。这是不是能连到「meta-learning 的 sample complexity 理论」上？值得查。

---

## 八、总结

> ARC 不是要「让模型学会解题」，而是要**测量模型在最少先验 + 最少经验的条件下、面对开发者都没见过的任务时、能否即时抽象出规则并泛化**。这也是它现阶段仍然阻挡 LLM 的核心原因——LLM 强在利用海量先验，弱在**约束住先验后的即时抽象**。
