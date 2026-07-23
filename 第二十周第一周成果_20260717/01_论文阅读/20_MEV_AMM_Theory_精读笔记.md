# 20《Price of MEV: Towards a Game Theoretical Approach to MEV》精读笔记

> 来源：`文献收集/20_MEV_AMM_Arbitrage_Theory.pdf`，PDF 共 10 页。页码按 PDF 页计。

## 一句话结论

论文把 MEV 描述为受 domain、排序机制、参与者信息集、资本/软件资源与执行成本共同约束的博弈；“看到交易”只是构造 profitable bundle 的必要条件之一，不是收益结论。（PDF p.1 摘要；p.2–4 Sec. 2）

## 论文中的关键形式化

- **Domain**：带共享状态、执行语义与合法排序规则的自洽系统。（PDF p.2，Definition 2.1）
- **Searcher/player**：假定 Sequencer 遵守某类规则，并提交策略性 action/bundle 最大化自身效用的参与者。（PDF p.2，Definition 2.2）
- **Ordering mechanism**：决定交易集合的纳入和排序的规则。（PDF p.2，Definition 2.3）
- **Sequencer**：论文区分 dummy、dummy Byzantine、rational 与 partially rational；其可行动作必须由具体 domain 约束。（PDF p.3，Definition 2.4）
- **Profitable bundle / local MEV**：若有序 bundle 改变状态后令某玩家资产价值增量为正，才是利润性 bundle；local MEV 还受可见信息、资本、软件、gas 效率与提出区块能力约束。（PDF p.3–4，Definition 2.5 与随后优化问题）

## 三角色能力矩阵（用于本项目）

| 角色 | 可见信息 | 可提交渠道 | 排序控制 | 资金/执行能力 | 不能据此假定的能力 |
|---|---|---|---|---|---|
| Arbitrum Sequencer | 公共 L1 消息、直接 L2 提交；是否有额外私有流须单独证明 | L2 批次与协议允许的纳入路径 | 可在协议边界内决定早期纳入和顺序 | 可运行排序/执行基础设施；是否自营交易另行假设 | 不能伪造 finalized L1、让无效状态被接受，亦不能无限绕过强制纳入边界。 |
| 外部策略者/searcher | 公共 L1 block/event；若无 live collector，则不能知道 first-seen | 普通 L1 Inbox、L2 RPC | 无直接排序权，只能影响或竞争 | 可预置资金、构造交易和支付费用 | 不能默认看到 Sequencer 私有队列、他人准确到达时间或获得优先通道。 |
| 普通用户 | 自己提交内容和公共链信息 | 标准桥/RPC | 无排序控制 | 正常桥接与调用能力 | 不应被赋予 searcher 的自动监控、资金和竞争执行能力。 |

## “看到信息”到“形成可执行收益”的最小条件

1. 目标消息在相关参与者的信息集中可见，且时点可被定义。
2. 参与者有合法提交路径，并能在窗口关闭前使动作进入待排序集合。
3. 参与者拥有完成交易所需资金、token、gas 与软件/路由能力。
4. 存在与原始顺序不同、但仍有效的交易序列或 bundle。
5. 在统一计价和成本扣除后，反事实执行净收益为正。

当前第 1 周只通过 L1 message 与 L2 receipt 验证第 1 项的一部分（以“L1 入块”为操作性锚点）及对象可映射性；第 2–5 项均未被当前数据证明。

## 对威胁模型的约束

本项目采用“Sequencer 可被视为受协议约束的部分理性排序者；外部策略者无私有排序权”的基线。若要讨论 Sequencer 与 searcher 共谋，必须单列扩展假设，不能从地址或窗口长度推断。
