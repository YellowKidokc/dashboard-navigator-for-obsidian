#!/usr/bin/env python3
"""
Build a large axiom dependency graph from exported workbook CSV files.

Outputs:
  - axiom_graph_nodes.csv
  - axiom_graph_edges.csv
  - axiom_graph.graphml
  - README_GRAPH.md
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple


DEFAULT_CSV_DIR = Path(
    r"C:\Users\lowes\OneDrive\Desktop\Desktop STAY\MASTER_AXIOM_CONSOLIDATED_FULL_EXPANDED_CSV_EXPORT_20260216_142911"
)
DEFAULT_AXIOMS_DIR = Path(r"O:\_Theophysics_v3\00_AXIOMS")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build axiom graph from CSV export")
    parser.add_argument("--csv-dir", default=str(DEFAULT_CSV_DIR), help="Workbook CSV export directory")
    parser.add_argument("--axioms-dir", default=str(DEFAULT_AXIOMS_DIR), help="00_AXIOMS markdown directory")
    parser.add_argument("--out-dir", default="", help="Output directory (default: <csv-dir>/_GRAPH_<timestamp>)")
    parser.add_argument(
        "--include-unresolved-links",
        action="store_true",
        help="Include unresolved links from 020_AXIOM_LINKS.csv",
    )
    parser.add_argument(
        "--skip-worldviews",
        action="store_true",
        help="Skip worldview stance edges (015_AXIOM_VS_WORLDVIEW.csv)",
    )
    parser.add_argument(
        "--skip-defeat",
        action="store_true",
        help="Skip defeat-condition and case-file extraction from markdown",
    )
    return parser.parse_args()


def clean_id(value: str) -> str:
    s = (value or "").strip()
    if not s:
        return ""
    s = s.strip("'\"")
    s = s.strip()
    # Normalize list-like singletons: "['A1.2']"
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1].strip().strip("'\"").strip()
    # Keep first token before separators if it looks like an ID.
    parts = re.split(r"[,;/]", s)
    s = parts[0].strip() if parts else s
    return s


def to_bool(value: str) -> str:
    s = (value or "").strip().lower()
    return "true" if s in {"true", "yes", "y", "1"} else "false"


def parse_float(value: str, default: float = 0.0) -> float:
    try:
        return float((value or "").strip())
    except Exception:
        return default


def parse_int(value: str, default: int = 0) -> int:
    try:
        return int(float((value or "").strip()))
    except Exception:
        return default


class Graph:
    def __init__(self) -> None:
        self.nodes: Dict[str, Dict[str, str]] = {}
        self.edges: List[Dict[str, str]] = []
        self._edge_seen = set()

    def add_node(self, node_id: str, **attrs: str) -> None:
        node_id = clean_id(node_id)
        if not node_id:
            return
        if node_id not in self.nodes:
            self.nodes[node_id] = {"id": node_id}
        for k, v in attrs.items():
            if v is None:
                continue
            v_str = str(v).strip()
            if not v_str:
                continue
            if k not in self.nodes[node_id] or not self.nodes[node_id][k]:
                self.nodes[node_id][k] = v_str

    def add_edge(self, source: str, target: str, relation: str, **attrs: str) -> None:
        source = clean_id(source)
        target = clean_id(target)
        if not source or not target:
            return
        key = (source, target, relation, attrs.get("stance", ""), attrs.get("link_code", ""))
        if key in self._edge_seen:
            return
        self._edge_seen.add(key)
        row = {
            "source": source,
            "target": target,
            "relation": relation,
        }
        for k, v in attrs.items():
            if v is None:
                continue
            v_str = str(v).strip()
            if v_str:
                row[k] = v_str
        self.edges.append(row)


def csv_reader(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_axiom_master(graph: Graph, path: Path) -> None:
    rows = csv_reader(path)
    for r in rows:
        aid = clean_id(r.get("Axiom_ID", ""))
        if not aid:
            continue
        graph.add_node(
            aid,
            label=r.get("Axiom_Name", "") or aid,
            node_type=(r.get("Type", "") or "AxiomItem"),
            tier=r.get("Tier", ""),
            primitive=r.get("Primitive?", ""),
            status=r.get("Status", ""),
            core_statement=r.get("Core_Statement", ""),
            tdi=r.get("TDI", ""),
            tdi_name=r.get("TDI_Name", ""),
            path=r.get("Path", ""),
            word_count=r.get("Word_Count", ""),
            source_dataset=path.name,
        )


def load_axiom_links(graph: Graph, path: Path, include_unresolved: bool) -> None:
    rows = csv_reader(path)
    for r in rows:
        src = clean_id(r.get("Source_ID", ""))
        tgt = clean_id(r.get("Target_ID", ""))
        if not src or not tgt:
            continue
        resolved = to_bool(r.get("Resolved?", ""))
        if not include_unresolved and resolved != "true":
            continue

        graph.add_node(src, label=r.get("Source_Title", "") or src, node_type="axiom_or_entity")
        graph.add_node(
            tgt,
            label=r.get("Target_Title", "") or tgt,
            node_type=r.get("Target_Type", "") or "axiom_or_entity",
        )
        graph.add_edge(
            src,
            tgt,
            "axiom_link",
            link_code=r.get("Link_Code", ""),
            symbol=r.get("Symbol", ""),
            justification_type=r.get("Justification_Type", ""),
            tdi_alignment=r.get("TDI_Alignment", ""),
            strength=str(parse_int(r.get("Strength", "0"), 0)),
            bidirectional=to_bool(r.get("Bidirectional?", "")),
            resolved=resolved,
            link_summary=r.get("Link_Summary", ""),
            source_dataset=path.name,
        )


def load_worldview_matrix(graph: Graph, path: Path) -> None:
    rows = csv_reader(path)
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    if len(fieldnames) <= 3:
        return
    worldview_cols = fieldnames[3:]

    for col in worldview_cols:
        wv_id = f"WV::{col}"
        graph.add_node(wv_id, label=col, node_type="worldview", source_dataset=path.name)

    for r in rows:
        aid = clean_id(r.get("ID", ""))
        if not aid or aid.upper() == "LEGEND":
            continue
        graph.add_node(aid, label=aid, node_type="axiom_or_entity")
        for col in worldview_cols:
            stance = (r.get(col, "") or "").strip()
            if not stance or stance.upper() == "S":
                continue
            graph.add_edge(
                aid,
                f"WV::{col}",
                "worldview_stance",
                stance=stance,
                source_dataset=path.name,
            )


def split_axiom_ids(raw: str) -> List[str]:
    text = (raw or "").strip()
    if not text:
        return []
    candidates = re.split(r"[,\s;/]+", text)
    out = []
    for c in candidates:
        c = clean_id(c)
        if not c:
            continue
        if re.match(r"^[A-Z]+[0-9]+(?:\.[0-9]+)?$", c):
            out.append(c)
    return out


def load_evidence_chains(graph: Graph, path: Path) -> None:
    rows = csv_reader(path)
    for r in rows:
        supports = split_axiom_ids(r.get("Supports_Axiom", ""))
        if not supports:
            continue
        eid = clean_id(r.get("Evidence_ID", ""))
        if not eid:
            continue
        ev_node = f"EVID::{eid}"
        graph.add_node(
            ev_node,
            label=r.get("Title", "") or eid,
            node_type="evidence",
            domain=r.get("Domain", ""),
            method=r.get("Method", ""),
            path=r.get("Path", ""),
            reproducible=r.get("Reproducible?", ""),
            source_dataset=path.name,
        )
        for aid in supports:
            graph.add_node(aid, label=aid, node_type="axiom_or_entity")
            graph.add_edge(
                ev_node,
                aid,
                "supports_axiom",
                strength=str(parse_int(r.get("Strength", "0"), 0)),
                source_dataset=path.name,
            )


def parse_frontmatter_value(text: str, key: str) -> str:
    if not text.startswith("---\n"):
        return ""
    end = text.find("\n---\n", 4)
    if end == -1:
        return ""
    fm = text[4:end]
    m = re.search(rf"(?m)^{re.escape(key)}:\s*(.*)$", fm)
    if not m:
        return ""
    return m.group(1).strip().strip("'\"")


def body_after_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 4)
    if end == -1:
        return text
    return text[end + 5 :]


def extract_section(body: str, title: str) -> str:
    pat = re.compile(
        rf"(?ms)^##\s+{re.escape(title)}\s*\n(.*?)(?=^##\s+|\Z)",
        flags=re.MULTILINE,
    )
    m = pat.search(body)
    if not m:
        return ""
    return re.sub(r"\s+", " ", m.group(1)).strip()


def extract_case_files(text: str) -> List[str]:
    found = []
    for m in re.finditer(r"CF\d{2}_[A-Za-z0-9_\-]+", text):
        cf = m.group(0)
        if cf not in found:
            found.append(cf)
    return found


def markdown_axiom_index(axioms_dir: Path) -> Dict[str, Path]:
    out: Dict[str, Path] = {}
    for p in axioms_dir.glob("[0-9][0-9][0-9]_*.md"):
        stem = p.stem
        parts = stem.split("_")
        id_from_name = parts[1] if len(parts) > 1 else ""
        text = p.read_text(encoding="utf-8", errors="ignore")
        id_from_fm = clean_id(parse_frontmatter_value(text, "axiom_id"))
        aid = clean_id(id_from_fm or id_from_name)
        if not aid:
            continue
        if aid not in out:
            out[aid] = p
    return out


def attach_defeat_and_case_data(graph: Graph, axioms_dir: Path) -> None:
    idx = markdown_axiom_index(axioms_dir)
    for aid, node in list(graph.nodes.items()):
        if aid.startswith("WV::") or aid.startswith("EVID::") or aid.startswith("CASE::") or aid.startswith("DEFEAT::"):
            continue
        md = idx.get(aid)
        if not md:
            continue
        text = md.read_text(encoding="utf-8", errors="ignore")
        body = body_after_frontmatter(text)
        defeat = extract_section(body, "Defeat Conditions")
        if not defeat:
            defeat = extract_section(body, "Falsification Criteria")
        if defeat:
            graph.nodes[aid]["defeat_text"] = defeat
            dnode = f"DEFEAT::{aid}"
            graph.add_node(
                dnode,
                label=f"Defeat {aid}",
                node_type="defeat_condition",
                text=defeat,
                source_file=str(md),
            )
            graph.add_edge(aid, dnode, "defeat_condition", source_dataset="markdown")

        case_files = extract_case_files(body)
        if case_files:
            graph.nodes[aid]["case_files"] = ", ".join(case_files)
            for cf in case_files:
                cnode = f"CASE::{cf}"
                graph.add_node(cnode, label=cf, node_type="case_file", source_dataset="markdown")
                graph.add_edge(aid, cnode, "case_file", source_dataset="markdown")


def write_nodes_csv(graph: Graph, path: Path) -> None:
    rows = sorted(graph.nodes.values(), key=lambda r: r.get("id", ""))
    keys = sorted({k for row in rows for k in row.keys()})
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def write_edges_csv(graph: Graph, path: Path) -> None:
    rows = []
    for i, e in enumerate(graph.edges, start=1):
        row = dict(e)
        row["edge_id"] = f"E{i:07d}"
        rows.append(row)
    keys = sorted({k for row in rows for k in row.keys()})
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def write_graphml(graph: Graph, path: Path) -> None:
    ns = "http://graphml.graphdrawing.org/xmlns"
    ET.register_namespace("", ns)

    root = ET.Element(f"{{{ns}}}graphml")

    node_keys = [
        ("label", "string"),
        ("node_type", "string"),
        ("tier", "string"),
        ("status", "string"),
        ("core_statement", "string"),
        ("defeat_text", "string"),
        ("case_files", "string"),
        ("path", "string"),
        ("source_dataset", "string"),
    ]
    edge_keys = [
        ("relation", "string"),
        ("link_code", "string"),
        ("symbol", "string"),
        ("justification_type", "string"),
        ("strength", "string"),
        ("resolved", "string"),
        ("stance", "string"),
        ("source_dataset", "string"),
    ]

    for k, t in node_keys:
        ET.SubElement(
            root,
            f"{{{ns}}}key",
            id=f"n_{k}",
            attrib={"for": "node", "attr.name": k, "attr.type": t},
        )
    for k, t in edge_keys:
        ET.SubElement(
            root,
            f"{{{ns}}}key",
            id=f"e_{k}",
            attrib={"for": "edge", "attr.name": k, "attr.type": t},
        )

    g = ET.SubElement(root, f"{{{ns}}}graph", id="G", edgedefault="directed")

    for nid, attrs in sorted(graph.nodes.items(), key=lambda x: x[0]):
        n = ET.SubElement(g, f"{{{ns}}}node", id=nid)
        for k, _ in node_keys:
            v = attrs.get(k, "")
            if v:
                d = ET.SubElement(n, f"{{{ns}}}data", key=f"n_{k}")
                d.text = v

    for i, e in enumerate(graph.edges, start=1):
        ed = ET.SubElement(
            g,
            f"{{{ns}}}edge",
            id=f"e{i}",
            source=e["source"],
            target=e["target"],
        )
        for k, _ in edge_keys:
            v = e.get(k, "")
            if v:
                d = ET.SubElement(ed, f"{{{ns}}}data", key=f"e_{k}")
                d.text = v

    tree = ET.ElementTree(root)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def write_readme(path: Path, stats: Dict[str, object]) -> None:
    now = dt.datetime.now().isoformat(timespec="seconds")
    txt = f"""# Axiom Graph Export

