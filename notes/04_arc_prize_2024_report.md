# 04 · ARC Prize 2024: Technical Report (Chollet et al., 2024) 精读笔记

> Chollet, F., Knoop, M., Kamradt, G., Landers, B. (2024). *ARC Prize 2024: Technical Report*. arXiv:2412.04604v2
> 精读日期：2026-07-10

---

## 一、这份报告在干什么

不是一篇 method paper，是**2024 一整年 ARC 竞赛的官方复盘**。作者视角：Chollet + 主办方，四个人共同署名。

三件事：
1. 报账：2024 年 SOTA 从 33% → 55.5% 的具体来源。
2. 归纳：把这一年冒出来的 top approaches 按**三类方法框架**梳理（program synthesis / TTT / 两者组合）。
3. 反思：为什么 ARC-AGI-1 已经不够用了，为什么要做 ARC-AGI-2。

对我们这种要"补齐 landscape"的入行者，这一篇价值在于**它替你读完了所有 top solution paper 并做了 taxonomy**——比自己去啃 5 篇 solution write-up 效率高。

---

## 二、关键数字（要记牢）

**Dataset structure**：
- ARC-AGI-1 = 1000 tasks，四拆：400 public training（easy）/ 400 public evaluation（hard）/ 100 semi-private eval（hard）/ 100 private eval（hard）
- **SOTA 只在 private eval 上报告**——防止过拟合
- Semi-private vs public eval：如果一个方案两个数字差 > 10%，判为 overfit

**Human baseline**（NYU H-ARC 2024）：
- 原始 private eval 两个人分别 97% / 98%，合起来 100%
- Mechanical Turk workers：99% 的 public eval task 至少有 1 人做对（每题 10 人）

**竞赛物理约束**（Kaggle 主赛道）：
- 单 P100 GPU / 12 小时 / 无网络
- 单题算力预算 ≈ $10（对比 ARC-AGI-Pub 主赛道允许 $10,000 API 花费——差 1000×）
- 4 年 SOTA 演化：2020→20% (icecuber, brute-force DSL), 2022→28.5%, 2023→31.4%, 2024→**55.5% (MindsAI, TTT, 未开源)**

**Kaggle 2024 top 5**（都开源）：

| 名次 | 队 | Private eval | 方法 |
|------|----|------|------|
| 1 | the ARChitects | 53.5% | TTT (NeMo-Minitron-8B) + augmentation-stability selection |
| 2 | Guillermo Barbadillo | 40% | OmniARC: Qwen2.5-0.5B TTT + program synthesis ensemble |
| 3 | alijs (Agnis Liukis) | 40% | pure brute-force DSL search |
| 4 | William Wu | 37% | — |
| 5 | PoohAI | 37% | — |

MindsAI 55.5% 因为没开源，无奖。

**Pub leaderboard**（API 无限花钱）top：
- Jeremy Berman 53.6% (semi-private) / 58.5% (public)
- Akyürek et al. 47.5% / 62.8%
- Greenblatt (GPT-4o 直推) 43% / 42%
- 大模型直接 pass@1：o1-preview 18%/21%，Claude 3.5 Sonnet 14%/21%，GPT-4o 5%/9%，Gemini 1.5 4.5%/8%

**惊人的观察**：Kaggle 12h/$10 场景下最好 53.5%，vs API $10k 无限时场景下最好 53.6%——**多花 1000× compute 几乎没换来任何分数**。这直接反证了「暴力堆 compute 不是 ARC 的钥匙」。

---

## 三、三条主线方法（本文最核心的分类）

### 主线 A · Deep learning-guided program synthesis

思想：LLM 生成候选程序 → 代码解释器执行 → 拿 demo pair 验证 → 选最短能过的。

四种子形式：
1. **DSL brute-force search**：Hodel DSL、icecuber 20% (2020)、alijs 40% (2024)。上限被 DSL 边界钉死。作者透露一个关键数据：**把 2020 年所有队的答案取并集，恰好 49% 的 private eval 已经被 brute-force 类方案覆盖**——意思是「ARC-AGI-1 的一半在 2020 年就技术上可解，只是没被单一系统整合」。
2. **LLM 开放式生成 Python** (Greenblatt)：GPT-4o 单题采样几千个 Python 程序，代码执行验证，选过的那个。42%。
3. **LLM-guided DSL search** (Ouellette)：LLM 当 DSL 搜索的启发式，剪枝。
4. **LLM 迭代 debug**：拿"接近但不对"的程序让 LLM 改。Greenblatt 的第二个 trick。

**作者预测**：如果按 Greenblatt 那套方法要打到 85%，粗算需要**每题采样 ~10^8 个程序**，成本达到几百万美元级别——即"能做到但完全不 efficiency"。所以纯 program synthesis 的 scaling 是**死路**。

