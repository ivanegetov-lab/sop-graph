#!/usr/bin/env python3
"""SOP graph: merge per-document extractions into a knowledge graph of how a plant is run.
Python 3 standard library only.

  pages   --docs DIR --out DIR         first-page images + text dumps of each PDF (needs pdftoppm/pdftotext; optional)
  names   --extracted DIR              every name used so far, so the next extraction reuses them
  check   --extracted DIR [...]        build in memory and print the issues and the candidates that need a human or Claude decision
  build   --extracted DIR --out DIR    graph.json, graph.db, plant-summary.md, qa-report.md, graph.html
"""
import argparse
import base64
import collections
import datetime
import glob
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys

TYPES = ["procedure", "equipment", "material", "product", "tool", "ppe", "role", "form", "supplier", "missing"]
LISTS = {"equipment": ("uses", "equipment"), "materials": ("uses", "material"), "tools": ("uses", "tool"), "ppe": ("requires", "ppe"),
         "roles": ("done_by", "role"), "forms": ("records_on", "form"), "products": ("covers", "product")}
LEADS = {"lead", "leader", "leadhand", "chargehand"}
TAG = re.compile(r"^[A-Z]{1,5}-?\d{1,4}[A-Z]?$")
GENERIC_ROLES = {"anyone", "everyone", "all employees", "all staff", "authorized employee", "affected employee"}
STOP = {"the", "a", "an", "of", "for", "and", "to", "at", "in", "on", "per", "is", "be", "must", "may", "who"}


def die(msg):
    sys.exit("sop_graph: " + msg)


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def toks(s):
    return {t for t in norm(s).split() if t not in STOP}


def slug(kind, name):
    return kind[:2] + ":" + norm(name).replace(" ", "-")


def load_extractions(folder):
    files = sorted(glob.glob(os.path.join(folder, "*.json")))
    if not files:
        die("no .json files in " + folder)
    out = []
    for f in files:
        try:
            with open(f, encoding="utf-8") as fh:
                d = json.load(fh)
        except Exception as ex:
            die("%s is not valid JSON: %s" % (f, ex))
        if not isinstance(d, dict) or "doc" not in d or not d["doc"].get("id"):
            die("%s has no doc.id" % f)
        d["_file"] = os.path.basename(f)
        out.append(d)
    ids = collections.Counter(d["doc"]["id"] for d in out)
    dup = [k for k, v in ids.items() if v > 1]
    if dup:
        die("the same doc.id appears in more than one extraction file: " + ", ".join(dup))
    return out


def ev(doc_id, item):
    return {"doc": doc_id, "where": item.get("where", ""), "quote": item.get("quote", "")}


class Graph:
    def __init__(self):
        self.nodes, self.edges, self.issues, self.params, self.rules, self.unsure = {}, [], [], [], [], []

    def node(self, nid, kind, name, **extra):
        n = self.nodes.get(nid)
        if not n:
            n = self.nodes[nid] = {"id": nid, "type": kind, "name": name}
        n.update({k: v for k, v in extra.items() if v not in (None, "", [])})
        return n

    def edge(self, src, dst, kind, evidence):
        for e in self.edges:
            if e["src"] == src and e["dst"] == dst and e["type"] == kind:
                if evidence and evidence not in e["evidence"]:
                    e["evidence"].append(evidence)
                return e
        e = {"src": src, "dst": dst, "type": kind, "evidence": [evidence] if evidence else []}
        self.edges.append(e)
        return e

    def issue(self, kind, severity, title, detail, evidence, docs):
        if any(i["type"] == kind and i["title"] == title for i in self.issues):
            return
        self.issues.append({"id": "I%03d" % (len(self.issues) + 1), "type": kind, "severity": severity, "title": title,
                            "detail": detail, "evidence": evidence, "docs": sorted(set(docs))})


def alias_map(path):
    if not path:
        return {}
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    m = {}
    for kind, groups in raw.items():
        for canonical, variants in groups.items():
            for v in variants:
                m[(kind, norm(v))] = canonical
    return m


