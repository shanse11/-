# 最小 Commit-Reveal 机制草案 v0.1

## 1. 定位与目标

这是一个**待验证的最小可见性约束方向**，不是已经实现的协议。其目标是在排序决策前避免向排序者直接暴露完整 `payload`，从而缩小“看见内容 + 拥有相对排序能力”这一条件组合的适用范围。

承诺形式：

```text
commitment = H(domain || chainId || rollupId || sender || nonce || payload || salt)
```

把 `domain`、链和对象身份纳入哈希是 domain separation 的最低要求，避免同一 commitment 在不同链、合约或生命周期阶段被重放/误解释。

## 2. 最小流程

```text
commit(payload 的承诺)
  → 进入排序 / slot 承诺
  → reveal(payload, salt)
  → 验证 commitment 与域
  → 执行；或在超时规则下处理未 reveal
```

| 阶段 | 输入/公开内容 | 目标 | 关键风险 |
|---|---|---|---|
| commit | commitment、必要身份/费用元数据 | 排序前隐藏完整 payload | 元数据泄漏、低熵 payload 猜测、垃圾承诺 |
| 顺序/slot 承诺 | commitment 的相对顺序或可验证 slot | 避免 reveal 后任意重排 | Sequencer 延迟、拒绝服务、承诺不等于强制纳入 |
| reveal | payload、salt | 恢复可验证执行输入 | 用户不揭示、网络延迟、选择性揭示 |
| verify/execute | 哈希验证、域检查、业务条件 | 仅执行对应承诺的内容 | 失败执行、过期、跨层生命周期不匹配 |
| timeout | deadline、惩罚/取消/退回规则 | 保证系统不被未 reveal 永久阻塞 | 用户体验、审查、资金锁定 |

## 3. 明确不隐藏或未必解决的内容

1. commitment 的提交时间、发送者、费用、大小、频率和关联账户等元数据仍可能泄漏策略线索。
2. 低熵 payload 即使经哈希也可能被字典枚举；salt 必须足够随机且不复用。
3. commit-reveal 不能自动阻止 Sequencer 不纳入、延迟、审查或在 reveal 后排序；若没有外部强制纳入路径，这些问题仍在。
4. 对跨层对象，L1 提交、L2 创建、reveal 与执行之间的生命周期是否兼容，必须由 V0/V4 核验，不能仅凭单链直觉假定。

## 4. 待验证性质与接口草案

### 待验证性质

- **隐藏性（目标级）**：排序前完整 payload 不应从 commitment 直接恢复；该目标受低熵和元数据限制。
- **绑定性（目标级）**：reveal 应唯一对应已提交的 commitment 和域。
- **活性**：未 reveal/超时不应无限阻塞其他对象。
- **抗重放/域隔离**：同一承诺不能在错误链、错误入口或错误 nonce 下被接受。
- **抗审查边界**：机制至少要说明强制纳入或超时路径；不承诺单独解决审查。

### 后续接口草案（非实现）

```text
submitCommit(bytes32 commitment, uint64 expiry, bytes32 context)
reveal(bytes payload, bytes32 salt, uint64 nonce)
expireCommit(bytes32 commitment)
```

`context` 在后续应绑定业务入口、目标链/rollup、用户身份或 nonce；具体 ABI、权限、费用、状态存储和跨层传递方式尚未设计。

## 5. 机制目标—性质—风险—后续验证方式

| 机制目标 | 待验证性质 | 主要风险 | 后续验证方式 |
|---|---|---|---|
| 隐藏排序前 payload | hiding（限定在高熵 payload/salt） | 字典猜测、元数据泄漏 | 威胁分析、泄漏实验、参数约束 |
| 防止 reveal 后替换内容 | binding / domain separation | nonce/链/入口未绑定、重放 | 属性测试、跨域负例 |
| 避免未 reveal 阻塞 | liveness / timeout | 垃圾承诺、资金锁定、用户延迟 | 状态机测试、压力场景 |
| 降低排序者的内容利用空间 | 仅限制内容可见性 | reveal 后重排、审查、强制纳入缺失 | 与威胁模型对照、机制组合分析 |
| 与跨层生命周期兼容 | 正确关联 commit/reveal/execute | L1/L2 阶段脱节、消息失败 | V0 对象核验与原型接口测试 |

## 6. 不解决的问题

本草案不声称拥有完整 hiding/binding 安全证明；不解决所有 MEV、纳入或审查；不声称 Gas 可接受、已经部署或已经获得防御效果。其唯一功能是为 RQ3 提供一个可被后续性质与实现评估否定或改进的最小起点。
