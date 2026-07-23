#!/usr/bin/env python3
"""Arbitrum One 第 1 周预实验 / 数据链路验证。

本脚本不把任意 L1/L2 时间差当成跨层窗口：
  W_ingest = L2 retryable creation block timestamp - L1 Inbox message block timestamp
  W_effect = successful auto-redeem block timestamp - L1 Inbox message block timestamp
  P_lag    = L1 SequencerInbox batch block timestamp - mapped L2 batch last-block timestamp

所有 RPC URL 均可由环境变量覆盖，且不会写入输出。默认端点为无密钥公共端点；
所有原始响应、固定区块哈希、参数和失败原因均保存到输出目录。
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import statistics
import subprocess
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests
from PIL import Image, ImageDraw, ImageFont

L1_CHAIN_ID = 1
L2_CHAIN_ID = 42161
BRIDGE = "0x8315177aB297bA92A06054cE80a67Ed4DBd7ed3a"
SEQUENCER_INBOX = "0x1c479675ad559DC151F6Ec7ed3FbF8ceE79582B6"
INBOX = "0x4Dbd4fc535Ac27206064B68FfCf827b0A60BAB3f"
NODE_INTERFACE = "0x00000000000000000000000000000000000000C8"
ARB_RETRYABLE_TX = "0x000000000000000000000000000000000000006E"

# 从官方 ISequencerInbox / IBridge ABI 的事件签名派生；本次运行也保存原始日志供复核。
SEQUENCER_BATCH_DELIVERED = "0x7394f4a19a13c7b92b5bb71033245305946ef78452f7b4986ac1390b5df4ebd7"
MESSAGE_DELIVERED = "0x5e3c1311ea442664e8b1611bfabef659120ea7a0a2cfc0667700bebc69cbffe1"
INBOX_MESSAGE_DELIVERED = "0xff64905f73a67fb594e0f940a8075a860db489ad991e032f48c81123eb52d60b"
FIND_BATCH_SELECTOR = "0x81f1adaf"  # findBatchContainingBlock(uint64)
NITRO_GENESIS_SELECTOR = "0x93a2fe21"  # nitroGenesisBlock()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def hx(value: Any) -> int:
    if isinstance(value, int):
        return value
    return int(value, 16)


def as_hex(value: int, width: int = 64) -> str:
    return "0x" + format(value, f"0{width}x")


def word(data: str, index: int) -> str:
    raw = data[2:] if data.startswith("0x") else data
    start = index * 64
    piece = raw[start : start + 64]
    if len(piece) != 64:
        raise ValueError(f"ABI data word {index} unavailable (data words={len(raw)//64})")
    return "0x" + piece


def address_from_word(value: str) -> str:
    return "0x" + value[-40:]


def quantiles(values: List[float]) -> Dict[str, Optional[float]]:
    if not values:
        return {"n": 0, "min": None, "p50": None, "mean": None, "p95": None, "max": None}
    ordered = sorted(values)
    def pct(p: float) -> float:
        if len(ordered) == 1:
            return float(ordered[0])
        pos = (len(ordered) - 1) * p
        lo, hi = int(math.floor(pos)), int(math.ceil(pos))
        return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)
    return {
        "n": len(ordered), "min": min(ordered), "p50": pct(0.5),
        "mean": statistics.fmean(ordered), "p95": pct(0.95), "max": max(ordered),
    }


@dataclass
class RpcClient:
    url: str
    label: str
    raw_dir: Path
    timeout: int = 35
    retries: int = 4

    def __post_init__(self) -> None:
        self.session = requests.Session()
        self.counter = 0

    def call(self, method: str, params: List[Any], raw_name: Optional[str] = None) -> Any:
        last: Optional[Exception] = None
        for attempt in range(self.retries):
            self.counter += 1
            payload = {"jsonrpc": "2.0", "id": self.counter, "method": method, "params": params}
            try:
                response = self.session.post(self.url, json=payload, timeout=self.timeout)
                response.raise_for_status()
                body = response.json()
                if raw_name:
                    (self.raw_dir / raw_name).write_text(json.dumps(body, indent=2), encoding="utf-8")
                if body.get("error"):
                    raise RuntimeError(f"{self.label}:{method}: {body['error']}")
                return body["result"]
            except Exception as exc:  # 保存最后的真实错误，由调用方写入失败分类
                last = exc
                time.sleep(1.2 * (attempt + 1))
        raise RuntimeError(str(last))


def fetch_logs_paginated(rpc: RpcClient, address: str, topic0: str, start: int, end: int,
                         raw_prefix: str, max_span: int = 500) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    cursor, part = start, 0
    while cursor <= end:
        part_end = min(end, cursor + max_span - 1)
        filt = {"address": address, "topics": [topic0], "fromBlock": hex(cursor), "toBlock": hex(part_end)}
        try:
            result = rpc.call("eth_getLogs", [filt], f"{raw_prefix}_{part:03d}.json")
            records.extend(result)
            cursor, part = part_end + 1, part + 1
        except RuntimeError:
            if cursor == part_end:
                raise
            # 范围或服务商限制时实际缩小范围，而非静默跳过。
            max_span = max(1, max_span // 2)
    return records


def parse_batch(log: Dict[str, Any]) -> Dict[str, Any]:
    data = log["data"]
    seq = hx(log["topics"][1])
    raw_location = hx(word(data, 6))
    locations = {0: "NoData", 1: "TxInput", 2: "SeparateBatchEvent", 3: "Blob"}
    return {
        "batch_sequence": seq,
        "before_acc": log["topics"][2],
        "after_acc": log["topics"][3],
        "delayed_acc": word(data, 0),
        "after_delayed_messages_read": hx(word(data, 1)),
        "timebound_min_timestamp": hx(word(data, 2)),
        "timebound_max_timestamp": hx(word(data, 3)),
        "timebound_min_l1_block": hx(word(data, 4)),
        "timebound_max_l1_block": hx(word(data, 5)),
        "data_location": locations.get(raw_location, f"unknown:{raw_location}"),
        "l1_tx_hash": log["transactionHash"],
        "l1_block_number": hx(log["blockNumber"]),
        "l1_block_hash": log["blockHash"],
        "l1_log_index": hx(log["logIndex"]),
    }


def parse_bridge_message(log: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "message_number": hx(log["topics"][1]),
        "before_inbox_acc": log["topics"][2],
        "inbox": address_from_word(word(log["data"], 0)).lower(),
        "kind": hx(word(log["data"], 1)),
        "sender": address_from_word(word(log["data"], 2)),
        "payload_hash_from_bridge": word(log["data"], 3),
        "parent_base_fee": hx(word(log["data"], 4)),
        "bridge_timestamp": hx(word(log["data"], 5)),
        "l1_tx_hash": log["transactionHash"],
        "l1_block_number": hx(log["blockNumber"]),
        "l1_block_hash": log["blockHash"],
        "l1_log_index": hx(log["logIndex"]),
    }


def inbox_event_payload(log: Dict[str, Any]) -> str:
    # ABI encoding of event InboxMessageDelivered(uint256 indexed, bytes): offset, length, bytes.
    raw = log["data"][2:]
    payload_len = hx("0x" + raw[64:128])
    start = 128
    payload = raw[start : start + payload_len * 2]
    if len(payload) != payload_len * 2:
        raise ValueError("InboxMessageDelivered dynamic bytes length mismatch")
    return "0x" + payload


def parse_retryable_payload(raw_event_data: str, bridge: Dict[str, Any]) -> Dict[str, Any]:
    # 与官方 SDK SubmitRetryableMessageDataParser 相同：前 9 个 uint256 + 尾部 calldata。
    data_len = hx(word(raw_event_data, 8))
    raw = raw_event_data[2:]
    call_data = "0x" + raw[-data_len * 2 :] if data_len else "0x"
    return {
        "child_chain_id": L2_CHAIN_ID,
        # 保持为十进制字符串，避免 JSON/JavaScript number 破坏 256-bit 金额字段。
        "message_number": str(bridge["message_number"]),
        "sender": bridge["sender"],
        "parent_base_fee": str(bridge["parent_base_fee"]),
        "dest_address": address_from_word(word(raw_event_data, 0)),
        "l2_call_value": str(hx(word(raw_event_data, 1))),
        "l1_value": str(hx(word(raw_event_data, 2))),
        "max_submission_fee": str(hx(word(raw_event_data, 3))),
        "excess_fee_refund_address": address_from_word(word(raw_event_data, 4)),
        "call_value_refund_address": address_from_word(word(raw_event_data, 5)),
        "gas_limit": str(hx(word(raw_event_data, 6))),
        "max_fee_per_gas": str(hx(word(raw_event_data, 7))),
        "call_data": call_data,
        "raw_event_data": raw_event_data,
    }


def lower_bound_batch(rpc: RpcClient, target_batch: int, low: int, high: int,
                      cache: Dict[int, int]) -> int:
    def value(block_num: int) -> int:
        if block_num not in cache:
            call_data = FIND_BATCH_SELECTOR + format(block_num, "064x")
            answer = rpc.call("eth_call", [{"to": NODE_INTERFACE, "data": call_data}, "latest"])
            cache[block_num] = hx(answer)
        return cache[block_num]

    while low < high:
        mid = (low + high) // 2
        if value(mid) < target_batch:
            low = mid + 1
        else:
            high = mid
    if value(low) != target_batch:
        raise ValueError(f"batch {target_batch} has no exact lower bound (found {value(low)})")
    return low


def get_block(rpc: RpcClient, number: int, cache: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
    if number not in cache:
        result = rpc.call("eth_getBlockByNumber", [hex(number), False])
        if result is None:
            raise ValueError(f"block {number} missing")
        cache[number] = result
    return cache[number]


def choose_contiguous_batches(parsed: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    parsed = sorted(parsed, key=lambda row: row["batch_sequence"])
    runs: List[List[Dict[str, Any]]] = []
    current: List[Dict[str, Any]] = []
    for row in parsed:
        if not current or row["batch_sequence"] == current[-1]["batch_sequence"] + 1:
            current.append(row)
        else:
            if current:
                runs.append(current)
            current = [row]
    if current:
        runs.append(current)
    eligible = [run for run in runs if len(run) >= limit]
    if not eligible:
        raise RuntimeError(f"no contiguous batch run of {limit}; longest run={max(map(len, runs), default=0)}")
    return eligible[-1][-limit:]


def safe_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    ]
    for item in candidates:
        if Path(item).exists():
            return ImageFont.truetype(item, size, index=0)
    return ImageFont.load_default()


def draw_bar(path: Path, title: str, items: List[Tuple[str, int]], foot: str) -> None:
    width, height = 1500, 900
    im = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(im)
    title_font, label_font, foot_font = safe_font(42), safe_font(28), safe_font(22)
    d.text((70, 50), title, fill="#14213d", font=title_font)
    maxv = max([v for _, v in items] + [1])
    left, top, bottom, barw, gap = 170, 170, 700, 150, 110
    for i, (name, val) in enumerate(items):
        x = left + i * (barw + gap)
        h = int((bottom - top) * val / maxv)
        d.rectangle((x, bottom - h, x + barw, bottom), fill="#2b6cb0")
        d.text((x + 45, bottom - h - 38), str(val), fill="#14213d", font=label_font)
        d.text((x - 15, bottom + 24), name, fill="#14213d", font=label_font)
    d.line((left - 30, bottom, width - 90, bottom), fill="#444444", width=2)
    d.text((70, 790), foot, fill="#555555", font=foot_font)
    im.save(path)


def draw_ecdf(path: Path, title: str, series: List[Tuple[str, List[float], str]], foot: str) -> None:
    width, height = 1500, 900
    im = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(im)
    title_font, label_font, foot_font = safe_font(42), safe_font(26), safe_font(21)
    d.text((70, 45), title, fill="#14213d", font=title_font)
    values = [v for _, arr, _ in series for v in arr]
    if not values:
        d.text((70, 280), "无有效样本：见失败分类图", fill="#9b2c2c", font=safe_font(36))
        d.text((70, 790), foot, fill="#555555", font=foot_font)
        im.save(path); return
    xmin, xmax = min(values), max(values)
    if xmin == xmax: xmax = xmin + 1
    left, top, right, bottom = 150, 160, 1370, 710
    d.line((left, bottom, right, bottom), fill="#444444", width=2)
    d.line((left, top, left, bottom), fill="#444444", width=2)
    for tick in range(6):
        x = left + (right-left)*tick/5
        val = xmin + (xmax-xmin)*tick/5
        d.text((x-30, bottom+18), f"{val:.0f}", fill="#555555", font=label_font)
    for tick in range(6):
        y = bottom - (bottom-top)*tick/5
        d.line((left, y, right, y), fill="#e6edf5", width=1)
        d.text((82, y-14), f"{tick/5:.1f}", fill="#555555", font=label_font)
    for name, arr, color in series:
        ordered = sorted(arr)
        points: List[Tuple[float, float]] = [(left, bottom)]
        for i, value in enumerate(ordered, start=1):
            x = left + (value-xmin)/(xmax-xmin)*(right-left)
            y = bottom - i/len(ordered)*(bottom-top)
            points.extend([(x, points[-1][1]), (x, y)])
        if len(points) > 1:
            d.line(points, fill=color, width=5)
        d.text((left+30, top+24 + 40*series.index((name, arr, color))), f"{name} (n={len(arr)})", fill=color, font=label_font)
    d.text((70, 790), foot, fill="#555555", font=foot_font)
    im.save(path)


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    keys = sorted({key for row in rows for key in row}) if rows else []
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in keys})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--l1-block-span", type=int, default=500)
    parser.add_argument("--batch-limit", type=int, default=40)
    parser.add_argument("--message-limit", type=int, default=25)
    parser.add_argument("--l1-rpc", default=os.getenv("ARBITRUM_L1_RPC", "https://eth.drpc.org"))
    parser.add_argument("--l2-rpc", default=os.getenv("ARBITRUM_L2_RPC", "https://arb1.arbitrum.io/rpc"))
    args = parser.parse_args()
    out = args.out_dir.resolve(); raw = out / "04_实验数据/raw"; processed = out / "04_实验数据/processed"; figures = out / "05_实验结果/figures"; logs = out / "07_运行日志"
    for d in (raw, processed, figures, logs): d.mkdir(parents=True, exist_ok=True)
    l1, l2 = RpcClient(args.l1_rpc, "L1", raw), RpcClient(args.l2_rpc, "L2", raw)
    diagnostics: List[Dict[str, Any]] = []
    try:
        assert hx(l1.call("eth_chainId", [], "l1_chain_id.json")) == L1_CHAIN_ID
        assert hx(l2.call("eth_chainId", [], "l2_chain_id.json")) == L2_CHAIN_ID
        finalized = l1.call("eth_getBlockByNumber", ["finalized", False], "l1_finalized_anchor.json")
        final_n = hx(finalized["number"]); start_n = final_n - args.l1_block_span + 1
        manifest = {
            "run_at_utc": utc_now(), "experiment_type": "预实验 / 数据链路验证",
            "l1_chain_id": L1_CHAIN_ID, "l2_chain_id": L2_CHAIN_ID,
            "l1_rpc_type": "public unauthenticated JSON-RPC (URL intentionally not persisted)",
            "l2_rpc_type": "public unauthenticated JSON-RPC (URL intentionally not persisted)",
            "l1_finalized_block": {"number": final_n, "hash": finalized["hash"], "timestamp": hx(finalized["timestamp"])},
            "query_range": {"start_block": start_n, "end_block": final_n, "span": args.l1_block_span},
            "contracts": {"Bridge": BRIDGE, "SequencerInbox": SEQUENCER_INBOX, "Inbox": INBOX, "NodeInterface": NODE_INTERFACE},
            "batch_limit": args.batch_limit, "message_limit": args.message_limit,
            "code": "run_preexperiment.py + derive_retryable_ids.mjs",
        }
        batch_logs = fetch_logs_paginated(l1, SEQUENCER_INBOX, SEQUENCER_BATCH_DELIVERED, start_n, final_n, "l1_sequencer_batch_logs")
        bridge_logs = fetch_logs_paginated(l1, BRIDGE, MESSAGE_DELIVERED, start_n, final_n, "l1_bridge_message_logs")
        inbox_logs = fetch_logs_paginated(l1, INBOX, INBOX_MESSAGE_DELIVERED, start_n, final_n, "l1_inbox_message_logs")
        batch_rows = choose_contiguous_batches([parse_batch(x) for x in batch_logs], args.batch_limit)
        l1_block_cache: Dict[int, Dict[str, Any]] = {}
        l2_block_cache: Dict[int, Dict[str, Any]] = {}
        for row in batch_rows:
            l1_block = get_block(l1, row["l1_block_number"], l1_block_cache)
            if l1_block["hash"].lower() != row["l1_block_hash"].lower():
                raise ValueError("batch log block hash mismatch with fixed L1 block")
            row["l1_block_timestamp"] = hx(l1_block["timestamp"])
        nitro_genesis = hx(l2.call("eth_call", [{"to": NODE_INTERFACE, "data": NITRO_GENESIS_SELECTOR}, "latest"], "l2_nitro_genesis.json"))
        l2_latest = hx(l2.call("eth_blockNumber", [], "l2_latest_block.json"))
        batch_cache: Dict[int, int] = {}
        lower_cache: Dict[int, int] = {}
        for row in batch_rows:
            seq = row["batch_sequence"]
            try:
                if seq not in lower_cache:
                    lower_cache[seq] = lower_bound_batch(l2, seq, nitro_genesis, l2_latest, batch_cache)
                first = lower_cache[seq]
                if seq + 1 not in lower_cache:
                    lower_cache[seq + 1] = lower_bound_batch(l2, seq + 1, first, l2_latest, batch_cache)
                next_first = lower_cache[seq + 1]
                last = next_first - 1
                first_block, last_block = get_block(l2, first, l2_block_cache), get_block(l2, last, l2_block_cache)
                row.update({
                    "mapping_status": "range", "mapping_method": "NodeInterface.findBatchContainingBlock monotone lower-bound",
                    "mapping_confidence": "high", "failure_reason": "",
                    "l2_first_block": first, "l2_first_hash": first_block["hash"], "l2_first_timestamp": hx(first_block["timestamp"]),
                    "l2_last_block": last, "l2_last_hash": last_block["hash"], "l2_last_timestamp": hx(last_block["timestamp"]),
                    "p_lag_seconds_last_block": row["l1_block_timestamp"] - hx(last_block["timestamp"]),
                    "p_lag_seconds_first_block": row["l1_block_timestamp"] - hx(first_block["timestamp"]),
                })
            except Exception as exc:
                row.update({"mapping_status": "unmapped", "mapping_method": "NodeInterface.findBatchContainingBlock", "mapping_confidence": "none", "failure_reason": str(exc)})
                diagnostics.append({"object_type": "batch", "object_id": seq, "reason": "nodeinterface_mapping_failure", "detail": str(exc)})
        bridge_by_number = {parse_bridge_message(x)["message_number"]: parse_bridge_message(x) for x in bridge_logs}
        candidates: List[Dict[str, Any]] = []
        for item in inbox_logs:
            msg_number = hx(item["topics"][1])
            bridge = bridge_by_number.get(msg_number)
            if not bridge:
                diagnostics.append({"object_type": "message", "object_id": msg_number, "reason": "bridge_event_missing_in_range", "detail": "Inbox event has no joined Bridge.MessageDelivered"})
                continue
            if bridge["inbox"] != INBOX.lower() or bridge["kind"] != 9:
                continue
            try:
                payload = inbox_event_payload(item)
                candidate = parse_retryable_payload(payload, bridge)
                candidate.update({
                    "l1_tx_hash": item["transactionHash"], "l1_block_number": hx(item["blockNumber"]), "l1_block_hash": item["blockHash"],
                    "l1_log_index": hx(item["logIndex"]), "message_kind": bridge["kind"], "mapping_status": "pending_ticket_derivation",
                })
                candidates.append(candidate)
            except Exception as exc:
                diagnostics.append({"object_type": "message", "object_id": msg_number, "reason": "retryable_payload_parse_failure", "detail": str(exc)})
        candidates = candidates[-args.message_limit:]
        # JSON number 在 Node 中会丢失超过 2^53 的精度；SDK 派生所用全部整数以十进制字符串传递。
        retryable_inputs = []
        integer_fields = {
            "child_chain_id", "message_number", "parent_base_fee", "l2_call_value", "l1_value",
            "max_submission_fee", "gas_limit", "max_fee_per_gas",
        }
        for candidate in candidates:
            retryable_inputs.append({key: (str(value) if key in integer_fields else value) for key, value in candidate.items()})
        retryable_inputs_path = processed / "retryable_derivation_inputs.json"
        retryable_inputs_path.write_text(json.dumps(retryable_inputs, indent=2), encoding="utf-8")
        ids_path = processed / "retryable_derivation_outputs.json"
        helper = Path(__file__).with_name("derive_retryable_ids.mjs")
        subprocess.run(["node", str(helper), str(retryable_inputs_path), str(ids_path)], check=True, capture_output=True, text=True)
        id_map = {int(item["message_number"]): item for item in json.loads(ids_path.read_text(encoding="utf-8"))}
        # 以 afterDelayedMessagesRead 找到首次读取该 message 的 batch；只作 batch-consumption 关联，不替代 ticket ID 映射。
        for row in candidates:
            msg_no = int(row["message_number"]); row.update(id_map[msg_no])
            l1_block = get_block(l1, row["l1_block_number"], l1_block_cache)
            row["l1_block_timestamp"] = hx(l1_block["timestamp"])
            consuming = next((b for b in batch_rows if b["after_delayed_messages_read"] > msg_no), None)
            row["consuming_batch_sequence"] = consuming["batch_sequence"] if consuming else None
            row["consuming_batch_link_status"] = "range" if consuming else "unobserved_in_selected_batch_window"
            receipt = l2.call("eth_getTransactionReceipt", [row["retryable_creation_id"]])
            if receipt is None:
                row.update({"mapping_status": "unmapped", "mapping_method": "SDK-compatible retryable creation id", "mapping_confidence": "high_id_low_observation", "failure_reason": "creation_receipt_not_available_from_current_L2_RPC", "creation_status": "not_found"})
                diagnostics.append({"object_type": "message", "object_id": msg_no, "reason": "creation_receipt_not_found", "detail": row["retryable_creation_id"]})
                continue
            l2bn = hx(receipt["blockNumber"]); l2block = get_block(l2, l2bn, l2_block_cache)
            row.update({
                "mapping_status": "exact", "mapping_method": "official SDK-compatible retryable creation id -> L2 receipt", "mapping_confidence": "high", "failure_reason": "",
                "l2_creation_tx_hash": row["retryable_creation_id"], "l2_creation_block": l2bn, "l2_creation_block_hash": l2block["hash"],
                "l2_creation_timestamp": hx(l2block["timestamp"]), "creation_receipt_status": hx(receipt.get("status", "0x0")),
                "l2_creation_tx_index": hx(receipt["transactionIndex"]), "l2_creation_gas_used": hx(receipt.get("gasUsed", "0x0")),
                "w_ingest_seconds": hx(l2block["timestamp"]) - row["l1_block_timestamp"],
            })
            if row["creation_receipt_status"] != 1:
                row.update({"creation_status": "creation_failed", "redeem_status": "not_applicable"})
                continue
            row["creation_status"] = "created"
            # 同一 receipt 先发 TicketCreated（仅 ticketId），后发 RedeemScheduled（ticketId, retryTxHash, sequence）。
            scheduled = [log for log in receipt.get("logs", []) if log.get("address", "").lower() == ARB_RETRYABLE_TX.lower() and len(log.get("topics", [])) >= 3 and row["retryable_creation_id"].lower() in [x.lower() for x in log.get("topics", [])]]
            if not scheduled:
                row.update({"redeem_status": "no_auto_redeem_event_observed", "w_effect_seconds": None})
                continue
            retry_hash = scheduled[0]["topics"][2]
            retry_receipt = l2.call("eth_getTransactionReceipt", [retry_hash])
            row["auto_redeem_tx_hash"] = retry_hash
            if retry_receipt is None:
                row.update({"redeem_status": "auto_redeem_receipt_not_found", "w_effect_seconds": None})
                continue
            retry_block = get_block(l2, hx(retry_receipt["blockNumber"]), l2_block_cache)
            retry_status = hx(retry_receipt.get("status", "0x0"))
            row.update({
                "auto_redeem_receipt_status": retry_status, "auto_redeem_block": hx(retry_receipt["blockNumber"]),
                "auto_redeem_timestamp": hx(retry_block["timestamp"]), "auto_redeem_gas_used": hx(retry_receipt.get("gasUsed", "0x0")),
                "redeem_status": "auto_redeem_success" if retry_status == 1 else "auto_redeem_failed",
                "w_effect_seconds": hx(retry_block["timestamp"]) - row["l1_block_timestamp"] if retry_status == 1 else None,
            })
        # 明细与汇总。
        write_csv(processed / "batch_golden_set.csv", batch_rows)
        write_csv(processed / "l1_to_l2_message_golden_set.csv", candidates)
        write_csv(processed / "failure_diagnostics.csv", diagnostics)
        valid_p_lag = [float(r["p_lag_seconds_last_block"]) for r in batch_rows if r.get("mapping_status") == "range"]
        valid_ingest = [float(r["w_ingest_seconds"]) for r in candidates if r.get("mapping_status") == "exact"]
        valid_effect = [float(r["w_effect_seconds"]) for r in candidates if r.get("w_effect_seconds") is not None]
        fields_expected = ["l1_tx_hash", "l1_block_number", "l1_block_hash", "l1_block_timestamp", "message_number", "sender", "retryable_creation_id", "mapping_status", "mapping_method", "mapping_confidence"]
        field_completeness = {name: sum(1 for r in candidates if r.get(name) not in (None, "")) / len(candidates) if candidates else 0 for name in fields_expected}
        summary = {
            "experiment_type": "预实验 / 数据链路验证（非正式实验）", "run_at_utc": utc_now(),
            "l1_range": manifest["query_range"], "finalized_anchor": manifest["l1_finalized_block"],
            "batch": {"sample_n": len(batch_rows), "mapping_status": dict(Counter(r["mapping_status"] for r in batch_rows)), "p_lag_seconds_last_block": quantiles(valid_p_lag)},
            "message": {"candidate_retryable_n": len(candidates), "mapping_status": dict(Counter(r["mapping_status"] for r in candidates)), "redeem_status": dict(Counter(r.get("redeem_status", "not_checked") for r in candidates)), "w_ingest_seconds": quantiles(valid_ingest), "w_effect_seconds": quantiles(valid_effect)},
            "field_completeness": field_completeness, "failure_categories": dict(Counter(x["reason"] for x in diagnostics)),
            "interpretation_boundary": "窗口/滞后仅为时间关系；本预实验不测量攻击频率、排序偏置、地址实体归属、MEV 利润或协议防御效果。",
        }
        (processed / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        manifest.update({"raw_log_counts": {"SequencerBatchDelivered": len(batch_logs), "Bridge.MessageDelivered": len(bridge_logs), "InboxMessageDelivered": len(inbox_logs)}, "summary_file": "04_实验数据/processed/summary.json"})
        (out / "provenance_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        interval = f"L1 finalized blocks {start_n}–{final_n}; unit: seconds; batch n={len(batch_rows)}, retryable candidates n={len(candidates)}"
        draw_bar(figures / "01_映射质量.png", "预实验映射质量（真实链上数据）", [("Batch range", sum(r["mapping_status"] == "range" for r in batch_rows)), ("Message exact", sum(r["mapping_status"] == "exact" for r in candidates)), ("Message unmapped", sum(r["mapping_status"] == "unmapped" for r in candidates))], interval + "；仅数据链路验证")
        draw_ecdf(figures / "02_窗口分布_ECDF.png", "L1→L2 窗口的描述性 ECDF", [("W_ingest", valid_ingest, "#2b6cb0"), ("W_effect（成功自动 redeem）", valid_effect, "#b83280")], interval + "；窗口存在不等于已发现可利用 MEV")
        draw_ecdf(figures / "03_batch发布滞后_ECDF.png", "L2→L1 batch publication lag（辅助指标）", [("P_lag（last L2 block anchor）", valid_p_lag, "#c05621")], interval + "；不是 L1→L2 主窗口")
        draw_bar(figures / "04_异常与失败分类.png", "异常与未完成链路的真实分类", [(k, v) for k, v in sorted(Counter(x["reason"] for x in diagnostics).items())] or [("无记录失败", 0)], interval)
        (logs / "run.log").write_text(json.dumps({"completed_at": utc_now(), "batch_rows": len(batch_rows), "message_rows": len(candidates), "diagnostic_rows": len(diagnostics), "l1_rpc_calls": l1.counter, "l2_rpc_calls": l2.counter}, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0
    except Exception as exc:
        (logs / "run_error.log").write_text(json.dumps({"failed_at": utc_now(), "error": repr(exc), "l1_rpc_calls": l1.counter, "l2_rpc_calls": l2.counter}, ensure_ascii=False, indent=2), encoding="utf-8")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