**作者暗推**：未来更值得试的是 **AlphaProof 式的 branching-guidance**——用小模型指导搜索树，而不是每次生成完整候选。这是 report 里少见的"作者主动提示未来 direction"的段落，值得高亮。

### 主线 B · Test-Time Training (TTT)

思想：拿到 test task 后，**用它的 demo pair 对预训练 LLM 做几步 fine-tune（LoRA / 全参）**，然后再让它直接 transduce（不写程序、直接吐 output grid）。

**关键论断**（原文）：
> 所有 top LLM-based transduction 方案都用 TTT；不做 TTT 的 static inference 方案没有一个超过 11%。

这句话意思是：**LLM 本身在 ARC 上零迁移能力接近零；TTT 是让 LLM 能沾边的唯一路径**。

四个要素：
1. **数据增强 / 预训练扩展**：ARC-Heavy/ARC-Potpourri (Ellis 400k 合成题) + Re-ARC (Hodel 无限重采样 400 training 题) + 各种旋转/颜色置换。
2. **微调策略**：LoRA vs full-fine-tune 都被试过；每题独立 fine-tune。
3. **2D-aware 架构**：Puget/NVIDIA 的 2D nGPT，用 2D 位置编码/attention。

TTT-in-2024 名单：OmniARC (Qwen2.5-0.5B) / Akyürek (8B, 53% on public) / MindsAI (T5 系列, 55.5% private) / ARChitects (NeMo-Minitron-8B, 53.5% private)。

**变种**：Bonnet & Macfarlane "Latent Program Networks"——不做梯度也不做离散搜索，而是**在 LLM 潜空间做随机搜索 + gradient descent**，找一个"程序表示"。理论新，得分弱，但概念上开辟了第三条路。

Chollet 亲自说的观点（这段很关键）：
> TTT 概念上和 program search 是**同一件事的两端**：都是"用预存 building block 的重组来解题"。program search 是**深度重组少量通用原语**；TTT 是**浅重组大量特化 building block**（LLM weights 里的向量函数）。

这个 framing 值得记住——它把两条路统一在了"combinatorial recombination"的抽象下。以后写 paper 想批评"TTT 违反 efficiency"或者"program synthesis 太脆"都要绕过这个 framing。

### 主线 C · Induction ⊕ Transduction

**关键观察**：program search (induction) 和 TTT (transduction) 解出的**任务集不重合**——即使两者分数都在 40% 左右，它们各自覆盖的题不太一样。

**推论**：所有 2024 top scorer（ARChitects, Barbadillo, Akyürek, Berman）**都是两条路 ensemble**。单一 induction-only 或 transduction-only 上限 ~40%。

这个 finding 出自 Li et al. 的 paper award 一等奖论文 "Combining Induction and Transduction for Abstract Reasoning"（arXiv:2411.02272）。

**对我们做 novelty 的启示**：要么做 induction-only 到 50%+（比现在多 10%）、要么做 transduction-only 到 50%+，要么发明第三条 axis。Ensemble 已经是"标准工程动作"，不再是 novelty。

---

## 四、Paper Awards（另外一条评分线，值得盯）

除了 Kaggle 分数榜，ARC Prize 还有独立的 **Paper Award**，奖励 novel idea 不看分数。2024 名单：

| 名次 | 论文 | idea |
|------|------|------|
| 1 | Li et al. *Combining Induction and Transduction* | 两条路都解不同任务的实证证明 |
| 2 | Akyürek et al. *Surprising Effectiveness of TTT* | TTT 定式化 |
| 3 | Bonnet & Macfarlane *Searching Latent Program Spaces* | LPN 潜空间搜索 |
| 亚军 | ARChitects *LLM ARChitect* | augmentation-stability selection criterion |
| 亚军 | Barbadillo *Omni-ARC* | 多任务预训练 + TTT ensemble |
| 亚军 | Fletcher-Hill *Mini-ARC* | 小 transformer 也能做 |
| 亚军 | Ouellette *Neurally-guided Induction* | LLM 指导 DSL 搜索 |
| 亚军 | Puget *2D nGPT* | 2D position encoding |

**这条线对我们非常关键**：Paper Track 不要求刷分，novelty 就能上——**这也是 2026 我要投的赛道**。看 2024 的入选清单可以反推评委喜欢什么样的 idea：**明确的方法 taxonomy 贡献、可复现的开源实现、能启发下一年的框架性观察**。

---

## 五、ARC-AGI-1 已知缺陷（催生 ARC-AGI-2 的三条理由）

1. **Private eval 太小（100 题）** + **五年被打了上万次分**——每次评分都泄漏一点点信息，实际上已经有轻度过拟合风险。
2. **暴力 brute-force 的天花板 49%**——2020 年所有队并集就已达到，说明 ARC-AGI-1 有一半题**对 brute-force DSL 天生不设防**，无 AGI signal。
3. **难度分布不一致**——不同 eval 集之间的 human difficulty 不匹配，跨集比较不可靠。

