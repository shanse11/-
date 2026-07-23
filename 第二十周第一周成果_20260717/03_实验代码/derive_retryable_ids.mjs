#!/usr/bin/env node
/*
 * 基于 Offchain Labs 官方 SDK ParentToChildMessage.calculateSubmitRetryableId
 * 的同构实现：只做 retryable creation transaction id 与 payload hash 的派生。
 * 输入和输出均为本地 JSON；不读取 RPC URL 或任何凭证。
 */
import fs from 'node:fs';
import { ethers } from 'ethers';

const [inputPath, outputPath] = process.argv.slice(2);
if (!inputPath || !outputPath) {
  throw new Error('usage: node derive_retryable_ids.mjs INPUT.json OUTPUT.json');
}

const formatNumber = value => ethers.utils.stripZeros(ethers.BigNumber.from(value).toHexString());
const asAddress = value => ethers.utils.getAddress(value);

function calculateSubmitRetryableId(record) {
  const fields = [
    formatNumber(record.child_chain_id),
    ethers.utils.zeroPad(formatNumber(record.message_number), 32),
    asAddress(record.sender),
    formatNumber(record.parent_base_fee),
    formatNumber(record.l1_value),
    formatNumber(record.max_fee_per_gas),
    formatNumber(record.gas_limit),
    record.dest_address === ethers.constants.AddressZero ? '0x' : asAddress(record.dest_address),
    formatNumber(record.l2_call_value),
    asAddress(record.call_value_refund_address),
    formatNumber(record.max_submission_fee),
    asAddress(record.excess_fee_refund_address),
    record.call_data,
  ];
  return ethers.utils.keccak256(ethers.utils.hexConcat([
    '0x69',
    ethers.utils.RLP.encode(fields),
  ]));
}

const records = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
const output = records.map(record => ({
  message_number: String(record.message_number),
  retryable_creation_id: calculateSubmitRetryableId(record),
  payload_hash: ethers.utils.keccak256(record.raw_event_data),
  derivation: 'SDK-compatible EIP-2718 type 0x69 RLP + keccak256',
}));
fs.writeFileSync(outputPath, JSON.stringify(output, null, 2));
