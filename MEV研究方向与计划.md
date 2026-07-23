# MEV 跨层防御研究方向与计划

> 作者：杨帆 | 更新日期：2026-07-02

---

## 目录

1. [文献收集概览](#一文献收集概览)
2. [20篇论文阅读综合结论](#二20篇论文阅读综合结论)
3. [研究版图与空白分析](#三研究版图与空白分析)
4. [调整后的研究方向](#四调整后的研究方向)
5. [核心技术方案](#五核心技术方案)
6. [详细研究计划](#六详细研究计划)
7. [目标投稿会议](#七目标投稿会议)

---

## 一、文献收集概览

共收集 **20 篇**相关论文，按方向分为五类：

### 类别一：MEV 基础与量化

| 编号 | 文件名 | 核心内容 |
|------|--------|----------|
| 01 | `FlashBoys2.0_MEV_Frontrunning` | MEV 奠基论文，前跑 / 夹击 / PGA |
| 02 | `Quantifying_BEV_Flashbots` | BEV 量化，sandwich / liquidation / arbitrage 数据 |
| 18 | `Theory_MEV_I` | AMM 上 MEV 博弈的形式化理论 |
| 13 | `Theory_MEV_Uncertainty` | MEV 不确定性原理（Fourier 分析） |
| 20 | `MEV_AMM_Arbitrage_Theory` | AMM 套利与 MEV 理论 |

### 类别二：跨链 / 跨域 MEV（核心新方向）

| 编号 | 文件名 | 核心内容 |
|------|--------|----------|
| 06 | `SoK_MEV_Evolution_CrossChain` | 2026年最新，MEV 从矿工到跨链的演化 SoK |
| 07 | `Arbitrum_Timeboost_Empirical_Analysis` | Arbitrum L2 排序机制实证分析（2025） |
| 03 | `Clockwork_Finance_MEV_Formal` | 智能合约经济安全形式化分析框架 |

### 类别三：防御与缓解机制

| 编号 | 文件名 | 核心内容 |
|------|--------|----------|
| 08 | `Mitigating_BEV_Distributed_Sequencing` | 分布式排序缓解 BEV（DTSS） |
| 14 | `MEV_Mitigation_Ethereum_L2_Survey` | L1+L2 MEV 缓解技术综述（2024） |
| 15 | `Network_Fairness_Frontrunning_Probability` | 前跑概率度量框架与可扩展性矛盾证明 |

### 类别四：公平排序协议

| 编号 | 文件名 | 核心内容 |
|------|--------|----------|
| 04 | `Aequitas_OrderFair_Consensus` | 经典公平排序共识协议（奠基之作） |
| 09 | `SoK_Consensus_Fair_Message_Ordering` | 公平消息排序共识 SoK 综述 |
| 10 | `Quick_Order_Fairness` | 快速公平排序协议（理论） |
| 11 | `Quick_Order_Fairness_Implementation` | 快速公平排序实现与评估（Go 实现） |
| 12 | `Wendy_Fairness_Widget` | 轻量公平性组件设计 |
| 16 | `Tilikum_Fair_Ordering_DAG` | 2025年最新，DAG 上的公平排序 |
| 17 | `FairDAG_Consensus_Fairness` | DAG 多提案者公平设计 |
| 19 | `Herring_Batch_Order_Fairness_DAG` | 2025年最新，批量公平排序 |

### 类别五：背景参考

| 编号 | 文件名 | 核心内容 |
|------|--------|----------|
| 05 | `SoK_Decentralized_Finance` | DeFi SoK 综述（背景知识） |

---

## 二、20篇论文阅读综合结论

### 2.1 第一组：MEV 基础量化（论文 01 / 02 / 03 / 18 / 13）

#### 各论文核心发现

**Flash Boys 2.0（2019，arXiv:1904.05234）**
- 首次定义 MEV，记录 PGA（Priority Gas Auction）竞价行为
- 纯收益机会下界 **>600万 USD**，MEV 已足以支撑 time-bandit 共识攻击
- **局限**：止步于描述和量化，明确指出"有效的实际缓解措施尚未出现"；未涉及 L2

**Quantifying BEV（2021，arXiv:2101.05511）**
- 32个月内检测到 **5.4054亿 USD** 的 BEV

| 类别 | 次数 | 金额 |
|------|------|------|
| Sandwich Attacks | 750,529 次 | 1.7434亿 USD |
| Liquidations | 31,057 笔 | 8918万 USD |
| DEX Arbitrage | 1,151,448 笔 | 2.7702亿 USD |
| 合计 | — | **5.4054亿 USD** |

- 单笔最大 BEV：**410万 USD**（区块奖励的 616.6 倍）
- **局限**：分析了 BEV Relay 的危害但未提出替代方案；未覆盖 L2 场景

**Clockwork Finance Framework（2023，arXiv:2109.04347）**
- 首个针对 DeFi 的通用形式化验证框架，平均每月自动发现 **5600万 USD** 的可提取价值
- **局限**：纯分析工具，完全不涉及 MEV 防御设计

**Theory of MEV I — AMM（2022，arXiv:2106.01870）**
- 首次严格形式化 AMM 上的 MEV 博弈，提出最优多层三明治攻击"Dagwood Sandwich"
- **局限**：未建模 swap fees 和 gas fees；完全聚焦攻击最优化，不涉及防御

**Theory of MEV II — Uncertainty（2023，arXiv:2309.14201）**
- 通过 Fourier 分析建立排序规则与支付函数复杂度的不确定性原理
- 核心命题：**公平排序和经济机制均无法单独缓解任意支付函数下的 MEV**
- **局限**：完全理论性，无实现；未给出如何设计应用特定排序规则的方法论

#### 第一组研究空白汇总

| 研究空白 | 紧迫性 |
|----------|--------|
| 可实际部署的 MEV 防御方案 | 极高 |
| Layer 2 / Rollup Sequencer 的 MEV 防御 | 高 |
| 含手续费约束的真实场景防御 | 高 |
| 跨区块 Multi-block MEV | 高 |
| 用户隐私保护与 MEV 缓解的协议级结合 | 高 |

---

### 2.2 第二组：跨域 MEV 与防御机制（论文 06 / 07 / 08 / 14 / 15）

#### 各论文核心发现

**SoK: The Evolution of MEV, From Miners to Cross-Chain（2026，arXiv:2603.07716）**
- 首篇系统梳理 MEV 从矿工到跨链演化的 SoK 论文，定义 RC-MEV（Realized Cross-Chain Extractable Value）
- Era III（2024至今）关键数据：
  - Cross-layer sandwich attacks（S1/S2/S3）：Arbitrum 平均延迟 **798秒**，潜在利润约 **200万 USD**
  - 跨链套利（9条链，242,535笔）：总交易量 **8.69亿 USD**，净利润 **865万 USD**
  - Dencun 升级后跨链 MEV 活动增长 **5.5倍**
- **局限**：明确指出 Era III 跨链 MEV 防御"总体尚不成熟（nascent）"

**Arbitrum Timeboost 实证分析（2025，arXiv:2509.22143）**
- 覆盖 **1160万条**交易 + **15万次**拍卖，实证证明 Timeboost 全面失败

| 机构 | 赢得拍卖份额 | 提交交易份额 |
|------|-------------|-------------|
| Selini Capital | **59.92%** | 41.99% |
| Wintermute | **32.1%** | 57.36% |

- **21.75%** 的 timeboosted 交易 revert；~**94%** 用于 CEX-DEX 套利
- **关键结论**：auction-based ordering 本质上是资本优势的固化机制，无密码学公平保证

**DTSS（2025，arXiv:2503.06279）**
- 首个将公平排序规则内嵌至共识协议的分布式排序方案
- 对抗性交易推后幅度：Frontrun Sandwich **+58.98%**，Replay **+61.58%**
- **明确局限**：对 Arbitrage（套利）类 MEV **完全无效**；仅聚焦单链内部

**MEV Mitigation Survey（2024，arXiv:2407.19572）**
- 首篇系统综述 L1+L2 MEV 缓解的四大类技术：公平排序、隐私保护、合约层保护、PBS
- 主流 Rollup（Arbitrum / Optimism / StarkNet / zkSync）**全部采用单一 Sequencer + FCFS**
- **局限**：跨层/跨链 MEV 未深入处理；缺乏量化性能基准

**Network Fairness and Scalability（2021，arXiv:2102.04326）**
- 严格证明公平性与可扩展性之间的根本矛盾（fairness-scalability tradeoff）
- 以太坊前跑概率估算 **p_f ≈ 0.36**；扩容至 Visa 级别后 p_f → **0.99**
- **局限**：仅考虑 PoW；未提供任何解决方案

#### 第二组研究空白汇总

1. **跨链 / 跨域 MEV 的专用防御框架几乎为零**
2. **auction-based sequencing 已证失败，密码学替代方案缺乏 L2 场景验证**
3. **Shared Sequencer 的跨 Rollup MEV 博弈论分析空白**
4. **套利类 MEV 无任何有效防御机制**

---

### 2.3 第三组：公平排序协议（论文 04 / 09 / 10 / 11 / 12）

#### 核心判断：五篇协议对 L2 单一 Sequencer 均不适用

| 协议 | 适用单一 Sequencer | 适用分布式 Sequencer | 关键限制 |
|------|:-----------------:|:-------------------:|----------|
| Aequitas | ❌ | 条件适用 | O(n⁴) 通信复杂度；需 n > 4f |
| SoK Fair Ordering | ❌ | 条件适用 | 明确排除 L2 单 Sequencer 场景 |
| Quick Order Fairness | ❌ | 条件适用 | 与 Aptos/Sui 并行执行不兼容 |
| QOF Implementation | ❌ | ✅ 推荐 | Section 5 讨论 Espresso 集成路径 |
| Wendy | ❌ | 条件适用 | 随机委员会集成未解决 |

**根本原因**：单一 Sequencer 是**信任问题**，而非协调问题。现有公平排序协议通过"多方博弈约束恶意少数节点"，而中心化 Sequencer 本身就是"那个可以任意重排序的节点"，多方博弈机制对其完全失效。

#### 对 L2 场景有实质参考价值的三条路径

1. **Blind Ordering / 加密 Mempool**：Sequencer 在不知道内容的情况下排序，无从实施 front-running。目前最具工程可行性。
2. **Permuted Ordering + VRF**：用可验证随机函数做伪随机置换，Sequencer 承诺排序规则且可链上验证。
3. **分布式 Sequencer 委员会**：将单一 Sequencer 替换为多节点 BFT 委员会，再嵌入 QOF 等协议。

---

### 2.4 第四组：最新论文（论文 16 / 17 / 19 / 05 / 20）

- **Tilikum（2025）/ Herring（2025）/ FairDAG（2025）**：将公平排序扩展到 DAG 共识，但仍假设多节点投票，不解决 L2 单 Sequencer 问题
- **SoK DeFi**：背景综述，确认 MEV 是 DeFi 生态核心未解问题
- **MEV AMM Theory**：AMM 套利理论延伸，仍聚焦攻击建模

---

## 三、研究版图与空白分析

### 3.1 已覆盖区域（不要重复）

```
✅ MEV 概念建立与 L1 量化（Flash Boys 2.0, BEV 量化）
✅ AMM 最优攻击策略构造（Theory MEV I/II, Clockwork Finance）
✅ 多节点 BFT 公平排序协议（Aequitas, QOF, Wendy, Themis...）
✅ 单链 MEV 缓解（DTSS，但不能处理套利类 MEV）
✅ 跨链 MEV 的现象实证（SoK Evolution，但无防御）
✅ auction-based 排序（Timeboost，已实证失败）
```

### 3.2 核心空白（你要填补的区域）

```
❌ L1→L2 跨层时序窗口的密码学 MEV 防御
❌ 对 L2 单一 Sequencer 有效的盲排序协议
❌ 可实验验证的链上防御机制（有代码 + 有数据 + 有对比）
```

### 3.3 三个驱动本研究的关键发现

> **发现 1**：Aequitas / QOF / Wendy 等公平排序协议全部假设"多个独立节点投票"，对 L2 单一 Sequencer 在语义上完全失效。SoK 论文明确写道这是"超出本文范围的开放问题"。

> **发现 2**：Timeboost 用经济拍卖决定排序权，实证结果是 90% 的拍卖由两家机构垄断，21.75% 的交易 revert，MEV 没有减少只是换了受益人——经济路径已证行不通，必须走密码学路径。

> **发现 3**：SoK Evolution（2026年3月）明确标记 Era III 跨层 MEV 防御"总体尚不成熟（nascent）"。在 20 篇论文中，没有任何一篇系统研究并实现了针对 L1→L2 时序窗口的密码学防御。

---

## 四、调整后的研究方向

### 4.1 题目

> **英文**：*Blind Commit-Reveal: Mitigating Cross-Layer MEV in L2 Rollup Sequencing*
>
> **中文**：盲提交揭示协议：面向 L2 Rollup 跨层 MEV 的密码学缓解机制

### 4.2 三点核心贡献

| 贡献 | 内容 | 对应阶段 |
|------|------|----------|
| **贡献 1（数据）** | 首个系统量化 L1→L2 跨层时序窗口 MEV 的测量研究 | 阶段一 |
| **贡献 2（协议）** | 首个对 L2 单一 Sequencer 有效、无需可信第三方的盲排序协议 | 阶段二 |
| **贡献 3（实现）** | Solidity 链上实现 + 安全性 / Gas / 延迟三组实验验证 | 阶段三/四 |

### 4.3 与现有方案的本质区别

| 方案 | 核心机制 | 防 sandwich | 防套利 | 单 Sequencer 有效 | 无需可信第三方 |
|------|----------|:-----------:|:------:|:-----------------:|:--------------:|
| Timeboost | 经济拍卖 | 部分 | ❌ | ✅ | ❌ |
| DTSS | 规则排序 | ✅ | ❌ | ✅ | ✅ |
| Aequitas / QOF | 多节点投票 | ✅ | 部分 | ❌ | ✅ |
| **本研究** | **密码学盲化** | **✅** | **✅** | **✅** | **✅** |

---

## 五、核心技术方案

### 5.1 协议流程

```
Step 1 — 用户提交 Commit
  C = Commit( H(tx_raw || nonce || timestamp) )
  → 提交到链上，锁定排序位置
  → Sequencer 只见哈希，无法得知交易内容

Step 2 — Sequencer 按时间戳盲排序
  → 以 commit timestamp 为唯一排序依据
  → 无信息可用来 front-run / sandwich / arbitrage

Step 3 — 用户在截止时间内 Reveal
  Reveal( tx_raw, nonce )
  → 链上验证 H(tx_raw || nonce) == 已承诺的 C
  → 验证通过则按锁定位置执行

Step 4 — 生成 OrderingProof
  → 链上记录可验证的排序承诺
  → 任何人可验证 Sequencer 未根据内容重排序

超时处理：
  → 未在窗口内 Reveal → Commit 自动 Expire
  → 不阻塞后续队列（Liveness 保证）
```

### 5.2 协议状态机

```
             commit()
INIT ───────────────────→ COMMITTED
                               │
                ├──────────────┤──────────────┤
             reveal()       (等待中)        timeout
                ↓                               ↓
           REVEALED                          EXPIRED
                │
            execute()
                ↓
           EXECUTED
```

### 5.3 三条安全性质

| 性质 | 含义 | 保证方式 |
|------|------|----------|
| **Binding（绑定性）** | Commit 之后无法更换交易内容 | 哈希函数碰撞安全性 |
| **Secrecy（保密性）** | Reveal 之前 Sequencer 无法获取交易语义 | 链上只存储哈希 |
| **Liveness（活性）** | 超时 Expire 保证队列不死锁 | 超时剔除机制 |

---

## 六、详细研究计划

### 阶段一：跨层 MEV 测量（第 1-3 周）

**目标**：用真实链上数据证明问题存在，建立论文的 Motivation Section

**数据来源**：
- Optimism / Arbitrum 公开 RPC 节点
- Etherscan API / Dune Analytics SQL

**具体工作**：

```python
# 任务 1：抓取 L1 batch 提交 → L2 确认 的时间差分布
# 任务 2：识别时序窗口内的 sandwich / frontrun / 套利交易
# 任务 3：统计规模（交易数、金额 USD、攻击者地址集中度）
```

**预期产出**：
- L1→L2 时序窗口 CDF 分布图
- 跨层 MEV 规模估算表（类比 Timeboost 论文数据格式）
- 攻击类型分布饼图

---

### 阶段二：协议设计与形式化（第 4-5 周）

**目标**：完成盲提交揭示协议的形式化定义，这是论文最重要的部分

**具体工作**：

1. **状态机定义**：`INIT → COMMITTED → [REVEALED / EXPIRED] → EXECUTED`
2. **三条安全性质的形式化论证**（Binding / Secrecy / Liveness）
3. **OrderingProof 构造**：每批交易结束后生成可验证排序承诺

---

### 阶段三：链上实现（第 6-8 周）

**目标**：写出可运行代码，满足导师"需要做实验"的要求

**核心合约骨架（Solidity）**：

```solidity
contract BlindCommitReveal {
    enum State { COMMITTED, REVEALED, EXECUTED, EXPIRED }

    struct TxSlot {
        bytes32  commitHash;     // H(tx_raw || nonce)
        uint256  commitTime;     // 排序依据（不可篡改）
        address  sender;
        State    state;
        uint256  revealDeadline;
    }

    mapping(bytes32 => TxSlot) public slots;

    function commit(bytes32 txHash) external returns (bytes32 slotId);
    function reveal(bytes32 slotId, bytes calldata txRaw, uint256 nonce) external;
    function expire(bytes32 slotId) external;        // 任何人可触发超时
    function verifyOrdering(bytes32[] calldata slotIds)
        external view returns (bool);                // 验证排序是否按 timestamp
}
```

**测试场景矩阵（Hardhat / Foundry）**：

| 场景 | 预期结果 |
|------|----------|
| 正常 commit → reveal → execute | ✅ 成功执行 |
| 攻击者根据哈希猜测内容构造 sandwich | ❌ 无内容可用，失败 |
| 攻击者伪造 reveal（哈希不匹配） | ❌ 链上验证拒绝 |
| 用户超时未 reveal | ⏱️ 自动 expire，队列推进 |
| Sequencer 尝试重排已 commit 的 slot | ❌ timestamp 锁定，不可重排 |

---

### 阶段四：实验评估（第 9-10 周）

**实验 A：安全性验证**

| 指标 | 无保护 | 有 BlindCommitReveal |
|------|:------:|:-------------------:|
| Sandwich 攻击成功率 | ~100% | ~0% |
| Frontrun 攻击成功率 | ~100% | ~0% |

产出：攻击成功率对比柱状图

**实验 B：Gas 开销分析**

- Commit 交易 gas 成本（绝对值 + 与普通交易对比）
- Reveal 交易 gas 成本
- 不同 payload 大小下的开销曲线

**实验 C：延迟影响**

- commit-reveal 增加的确认延迟（Δ 秒）
- 不同 reveal 窗口大小下的用户体验 trade-off 曲线
- 与 Timeboost 的延迟数据直接对比（引用 arXiv:2509.22143 数据）

---

### 阶段五：论文写作（第 11-13 周）

**论文结构**：

```
§1  Introduction（1.5页）
    - 跨层 MEV 规模引入（阶段一测量结果）
    - 现有方案不足：公平排序不适用 L2，拍卖方案实证失败
    - 本文三点贡献

§2  Background & Related Work（2页）
    - L2 交易流程与跨层时序窗口
    - 现有防御分类（引用 20 篇文献）

§3  Cross-Layer MEV Measurement（2页）
    - 数据方法 + 窗口分布 + 规模统计（阶段一产出）

§4  Blind Commit-Reveal Protocol（3页）
    - 协议形式化定义 + 状态机 + 安全性质证明（阶段二产出）

§5  Implementation & Evaluation（2.5页）
    - 合约实现 + 三组实验数据（阶段三/四产出）

§6  Discussion & Limitations（0.5页）
§7  Conclusion（0.5页）
```

---

### 时间线总览

```
Week 1-3    ████████████░░░░░░░░░░░░░░  数据抓取 + 跨层 MEV 测量
Week 4-5    ░░░░░░████████░░░░░░░░░░░░  协议形式化设计
Week 6-8    ░░░░░░░░░░████████████░░░░  Solidity 实现 + 测试
Week 9-10   ░░░░░░░░░░░░░░████████░░░░  三组实验 + 数据整理
Week 11-13  ░░░░░░░░░░░░░░░░░░████████  论文写作初稿
```

---

## 七、目标投稿会议

| 会议 | 类型 | 适配度 | 参考 DDL |
|------|------|:------:|----------|
| **Financial Cryptography (FC) 2027** | 区块链 / 密码学 | ⭐⭐⭐⭐⭐ | 2026年10月 |
| **IEEE S&P 2027** | 系统安全 | ⭐⭐⭐⭐ | 2026年9月 |
| **ACM CCS 2027** | 安全密码学 | ⭐⭐⭐⭐ | 2027年初 |
| **USENIX Security 2027** | 系统安全 | ⭐⭐⭐ | 2026年底 |

**最推荐：Financial Cryptography 2027**
- 专门收录区块链经济安全方向，与研究定位最匹配
- 竞争强度相对 S&P / CCS 略低，适合作为第一篇独立工作

---

## 附录：推荐阅读顺序

```
第一步（理解现有防御全貌）：
  14_MEV_Mitigation_Survey
      → 06_SoK_MEV_Evolution_CrossChain

第二步（找研究空白）：
  08_Mitigating_BEV_Distributed_Sequencing
      → 07_Arbitrum_Timeboost_Empirical_Analysis

第三步（设计协议时参考）：
  09_SoK_Consensus_Fair_Message_Ordering
      → 10_Quick_Order_Fairness
      → 11_Quick_Order_Fairness_Implementation
      → 04_Aequitas_OrderFair_Consensus

第四步（理论支撑）：
  13_Theory_MEV_Uncertainty
      → 15_Network_Fairness_Frontrunning_Probability
```

---

*本文档基于对 20 篇文献的系统并行阅读综合生成 | 2026-07-02*
