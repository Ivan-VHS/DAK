#!/usr/bin/env node
import { readFileSync, statSync, realpathSync } from "node:fs";
import { dirname, isAbsolute, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),"..");
const EXPECTED=new Map([["reaper",["Ivan-VHS/Reaper","Apache-2.0"]],["pytyliki",["Ivan-VHS/Pytyliki","MIT"]],["oplague",["Ivan-VHS/OPlague","Apache-2.0"]],["ventusample",["Ivan-VHS/VentuSample","Apache-2.0"]]]);
function jsonAt(root,path){return JSON.parse(readFileSync(resolve(root,path),"utf8"));}
function safeFile(root,path){
 if(typeof path!=="string"||!path||isAbsolute(path)||path.includes(String.fromCharCode(92))||path.split("/").some(p=>p===".."||p===""))throw new Error("unsafe artifact path: "+String(path));
 const absolute=resolve(root,path),rel=relative(root,absolute);
 if(rel.startsWith(".."+sep)||rel==="..")throw new Error("artifact escapes root: "+path);
 if(!statSync(absolute).isFile())throw new Error("artifact is not a regular file: "+path);
 const realRel=relative(root,realpathSync(absolute));
 if(realRel.startsWith(".."+sep)||realRel==="..")throw new Error("artifact resolves outside root: "+path);
 return absolute;
}
export function validateEcosystem(graph,registry,workbenches,root=ROOT){
 const errors=[],add=m=>errors.push(m);
 if(graph?.schema!=="dak.ecosystem-integration-graph.v1"||graph?.version!==1)add("unsupported graph schema/version");
 if(graph?.host?.id!=="dak"||graph?.host?.kernel_may_load_peer_code!==false)add("peer code must remain outside the kernel");
 const registered=new Map((registry?.repositories??[]).map(x=>[x.id,x]));
 const nodes=new Map((graph?.projects??[]).map(x=>[x.id,x]));
 if(registered.size!==EXPECTED.size||nodes.size!==EXPECTED.size)add("graph and registry must contain four unique peers");
 for(const [id,[repo,license]] of EXPECTED){
  const pin=registered.get(id),node=nodes.get(id);
  if(!pin||!node){add("missing project node/pin: "+id);continue;}
  if(pin.repository!==repo||node.repository!==repo)add(id+": repository identity mismatch");
  if(pin.license!==license||node.license!==license)add(id+": license mismatch");
  if(node.path!==pin.path||node.path!=="projects/"+id)add(id+": submodule path mismatch");
  if(node.pinned_commit!==pin.pinned_commit||!/^[0-9a-f]{40}$/.test(pin.pinned_commit??""))add(id+": exact commit pin mismatch");
  if(node.license_file!==node.path+"/LICENSE")add(id+": upstream license file path mismatch");
  if(node.auto_build!==false||node.auto_execute!==false||pin.auto_build!==false||pin.auto_execute!==false)add(id+": auto build/execute is forbidden");
  try{safeFile(root,node.license_file);}catch(error){add(id+": "+error.message);}
 }
 const wb=new Map((workbenches?.workbenches??[]).map(x=>[x.project,x]));
 if(wb.size!==EXPECTED.size)add("Mora workbench registry must contain exactly four peers");
 for(const id of EXPECTED.keys())if(!wb.has(id)||wb.get(id).path!=="projects/"+id)add("missing/mismatched Mora workbench: "+id);
 if(workbenches?.policy?.external_process_launch!==false||workbenches?.policy?.auto_execute!==false)add("Mora external launch policy must remain disabled");
 const edgeIds=new Set();
 for(const edge of graph?.interfaces??[]){
  if(edgeIds.has(edge.id))add("duplicate interface id: "+edge.id);edgeIds.add(edge.id);
  if((!EXPECTED.has(edge.producer)&&edge.producer!=="dak")||(!EXPECTED.has(edge.consumer)&&edge.consumer!=="dak")||edge.producer===edge.consumer)add(edge.id+": invalid endpoints");
  if(!["implemented_interop","policy_adapter_only","specified_only"].includes(edge.status))add(edge.id+": invalid maturity label");
  if(!Array.isArray(edge.artifacts)||edge.artifacts.length===0)add(edge.id+": no evidence artifacts");
  else for(const artifact of edge.artifacts){
   try{
    safeFile(root,artifact);
    if(artifact.endsWith(".schema.json")){
     const contractSchema=jsonAt(root,artifact);
     if(contractSchema?.properties?.schema?.const!==edge.contract)add(edge.id+": schema contract identifier mismatch at "+artifact);
    }
   }catch(error){add(edge.id+": "+error.message);}
  }
 }
 if(!graph?.interfaces?.some(e=>e.id==="ventusample.reaper.pack.v1"&&e.status==="specified_only"))add("VentuSample pack must remain specified_only until a consumer exists");
 if(!graph?.interfaces?.some(e=>e.id==="oplague.dak.gpu-telemetry.v1"&&e.status==="policy_adapter_only"))add("GPU telemetry must remain policy_adapter_only until trusted ingest exists");
 const release=graph?.release_pipeline;
 if(release?.script!=="boot/build-release-iso.sh"||release?.workflow!==".github/workflows/release-iso.yml"||release?.workbench_registry!=="federation/mora-workbenches.v1.json")add("release pipeline metadata points to wrong files");
 for(const id of EXPECTED.keys())if(!release?.tested_projects?.includes(id))add("release pipeline omits "+id);
 if(release?.payload_contains_source!==true||release?.payload_contains_license_notices!==true||release?.host_binaries_are_kernel_binaries!==false||release?.user_application_launch_from_kernel!==false)add("release package crosses host/kernel boundary");
 return errors;
}
export function validateRepository(root=ROOT){
 const graph=jsonAt(root,"federation/integration-graph.v1.json"),registry=jsonAt(root,"federation/repositories.v1.json"),workbenches=jsonAt(root,"federation/mora-workbenches.v1.json");
 const errors=validateEcosystem(graph,registry,workbenches,root);
 for(const path of ["boot/build-release-iso.sh",".github/workflows/release-iso.yml","federation/mora-workbenches.v1.json","schemas/ecosystem-integration-graph.v1.schema.json"]){try{safeFile(root,path);}catch(error){errors.push(error.message);}}
 const release=readFileSync(resolve(root,"boot/build-release-iso.sh"),"utf8");
 for(const id of EXPECTED.keys())if(!release.includes("projects/"+id))errors.push("release script omits "+id);
 const pyHeader=readFileSync(resolve(root,"projects/pytyliki/src/interop.h"),"utf8");
 const reaperNative=readFileSync(resolve(root,"projects/reaper/reaper/native.py"),"utf8");
 if(!pyHeader.includes("#define PYTYLIKI_ABI_VERSION 1u")||!pyHeader.includes("pytyliki_abi_version")||!reaperNative.includes("ABI_VERSION = 1")||!reaperNative.includes("must be absolute and explicit"))errors.push("Pytyliki/Reaper C ABI v1 contract evidence mismatch");
 return errors;
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const errors=validateRepository();
 if(errors.length){for(const error of errors)process.stderr.write("ERROR: "+error+"\\n");process.exitCode=1;}
 else process.stdout.write("DAK ecosystem integration graph: validated\\n");
}