Generated: {now}

## Files
- `axiom_graph_nodes.csv`
- `axiom_graph_edges.csv`
- `axiom_graph.graphml`
- `axiom_graph_viewer.html`
- `graph_stats.json`

## Stats
- Nodes: {stats.get("nodes", 0)}
- Edges: {stats.get("edges", 0)}
- Relations: {", ".join(stats.get("relations", []))}

## Recommended Viewers
1. Gephi (best for very large graphs): import `axiom_graph.graphml`.
2. Cytoscape: import GraphML or CSV edge/node tables.
3. Neo4j: import CSVs (`nodes.csv` / `edges.csv`) for queryable graph analysis.
4. yEd Live: quick web visualization from GraphML.
5. GitHub Pages: open `axiom_graph_viewer.html` for browser-based exploration.

## Notes
- Mermaid is excellent for small subgraphs, but this full graph is too large for Mermaid readability.
- Use filters by relation (`axiom_link`, `defeat_condition`, `case_file`, `worldview_stance`) for practical exploration.
"""
    path.write_text(txt, encoding="utf-8")


def escape_js_string(s: str) -> str:
    return (
        s.replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("${", "\\${")
    )


def write_html_viewer(path: Path, graph: Graph) -> None:
    nodes = []
    for nid, attrs in graph.nodes.items():
        label = attrs.get("label", nid)
        node_type = attrs.get("node_type", "node")
        title_parts = [
            f"id: {nid}",
            f"type: {node_type}",
        ]
        for k in ("tier", "status", "core_statement", "defeat_text", "case_files"):
            v = attrs.get(k, "")
            if v:
                title_parts.append(f"{k}: {v[:500]}")
        title = "\n".join(title_parts)
        nodes.append(
            {
                "id": nid,
                "label": label[:60],
                "group": node_type,
                "title": title,
            }
        )

    edges = []
    for e in graph.edges:
        relation = e.get("relation", "edge")
        title_parts = [f"relation: {relation}"]
        for k in ("link_code", "justification_type", "strength", "resolved", "stance"):
            v = e.get(k, "")
            if v:
                title_parts.append(f"{k}: {v}")
        title = "\n".join(title_parts)
        edges.append(
            {
                "from": e["source"],
                "to": e["target"],
                "label": relation,
                "title": title,
            }
        )

    rels = sorted({e.get("relation", "") for e in graph.edges if e.get("relation")})

    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Axiom Graph Viewer</title>
  <script src="https://unpkg.com/vis-network@9.1.9/dist/vis-network.min.js"></script>
  <style>
    body {{ margin: 0; font-family: Arial, sans-serif; }}
    #toolbar {{ padding: 10px; border-bottom: 1px solid #ddd; display: flex; gap: 10px; flex-wrap: wrap; }}
    #network {{ width: 100vw; height: calc(100vh - 70px); }}
    .rel {{ padding: 3px 8px; border: 1px solid #ccc; border-radius: 6px; }}
  </style>
</head>
<body>
  <div id="toolbar">
    <strong>Relations:</strong>
    <span id="rels"></span>
    <button id="fitBtn">Fit</button>
    <button id="physicsBtn">Toggle Physics</button>
  </div>
  <div id="network"></div>

  <script>
    const allNodes = {json.dumps(nodes)};
    const allEdges = {json.dumps(edges)};
    const relations = {json.dumps(rels)};
    const active = new Set(relations);
    let physicsOn = true;

    const relWrap = document.getElementById('rels');
    relations.forEach(r => {{
      const id = `rel_${{r}}`;
      const label = document.createElement('label');
      label.className = 'rel';
      label.innerHTML = `<input type="checkbox" id="${{id}}" checked /> ${{r}}`;
      relWrap.appendChild(label);
      document.getElementById(id).addEventListener('change', (e) => {{
        if (e.target.checked) active.add(r); else active.delete(r);
        refresh();
      }});
    }});

    const nodes = new vis.DataSet(allNodes);
    const edges = new vis.DataSet(allEdges);
    const container = document.getElementById('network');
    const data = {{ nodes, edges }};
    const options = {{
      interaction: {{ hover: true, tooltipDelay: 100 }},
      physics: {{ enabled: true, stabilization: true }},
      nodes: {{ shape: 'dot', size: 8, font: {{ size: 10 }} }},
      edges: {{ arrows: 'to', smooth: false, width: 0.5 }},
      groups: {{
        worldview: {{ color: '#8ecae6' }},
        evidence: {{ color: '#90be6d' }},
        defeat_condition: {{ color: '#f94144' }},
        case_file: {{ color: '#f8961e' }},
        Axiom: {{ color: '#577590' }},
        axiom_or_entity: {{ color: '#277da1' }}
      }}
    }};
    const network = new vis.Network(container, data, options);

    function refresh() {{
      const filtered = allEdges.filter(e => active.has(e.label));
      edges.clear();
      edges.add(filtered);
    }}

    document.getElementById('fitBtn').onclick = () => network.fit();
    document.getElementById('physicsBtn').onclick = () => {{
      physicsOn = !physicsOn;
      network.setOptions({{ physics: {{ enabled: physicsOn }} }});
    }};
  </script>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def main() -> int:
    args = parse_args()
    csv_dir = Path(args.csv_dir)
    axioms_dir = Path(args.axioms_dir)
    if not csv_dir.exists():
        raise FileNotFoundError(f"CSV dir not found: {csv_dir}")
    if not axioms_dir.exists():
        raise FileNotFoundError(f"Axioms dir not found: {axioms_dir}")

    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.out_dir) if args.out_dir else csv_dir / f"_GRAPH_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)

    graph = Graph()

    load_axiom_master(graph, csv_dir / "019_AXIOMS_MASTER.csv")
    load_axiom_links(graph, csv_dir / "020_AXIOM_LINKS.csv", args.include_unresolved_links)
    load_evidence_chains(graph, csv_dir / "021_EVIDENCE_CHAINS.csv")
    if not args.skip_worldviews:
        load_worldview_matrix(graph, csv_dir / "015_AXIOM_VS_WORLDVIEW.csv")
    if not args.skip_defeat:
        attach_defeat_and_case_data(graph, axioms_dir)

    nodes_csv = out_dir / "axiom_graph_nodes.csv"
    edges_csv = out_dir / "axiom_graph_edges.csv"
    graphml = out_dir / "axiom_graph.graphml"
    stats_json = out_dir / "graph_stats.json"
    readme = out_dir / "README_GRAPH.md"
    html_viewer = out_dir / "axiom_graph_viewer.html"

    write_nodes_csv(graph, nodes_csv)
    write_edges_csv(graph, edges_csv)
    write_graphml(graph, graphml)
    write_html_viewer(html_viewer, graph)

    relations = sorted({e["relation"] for e in graph.edges})
    stats = {
        "nodes": len(graph.nodes),
        "edges": len(graph.edges),
        "relations": relations,
        "include_unresolved_links": bool(args.include_unresolved_links),
        "skip_worldviews": bool(args.skip_worldviews),
        "skip_defeat": bool(args.skip_defeat),
    }
    stats_json.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    write_readme(readme, stats)

    print(f"Output directory: {out_dir}")
    print(f"Nodes: {len(graph.nodes)}")
    print(f"Edges: {len(graph.edges)}")
    print(f"Relations: {', '.join(relations)}")
    print(f"GraphML: {graphml}")
    print(f"HTML Viewer: {html_viewer}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
