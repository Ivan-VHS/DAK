"""Formula parsing, graph construction and safe Jora source-package synthesis."""
from __future__ import annotations
import hashlib, json, os, re, shutil, sys, zipfile
from pathlib import Path, PurePosixPath
from difflib import get_close_matches
from typing import Any
from .catalog import PARAMETERS, resolve_parameter

PACKAGE_SCHEMA="jora.app-package.v1"
MAX_FORMULA_CHARS=2048
MAX_COMPONENTS=64
MAX_PACKAGE_BYTES=32*1024*1024
MAX_FILES=256
MAX_FILE_BYTES=8*1024*1024

class FormulaError(ValueError):
    """Formula cannot be normalized or composed safely."""

def normalize_formula(formula: str) -> list[dict[str,Any]]:
    if not isinstance(formula,str) or not formula.strip():
        raise FormulaError("formula must contain at least one component")
    if len(formula)>MAX_FORMULA_CHARS:
        raise FormulaError(f"formula exceeds {MAX_FORMULA_CHARS} characters")
    chunks=re.split(r"\s*(?:\+|,|&|\bи\b|\band\b)\s*",formula,flags=re.IGNORECASE)
    if len(chunks)>MAX_COMPONENTS:
        raise FormulaError(f"formula exceeds the {MAX_COMPONENTS}-component limit")
    components=[]
    seen=set()
    for index,raw in enumerate(chunks):
        token=raw.strip().strip("[](){} ")
        role="primary" if index==0 else "standard"
        match=re.match(r"^(основной|primary|главный|optional|опциональный|фоновый)\s*:\s*(.+)$",token,re.IGNORECASE)
        if match:
            role="primary" if match.group(1).casefold() in {"основной","primary","главный"} else "optional"
            token=match.group(2).strip()
        if not token:
            raise FormulaError("formula contains an empty component")
        parameter=resolve_parameter(token)
        if parameter is None:
            suggestions=get_close_matches(token.casefold(),[p["id"].replace("_"," ") for p in PARAMETERS]+[p["name"].casefold() for p in PARAMETERS],n=3,cutoff=.72)
            hint="; possible matches: "+", ".join(suggestions) if suggestions else ""
            raise FormulaError(f"unknown component {token!r}{hint}")
        if parameter["id"] in seen:
            raise FormulaError(f"duplicate component: {parameter['id']}")
        seen.add(parameter["id"])
        components.append({"id":parameter["id"],"name":parameter["name"],"domain":parameter["domain"],"role":role,"description":parameter["description"]})
    for component in components:
        parameter=next(p for p in PARAMETERS if p["id"]==component["id"])
        collision=set(parameter.get("conflicts",[])).intersection(seen)
        if collision:
            raise FormulaError(f"conflicting components: {component['id']} conflicts with {', '.join(sorted(collision))}")
    return components

def _edge(source:str,target:str,kind:str,layer:str="functional")->dict[str,str]:
    return {"source":source,"target":target,"kind":kind,"layer":layer}

def build_graph(components:list[dict[str,Any]])->dict[str,Any]:
    if not components: raise FormulaError("cannot build a graph without components")
    nodes=[{"id":"reaper:core","kind":"coordinator","layer":"language","name":"Reaper core"},{"id":"data:unified-project","kind":"data-hub","layer":"data","name":"Unified project model"}]
    nodes.extend({"id":f"component:{c['id']}","kind":"component","layer":"functional","name":c["name"],"domain":c["domain"]} for c in components)
    edges=[]
    clusters:dict[str,list[str]]={}
    if len(components)<=12:
        for c in components:
            node=f"component:{c['id']}"
            edges.extend([_edge(node,"reaper:core","register_component"),_edge(node,"data:unified-project","bind_project_data","data")])
        for i,left in enumerate(components):
            for right in components[i+1:]:
                if left["domain"]==right["domain"] or len(components)==3:
                    edges.append(_edge(f"component:{left['id']}",f"component:{right['id']}","domain_synergy"))
    else:
        for c in components: clusters.setdefault(c["domain"],[]).append(c["id"])
        for domain,members in sorted(clusters.items()):
            gateway="cluster:"+domain
            nodes.append({"id":gateway,"kind":"cluster-gateway","layer":"functional","name":domain.title()+" gateway","member_count":len(members)})
            edges.append(_edge(gateway,"reaper:core","cluster_route"))
            for member in members:
                edges.extend([_edge(f"component:{member}",gateway,"cluster_membership"),_edge(f"component:{member}","data:unified-project","bind_project_data","data")])
        for members in clusters.values():
            for i,member in enumerate(members[:-1]):
                edges.append(_edge(f"component:{member}",f"component:{members[i+1]}","local_domain_synergy"))
    return {"schema":"jora.formula-graph.v1","topology":"dense-triad" if len(components)==3 else ("clustered-hub" if len(components)>12 else "hub-and-spoke"),"component_count":len(components),"nodes":nodes,"edges":edges,"clusters":dict(sorted(clusters.items())),"growth_policy":{"max_components":MAX_COMPONENTS,"dense_pairwise_only_for_base_triad":True,"large_formula_strategy":"domain clusters, gateways and bounded local adjacency","edge_complexity":"O(N) for N > 12"}}