def build(args):
    X = load_extractions(args.extracted)
    al = alias_map(args.aliases)
    G = Graph()
    docs = {d["doc"]["id"]: d["doc"] for d in X}

    def canon(kind, name):
        return al.get((kind, norm(name)), name).strip()

    for d in X:
        m = d["doc"]
        G.node(m["id"], "procedure", m.get("title", m["id"]), rev=m.get("rev"), effective=m.get("effective"), owner=m.get("owner"),
               doc_type=m.get("type"), file=m.get("file"), pages=m.get("pages"), purpose=m.get("purpose"))
    training = collections.defaultdict(dict)   # role -> {doc_id: (rev, evidence)}
    stale = set()
    training_docs = {d["doc"]["id"] for d in X if d.get("training")}
    for d in X:
        did = d["doc"]["id"]
        for key, (etype, kind) in LISTS.items():
            for it in d.get(key) or []:
                name = canon(kind, it.get("name") or it.get("id") or "")
                if not name:
                    continue
                if kind in ("equipment", "form", "product") and it.get("id"):
                    nid = it["id"].strip()
                elif kind == "equipment" and TAG.match(name):
                    nid = name
                else:
                    nid = slug(kind, name)
                G.node(nid, kind, name)
                if kind == "role" and it.get("does"):
                    G.nodes[nid].setdefault("does", {})[did] = it["does"]
                G.edge(did, nid, etype, ev(did, it))
        for it in d.get("suppliers") or []:
            if not it.get("supplier") or not it.get("material"):
                continue
            sid, mname = slug("supplier", it["supplier"]), canon("material", it["material"])
            G.node(sid, "supplier", it["supplier"].strip())
            G.node(slug("material", mname), "material", mname)
            G.edge(sid, slug("material", mname), "supplies", ev(did, it))
            G.edge(did, sid, "names_supplier", ev(did, it))
        for it in d.get("references") or []:
            rid = (it.get("id") or "").strip()
            if not rid or rid == did:
                continue
            if rid not in docs:
                G.node(rid, "missing", it.get("as_written") or rid)
                G.issue("missing_document", "high", "%s points to %s, which is not in the set" % (did, rid),
                        "The document is referenced but was not among the files provided. It may be missing, withdrawn or renumbered.",
                        [ev(did, it)], [did])
            elif it.get("rev") and docs[rid].get("rev") and norm(it["rev"]) != norm(docs[rid]["rev"]) and (did, rid) not in stale:
                stale.add((did, rid))
                G.issue("old_revision", "high", "%s cites %s Rev %s; the current revision is %s" % (did, rid, it["rev"], docs[rid]["rev"]),
                        "Work may be following a withdrawn version.", [ev(did, it)], [did, rid])
            G.edge(did, rid, "refers_to", ev(did, it))
        for it in d.get("training") or []:
            role = canon("role", it.get("role", ""))
            if not role:
                continue
            rid = slug("role", role)
            G.node(rid, "role", role)
            for t in it.get("docs") or []:
                tid = (t.get("id") or "").strip()
                if not tid:
                    continue
                training[rid][tid] = (t.get("rev"), ev(did, it))
                if tid in docs:
                    G.edge(rid, tid, "trained_on", ev(did, it))
                    if t.get("rev") and docs[tid].get("rev") and norm(t["rev"]) != norm(docs[tid]["rev"]) and (did, tid) not in stale:
                        stale.add((did, tid))
                        G.issue("old_revision", "high", "%s lists %s Rev %s for training; the current revision is %s" % (did, tid, t["rev"], docs[tid]["rev"]),
                                "People may be signed off on a withdrawn version.", [ev(did, it)], [did, tid])
        for it in d.get("parameters") or []:
            G.params.append(dict(it, doc=did))
        for it in d.get("rules") or []:
            G.rules.append(dict(it, doc=did))
        for it in d.get("unsure") or []:
            G.unsure.append({"doc": did, "what": it.get("what", "unclear item"), "why": it.get("why", ""), "where": it.get("where", "")})

    # value conflicts: the same parameter given different values in different documents
    def group(items, keyf):
        groups = []
        for it in items:
            k = keyf(it)
            for g in groups:
                if k == g["key"] or (k and g["key"] and len(k & g["key"]) / len(k | g["key"]) >= 0.75):
                    g["items"].append(it)
                    break
            else:
                groups.append({"key": k, "items": [it]})
        return groups
    candidates = []
    for g in group(G.params, lambda p: frozenset(toks(p.get("what", "")) | toks(p.get("applies_to", "")))):
        vals = {(norm(str(p.get("value", ""))), norm(p.get("unit", ""))) for p in g["items"]}
        if len({p["doc"] for p in g["items"]}) > 1 and len(vals) > 1:
            p0 = g["items"][0]
            label = (p0.get("what", "") + (" (%s)" % p0["applies_to"] if p0.get("applies_to") else "")).strip()
            said = "; ".join("%s says %s %s" % (p["doc"], p.get("value", ""), p.get("unit", "")) for p in g["items"])
            candidates.append({"key": "value:" + norm(label), "kind": "value_conflict", "title": "Two values for %s" % label, "detail": said.replace("  ", " "),
                               "evidence": [ev(p["doc"], p) for p in g["items"]], "docs": [p["doc"] for p in g["items"]]})
    for g in group(G.rules, lambda r: frozenset(toks(r.get("topic", "")))):
        if len({r["doc"] for r in g["items"]}) > 1:
            r0 = g["items"][0]
            candidates.append({"key": "rule:" + norm(r0.get("topic", "")), "kind": "rule_conflict", "title": "Compare: %s" % r0.get("topic", ""),
                               "detail": " | ".join("%s: %s" % (r["doc"], r.get("statement", "")) for r in g["items"]),
                               "evidence": [ev(r["doc"], r) for r in g["items"]], "docs": [r["doc"] for r in g["items"]]})

    review = {}
    if args.review:
        with open(args.review, encoding="utf-8") as fh:
            review = json.load(fh)
    decided = {norm(x.get("key", "")): x for x in review.get("decisions", [])}

    def ruling(c):
        k = norm(c["key"])
        if k in decided:
            return decided[k]
        for dk, d in decided.items():
            if dk and dk.split()[0] == k.split()[0] and (k.startswith(dk) or dk.startswith(k)):
                return d
        return None
    open_candidates, dismissed = [], []
    for c in candidates:
        dec = ruling(c)
        if dec and dec.get("verdict") == "conflict":
            G.issue(c["kind"], dec.get("severity", "high"), dec.get("title") or c["title"], dec.get("why") or c["detail"], c["evidence"], c["docs"])
        elif dec and dec.get("verdict") == "ok":
            dismissed.append({"title": c["title"], "why": dec.get("why", ""), "docs": sorted(set(c["docs"]))})
        elif c["kind"] == "value_conflict":
            G.issue("value_conflict", "high", c["title"], c["detail"], c["evidence"], c["docs"])
        else:
            open_candidates.append(c)
    G.dismissed = dismissed
    G.value_keys = [{"key": c["key"], "title": c["title"], "detail": c["detail"]} for c in candidates if c["kind"] == "value_conflict"]
    for f in review.get("findings", []):
        G.issue(f.get("type", "gap"), f.get("severity", "medium"), f.get("title", "Finding"), f.get("detail", ""),
                f.get("evidence", []), [e.get("doc") for e in f.get("evidence", []) if e.get("doc")])

    # people with a job in a procedure that is not on their training list
    if training:
        gaps, absent = collections.defaultdict(list), collections.defaultdict(set)
        for e in G.edges:
            if e["type"] != "done_by":
                continue
            role, did = G.nodes[e["dst"]], e["src"]
            if norm(role["name"]) in GENERIC_ROLES:
                continue
            if e["dst"] not in training:
                absent[role["name"]].add(did)
            elif did not in training[e["dst"]] and did not in training_docs:
                gaps[e["dst"]].append((did, e["evidence"][:1]))
        for rid, items in sorted(gaps.items(), key=lambda kv: -len(kv[1])):
            ds = sorted({d for d, _ in items})
            G.issue("not_trained", "medium", "%s has a job in %d procedure%s that %s not on its training list" % (
                        G.nodes[rid]["name"], len(ds), "" if len(ds) == 1 else "s", "is" if len(ds) == 1 else "are"),
                    "Procedures: %s." % ", ".join(ds), [x for _, evs in items for x in evs][:8], ds)
        if absent:
            G.issue("role_not_in_matrix", "low", "%d role%s with jobs in procedures %s not in the training list" % (
                        len(absent), "" if len(absent) == 1 else "s", "is" if len(absent) == 1 else "are"),
                    "; ".join("%s (%s)" % (r, ", ".join(sorted(ds))) for r, ds in sorted(absent.items())) + ". Some may be other names for listed roles.",
                    [], sorted({d for ds in absent.values() for d in ds}))

    # overdue review
    today = datetime.date.fromisoformat(args.today) if args.today else datetime.date.today()
    old = []
    for did, m in sorted(docs.items()):
        try:
            eff = datetime.date.fromisoformat((m.get("effective") or "")[:10])
        except ValueError:
            continue
        years = (today - eff).days / 365.25
        if years > args.review_years:
            old.append((years, did))
    if old:
        old.sort(reverse=True)
        G.issue("overdue_review", "low", "%d document%s not revised in more than %g years" % (len(old), "" if len(old) == 1 else "s", args.review_years),
                ", ".join("%s (%.1f years)" % (d, y) for y, d in old) + ".", [], [d for _, d in old])

    # names that may be the same thing
    for kind in ("role", "material", "tool", "ppe"):
        ns = [n for n in G.nodes.values() if n["type"] == kind]
        for i, a in enumerate(ns):
            for b in ns[i + 1:]:
                ta, tb = toks(a["name"]), toks(b["name"])
                if not ta or not tb:
                    continue
                heads = norm(a["name"]).split()[-1] in LEADS and norm(b["name"]).split()[-1] in LEADS
                if ta < tb or tb < ta or (kind == "role" and heads):
                    G.issue("similar_names", "low", "“%s” and “%s” may be the same %s" % (a["name"], b["name"], kind),
                            "If they are, add them to aliases.json and rebuild so the graph treats them as one.", [], [])

    deg = collections.Counter()
    for e in G.edges:
        deg[e["src"]] += 1
        deg[e["dst"]] += 1
    for n in G.nodes.values():
        n["degree"] = deg[n["id"]]
    for i in G.issues:
        if i["severity"] == "low":
            continue
        for d in i["docs"]:
            if d in G.nodes:
                G.nodes[d]["issues"] = G.nodes[d].get("issues", 0) + 1
    order = {"high": 0, "medium": 1, "low": 2}
    G.issues.sort(key=lambda i: (order.get(i["severity"], 3), i["type"], i["id"]))
    return G, docs, open_candidates, training


