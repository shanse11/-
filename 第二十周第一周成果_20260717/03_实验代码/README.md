# Arbitrum One 第 1 周预实验代码

本目录实现的是“预实验 / 数据链路验证”，不是正式实验。它把 L1→L2 retryable creation window 与 L2→L1 batch publication lag 分开保存和统计。

## 依赖

```bash
python3 -m pip install -r requirements.txt
npm install
```

`ethers@5` 已锁定在本目录 `package.json` / `package-lock.json` 中，仅用于复刻官方 SDK 的 retryable creation ID 派生；Python 负责 RPC、清洗、映射、统计和图表。

## 运行

```bash
python3 run_preexperiment.py \
  --out-dir /Users/shanse/Desktop/组会/第二十周第一周成果_20260717 \
  --l1-block-span 1500 --batch-limit 40 --message-limit 25
```

可选环境变量：`ARBITRUM_L1_RPC`、`ARBITRUM_L2_RPC`。脚本不会把 URL 或 token 写入 manifest；不要在命令行参数中传递密钥。

## 核验

```bash
python3 -m unittest discover -s . -p 'test_*.py'
python3 run_preexperiment.py --help
```

输出位于 `04_实验数据/raw`、`04_实验数据/processed`、`05_实验结果/figures`、`07_运行日志`。`provenance_manifest.json` 固定 L1 finalized block/hash、合约地址、参数和代码路径。
