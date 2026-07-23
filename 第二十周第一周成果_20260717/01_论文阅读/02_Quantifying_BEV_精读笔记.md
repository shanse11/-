# 02《Quantifying Blockchain Extractable Value: How dark is the forest?》精读笔记

> 来源：`文献收集/02_Quantifying_BEV_Flashbots.pdf`，PDF 共 17 页；以下页码按 PDF 页计。本笔记只归纳论文实际提出的模型、启发式和局限，不把其 Ethereum 结论外推为 Arbitrum 事实。

## 一句话结论

论文以 sandwich、liquidation、DEX arbitrage、transaction replay 与 clogging 为对象，使用链上启发式、重放与人工收紧规则量化 BEV；它最有价值的启示不是数值本身，而是“可观测规则必须附带误判边界和验证步骤”。（PDF p.1 摘要；p.4–8 第 IV 节；p.9 第 V 节）

## 与当前项目直接相关的阅读结果

### 行为—字段—识别方法—证据等级—误判风险—可迁移性

| 行为 | 论文使用的主要字段/状态 | 识别或验证方法 | 证据等级 | 误判风险 | 对 Arbitrum 跨层项目的可迁移性 |
|---|---|---|---|---|---|
| Sandwich | 同区块交易序列、swap token 流、发起地址、受害交易 | 前/后交易与受害 swap 的结构化启发式；要求资产方向、数量等条件 | 候选链上模式 | 地址复用、复杂路径、私有订单流会造成漏检或误配 | 只能迁移“字段与人工复核框架”；不能从 L1→L2 时间窗口直接推导 sandwich。 |
| Liquidation | 借贷仓位、前一块与当前块状态、价格变化、gas | 检查仓位在前一状态是否已可清算，区分 block-state 与 network-state 机会 | 条件性行为证据 | 协议状态重建和价格源不完整；相邻块比较不等于观察到 mempool | 可迁移“前态/后态反事实”的思想；当前预实验尚未重建 DeFi 状态。 |
| DEX arbitrage | 多次 swap、资产闭环、输入/输出金额、手续费 | 多 swap 启发式和收益计算；论文进一步在前一块状态重放 | 经反事实增强的候选 | 路径解析、价格口径、未观测私有交易均影响判定 | 可为后续 `candidate_arbitrage` 设计提供模板；第 1 周不做该标签。 |
| Transaction replay | tx calldata、账户余额变化、gas、执行结果 | 构造 replay 并以扣除交易费后的余额变化判断盈利 | 可执行反事实证据 | 论文也明确无 ground truth，且部分可见性假设会高估潜在重放 | 可迁移“净收益必须扣成本、必须能重执行”；不可在历史 Arbitrum block 数据上直接宣布可重放。 |
| Clogging | 区块容量、gas、连续区块活动 | 检测拥塞/占满模式 | 弱候选 | 高 gas 使用可能来自正常需求 | 当前不纳入主问题；没有到达时间时更不能推断恶意占用。 |

## 方法与局限的关键依据

- 论文把攻击面区分为 block state 和 mempool/network state；前者可由已上链状态重建，后者依赖更局部、易变的可见性。（PDF p.3，Table I 与 Sec. III）
- Sandwich 启发式由多个约束联合收紧，论文明确以避免重复计数和过度报告为目标。（PDF p.4，Sec. IV-A）
- 对 arbitrage 的重放检查显示：仅凭启发式识别出的交易并不必然在前一块状态中仍盈利，因而“候选模式”不能自动升级为攻击结论。（PDF p.7–8，Sec. IV-C）
- 论文在局限部分明确承认没有 ground truth，定制启发式可能造成 false negative；同时也提醒某些模式未必是攻击，可能产生 false positive。（PDF p.8，Sec. IV-E）

## 本项目可直接采用的规则

1. 每个候选行为规则必须写出所需字段、反例和人工复核方式。
2. 将“链上结构候选”“可重执行反事实”“已确认收益”分为不同证据等级。
3. 收益口径必须显式扣除 gas/执行成本；没有状态重放和资产估值时不能报利润。
4. 所有标签命名为 `candidate_*`，直到有可审计的反事实验证。

## 不能直接迁移的部分

- 论文的 mempool/network-state 结论不等于 Arbitrum Sequencer 私有队列可见性；历史 RPC 只有入块时间，不含 first-seen。
- Ethereum 同区块相邻位置不能代替 L1 Inbox message 与 L2 retryable creation 的对象映射。
- 论文的历史金额、地址数量、攻击数量和 Flashbots 机制均不是本项目样本的结果或先验。

## 对第 1 周的实际作用

为“字段字典—候选规则—误判审计”提供质量标准；本周只验证时间锚点与对象映射，不使用该文启发式计算攻击频率或 MEV 利润。