# ---------- quote verification ----------

def verify_quotes(G, text_dir):
    if not text_dir or not os.path.isdir(text_dir):
        return None
    texts = {}
    for f in glob.glob(os.path.join(text_dir, "*.txt")):
        with open(f, encoding="utf-8", errors="ignore") as fh:
            texts[os.path.basename(f)] = norm(fh.read())

    def text_for(doc_id):
        for name, t in texts.items():
            if norm(name).startswith(norm(doc_id)):
                return t
        return None
    seen = bad = 0
    missing = []
    pool = [e2 for e in G.edges for e2 in e["evidence"]] + [dict(doc=p["doc"], quote=p.get("quote", ""), where=p.get("where", "")) for p in G.params + G.rules]
    for e in pool:
        q = norm(e.get("quote", ""))
        if not q:
            continue
        t = text_for(e["doc"])
        if t is None:
            continue
        seen += 1
        if q not in t:
            words = q.split()
            hits = sum(1 for i in range(0, max(1, len(words) - 3)) if " ".join(words[i:i + 4]) in t)
            if hits < 0.6 * max(1, len(words) - 3):
                bad += 1
                missing.append({"doc": e["doc"], "where": e.get("where", ""), "quote": e.get("quote", "")})
    return {"checked": seen, "not_found": bad, "examples": missing[:15]}


