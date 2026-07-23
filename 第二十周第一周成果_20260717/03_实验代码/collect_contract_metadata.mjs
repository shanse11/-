#!/usr/bin/env node
/* 只读收集合约 code hash 与官方 ABI/source 依据；不写入 RPC URL 或凭证。 */
import fs from 'node:fs';
import path from 'node:path';
import { ethers } from 'ethers';

const outputRoot = process.argv[2];
if (!outputRoot) throw new Error('usage: node collect_contract_metadata.mjs OUTPUT_ROOT');
const l1Rpc = process.env.ARBITRUM_L1_RPC || 'https://eth.drpc.org';
const rawDir = path.join(outputRoot, '04_实验数据', 'raw');
const manifestPath = path.join(outputRoot, 'provenance_manifest.json');
const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
const finalTag = '0x' + Number(manifest.l1_finalized_block.number).toString(16);
const contracts = {
  Bridge: '0x8315177aB297bA92A06054cE80a67Ed4DBd7ed3a',
  SequencerInbox: '0x1c479675ad559DC151F6Ec7ed3FbF8ceE79582B6',
  Inbox: '0x4Dbd4fc535Ac27206064B68FfCf827b0A60BAB3f',
};
let id = 100;
async function rpc(method, params) {
  const resp = await fetch(l1Rpc, {method: 'POST', headers: {'content-type': 'application/json'}, body: JSON.stringify({jsonrpc:'2.0', id:id++, method, params})});
  const body = await resp.json();
  if (body.error) throw new Error(`${method}: ${JSON.stringify(body.error)}`);
  return body;
}
const actual = {};
for (const [name, address] of Object.entries(contracts)) {
  const body = await rpc('eth_getCode', [address, finalTag]);
  fs.writeFileSync(path.join(rawDir, `l1_${name}_code.json`), JSON.stringify(body, null, 2));
  actual[name] = {address, code_bytes:(body.result.length-2)/2, code_hash:ethers.utils.keccak256(body.result)};
}
const metadata = {
  l1_finalized_block: manifest.l1_finalized_block,
  code_query_block_tag: finalTag,
  contracts: actual,
  abi_and_source: {
    IBridge:'https://github.com/OffchainLabs/nitro-contracts/blob/master/src/bridge/IBridge.sol',
    ISequencerInbox:'https://github.com/OffchainLabs/nitro-contracts/blob/master/src/bridge/ISequencerInbox.sol',
    AbsInbox:'https://github.com/OffchainLabs/nitro-contracts/blob/master/src/bridge/AbsInbox.sol',
    NodeInterface:'https://github.com/OffchainLabs/nitro-contracts/blob/master/src/node-interface/NodeInterface.sol'
  }
};
fs.writeFileSync(path.join(outputRoot, '04_实验数据', 'processed', 'contract_metadata.json'), JSON.stringify(metadata, null, 2));
manifest.contract_code_metadata = actual;
manifest.contract_code_query_block_tag = finalTag;
manifest.contract_metadata_file = '04_实验数据/processed/contract_metadata.json';
fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
