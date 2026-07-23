# 论文精读要点：SoK: The Evolution of MEV, From Miners to Cross-Chain

## 论文与本周用途

- 文献：Mancino, D.; Sevim, H. O. *SoK: The Evolution of Maximal Extractable Value, From Miners to Cross-Chain*，2026。
- 本地文件：`文献收集/06_SoK_MEV_Evolution_CrossChain.pdf`。
- 本周只用于厘清定义、测量边界和研究位置；不把该文的跨域综述当作 Arbitrum 跨层对象已经可映射、已存在 MEV 的证据。

## 两页 PPT 采用的可核验内容

| PPT 要点 | 文中依据 | 对本项目的作用 |
|---|---|---|
| 用 `single-domain / cross-domain` 与 `potential / realized` 两条轴组织 MEV | 摘要、引言和 Sec. II（pp. 1–2） | 强制区分问题属于单一排序域还是需要联合排序，以及问题是理论可能还是经验已实现。 |
| domain 是指定角色控制状态变更顺序的系统；Rollup 通常由 Sequencer 排序 | Sec. II-B（p. 2） | 先界定 L1、L2、bridge/message lifecycle 中每一个可能的 ordering domain。 |
| potential 不是 realized；两者差异受竞争、执行失败、延迟、交易成本等影响 | Sec. II-E（pp. 2–3） | 说明“可见窗口”“靠前位置”或“时间差”不足以直接报告为收益或攻击。 |

## 对当前研究问题的直接启发

1. **对象优先于时间差。** 跨层研究不能把 batch publication 与用户 L1→L2 message 生命周期等同；必须说明对象在哪个域中被创建、排序和执行。
2. **收益判断需要见证链。** 本项目把 SoK 的 potential/realized 区分落实为：可见性 → 行动能力 → 前置状态 → 有效反事实顺序 → 扣除成本的净收益。
3. **Sequencer 是角色，不是结论。** 单 Sequencer 给出可能的排序控制点，但不等于其恶意、自营、合谋或已经提取收益。

## 不可外推的部分

- 该文是跨域 MEV 的 SoK，不提供本项目某一类 Arbitrum message 的唯一映射规则、private first-seen 时间或反事实利润重放结果。
- 该文的通用 taxonomy 不能替代 V0 对官方对象语义和 V1 小样本链路的核验。
- 文中概述的其他工作或统计不能被转写为本项目的经验发现。

