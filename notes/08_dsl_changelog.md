# 08 · DSL Changelog & 版本对照

> 目的：记录 solver DSL 每一版都加了什么、为什么加、加完效果如何。
> 一个方法一句话，一行看得清。所有原语在 `solver/dsl.py`。

---

## 版本 → solve rate 曲线（ARC-1 training, depth≤2, 5s/task）

| 版本 | Primitives | Solved / 400 | Solve rate | 新命中来源 | 耗时 |
|------|-----------|--------------|-----------|-----------|------|
| v1 (7/11 AM) | 63  | 10 | 2.5%  | 起点     | 27s |
| v2 (7/11 PM) | 170 | 19 | 4.75% | +9，全来自 `crop_bbox_nz` / `gravity_*` / `scale_*` / 组合  | 204s |
| v3 (7/11 PM, 计划) | 197 | ? | ? | 目标 8-12% | ~5min |

**规律观察**：63→170（+170% 原语）只换来 solve rate 1.9×。**边际递减**。
v3 是**最后一版 DSL**——之后精力全给 Direction A。

---

## 全部原语清单（按版本）

### v1（63 个）— 几何 + 对称换色 + 背景填充

| 组 | 原语 | 说明 |
|---|---|---|
| identity | `identity` | 恒等（占位 & 有时确实是解） |
| geometric | `rot90`, `rot180`, `rot270`, `flip_h`, `flip_v`, `transpose` | D4 群 6 个操作 |
| reshape | `tile_2x2`, `crop_tl_half` | 2×2 复制、左上四分之一裁剪 |
| color swap | `swap_a_b` for 0≤a\<b≤9 | 对称换色 45 个 |
| bg fill | `fill_bg_c` for 1≤c≤9 | 把 0 换成 c，9 个 |

### v2 增量（+107 个，总 170）— 定向换色 + 物体抠取 + 引力 + 缩放

| 组 | 原语 | 数量 | 目标 |
|---|---|---|---|
| directional recolor | `map_a_to_b` for a≠b | 90 | 单向重涂（跟 swap 互补） |
| object mask | `keep_only_c` for c∈1..9 | 9 | 只留颜色 c，其余归零 |
| gravity | `gravity_{up,down,left,right}` | 4 | 非零元素向一边下坠 |
| bbox crop | `crop_bbox_nz` | 1 | 裁到非零像素的紧包围盒 |
| full sym | `anti_transpose` | 1 | 反对角翻转，补齐 D4 |
| scale up | `scale_2`, `scale_3` | 2 | 每格 → k×k 块 |

**v2 实测最有用的**（按 solved 题里的出现频次）：
- `crop_bbox_nz`（5 题）— 显著大于其他 v2 新增
- `gravity_up/down`（各 1）
- `scale_2/3`（各 1）

**加了但没贡献**：全部 90 个 `map_a_to_b`——ARC-1 里"单向重涂"几乎从不独立出现，总是和抠对象/换尺寸绑定。这条经验记下来：**别再赌参数化重涂**。

### v3 增量（+27 个，总 197）— 结构化操作

| 组 | 原语 | 数量 | 目标题型 |
|---|---|---|---|
| connected components | `keep_largest_obj`, `outline_objects`, `interior_of_objects` | 3 | 最大物体、描边、内域 |
| symmetry from half | `sym_h_from_{left,right}`, `sym_v_from_{top,bottom}` | 4 | 半边镜像补全 |
| symmetry OR overlay | `overlay_{flip_h,flip_v,rot180,transpose}_or` | 4 | 残缺输入的对称重构（逐元素 max） |
| self stacking | `hcat_self`, `hcat_flip_h`, `vcat_self`, `vcat_flip_v` | 4 | 沿一轴翻倍拼接 |
| shape reduction | `remove_empty_rows`, `remove_empty_cols`, `binarize_nz_to_1` | 3 | 压缩空行/空列、二值化 |
| enclosed fill | `fill_enclosed_c` for c∈1..9 | 9 | 洪水填充内部 0 区（不含从边界可达的 0） |

---

## 设计约束（自我强制，避免 DSL 无限膨胀）

1. **纯 Grid → Grid**：每个原语都是 `tuple[tuple[int,...],...] -> tuple[...]`，无副作用，无外部状态。这让 depth-2 暴力枚举可控。
2. **无隐式参数**：颜色 / 方向 / 尺度都在**生成 primitives 时展开**成有名字的具体函数（如 `swap_1_2`, `gravity_up`），不留给搜索器猜。
3. **确定性**：同输入总同输出，没有随机 tie-break。
4. **对空 grid 安全**：所有 primitive 遇到 0×0 输入直接返回 0×0，避免 IndexError 打断搜索。

---

## 冻结声明（v3 之后不再扩 DSL）

理由：
- ARC 里剩下的 solve 难点是**counting / connected-components-with-context / pattern-generation / test-input-conditioned rules**，纯 Grid→Grid 已经吃不到。
- 边际 solve rate / 边际原语 数量 已跌破 0.03（v1→v2 是 0.14，v2→v3 我们观察）。
- 目标转向 Direction A：**operator learning**——让模型学 primitive selector 或直接生成 primitive，而不是靠人肉扩 DSL。

---

## 附：怎么复现

```cmd
.venv\Scripts\activate
python -m solver.runner --split training --max-tasks -1 --depth 2 --budget 5
```

结果落在 `solver/results/arc-agi-1_training_<timestamp>.json`。