对应 ARC-AGI-2 的设计动作（2025 发布）：
- 加大 semi-private 和 private 尺寸（分开一个"日常报告集"和一个"最终评分集"）
- 主动**剔除 brute-force 可解题**（这个动作直接决定了 SOTA 会跌回个位数）
- 校准 human difficulty 分布

---

## 六、报告里没明说但值得看到的东西

1. **1430 支队 / 17789 次提交 / $75k paper awards**——赛事规模远超 2020/2023，且未来会 annual 化。**这对我作为 2026 参赛者是好消息**：曝光度稳定、评委机制固定。
2. **主办方视 TTT 为「催化剂」而非终点**——原文："we expect TTT will be the primary technique ... won't be productionized for a couple of years – but ... should become popular from 2026 onwards"。**Chollet 明确点出 2026 是 TTT 从"实验室 SOTA"走向"被生产系统吸收"的窗口年**——正好是我们研究的时间点。
3. **"从 startup 到 corporate lab 都在做 ARC"**：Basis AI / Tufa Labs / Agemo / Symbolica 都是有 $1M+ 资金的团队。这意味着**"业余爱好者组合方法拿 SOTA"的窗口正在关闭**——2026 主赛道 SOTA 会被资金+算力挤占，**Paper Track 反而成了"个人研究者能拿名次"的唯一现实路径**。这一段严肃支持我们"以 Paper Track 为主"的决定。
4. **"algorithm improvements towards AGI hold significant power and massive compute may not be necessary"**——作者暗示 ARC 上算法 novelty 比算力更重要。这是给学术圈的定心丸，也是给"没有大集群的研究者"的邀请函。

---

## 七、批注

1. **报告的最大盲区：没提 few-shot 抽象在数学上到底是什么**。全篇讲的都是工程 taxonomy，没有一次尝试把"抽象效率"这个量做形式化——即使这是 Chollet 自己 2019 论文的核心。这是**留给学术的空档**，也是我们 Direction B 的落脚点（differentiable proxy for skill-acquisition efficiency）。
2. **"induction ∪ transduction ≠ solved"**——即使两条路合起来也只 55%，说明**存在一大类任务两条方法都不擅长**。这些任务是什么？报告没做误差 taxonomy——这是我们 taxonomy work（notes/02）能补上的 diagnostic gap。
3. **TTT 的 efficiency 争议**：Chollet 一方面承认 TTT 是 2024 SOTA，一方面在 ARC-AGI-2 里明确说要"惩罚这类 test-time compute 消耗"。这两个信号是矛盾的。**猜测**：ARC-AGI-2 会引入 per-task compute cap 或 Efficiency-adjusted score，把 TTT 打压回来。**如果这样做**，Direction A（把 TTT 当 discrete operator 学、避免每题重训）会突然价值飙升。
4. **两个未来 direction 作者亲自点了名**（值得追）：
   - "AlphaProof-style branch guidance for discrete search"——DeepMind 已经在 IMO 上做出来了，还没被搬到 ARC。
   - "TTT / 其 derivative 从 2026 起 become popular"——Chollet 预期 TTT 或其变体从 2026 起被产品化系统吸收。**这直接给我 Direction A 的时间价值背书**。
5. **对我自己的战略含义**：
   - Paper Track novelty > Kaggle score 榜——这是**已被 2024 数据验证**的策略。
   - 做 TTT 变体是红海，做 induction 单方向也是红海；蓝海是（i）efficiency 形式化、（ii）induction/transduction 之外的第三条 axis、（iii）ARC-AGI-2 上暴露的新盲区。
   - Chen 老师"operator learning"框架 → 天然贴 induction (few-shot function fitting) 但可以纳入 TTT 作为"每题定制的 operator"，两边都能连。

---

## 八、总结

> ARC Prize 2024 把 SOTA 从 33% → 55.5%，靠的是 **TTT** 和 **induction⊕transduction ensemble** 两件事。但对 AGI 目标 85% 而言仍有巨大 gap，且 Chollet 认为这个 gap **不能靠 compute 填**（Kaggle $10 vs Pub $10k 场景分数几乎相同）。真正的进步需要算法层面的 novelty——这也是 ARC-AGI-2 和未来 Paper Track 的存在理由。

**对我的三条 takeaway**：
1. Paper Track 是**当前最适合个人研究者的入场路径**——评委喜欢方法 taxonomy 和可复现开源。
2. **Induction ∪ Transduction ≠ 覆盖全部 ARC**——两条路都没解出的那批题是 next-year novelty 的富矿。
3. **Chollet 亲口预测 TTT 在 2026 主流化**——恰好是我们做研究的时点，Direction A 的时间窗匹配。