# ---------- outputs ----------

LABEL = {"value_conflict": "Two documents, two numbers", "rule_conflict": "Two documents, two rules", "gap": "Gap between documents",
         "old_revision": "Cites an old revision", "missing_document": "Points to a document that isn't there",
         "not_trained": "Job without required training", "role_not_in_matrix": "Role missing from the training list",
         "overdue_review": "Not revised for years", "similar_names": "Names that may be the same thing"}


def write_db(G, path):
    if os.path.exists(path):
        os.remove(path)
    con = sqlite3.connect(path)
    con.executescript("""
      create table nodes(id text primary key, type text, name text, rev text, effective text, owner text, file text, degree int);
      create table edges(src text, dst text, type text, doc text, place text, quote text);
      create table parameters(doc text, what text, applies_to text, value text, unit text, tolerance text, place text, quote text);
      create table rules(doc text, topic text, statement text, place text, quote text);
      create table issues(id text primary key, type text, severity text, title text, detail text, docs text);
    """)
    for n in G.nodes.values():
        con.execute("insert into nodes values(?,?,?,?,?,?,?,?)", (n["id"], n["type"], n["name"], n.get("rev"), n.get("effective"), n.get("owner"), n.get("file"), n.get("degree", 0)))
    for e in G.edges:
        for x in e["evidence"] or [{}]:
            con.execute("insert into edges values(?,?,?,?,?,?)", (e["src"], e["dst"], e["type"], x.get("doc"), x.get("where"), x.get("quote")))
    for p in G.params:
        con.execute("insert into parameters values(?,?,?,?,?,?,?,?)", (p["doc"], p.get("what"), p.get("applies_to"), str(p.get("value", "")), p.get("unit"), p.get("tolerance"), p.get("where"), p.get("quote")))
    for r in G.rules:
        con.execute("insert into rules values(?,?,?,?,?)", (r["doc"], r.get("topic"), r.get("statement"), r.get("where"), r.get("quote")))
    for i in G.issues:
        con.execute("insert into issues values(?,?,?,?,?,?)", (i["id"], i["type"], i["severity"], i["title"], i["detail"], ", ".join(i["docs"])))
    con.commit()
    con.close()


