import { readFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { createHash } from "crypto";
import { createRequire } from "module";
import { fileURLToPath } from "url";

const __dir    = dirname(fileURLToPath(import.meta.url));
const TS_DIR   = join(__dir, "..", "uci-typescript");
const _require = createRequire(join(TS_DIR, "package.json"));
const Ajv      = _require("ajv/dist/2020.js");

const EXCHANGE = join(__dir, "exchange");
const SCHEMAS  = join(TS_DIR, "schemas");
const GREEN = "\x1b[32m", RED = "\x1b[31m", RST = "\x1b[0m";

const ajv = new Ajv({ strict: false });
const vM = ajv.compile(JSON.parse(readFileSync(join(SCHEMAS,"uci_manifest_v0_1.json"),"utf-8")));
const vR = ajv.compile(JSON.parse(readFileSync(join(SCHEMAS,"uci_response_v0_1.json"),"utf-8")));
const vA = ajv.compile(JSON.parse(readFileSync(join(SCHEMAS,"uci_audit_session_v0_1.json"),"utf-8")));

const GENESIS = "0".repeat(64);
const results = [];
const check = (name, ok, detail="") => {
  results.push(ok);
  console.log(`  [${ok?GREEN+"PASS"+RST:RED+"FAIL"+RST}] ${name}${!ok&&detail?"  — "+detail:""}`);
};
const load = f => existsSync(join(EXCHANGE,f))?JSON.parse(readFileSync(join(EXCHANGE,f),"utf-8")):null;

function canonicalJSON(obj) {
  if (obj === null || typeof obj !== "object" || Array.isArray(obj)) return JSON.stringify(obj);
  const keys = Object.keys(obj).sort();
  return "{" + keys.map(k => JSON.stringify(k) + ":" + canonicalJSON(obj[k])).join(",") + "}";
}

const computeHash = (r, prev) => createHash("sha256").update(canonicalJSON({
  previous_hash:prev, sequence:r.sequence, event_id:r.event_id, event_type:r.event_type,
  node_id:r.node_id, timestamp:r.timestamp, actor:r.actor, outcome:r.outcome, detail:r.detail
})).digest("hex");

console.log("\n── TypeScript validates Python output ──────────────────");

console.log("\n[1] python_manifest.json");
const m = load("python_manifest.json");
if(m){
  check("Schema valid",vM(m),ajv.errorsText(vM.errors??[]));
  check("node_id non-empty",!!m.node?.node_id);
  check("display_name non-empty",!!m.node?.display_name);
  check("Has capabilities",m.capabilities?.length>0);
  check("Has transports",m.transports?.length>0);
  check("health block present","health" in m);
  check("version is 0.1",m.uci_manifest_version==="0.1");
}

console.log("\n[2] python_invocation.json");
const i=load("python_invocation.json");
if(i){
  check("Has invocation_id",!!i.invocation_id);
  check("Has correlation_id",!!i.correlation_id);
  check("Has caller.node_id",!!i.caller?.node_id);
  check("Has target.node_id",!!i.target?.node_id);
  check("version is 0.1",i.uci_invocation_version==="0.1");
}

console.log("\n[3] python_response_success.json");
const rs=load("python_response_success.json");
if(rs){
  check("Schema valid",vR(rs),ajv.errorsText(vR.errors??[]));
  check("success == true",rs.success===true);
  check("state == completed",rs.state==="completed");
  check("output present",rs.output!==null&&rs.output!==undefined);
  check("error is null",rs.error===null);
}

console.log("\n[4] python_response_failure.json");
const rf=load("python_response_failure.json");
if(rf){
  check("Schema valid",vR(rf),ajv.errorsText(vR.errors??[]));
  check("success == false",rf.success===false);
  check("state == denied",rf.state==="denied");
  check("error.code canonical",rf.error?.code==="permission_denied");
  check("error.retryable is bool",typeof rf.error?.retryable==="boolean");
  check("error.severity present",!!rf.error?.severity);
}

console.log("\n[5] python_audit_session.json");
const a=load("python_audit_session.json");
if(a){
  check("Schema valid",vA(a),ajv.errorsText(vA.errors??[]));
  const tail=a.records[a.records.length-1].chain_hash;
  const expSH=createHash("sha256").update(`${a.session_id}:${tail}`).digest("hex");
  check("Session hash verifies",a.session_hash===expSH);
  let prev=GENESIS,ok=true;
  for(const r of a.records){if(computeHash(r,prev)!==r.chain_hash){ok=false;break;}prev=r.chain_hash;}
  check("Chain integrity intact",ok);
  const types=new Set(a.records.map(r=>r.event_type));
  check("node_discovered present",types.has("node_discovered"));
  check("trust_assigned present",types.has("trust_assigned"));
  check("node_ready present",types.has("node_ready"));
}

const p=results.filter(Boolean).length,f=results.length-p;
console.log(`\n${"─".repeat(56)}`);
console.log(f===0?`${GREEN}  ✓ TypeScript validates Python: ${p}/${results.length} passed${RST}`
                 :`${RED}  ✗ ${p}/${results.length} passed, ${f} failed${RST}`);
console.log("─".repeat(56)+"\n");
process.exit(f===0?0:1);