def select_languages(components:list[dict[str,Any]])->list[dict[str,Any]]:
    selected=[{"id":"reaper","role":"core language and coordination","required":True,"availability":"checked_by_duckos_reaper_adapter","reason":"Reaper is the canonical language and orchestration core."}]
    ids={c["id"] for c in components}
    if ids.intersection({"text_editor","translator","subtitles"}):
        selected.append({"id":"python","role":"text processing and translation adapters","required":False,"availability":"current_duckos_python","reason":"Python supplies the available reference-runtime text ecosystem."})
    if "audio_editor" in ids:
        rustc=shutil.which("rustc")
        if rustc:
            selected.append({"id":"rust","role":"optional audio/DSP adapter","required":False,"availability":"toolchain_detected","compiler":str(Path(rustc).resolve()),"reason":"Rust compiler detected for an isolated high-performance adapter."})
        else:
            selected.append({"id":"python","role":"audio metadata and non-real-time fallback","required":False,"availability":"current_duckos_python","reason":"rustc not found; do not claim native real-time DSP."})
    unique={}
    for item in selected: unique.setdefault(item["id"],item)
    return list(unique.values())

def _slug(value:str)->str:
    return (re.sub(r"[^a-z0-9]+","-",value.casefold()).strip("-")[:56].strip("-") or "jora-app")

def _identity(components:list[dict[str,Any]])->tuple[str,str,list[str]]:
    ids={c["id"] for c in components}
    if {"text_editor","audio_editor","translator"}.issubset(ids):
        return "Слововолна","slovovolna",["WordWave","Голосослов"]
    labels={"text":"Text","audio":"Sound","translator":"Lingua","notes":"Note","task":"Task","calendar":"Time","subtitles":"Caption","offline":"Local","cloud":"Cloud"}
    roots=[c["id"].split("_")[0] for c in components[:3]]
    name="".join(labels.get(root,root.title()) for root in roots) or "Jora"
    if len(components)>1: name+=" Studio"
    return name[:40],_slug("-".join(roots)),[name+" Studio","Jora "+name]

def _demo(components:list[dict[str,Any]])->dict[str,Any]:
    ids={c["id"] for c in components}
    has_text="text_editor" in ids
    has_audio="audio_editor" in ids
    has_translation="translator" in ids
    source=["Добро пожаловать в проект.","Текст, звук и смысл связаны в одном рабочем пространстве.","Изменения сегмента отмечают связанные данные для проверки.","Экспорт сохраняет структуру и временные связи."]
    english=["Welcome to the project.","Text, sound and meaning share one workspace.","Segment edits mark related data for review.","Export preserves structure and timing links."]
    segments=[]
    for i,(ru,en) in enumerate(zip(source,english),1):
        unit={"id":f"seg_{i:03d}","status":"demo"}
        if has_text: unit["source_text"]=ru
        if has_translation: unit.update({"translated_text":en,"translation_status":"demo_not_reviewed"})
        if has_audio: unit.update({"start_ms":(i-1)*2500,"end_ms":i*2500,"audio_ref":f"audio.placeholder.segment_{i:03d}","audio_asset_status":"metadata_placeholder_no_audio_file"})
        segments.append(unit)
    return {"schema":"jora.demo-project.v1","name":"Утренний подкаст о языках и звуке","generated_content":True,"segments":segments,"glossary":[{"source":"timeline","target":"таймлайн"},{"source":"segment","target":"сегмент"},{"source":"workflow","target":"рабочий процесс"}] if has_translation else [],"assets":{"audio":"placeholder-metadata-only" if has_audio else "not-requested","images":"not-generated"}}

def _source(name:str,formula:str)->str:
    app=json.dumps(name,ensure_ascii=False)
    form=json.dumps(formula,ensure_ascii=False)
    return "# Generated by Jora for DuckOS. Review before execution.\n"+f"make app_name := {app}\n"+f"make formula := {form}\n"+'emit "Jora source package: " ++ app_name\n'+'emit "Formula: " ++ formula\n'