def neighbours(G, nid, etypes=None, direction="out"):
    out = []
    for e in G.edges:
        if etypes and e["type"] not in etypes:
            continue
        if direction in ("out", "both") and e["src"] == nid:
            out.append(e["dst"])
        if direction in ("in", "both") and e["dst"] == nid:
            out.append(e["src"])
    return sorted(set(out))


def write_summary(G, docs, path, title):
    L = ["# %s" % title, "", "Built from %d documents. Give this file to an AI assistant as context. Every statement comes from the documents named beside it." % len(docs), "",
         "## Documents", ""]
    for did in sorted(docs):
        n = G.nodes[did]
        L.append("- **%s %s** (Rev %s, effective %s, owner %s). %s" % (did, n["name"], n.get("rev", "?"), n.get("effective", "?"), n.get("owner", "?"), n.get("purpose", "")))
    L += ["", "## Who does what", ""]
    for r in sorted((n for n in G.nodes.values() if n["type"] == "role"), key=lambda n: -n["degree"]):
        ds = neighbours(G, r["id"], {"done_by"}, "in")
        if ds:
            L.append("- **%s**: has jobs in %s." % (r["name"], ", ".join(ds)))
    L += ["", "## Equipment and the documents that cover it", ""]
    for q in sorted((n for n in G.nodes.values() if n["type"] == "equipment"), key=lambda n: n["id"]):
        L.append("- **%s** (%s): %s." % (q["id"], q["name"], ", ".join(neighbours(G, q["id"], {"uses"}, "in")) or "no document"))
    L += ["", "## Materials and suppliers", ""]
    for m in sorted((n for n in G.nodes.values() if n["type"] == "material"), key=lambda n: n["name"]):
        sup = [G.nodes[s]["name"] for s in neighbours(G, m["id"], {"supplies"}, "in")]
        L.append("- **%s**: used in %s.%s" % (m["name"], ", ".join(neighbours(G, m["id"], {"uses"}, "in")) or "no document", " Supplier: %s." % ", ".join(sup) if sup else ""))
    L += ["", "## Settings and limits", "", "| Setting | Applies to | Value | Document | Where |", "|---|---|---|---|---|"]
    for p in sorted(G.params, key=lambda p: (norm(p.get("what", "")), p["doc"])):
        L.append("| %s | %s | %s %s %s | %s | %s |" % (p.get("what", ""), p.get("applies_to", ""), p.get("value", ""), p.get("unit", ""), p.get("tolerance", "") or "", p["doc"], p.get("where", "")))
    L += ["", "## Rules", ""]
    for r in sorted(G.rules, key=lambda r: (norm(r.get("topic", "")), r["doc"])):
        L.append("- **%s** (%s, %s): %s" % (r.get("topic", ""), r["doc"], r.get("where", ""), r.get("statement", "")))
    hi = [i for i in G.issues if i["severity"] == "high"]
    if hi:
        L += ["", "## Known conflicts in the documents", "", "Do not answer a question that touches one of these without saying the documents disagree.", ""]
        L += ["- %s. %s" % (i["title"], i["detail"]) for i in hi]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")


