# Batch golden set 人工核验记录

人工核验日期：2026-07-23。核验方法：逐项比对 `SequencerBatchDelivered` 的 sequence、L1 block hash、accumulator/after-delayed count 与 `NodeInterface.findBatchContainingBlock` 得到的 L2 首末区块；检查相邻 batch 的 L2 区间连续、不重叠。

按“至少 10 个或总样本 10%，取较严格者”执行：本次抽查首个连续片段的 10 / 40 个 batch（25%）。其中前三条用于连续 batch 的逐条展示；其余七条用于延续性抽查。

| batch sequence | L1 block | L1 block hash | after delayed messages read | L2 区间 | `P_lag`（last-block anchor） | 结论 |
|---:|---:|---|---:|---|---:|---|
| 1300992 | 25593706 | `0xdb7242e21d98882acce503c5356f626b9cf80d8e0cc4e7d502e86bb8fb849187` | 2514462 | 486789735–486790340 | 19 s | `range/high` |
| 1300993 | 25593716 | `0x7dcd1a9fb798099cd6411378ab4eadbd38f1a56887c1b91b1ff7d2efcb41435e` | 2514462 | 486790341–486790828 | 16 s | `range/high` |
| 1300994 | 25593726 | `0xfa2199f826f5a3c0cbd6f935773bd41982d70bf54802d00855816071fadb40a5` | 2514462 | 486790829–486791319 | 12 s | `range/high` |
| 1300995 | 25593738 | `0xc52efdc6d947d238cfdfa0bc3f02b53e487b0c9a0907c36efe9b6ddabdc91aeb` | 2514466 | 486791320–486791912 | 7 s | `range/high` |
| 1300996 | 25593754 | `0x87dbc9c25f2b97eb54a1deb9fccbda3f0cc60db1e59806901df07f9797097138` | 2514466 | 486791913–486792648 | 12 s | `range/high` |
| 1300997 | 25593768 | `0xda451cd3c2d6e64333a05b7bea727607edad7fb827ac0040bccacd11950baad3` | 2514473 | 486792649–486793328 | 10 s | `range/high` |
| 1300998 | 25593781 | `0x2abdfdca1ca846faa8d2d6f005dc0fe8625c4e6a02f939b5e5b2e455818d2f9d` | 2514473 | 486793329–486793905 | 20 s | `range/high` |
| 1300999 | 25593796 | `0xb4f863207cb50b34df8642e39b4135cdc59b6a8c4be2a518ad7bbdb101df2a22` | 2514473 | 486793906–486794624 | 20 s | `range/high` |
| 1301000 | 25593807 | `0x3ef0ac2a9bec04fb1106cbabaccc26614e0628bf3bb4d3aaa5483833a0d46b37` | 2514476 | 486794625–486795203 | 7 s | `range/high` |
| 1301001 | 25593817 | `0x31480374dafb10cddc21f121d14b8bc147892ea8c37639e38b45144d485711be` | 2514476 | 486795204–486795640 | 17 s | `range/high` |

前十条的相邻区间首末连续，例如 `486790340→486790341`、`486790828→486790829`、`486791319→486791320`、`486795203→486795204`；未观察到重叠或跳跃。这个核验只证明 batch 的区间映射和 publication-lag 锚点可用，不证明 L1→L2 MEV。