def build_application(formula:str,*,requested_name:str|None=None)->dict[str,Any]:
    components=normalize_formula(formula)
    display,slug,alternatives=_identity(components)
    if requested_name is not None:
        candidate=requested_name.strip()
        if not candidate or len(candidate)>64 or any(ord(c)<32 for c in candidate): raise FormulaError("custom name must be 1-64 printable characters")
        display,slug=candidate,_slug(candidate)
    label=" + ".join(c["name"] for c in components)
    graph=build_graph(components)
    languages=select_languages(components)
    files={
        "README.md":(f"# {display}\n\nGenerated from: {label}.\n\nThis is a source package, not an installed or executable application. Inspect and validate it before any future execution.\n").encode(),
        "formula.graph.json":(json.dumps(graph,ensure_ascii=False,indent=2)+"\n").encode(),
        "content/demo-project.json":(json.dumps(_demo(components),ensure_ascii=False,indent=2)+"\n").encode(),
        "source/main.rpr":_source(display,label).encode(),
        "polyglot/languages.json":(json.dumps(languages,ensure_ascii=False,indent=2)+"\n").encode(),
    }
    inventory={path:{"size_bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()} for path,data in sorted(files.items())}
    formula_hash=hashlib.sha256(json.dumps([c["id"] for c in components],separators=(",",":")).encode()).hexdigest()
    manifest={"schema":PACKAGE_SCHEMA,"format_version":1,"app":{"id":slug,"display_name":display,"alternative_names":alternatives,"tagline":"Приложение, собранное из совместимых возможностей."},"formula":{"source":formula,"canonical":label,"components":components,"sha256":formula_hash},"runtime":{"core_language":"reaper","selected_languages":languages,"target_profile":"duckos-user-space-source-package"},"graph":{"path":"formula.graph.json","topology":graph["topology"],"node_count":len(graph["nodes"]),"edge_count":len(graph["edges"])},"content":{"path":"content/demo-project.json","audio_payload_included":False,"generated_from_seed_scenario":True},"build":{"status":"source_generated","compiled":False,"tested":False,"published":False,"installation_performed":False},"integrity":{"algorithm":"sha256","files":inventory},"generation":{"generator":"DuckOS Jora","generator_version":"0.1.0","reproducibility":"deterministic-for-identical-formula-and-generator-version"}}
    files["jora.manifest.json"]=(json.dumps(manifest,ensure_ascii=False,indent=2,sort_keys=True)+"\n").encode()
    return {"manifest":manifest,"graph":graph,"languages":languages,"files":files}

def _safe_path(name:str)->str:
    if not isinstance(name,str) or not name or "\\" in name or name.startswith("/"): raise ValueError(f"unsafe package path: {name!r}")
    path=PurePosixPath(name)
    if path.is_absolute() or path.as_posix()!=name or any(part in {"",".",".."} for part in path.parts): raise ValueError(f"unsafe package path: {name!r}")
    return path.as_posix()

def write_package(application:dict[str,Any],output:str|Path)->dict[str,Any]:
    target=Path(output).expanduser()
    if target.exists() or target.is_symlink(): raise ValueError(f"output already exists: {target}")
    files=application.get("files")
    if not isinstance(files,dict) or not files: raise ValueError("application package has no files")
    if len(files)>MAX_FILES or sum(len(x) for x in files.values())>MAX_PACKAGE_BYTES: raise ValueError("package exceeds file-count or size limit")
    for name,data in files.items():
        _safe_path(name)
        if not isinstance(data,bytes) or len(data)>MAX_FILE_BYTES: raise ValueError(f"invalid generated file: {name}")
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.suffix.casefold()==".zip":
        temporary=target.with_name(target.name+".tmp")
        if temporary.exists() or temporary.is_symlink():
            raise ValueError(f"temporary output already exists: {temporary}")
        try:
            with zipfile.ZipFile(temporary,"x",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
                for name,data in sorted(files.items()):
                    info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0))
                    info.compress_type=zipfile.ZIP_DEFLATED
                    info.external_attr=0o100644<<16
                    archive.writestr(info,data)
            os.replace(temporary,target)
        finally:
            if temporary.exists(): temporary.unlink()
        kind="zip"
    else:
        target.mkdir()
        for name,data in sorted(files.items()):
            destination=target.joinpath(*PurePosixPath(_safe_path(name)).parts)
            destination.parent.mkdir(parents=True,exist_ok=True)
            destination.write_bytes(data)
        kind="directory"
    return {"path":str(target.resolve()),"kind":kind,"files":len(files),"size_bytes":sum(len(x) for x in files.values()),"app_id":application["manifest"]["app"]["id"],"display_name":application["manifest"]["app"]["display_name"]}

def _read_package(path:Path)->dict[str,bytes]:
    if path.is_symlink(): raise ValueError("package path must not be a symbolic link")
    if path.is_dir():
        root=path.resolve()
        result={}
        total=0
        for item in root.rglob("*"):
            if item.is_symlink(): raise ValueError("symbolic links are not allowed in packages")
            if item.is_file():
                name=_safe_path(item.relative_to(root).as_posix())
                data=item.read_bytes()
                if len(data)>MAX_FILE_BYTES: raise ValueError(f"file exceeds size limit: {name}")
                total += len(data)
                if total>MAX_PACKAGE_BYTES: raise ValueError("package expanded size exceeds limit")
                result[name]=data
                if len(result)>MAX_FILES: raise ValueError("package exceeds file-count limit")
        return result
    if not path.is_file() or path.suffix.casefold()!=".zip": raise ValueError("package must be a directory or .zip archive")
    result={}
    total=0
    with zipfile.ZipFile(path,"r") as archive:
        members=archive.infolist()
        if len(members)>MAX_FILES: raise ValueError("package exceeds file-count limit")
        for info in members:
            if info.is_dir(): continue
            name=_safe_path(info.filename)
            if name in result: raise ValueError(f"duplicate package member: {name}")
            if ((info.external_attr>>16)&0o170000)==0o120000: raise ValueError(f"symbolic link is not allowed: {name}")
            if info.file_size>MAX_FILE_BYTES: raise ValueError(f"file exceeds size limit: {name}")
            total+=info.file_size
            if total>MAX_PACKAGE_BYTES: raise ValueError("package expanded size exceeds limit")
            result[name]=archive.read(info)
    return result

def validate_package(path:str|Path,*,check_reaper:bool=True)->dict[str,Any]:
    files=_read_package(Path(path).expanduser())
    raw=files.get("jora.manifest.json")
    if raw is None: raise ValueError("jora.manifest.json is missing")
    try: manifest=json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError,json.JSONDecodeError) as error: raise ValueError(f"invalid Jora manifest: {error}") from error
    if not isinstance(manifest,dict) or manifest.get("schema")!=PACKAGE_SCHEMA: raise ValueError(f"manifest schema must be {PACKAGE_SCHEMA}")
    app=manifest.get("app")
    formula=manifest.get("formula")
    integrity=manifest.get("integrity")
    if not isinstance(app,dict) or not isinstance(app.get("id"),str) or not app["id"] or not isinstance(app.get("display_name"),str) or not app["display_name"]:
        raise ValueError("manifest app identity is invalid")
    if not isinstance(formula,dict) or not isinstance(formula.get("components"),list) or not formula["components"]:
        raise ValueError("manifest formula is invalid")
    if len(formula["components"])>MAX_COMPONENTS:
        raise ValueError("manifest formula exceeds component limit")
    if not isinstance(integrity,dict) or integrity.get("algorithm")!="sha256":
        raise ValueError("manifest integrity algorithm must be sha256")
    inventory=integrity.get("files")
    if not isinstance(inventory,dict) or not inventory: raise ValueError("manifest integrity inventory is missing")
    verified=[]
    for name,record in inventory.items():
        safe=_safe_path(name)
        data=files.get(safe)
        if data is None: raise ValueError(f"manifest file is missing: {safe}")
        if not isinstance(record,dict) or record.get("size_bytes")!=len(data): raise ValueError(f"size mismatch: {safe}")
        digest=record.get("sha256")
        if not isinstance(digest,str) or digest!=hashlib.sha256(data).hexdigest(): raise ValueError(f"SHA-256 mismatch: {safe}")
        verified.append(safe)
    extras=set(files)-set(verified)-{"jora.manifest.json"}
    if extras: raise ValueError("unlisted package files: "+", ".join(sorted(extras)))
    for pointer in (manifest.get("graph",{}).get("path"),manifest.get("content",{}).get("path")):
        if not isinstance(pointer,str) or _safe_path(pointer) not in files:
            raise ValueError("manifest graph/content artifact pointer is invalid")
    source=files.get("source/main.rpr")
    if source is None: raise ValueError("source/main.rpr is missing")
    reaper={"status":"not_checked"}
    if check_reaper:
        try:
            from duckos.desktop.reaper import ReaperWorkbench
            workbench=ReaperWorkbench()
            if workbench.available:
                import tempfile
                with tempfile.TemporaryDirectory(prefix="duckos-jora-check-") as temporary:
                    selected=Path(temporary)/"main.rpr"
                    selected.write_bytes(source)
                    result=workbench.check(selected)
                    reaper={"status":"passed" if result.get("ok") else "failed","exit_code":result.get("exit_code"),"stdout":result.get("stdout",""),"stderr":result.get("stderr","")}
            else: reaper={"status":"skipped","reason":"Reaper checkout not found"}
        except Exception as error: reaper={"status":"unavailable","reason":str(error)}
    return {"schema":"jora.package-validation.v1","valid":True,"app_id":manifest["app"]["id"],"display_name":manifest["app"]["display_name"],"verified_files":sorted(verified),"reaper_static_check":reaper,"installation_performed":False,"execution_performed":False}