def write_qa(G, docs, cands, quotes, path, title):
    real = [i for i in G.issues if i["severity"] != "low"]
    L = ["# Review report: %s" % title, "", "%d documents, %d things they touch, %d links. **%d findings**, plus %d housekeeping items and %d things Claude was unsure about." % (
        len(docs), sum(1 for n in G.nodes.values() if n["type"] not in ("procedure", "missing")), len(G.edges), len(real), len(G.issues) - len(real), len(G.unsure)), "",
        "This report lists what the documents say. Whether each item matters is an engineering and quality decision.", ""]
    if quotes:
        L += ["**Quote check:** %d quotes were compared with the document text. %d could not be found word for word%s" % (
            quotes["checked"], quotes["not_found"], "." if not quotes["not_found"] else ":"), ""]
        L += ["- %s, %s: “%s”" % (q["doc"], q["where"], q["quote"]) for q in quotes["examples"]]
        L += [""] if quotes["examples"] else []
    by = collections.defaultdict(list)
    for i in G.issues:
        by[i["type"]].append(i)
    for kind in LABEL:
        if kind not in by:
            continue
        L += ["## %s (%d)" % (LABEL[kind], len(by[kind])), ""]
        for i in by[kind]:
            L.append("- **%s** %s" % (i["title"], i["detail"]))
            for e in i["evidence"]:
                if e.get("quote") or e.get("where"):
                    L.append("  - %s, %s%s" % (e.get("doc", ""), e.get("where", ""), ": “%s”" % e["quote"] if e.get("quote") else ""))
        L.append("")
    if G.unsure:
        L += ["## Unclear to Claude (%d)" % len(G.unsure), "", "Things that could not be read or had to be left open. Check these against the documents.", ""]
        L += ["- **%s** %s: %s %s" % (u["doc"], u["where"], u["what"], u["why"]) for u in G.unsure]
        L.append("")
    if getattr(G, "dismissed", None):
        L += ["## Compared and found consistent (%d)" % len(G.dismissed), ""]
        L += ["- %s (%s). %s" % (d["title"], ", ".join(d["docs"]), d["why"]) for d in G.dismissed]
        L.append("")
    if cands:
        L += ["## Still to decide (%d)" % len(cands), "", "The same topic appears in more than one document. Read both and decide whether they agree.", ""]
        L += ["- **%s** `%s` %s" % (c["title"], c["key"], c["detail"]) for c in cands]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")


def thumbs(pages_dir, docs):
    out = {}
    if not pages_dir or not os.path.isdir(pages_dir):
        return out
    for f in sorted(glob.glob(os.path.join(pages_dir, "*.jpg"))):
        base = os.path.basename(f)
        for did in docs:
            if norm(base).startswith(norm(did) + " ") or norm(base) == norm(did):
                with open(f, "rb") as fh:
                    out[did] = "data:image/jpeg;base64," + base64.b64encode(fh.read()).decode()
    return out


def cmd_pages(args):
    os.makedirs(args.out, exist_ok=True)
    pdfs = sorted(glob.glob(os.path.join(args.docs, "*.pdf")))
    if not pdfs:
        die("no PDF files in " + args.docs)
    ppm, ptt, made = shutil.which("pdftoppm"), shutil.which("pdftotext"), 0
    for f in pdfs:
        stem = os.path.splitext(os.path.basename(f))[0]
        if ppm:
            subprocess.run([ppm, "-r", str(args.dpi), "-jpeg", "-jpegopt", "quality=70", "-f", "1", "-l", "1", "-singlefile", f, os.path.join(args.out, stem)], check=False)
            made += 1
        if ptt:
            subprocess.run([ptt, "-layout", f, os.path.join(args.out, stem + ".txt")], check=False)
    if not ppm:
        print("pdftoppm not found: no page images (install poppler to get them). The graph still works without them.")
    if not ptt:
        print("pdftotext not found: quotes will not be checked against the document text.")
    print("%d documents, %d page images in %s" % (len(pdfs), made, args.out))


def cmd_names(args):
    X = load_extractions(args.extracted)
    out = collections.defaultdict(set)
    for d in X:
        for key, (_, kind) in LISTS.items():
            for it in d.get(key) or []:
                out[kind].add((it.get("id") + " = " if it.get("id") and kind in ("equipment", "form") else "") + (it.get("name") or ""))
        for p in d.get("parameters") or []:
            out["parameter (what | applies_to)"].add("%s | %s" % (p.get("what", ""), p.get("applies_to", "")))
        for r in d.get("rules") or []:
            out["rule topic"].add(r.get("topic", ""))
    print("Names already used in %d extractions. Reuse them exactly when the next document means the same thing.\n" % len(X))
    for k in sorted(out):
        print("%s:\n  %s\n" % (k, "\n  ".join(sorted(out[k]))))


def main():
    ap = argparse.ArgumentParser(description="SOP graph")
    ap.add_argument("command", choices=["pages", "names", "check", "build"])
    ap.add_argument("--docs", help="folder with the source PDFs")
    ap.add_argument("--extracted", help="folder with one extraction .json per document")
    ap.add_argument("--out", help="output folder")
    ap.add_argument("--pages", help="folder made by the pages command (page images + text)")
    ap.add_argument("--aliases", help="aliases.json: names to treat as one")
    ap.add_argument("--review", help="review.json: decisions on candidates and extra findings")
    ap.add_argument("--story", help="story.json: title and the example question for the page")
    ap.add_argument("--title", default="How the plant is run")
    ap.add_argument("--review-years", type=float, default=3.0)
    ap.add_argument("--today", help="YYYY-MM-DD, for the overdue-review check (default: today)")
    ap.add_argument("--dpi", type=int, default=56)
    ap.add_argument("--sample", action="store_true")
    args = ap.parse_args()
    if args.command == "pages":
        if not args.docs or not args.out:
            die("pages needs --docs and --out")
        return cmd_pages(args)
    if not args.extracted:
        die("%s needs --extracted" % args.command)
    if args.command == "names":
        return cmd_names(args)
    G, docs, cands, training = build(args)
    quotes = verify_quotes(G, args.pages)
    if args.command == "check":
        print(json.dumps({"documents": len(docs), "nodes": len(G.nodes), "links": len(G.edges),
                          "findings": sum(1 for i in G.issues if i["severity"] != "low"),
                          "issues": [{k: i[k] for k in ("type", "severity", "title", "detail")} for i in G.issues],
                          "to_decide": [{k: c[k] for k in ("key", "kind", "title", "detail")} for c in cands],
                          "value_conflict_keys": G.value_keys, "ruled_consistent": G.dismissed, "unsure": len(G.unsure),
                          "quote_check": quotes}, indent=1, ensure_ascii=False))
        return
    if not args.out:
        die("build needs --out")
    os.makedirs(args.out, exist_ok=True)
    story = {}
    if args.story:
        with open(args.story, encoding="utf-8") as fh:
            story = json.load(fh)
    title = story.get("title") or args.title
    data = {"meta": {"title": title, "sample": bool(args.sample), "documents": len(docs), "built": str(datetime.date.today()),
                     "labels": LABEL, "quotes": quotes, "story": story},
            "nodes": sorted(G.nodes.values(), key=lambda n: (TYPES.index(n["type"]), n["id"])), "edges": G.edges,
            "parameters": G.params, "rules": G.rules, "issues": G.issues, "to_decide": cands, "unsure": G.unsure, "consistent": G.dismissed}
    with open(os.path.join(args.out, "graph.json"), "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1, ensure_ascii=False)
    write_db(G, os.path.join(args.out, "graph.db"))
    write_summary(G, docs, os.path.join(args.out, "plant-summary.md"), title)
    write_qa(G, docs, cands, quotes, os.path.join(args.out, "qa-report.md"), title)
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "..", "assets", "viewer.html"), encoding="utf-8") as fh:
        tpl = fh.read()
    page = dict(data, thumbs=thumbs(args.pages, docs))
    html = tpl.replace("{{TITLE}}", title.replace("<", "&lt;")).replace("/*__DATA__*/null", json.dumps(page, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"))
    with open(os.path.join(args.out, "graph.html"), "w", encoding="utf-8") as fh:
        fh.write(html)
    hi = sum(1 for i in G.issues if i["severity"] == "high")
    real = sum(1 for i in G.issues if i["severity"] != "low")
    print("%d documents, %d nodes, %d links, %d findings (%d high), %d housekeeping, %d unsure, %d still to decide" % (
        len(docs), len(G.nodes), len(G.edges), real, hi, len(G.issues) - real, len(G.unsure), len(cands)))
    print("wrote graph.json, graph.db, plant-summary.md, qa-report.md, graph.html in " + args.out)


if __name__ == "__main__":
    main()
