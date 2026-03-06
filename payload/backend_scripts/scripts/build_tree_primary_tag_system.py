#!/usr/bin/env python3
"""
Build tree-primary tag architecture sheets in the master vault workbook.

This script creates/refreshes:
- TAG_ENUMS
- TAG_REGISTRY_PRIMARY
- TAG_FOLDER_PROFILES
- TAG_ASSIGNMENTS
- IMG_REGISTRY
- IMG_USAGE_MAP
- TREE_NODES_MASTER
- AXIOM_EVIDENCE_MAP
- AXIOM_CROSSREF_MAP
- AXIOM_FORMALIZATION_188
- NOTE_MASTERS
- YAML_SYNTH_QUEUE
- HEART_INDEX
- HEART_GOD_LAYER
- HEART_PHYSICS_LAYER
- HEART_CROSS_DOMAIN_LAYER
- HEART_AI_LAYER
- HEART_SYSTEM_ENGINE_LAYER
- TAG_AI_PROMPTS
- TAG_YAML_TEMPLATE
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from textwrap import dedent
from uuid import uuid4

from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.workbook.defined_name import DefinedName


HEADER_FILL = PatternFill(start_color="1F2A44", end_color="1F2A44", fill_type="solid")
HEADER_FONT = Font(color="FFFFFF", bold=True)


def ensure_sheet(wb, name: str):
    if name in wb.sheetnames:
        idx = wb.sheetnames.index(name)
        del wb[name]
        return wb.create_sheet(name, idx)
    return wb.create_sheet(name)


def style_header(ws, row: int = 1):
    for cell in ws[row]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def autosize(ws, min_width: int = 12, max_width: int = 60):
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        width = max((len(str(c.value)) if c.value is not None else 0) for c in col) + 2
        ws.column_dimensions[col_letter].width = min(max(width, min_width), max_width)


def upsert_named_range(wb, name: str, ref: str):
    # Remove existing defined name with same id.
    try:
        if name in wb.defined_names:
            del wb.defined_names[name]
    except Exception:
        pass

    dn = DefinedName(name=name, attr_text=ref)
    try:
        wb.defined_names.add(dn)
    except Exception:
        # Compatibility fallback for older openpyxl releases.
        wb.defined_names.append(dn)


def add_list_validation(ws, col: int, start_row: int, end_row: int, formula: str):
    dv = DataValidation(type="list", formula1=formula, allow_blank=True)
    ws.add_data_validation(dv)
    col_letter = get_column_letter(col)
    dv.add(f"{col_letter}{start_row}:{col_letter}{end_row}")


def build_enums_sheet(wb):
    ws = ensure_sheet(wb, "TAG_ENUMS")
    ws.append(["FIELD", "VALUE", "CODE", "DESCRIPTION", "ACTIVE"])

    enums = {
        "tag_family": [
            ("pillar", "PIL", "Top-level domain tag family"),
            ("corpus", "COR", "Corpus routing tags"),
            ("node", "NOD", "Q-level and branch tags"),
            ("mode", "MOD", "Deviation mode tags"),
            ("death_condition", "DCT", "Death-condition tags"),
            ("boundary_condition", "BCT", "Boundary-condition tags"),
            ("gsh", "GSH", "God-shaped-hole tags"),
            ("theory", "THY", "Published-theory tags"),
            ("simulation", "SIM", "Simulation tags"),
            ("governance", "GOV", "Tag lifecycle governance"),
            ("metadata_module", "MDM", "On-demand metadata bundles"),
        ],
        "tag_scope": [
            ("global", "GLB", "Applies across all corpora"),
            ("corpus", "CRP", "Applies to one corpus"),
            ("folder", "FLD", "Applies to one folder profile"),
            ("node", "NOD", "Applies to one tree node"),
            ("note", "NTE", "Applies to one note"),
        ],
        "governance_action": [
            ("approved", "APR", "Allowed and persistent"),
            ("pending", "PND", "Waiting for review"),
            ("rejected", "REJ", "Rejected this cycle"),
            ("ignore_forever", "IGN", "Never suggest again"),
            ("deprecated", "DEP", "Legacy tag retained for history"),
        ],
        "yes_no": [("yes", "Y", "Enabled/true"), ("no", "N", "Disabled/false")],
        "question_type": [
            ("QT1", "QT1", "What must be true?"),
            ("QT2", "QT2", "What is X?"),
            ("QT3", "QT3", "What follows if true?"),
            ("QT4", "QT4", "What fails if false?"),
        ],
        "mode": [
            ("M1", "M1", "Prime deviation"),
            ("M2", "M2", "Pre-activation"),
            ("M3", "M3", "Mirror/deception"),
            ("M4", "M4", "Grace attenuation"),
        ],
        "death_condition": [
            ("DC-SR", "DCSR", "Self-refutation"),
            ("DC-IR", "DCIR", "Infinite regress"),
            ("DC-EC", "DCEC", "Empirical contradiction"),
            ("DC-LI", "DCLI", "Logical incoherence"),
            ("ET", "ET", "Explanatory terminal"),
        ],
        "boundary_condition": [(f"BC{i}", f"BC{i}", f"Boundary condition {i}") for i in range(1, 9)],
        "corpus": [
            ("AI", "AI", "00_AI"),
            ("SYSTEM", "SYS", "00_SYSTEM"),
            ("ENGINE_ROOM", "ENG", "00_SYSTEM/00_ENGINE"),
            ("AXIOMS", "AX", "00_AXIOMS"),
            ("INTRO", "INT", "00_INTRO_TO_THEOPHYSICS"),
            ("THREE_TRUTHS", "TT", "[5.5] THREE TRUTHS"),
            ("LOGOS_V3", "LOG", "[6.6] LOGOS_V3"),
            ("GREAT_CORRECTION", "GC", "[8.2] The_Great_Correction"),
        ],
        "metadata_module": [
            ("AXIOMS", "AX", "Axiom and chain metadata"),
            ("TAGS", "TAG", "Tag governance and control"),
            ("IMAGES", "IMG", "Image/media metadata"),
            ("PHILOSOPHY", "PHI", "Philosophy/worldview metadata"),
            ("LOGOS_PAPERS", "LOG", "Logos paper metadata"),
            ("COHERENCE", "COH", "Coherence and scoring metadata"),
            ("MATH", "MTH", "Math translation metadata"),
            ("PUBLICATION", "PUB", "Publishing and RSS metadata"),
        ],
        "assignment_decision": [
            ("approved", "APR", "Tag attached and accepted"),
            ("pending", "PND", "Awaiting review"),
            ("rejected", "REJ", "Rejected this item"),
            ("ignore_forever", "IGN", "Never suggest this tag again"),
        ],
        "source_type": [
            ("manual", "MAN", "Human-added"),
            ("ai_suggested", "AIS", "AI suggestion"),
            ("rule_engine", "RUL", "Rule-based suggestion"),
            ("imported", "IMP", "Imported from legacy source"),
        ],
        "image_type": [
            ("diagram", "DIA", "Conceptual or structural diagram"),
            ("chart", "CHT", "Quantitative chart"),
            ("equation_visual", "EQV", "Equation-centric visual"),
            ("concept_map", "MAP", "Concept relationship map"),
            ("timeline", "TML", "Chronological sequence visual"),
            ("process_flow", "FLW", "Workflow or process flow"),
            ("table_visual", "TBL", "Table rendered as image"),
            ("render_3d", "R3D", "3D render"),
            ("photo_reference", "PHO", "Photo/reference image"),
        ],
        "image_purpose": [
            ("define", "DEF", "Define a concept"),
            ("explain", "EXP", "Explain mechanism"),
            ("compare", "CMP", "Compare alternatives"),
            ("prove", "PRV", "Support evidence/proof"),
            ("summarize", "SUM", "Summarize chapter or section"),
            ("workflow", "WRK", "Show procedure"),
            ("evidence", "EVD", "Primary evidence visual"),
            ("cover", "COV", "Cover/hero visual"),
        ],
        "audience_level": [
            ("intro", "INT", "General audience"),
            ("intermediate", "MID", "Semi-technical audience"),
            ("advanced", "ADV", "Advanced readers"),
            ("technical", "TEC", "Technical/academic"),
        ],
        "placement_role": [
            ("hero", "HER", "Top section hero image"),
            ("inline", "INL", "Inline with body content"),
            ("callout", "CAL", "Callout support visual"),
            ("appendix", "APP", "Appendix placement"),
            ("cover", "COV", "Cover image"),
            ("sidebar", "SDB", "Sidebar support"),
        ],
        "license_type": [
            ("owned", "OWN", "Owned internal asset"),
            ("cc_by", "CCB", "Creative Commons BY"),
            ("cc_by_sa", "CBS", "Creative Commons BY-SA"),
            ("public_domain", "PDM", "Public domain"),
            ("fair_use", "FAU", "Fair use"),
            ("restricted", "RST", "Restricted use"),
        ],
        "quality_status": [
            ("draft", "DRF", "Draft"),
            ("review", "REV", "Under review"),
            ("canonical", "CAN", "Canonical approved"),
            ("deprecated", "DEP", "Deprecated"),
        ],
        "contrast_status": [
            ("unknown", "UNK", "Not tested"),
            ("pass", "PAS", "Contrast checked and passed"),
            ("fail", "FIL", "Contrast check failed"),
        ],
        "layer_status": [
            ("active", "ACT", "Active working layer"),
            ("review", "REV", "Under structured review"),
            ("locked", "LCK", "Constitutional lock"),
            ("deprecated", "DEP", "Legacy layer"),
        ],
        "trinity_focus": [
            ("God", "GOD", "God the Father emphasis"),
            ("Jesus", "JES", "Jesus/Logos emphasis"),
            ("Holy_Spirit", "HSP", "Holy Spirit emphasis"),
            ("Trinity", "TRI", "Trinitarian integrated focus"),
        ],
        "law_id": [
            ("L00", "L00", "Meta law"),
            ("L01", "L01", "Law 1"),
            ("L02", "L02", "Law 2"),
            ("L03", "L03", "Law 3"),
            ("L04", "L04", "Law 4"),
            ("L05", "L05", "Law 5"),
            ("L06", "L06", "Law 6"),
            ("L07", "L07", "Law 7"),
            ("L08", "L08", "Law 8"),
            ("L09", "L09", "Law 9"),
            ("L10", "L10", "Law 10"),
        ],
        "evidence_class": [
            ("axiom", "AX", "Axiom-level evidence"),
            ("theorem", "TH", "Theorem-level evidence"),
            ("dataset", "DS", "Dataset evidence"),
            ("experiment", "EX", "Experiment evidence"),
            ("scripture", "SC", "Scripture witness"),
            ("published_theory", "PT", "Published theory witness"),
        ],
        "symmetry_type": [
            ("z2_mirror", "Z2", "Z2 mirror pair"),
            ("dual_pair", "DUP", "Dual symmetry pair"),
            ("operator_mirror", "OPM", "Operator-level symmetry"),
            ("none", "NON", "No symmetry binding"),
        ],
        "worldview_outcome": [
            ("accept", "ACC", "Survives at node"),
            ("partial", "PAR", "Partially survives"),
            ("reject", "REJ", "Eliminated at node"),
        ],
        "branch_status": [
            ("continues", "CON", "Branch continues"),
            ("terminal", "TER", "Branch terminates"),
            ("conditional", "CDN", "Branch depends on condition"),
        ],
        "proof_status": [
            ("asserted", "ASR", "Asserted"),
            ("formal", "FRM", "Formal"),
            ("empirical_supported", "EMP", "Empirically supported"),
            ("inconclusive", "INC", "Inconclusive"),
            ("falsified", "FAL", "Falsified"),
        ],
        "axiom_row_status": [
            ("unfalsified", "UNF", "Unfalsified"),
            ("contested", "CON", "Contested"),
            ("pending", "PND", "Pending"),
            ("derived", "DRV", "Derived"),
        ],
        "axiom_domain": [
            ("Primordial", "PRI", "Primordial domain"),
            ("Ontological", "ONT", "Ontological domain"),
            ("Divine", "DIV", "Divine domain"),
            ("Spiritual", "SPR", "Spiritual domain"),
            ("Human", "HUM", "Human domain"),
            ("Material", "MAT", "Material domain"),
            ("Relational", "REL", "Relational domain"),
            ("Laws", "LAW", "Laws domain"),
            ("Equations", "EQU", "Equations domain"),
            ("Eschatology", "ESC", "Eschatology domain"),
            ("Falsification", "FAL", "Falsification domain"),
        ],
        "tier": [
            ("1", "T1", "Foundation"),
            ("2", "T2", "Derived"),
            ("3", "T3", "Application"),
        ],
        "crossref_entity_type": [
            ("axiom", "AX", "Axiom record"),
            ("node", "NOD", "Tree node"),
            ("mode", "MOD", "Deviation mode"),
            ("boundary_condition", "BC", "Boundary condition"),
            ("death_condition", "DC", "Death condition"),
            ("published_theory", "PT", "Published theory"),
            ("simulation", "SIM", "Simulation/duality experiment"),
            ("worldview", "WVW", "Worldview"),
            ("scripture", "SCR", "Scripture witness"),
            ("paper", "PAP", "Paper or canonical note"),
        ],
        "crossref_relation_type": [
            ("depends_on", "DEP", "Source requires target"),
            ("enables", "ENB", "Source enables target"),
            ("binds_to_node", "BTN", "Source binds to node"),
            ("supports_node", "SUP", "Source supports node"),
            ("supported_by_theory", "SBT", "Supported by published theory"),
            ("constrains", "CON", "Constrains mode/boundary"),
            ("defends_against", "DFA", "Defends against death condition"),
            ("tested_by_simulation", "TBS", "Simulation test linkage"),
            ("eliminates_worldview", "ELW", "Eliminates worldview"),
            ("references", "REF", "General reference edge"),
        ],
    }

    row = 2
    range_map = {}
    for field, values in enums.items():
        start = row
        for value, code, desc in values:
            ws.append([field, value, code, desc, "yes"])
            row += 1
        end = row - 1
        range_map[field] = (start, end)

    style_header(ws)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:E{ws.max_row}"
    autosize(ws)

    # Named ranges over VALUE column for easy dropdowns.
    for field, (start, end) in range_map.items():
        range_name = f"enum_{field.lower()}".replace("-", "_")
        ref = f"'TAG_ENUMS'!$B${start}:$B${end}"
        upsert_named_range(wb, range_name, ref)


def build_tag_registry_sheet(wb):
    ws = ensure_sheet(wb, "TAG_REGISTRY_PRIMARY")
    headers = [
        "Tag_Record_ID",
        "Tag_Code",
        "Tag_Label",
        "Tag_Family",
        "Tag_Scope",
        "Description",
        "Question_Type",
        "Node_Binding",
        "Mode_Binding",
        "Death_Condition_Binding",
        "Boundary_Condition_Binding",
        "Corpus_Default",
        "Synonyms",
        "Active",
        "Governance_Action",
        "Created_By",
        "Created_On",
        "Notes",
    ]
    ws.append(headers)

    now = datetime.now().date().isoformat()
    seed = [
        [str(uuid4()), "AX", "Axiom evidence", "metadata_module", "global", "Axiom support chain tags", "QT3", "", "", "", "", "AXIOMS", "axiom, evidence", "yes", "approved", "system", now, ""],
        [str(uuid4()), "TAG", "Tag governance", "metadata_module", "global", "Tag governance controls", "QT1", "", "", "", "", "SYSTEM", "tag, governance", "yes", "approved", "system", now, ""],
        [str(uuid4()), "IMG", "Image metadata", "metadata_module", "global", "Image and figure tagging", "QT2", "", "", "", "", "LOGOS_V3", "image, figure", "yes", "approved", "system", now, ""],
        [str(uuid4()), "PHI", "Philosophy metadata", "metadata_module", "global", "Worldview and ontology tags", "QT2", "", "", "", "", "THREE_TRUTHS", "philosophy, worldview", "yes", "approved", "system", now, ""],
        [str(uuid4()), "LOG", "Logos paper metadata", "metadata_module", "global", "Logos-series tag bundle", "QT3", "", "", "", "", "LOGOS_V3", "logos, paper", "yes", "approved", "system", now, ""],
        [str(uuid4()), "COH", "Coherence metadata", "metadata_module", "global", "Coherence-factor and scoring tags", "QT4", "", "", "", "", "SYSTEM", "coherence, scoring", "yes", "approved", "system", now, ""],
    ]
    for row in seed:
        ws.append(row)

    style_header(ws)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:R{ws.max_row}"
    autosize(ws)

    # Data validation
    add_list_validation(ws, 4, 2, 5000, "=enum_tag_family")
    add_list_validation(ws, 5, 2, 5000, "=enum_tag_scope")
    add_list_validation(ws, 7, 2, 5000, "=enum_question_type")
    add_list_validation(ws, 9, 2, 5000, "=enum_mode")
    add_list_validation(ws, 10, 2, 5000, "=enum_death_condition")
    add_list_validation(ws, 11, 2, 5000, "=enum_boundary_condition")
    add_list_validation(ws, 12, 2, 5000, "=enum_corpus")
    add_list_validation(ws, 14, 2, 5000, "=enum_yes_no")
    add_list_validation(ws, 15, 2, 5000, "=enum_governance_action")


def build_folder_profiles_sheet(wb):
    ws = ensure_sheet(wb, "TAG_FOLDER_PROFILES")
    headers = [
        "Profile_ID",
        "Corpus",
        "Folder_Path",
        "Metadata_Module_Code",
        "Module_Name",
        "Required_Tag_Codes",
        "Optional_Tag_Codes",
        "Auto_Apply_Global_Tags",
        "Prompt_Block_ID",
        "Status",
        "Notes",
    ]
    ws.append(headers)

    rows = [
        ["FP-AI", "AI", "00_AI", "TAG", "AI routing + governance", "TAG", "COH;PUB", "yes", "PROMPT-TAG-01", "active", ""],
        ["FP-SYS", "SYSTEM", "00_SYSTEM", "COH", "System + coherence", "COH;TAG", "PHI;PUB", "yes", "PROMPT-TAG-01", "active", ""],
        ["FP-ENG", "ENGINE_ROOM", "00_SYSTEM/00_ENGINE", "TAG", "Engine metadata", "TAG;AX", "COH", "yes", "PROMPT-TAG-02", "active", ""],
        ["FP-AX", "AXIOMS", "00_AXIOMS", "AX", "Axiom node/evidence", "AX;TAG", "PHI;MTH", "yes", "PROMPT-TAG-03", "active", ""],
        ["FP-TT", "THREE_TRUTHS", "04_THEOPYHISCS/[5.5] THREE TRUTHS", "PHI", "Three Truths worldview", "PHI;TAG", "AX;COH", "yes", "PROMPT-TAG-03", "active", ""],
        ["FP-LOG", "LOGOS_V3", "04_THEOPYHISCS/[6.6] LOGOS_V3", "LOG", "Logos paper stack", "LOG;TAG", "IMG;MTH;COH", "yes", "PROMPT-TAG-04", "active", ""],
        ["FP-GC", "GREAT_CORRECTION", "04_THEOPYHISCS/[8.2] The_Great_Correction", "PHI", "Great Correction metadata", "PHI;TAG", "COH;PUB", "yes", "PROMPT-TAG-04", "active", ""],
    ]
    for r in rows:
        ws.append(r)

    style_header(ws)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:K{ws.max_row}"
    autosize(ws)

    add_list_validation(ws, 2, 2, 2000, "=enum_corpus")
    add_list_validation(ws, 4, 2, 2000, "=enum_metadata_module")
    add_list_validation(ws, 8, 2, 2000, "=enum_yes_no")


def build_assignments_sheet(wb):
    ws = ensure_sheet(wb, "TAG_ASSIGNMENTS")
    headers = [
        "Assignment_ID",
        "Target_Type",
        "Target_ID_or_Path",
        "Tag_Code",
        "Tag_Label",
        "Node_ID",
        "Source_Type",
        "Confidence",
        "Decision",
        "Reviewer",
        "Updated_On",
        "Comments",
    ]
    ws.append(headers)

    # One starter row to show shape.
    ws.append(
        [str(uuid4()), "note", "04_THEOPYHISCS/[6.6] LOGOS_V3/THEOPHYSICS_MASTER_PAPER.md", "LOG", "Logos paper metadata", "Q2-C", "manual", 1.0, "approved", "David Lowe", datetime.now().date().isoformat(), ""]
    )

    style_header(ws)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:L{ws.max_row}"
    autosize(ws)

    add_list_validation(ws, 7, 2, 10000, "=enum_source_type")
    add_list_validation(ws, 9, 2, 10000, "=enum_assignment_decision")


def build_image_registry_sheet(wb):
    ws = ensure_sheet(wb, "IMG_REGISTRY")
    headers = [
        "Image_ID",
        "Title",
        "Aliases",
        "Short_Codes",
        "Image_Type",
        "Purpose",
        "Audience_Level",
        "Definition_1Line",
        "Explanation_Long",
        "Keywords",
        "Search_Phrases",
        "Negative_Keywords",
        "Primary_Node",
        "Question_Type",
        "Modes",
        "Death_Conditions",
        "Boundary_Conditions",
        "God_Shaped_Hole",
        "Published_Theories",
        "Axioms_Supported",
        "Used_In_Papers",
        "Used_In_Notes",
        "Section_Placements",
        "File_Path",
        "Thumbnail_Path",
        "Alt_Text",
        "Contrast_Status",
        "Rights_License",
        "Creator",
        "Source_URL",
        "Status",
        "Reviewer",
        "Review_Date",
        "Notes",
    ]
    ws.append(headers)

    ws.append(
        [
            "IMG-P03-KC-REV-01",
            "Paper 3: Kolmogorov Complexity (Revised)",
            "Kolmogorov complexity visual; program size of reality; low-k high-k",
            "IMG;KC;P3",
            "diagram",
            "explain",
            "intermediate",
            "Contrasts low-K ordered output with high-K chaotic output.",
            "Shows that low algorithmic complexity can generate large coherent structure while high complexity can produce small chaotic outputs. The visual supports efficiency-vs-inefficiency framing in Paper 3.",
            "kolmogorov;complexity;order;chaos;program size;information theory",
            "paper 3 complexity diagram;low-k vs high-k visual;program size of reality image",
            "portrait;logo;icon;avatar",
            "Q4-A",
            "QT2",
            "M1;M2",
            "DC-LI",
            "BC2;BC4",
            "GSH-Q4",
            "PT-Kolmogorov-1965;PT-Chaitin-1975;PT-Shannon-1948",
            "A4.2;D4.1;D4.2;E4.1",
            "Paper 3 The Algorithm of Reality;THEOPHYSICS_MASTER_PAPER",
            "04_THEOPYHISCS/[6.6] LOGOS_V3/THEOPHYSICS_MASTER_PAPER.md",
            "hero;inline;complexity section",
            "assets/images/paper3_kolmogorov_complexity_revised.png",
            "assets/images/thumbnails/paper3_kolmogorov_complexity_revised_thumb.png",
            "Diagram comparing low-K ordered output and high-K chaotic output in Kolmogorov complexity framing.",
            "unknown",
            "owned",
            "David Lowe + AI collaboration",
            "",
            "review",
            "",
            datetime.now().date().isoformat(),
            "Confirm final paper list before canonical lock.",
        ]
    )

    style_header(ws)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:AH{ws.max_row}"
    autosize(ws)

    add_list_validation(ws, 5, 2, 10000, "=enum_image_type")
    add_list_validation(ws, 6, 2, 10000, "=enum_image_purpose")
    add_list_validation(ws, 7, 2, 10000, "=enum_audience_level")
    add_list_validation(ws, 14, 2, 10000, "=enum_question_type")
    add_list_validation(ws, 27, 2, 10000, "=enum_contrast_status")
    add_list_validation(ws, 28, 2, 10000, "=enum_license_type")
    add_list_validation(ws, 31, 2, 10000, "=enum_quality_status")


def build_image_usage_sheet(wb):
    ws = ensure_sheet(wb, "IMG_USAGE_MAP")
    headers = [
        "Usage_ID",
        "Image_ID",
        "Corpus",
        "Paper_or_Note",
        "Section",
        "Placement_Role",
        "Caption_Short",
        "Caption_Long",
        "Priority",
        "Visible_By_Default",
        "RSS_Eligible",
        "Last_Checked",
        "Notes",
    ]
    ws.append(headers)
    ws.append(
        [
            str(uuid4()),
            "IMG-P03-KC-REV-01",
            "LOGOS_V3",
            "THEOPHYSICS_MASTER_PAPER",
            "Complexity section",
            "hero",
            "Low-K creates large order; high-K creates tiny chaos.",
            "Program-size framing of reality: structured simplicity scales while chaotic inefficiency fragments.",
            1,
            "yes",
            "yes",
            datetime.now().date().isoformat(),
            "",
        ]
    )

    style_header(ws)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:M{ws.max_row}"
    autosize(ws)

    add_list_validation(ws, 3, 2, 10000, "=enum_corpus")
    add_list_validation(ws, 6, 2, 10000, "=enum_placement_role")
    add_list_validation(ws, 10, 2, 10000, "=enum_yes_no")
    add_list_validation(ws, 11, 2, 10000, "=enum_yes_no")


def build_tree_nodes_master_sheet(wb):
    ws = ensure_sheet(wb, "TREE_NODES_MASTER")
    headers = [
        "Node_ID",
        "Level",
        "Branch",
        "AA_Code",
        "Topic",
        "Keywords",
        "Node_Title",
        "Heart_Question",
        "Question_Type",
        "Branch_Status",
        "Death_Test",
        "Boundary_Conditions",
        "Modes",
        "God_Shaped_Hole",
        "Master_Equation_Components",
        "Laws",
        "Symmetry_Type",
        "Published_Theories",
        "Worldviews_Accept",
        "Worldviews_Partial",
        "Worldviews_Reject",
        "Supporting_Axioms",
        "Status",
        "Reviewer",
        "Review_Date",
        "Notes",
    ]
    ws.append(headers)

    now = datetime.now().date().isoformat()
    rows = [
        [
            "Q1-B",
            "Q1",
            "B",
            "AA-AI",
            "AI Governance",
            "ai, prompts, yaml, guardrails",
            "AI metadata governance node",
            "How do we constrain AI actions in the vault?",
            "QT4",
            "continues",
            "DC-SR;DC-LI",
            "BC1;BC3",
            "M1;M3",
            "GSH-Q1",
            "K;C",
            "L04;L05",
            "none",
            "PT-Turing-1936;PT-Wheeler-1990",
            2,
            3,
            10,
            "A1.1;A1.3",
            "active",
            "David Lowe",
            now,
            "",
        ],
        [
            "Q2-A",
            "Q2",
            "A",
            "AA-SYS",
            "System Runtime",
            "engine, validation, launchers, quality gates",
            "System and engine execution node",
            "How is framework execution kept reliable?",
            "QT1",
            "continues",
            "DC-EC;DC-LI",
            "BC1;BC2;BC7",
            "M1;M2;M4",
            "GSH-Q2",
            "K;C;T",
            "L01;L04;L06",
            "none",
            "PT-Shannon-1948;PT-Landauer-1961",
            2,
            4,
            9,
            "A2.1;A2.2",
            "active",
            "David Lowe",
            now,
            "",
        ],
        [
            "Q3-A",
            "Q3",
            "A",
            "AA-GOD",
            "Trinity Grounding",
            "God, Jesus, Holy Spirit, grace, faith, salvation",
            "Trinitarian grounding node",
            "How is divine grounding expressed and tested?",
            "QT2",
            "continues",
            "DC-LI;ET",
            "BC1;BC4;BC6",
            "M4",
            "GSH-Q3",
            "G;F;C;R",
            "L07;L09;L10",
            "z2_mirror",
            "PT-Wheeler-1990;PT-Shannon-1948",
            2,
            9,
            6,
            "A11.1;A11.2",
            "active",
            "David Lowe",
            now,
            "",
        ],
        [
            "Q4-A",
            "Q4",
            "A",
            "AA-PHY",
            "Physics Backbone",
            "axioms, laws, modes, boundary conditions, symmetry",
            "Physics and axiom evidence node",
            "What is the formal physical backbone?",
            "QT1",
            "continues",
            "DC-SR;DC-IR;DC-EC;DC-LI",
            "BC1;BC2;BC3;BC4;BC5;BC6;BC7;BC8",
            "M1;M2;M3",
            "GSH-Q4",
            "G;M;E;S;T;K;R;Q;F;C",
            "L01;L02;L03;L04;L05;L06;L07;L08;L09;L10",
            "z2_mirror;dual_pair",
            "PT-Shannon-1948;PT-Landauer-1961;PT-Chaitin-1975",
            2,
            9,
            6,
            "A1.3;D1.1;D1.2;LN1.1;LN1.2",
            "active",
            "David Lowe",
            now,
            "",
        ],
        [
            "Q6-B",
            "Q6",
            "B",
            "AA-XDM",
            "Cross-Domain Coherence",
            "cross-domain, coherence, semantic entropy, somatic entropy",
            "Cross-domain coherence transfer node",
            "How does coherence propagate across domains?",
            "QT3",
            "continues",
            "DC-EC;DC-LI",
            "BC2;BC5",
            "M2;M3;M4",
            "GSH-Q6",
            "C;K;R",
            "L03;L06;L08",
            "dual_pair",
            "PT-Shannon-1948;PT-Landauer-1961",
            2,
            9,
            6,
            "A3.1;A3.2;D3.1",
            "active",
            "David Lowe",
            now,
            "",
        ],
    ]
    for r in rows:
        ws.append(r)

    style_header(ws)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:Z{ws.max_row}"
    autosize(ws)

    add_list_validation(ws, 9, 2, 10000, "=enum_question_type")
    add_list_validation(ws, 10, 2, 10000, "=enum_branch_status")
    add_list_validation(ws, 17, 2, 10000, "=enum_symmetry_type")
    add_list_validation(ws, 23, 2, 10000, "=enum_layer_status")


def build_axiom_evidence_map_sheet(wb):
    ws = ensure_sheet(wb, "AXIOM_EVIDENCE_MAP")
    headers = [
        "Record_ID",
        "Axiom_ID",
        "AA_Code",
        "Topic",
        "Keywords",
        "Supporting_Node",
        "Evidence_Class",
        "Evidence_Weight_1_5",
        "Proof_Status",
        "Death_Conditions_Defended",
        "Modes_Constrained",
        "Published_Theories",
        "Scripture_Witness",
        "Status",
        "Reviewer",
        "Review_Date",
        "Notes",
    ]
    ws.append(headers)
    now = datetime.now().date().isoformat()

    rows = [
        [
            str(uuid4()),
            "A1.3",
            "AA-PHY",
            "Information Primacy",
            "information, ontology, distinction, bit",
            "Q4-A",
            "axiom",
            5,
            "formal",
            "DC-SR;DC-LI",
            "M1;M2",
            "PT-Shannon-1948;PT-Wheeler-1990",
            "",
            "active",
            "David Lowe",
            now,
            "",
        ],
        [
            str(uuid4()),
            "D1.1",
            "AA-PHY",
            "Information Definition",
            "definition, information, formalism",
            "Q4-A",
            "theorem",
            4,
            "formal",
            "DC-LI",
            "M2",
            "PT-Shannon-1948",
            "",
            "active",
            "David Lowe",
            now,
            "",
        ],
        [
            str(uuid4()),
            "A11.2",
            "AA-GOD",
            "Coherence Morality Identity",
            "morality, coherence, identity, trinity",
            "Q3-A",
            "axiom",
            4,
            "asserted",
            "DC-LI;ET",
            "M4",
            "PT-Wheeler-1990",
            "RM_5_1;EPH_2_8",
            "active",
            "David Lowe",
            now,
            "",
        ],
        [
            str(uuid4()),
            "A3.2",
            "AA-XDM",
            "Coherence Measure",
            "coherence, measure, domain transfer",
            "Q6-B",
            "dataset",
            4,
            "empirical_supported",
            "DC-EC",
            "M2;M3",
            "PT-Landauer-1961",
            "",
            "active",
            "David Lowe",
            now,
            "",
        ],
    ]
    for r in rows:
        ws.append(r)

    style_header(ws)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:Q{ws.max_row}"
    autosize(ws)

    add_list_validation(ws, 7, 2, 10000, "=enum_evidence_class")
    add_list_validation(ws, 9, 2, 10000, "=enum_proof_status")
    add_list_validation(ws, 14, 2, 10000, "=enum_layer_status")


def build_axiom_crossref_sheet(wb):
    ws = ensure_sheet(wb, "AXIOM_CROSSREF_MAP")
    headers = [
        "CrossRef_ID",
        "Source_Type",
        "Source_ID",
        "Relation_Type",
        "Target_Type",
        "Target_ID",
        "Target_Label",
        "Weight_1_5",
        "Evidence_Class",
        "Status",
        "Origin",
        "Reviewer",
        "Updated_On",
        "Notes",
    ]
    ws.append(headers)
    ws.append(
        [
            str(uuid4()),
            "axiom",
            "AX-003",
            "binds_to_node",
            "node",
            "Q2-C",
            "Information Primacy",
            5,
            "axiom",
            "active",
            "manual",
            "David Lowe",
            datetime.now().date().isoformat(),
            "Starter cross-reference row. Auto rows generated by pipeline.",
        ]
    )

    style_header(ws)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:N{ws.max_row}"
    autosize(ws)

    add_list_validation(ws, 2, 2, 50000, "=enum_crossref_entity_type")
    add_list_validation(ws, 4, 2, 50000, "=enum_crossref_relation_type")
    add_list_validation(ws, 5, 2, 50000, "=enum_crossref_entity_type")
    add_list_validation(ws, 9, 2, 50000, "=enum_evidence_class")
    add_list_validation(ws, 10, 2, 50000, "=enum_layer_status")
    add_list_validation(ws, 11, 2, 50000, "=enum_source_type")


def build_axiom_formalization_sheet(wb):
    ws = ensure_sheet(wb, "AXIOM_FORMALIZATION_188")
    headers = [
        "axiom_id",
        "title",
        "claim",
        "tree_level",
        "tree_branch",
        "question_type",
        "aa_code",
        "topic",
        "keywords",
        "domain",
        "tier",
        "depends_on",
        "enables",
        "published_theory",
        "theory_question_left_open",
        "boundary_condition",
        "four_mode_relevance",
        "defeat_conditions",
        "status",
        "formal_expression",
        "duality_experiment",
        "worldviews_eliminated",
        "propagation_test",
        "honest_blank",
    ]
    ws.append(headers)

    seed_rows = [
        [
            "AX-001",
            "Existence",
            "Something exists rather than nothing.",
            "Q0",
            "Q0-B",
            "QT1",
            "AA-PHY",
            "Existence floor",
            "existence,ontology,foundation",
            "Primordial",
            "1",
            "—",
            "AX-002,AX-003",
            "—",
            "If nothing exists, who states the claim?",
            "—",
            "—",
            "Attempt coherent denial of existence.",
            "unfalsified",
            "∃x",
            "—",
            "Nihilism (strict form)",
            "YES - required for all downstream levels",
            "Minimal but non-negotiable axiom.",
        ],
        [
            "AX-003",
            "Information Primacy",
            "Distinguishability is information; information is ontologically primitive.",
            "Q2",
            "Q2-C",
            "QT2",
            "AA-PHY",
            "Information substrate",
            "information,distinction,substrate",
            "Primordial",
            "1",
            "AX-001,AX-002",
            "AX-004,AX-008",
            "Shannon 1948; Wheeler 1990; Landauer 1961",
            "Where does the bit come from? What instantiates information?",
            "—",
            "M2 pre-activation context",
            "Show non-informational distinguishability.",
            "unfalsified",
            "I ≡ Distinguishability",
            "—",
            "Strict materialism; eliminativism",
            "YES - propagates through order, grounding, and observer levels",
            "Structural realism steelman is strongest challenge.",
        ],
        [
            "AX-017",
            "Moral Realism",
            "Moral distinctions are objective coherence distinctions.",
            "Q10",
            "Q10-A",
            "QT4",
            "AA-GOD",
            "Moral sign structure",
            "morality,coherence,sign",
            "Relational",
            "2",
            "AX-003,AX-011",
            "AX-123,AX-124,AX-128",
            "Tononi IIT; Friston FEP",
            "Why normativity and not just optimization?",
            "BC5;BC8",
            "M1;M3;M4",
            "Demonstrate durable coherence without objective sign constraints.",
            "pending",
            "σ ∈ {+1,-1}",
            "DP-08",
            "Moral nihilism, strict relativism",
            "YES - if BC5 + BC8 hold",
            "Needs full cross-domain empirical bridge writeup.",
        ],
    ]
    for row in seed_rows:
        ws.append(row)

    style_header(ws)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:X{ws.max_row}"
    autosize(ws)
    ws.column_dimensions["C"].width = 60
    ws.column_dimensions["O"].width = 60
    ws.column_dimensions["R"].width = 50
    ws.column_dimensions["W"].width = 48
    ws.column_dimensions["X"].width = 48
    for col in ("C", "O", "R", "W", "X"):
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=ws[col + "1"].column, max_col=ws[col + "1"].column):
            row[0].alignment = Alignment(vertical="top", wrap_text=True)

    add_list_validation(ws, 6, 2, 20000, "=enum_question_type")
    add_list_validation(ws, 10, 2, 20000, "=enum_axiom_domain")
    add_list_validation(ws, 11, 2, 20000, "=enum_tier")
    add_list_validation(ws, 19, 2, 20000, "=enum_axiom_row_status")


def build_note_masters_sheet(wb):
    ws = ensure_sheet(wb, "NOTE_MASTERS")
    headers = [
        "Master_ID",
        "Selected",
        "Master_Title",
        "Master_Path",
        "Scope",
        "Target_Layer",
        "Default_AA_Code",
        "Default_Topic",
        "Default_Keywords",
        "Status",
        "Notes",
    ]
    ws.append(headers)
    rows = [
        [
            "NM-001",
            "yes",
            "Theophysics Dashboards Index",
            r"O:\999_IGNORE\Obsidian Data Analytics\_Index.md",
            "analytics-hub",
            "LAYER-SYSENG",
            "AA-SYS",
            "Dashboard routing",
            "dashboard,index,analytics,system",
            "active",
            "",
        ],
        [
            "NM-002",
            "yes",
            "Equation Index",
            r"O:\999_IGNORE\Obsidian Data Analytics\Equation_Index.md",
            "equations-hub",
            "LAYER-PHY",
            "AA-PHY",
            "Equation governance",
            "equation,index,law,symbolic form",
            "active",
            "",
        ],
        [
            "NM-003",
            "yes",
            "Law Index",
            r"O:\999_IGNORE\Obsidian Data Analytics\Data_Analytics\Theophysics_Assets\Law_Index.md",
            "laws-hub",
            "LAYER-PHY",
            "AA-PHY",
            "Law mapping",
            "laws,index,trinity,atoms",
            "active",
            "",
        ],
        [
            "NM-004",
            "yes",
            "Concept Hubs Index",
            r"O:\999_IGNORE\Obsidian Data Analytics\Concept_Hubs_Index.md",
            "concept-hub",
            "LAYER-XDOM",
            "AA-XDM",
            "Concept map",
            "concepts,hubs,coherence,cross-domain",
            "active",
            "",
        ],
        [
            "NM-005",
            "no",
            "Master Index (placeholder)",
            r"O:\999_IGNORE\Obsidian Data Analytics\Master_Index.md",
            "placeholder",
            "LAYER-SYSENG",
            "AA-SYS",
            "Master index",
            "master,index",
            "review",
            "Currently empty; fill before selecting.",
        ],
    ]
    for r in rows:
        ws.append(r)

    style_header(ws)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:K{ws.max_row}"
    autosize(ws)

    add_list_validation(ws, 2, 2, 5000, "=enum_yes_no")
    add_list_validation(ws, 10, 2, 5000, "=enum_layer_status")


def build_yaml_synth_queue_sheet(wb):
    ws = ensure_sheet(wb, "YAML_SYNTH_QUEUE")
    headers = [
        "Queue_ID",
        "Master_ID",
        "Selected",
        "Source_Master",
        "Linked_Note",
        "Resolved_Path",
        "AA_Code",
        "Topic",
        "Keywords",
        "Suggested_Node",
        "Question_Type",
        "Suggested_Layer",
        "YAML_Template",
        "YAML_Snippet",
        "Status",
        "Notes",
    ]
    ws.append(headers)
    ws.append(
        [
            str(uuid4()),
            "NM-001",
            "yes",
            "_Index.md",
            "TM SUBSTACK/04_ANALYTICS/Validation",
            "",
            "AA-SYS",
            "Validation dashboard",
            "validation,dashboard,analytics",
            "Q2-A",
            "QT1",
            "LAYER-SYSENG",
            "theophysics_unified_yaml@1.0.0",
            "title: \"Validation Dashboard\"",
            "pending",
            "Auto-generated starter row",
        ]
    )

    style_header(ws)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:P{ws.max_row}"
    autosize(ws)
    ws.column_dimensions["N"].width = 80
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=14, max_col=14):
        row[0].alignment = Alignment(vertical="top", wrap_text=True)

    add_list_validation(ws, 3, 2, 20000, "=enum_yes_no")
    add_list_validation(ws, 11, 2, 20000, "=enum_question_type")
    add_list_validation(ws, 15, 2, 20000, "=enum_layer_status")


def _build_heart_detail_sheet(wb, sheet_name: str, seed_row: list[str]):
    ws = ensure_sheet(wb, sheet_name)
    headers = [
        "Layer_ID",
        "Layer_Name",
        "AA_Code",
        "Topic",
        "Keywords",
        "Heart_Question",
        "Core_Definition",
        "Primary_Node",
        "Branch_ID",
        "Question_Type",
        "Modes",
        "Boundary_Conditions",
        "Death_Conditions",
        "God_Shaped_Hole",
        "Master_Equation_Components",
        "Laws",
        "Symmetry_Pairs",
        "Key_Theories",
        "Evidence_Classes",
        "Core_Keywords",
        "Governance_Questions",
        "Related_Folders",
        "Canonical_Papers",
        "Scripture_Refs",
        "Trinity_Focus",
        "Status",
        "Reviewer",
        "Review_Date",
        "Notes",
    ]
    ws.append(headers)
    ws.append(seed_row)
    style_header(ws)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:AC{ws.max_row}"
    autosize(ws)

    add_list_validation(ws, 10, 2, 5000, "=enum_question_type")
    add_list_validation(ws, 25, 2, 5000, "=enum_trinity_focus")
    add_list_validation(ws, 26, 2, 5000, "=enum_layer_status")


def build_heart_index_sheet(wb):
    ws = ensure_sheet(wb, "HEART_INDEX")
    headers = [
        "Layer_ID",
        "Layer_Name",
        "Primary_Purpose",
        "Sheet_Name",
        "Core_Folder",
        "Primary_Metadata_Module",
        "Status",
        "Last_Updated",
        "Notes",
    ]
    ws.append(headers)
    now = datetime.now().date().isoformat()
    rows = [
        ["LAYER-GOD", "God Layer", "Trinity + scripture + grace/faith/salvation mappings", "HEART_GOD_LAYER", "04_THEOPYHISCS", "PHILOSOPHY", "active", now, ""],
        ["LAYER-PHY", "Physics Layer", "Axioms/evidence/theory/modes/BC/laws/symmetry", "HEART_PHYSICS_LAYER", "00_AXIOMS", "AXIOMS", "active", now, ""],
        ["LAYER-XDOM", "Cross-Domain Layer", "Coherence transfer across domains and applications", "HEART_CROSS_DOMAIN_LAYER", "04_THEOPYHISCS/Cross-Domain Coherence Project", "COHERENCE", "active", now, ""],
        ["LAYER-AI", "AI Layer", "00_AI operating prompts, governance, and workflows", "HEART_AI_LAYER", "00_AI", "TAGS", "active", now, ""],
        ["LAYER-SYSENG", "System+Engine Layer", "00_SYSTEM + engine room execution and controls", "HEART_SYSTEM_ENGINE_LAYER", "00_SYSTEM/00_ENGINE", "TAGS", "active", now, ""],
    ]
    for r in rows:
        ws.append(r)

    style_header(ws)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:I{ws.max_row}"
    autosize(ws)
    add_list_validation(ws, 7, 2, 2000, "=enum_layer_status")


def build_heart_god_sheet(wb):
    seed = [
        "LAYER-GOD",
        "God Layer",
        "AA-GOD",
        "Trinity Grounding",
        "God, Jesus, Holy Spirit, Trinity, grace, faith, salvation",
        "How are God, Jesus, Holy Spirit, and Trinity expressed as the grounding of the framework?",
        "Defines trinitarian core, scripture anchor set, and mathematical meanings of grace/faith/salvation.",
        "Q3-A",
        "A",
        "QT2",
        "M4",
        "BC1;BC4;BC6",
        "DC-LI;ET",
        "GSH-Q3",
        "G;F;C;R",
        "L07;L09;L10",
        "z2_mirror",
        "PT-Wheeler-1990;PT-Shannon-1948",
        "scripture;axiom;published_theory",
        "God;Jesus;Holy Spirit;Trinity;grace;faith;salvation;logos",
        "Are scripture links explicit? Are grace/faith/salvation mathematically bound?",
        "04_THEOPYHISCS/[6.6] LOGOS_V3;04_THEOPYHISCS/[5.5] THREE TRUTHS",
        "THEOPHYSICS_MASTER_PAPER;00_DE REVOLUTIONIBUS VERITATIS",
        "JN_1_1;MT_28_19;EPH_2_8;RM_5_1",
        "Trinity",
        "active",
        "David Lowe",
        datetime.now().date().isoformat(),
        "Lock scripture map after canonical review.",
    ]
    _build_heart_detail_sheet(wb, "HEART_GOD_LAYER", seed)


def build_heart_physics_sheet(wb):
    seed = [
        "LAYER-PHY",
        "Physics Layer",
        "AA-PHY",
        "Physics Backbone",
        "axioms, evidence, laws, modes, boundary conditions, symmetry",
        "What is the formal physical backbone: axioms, evidence, laws, BCs, modes, and symmetries?",
        "Tracks theoretical grounding, evidence classes, master-equation law mapping, and symmetry usage.",
        "Q4-A",
        "A",
        "QT1",
        "M1;M2;M3",
        "BC1;BC2;BC3;BC4;BC5;BC6;BC7;BC8",
        "DC-SR;DC-IR;DC-EC;DC-LI",
        "GSH-Q4",
        "G;M;E;S;T;K;R;Q;F;C",
        "L01;L02;L03;L04;L05;L06;L07;L08;L09;L10",
        "z2_mirror;dual_pair",
        "PT-Shannon-1948;PT-Landauer-1961;PT-Chaitin-1975",
        "axiom;theorem;dataset;experiment;published_theory",
        "axiom chain;evidence;boundary conditions;modes;symmetry;master equation",
        "Do all claims map to nodes? Are BC and DC tests complete? Are symmetry pairs registered?",
        "00_AXIOMS;MASTER_EQUATION;04_THEOPYHISCS/[6.6] LOGOS_V3",
        "AXIOMS_THEOPHYSICS_COMPLETE;THEOPHYSICS_MASTER_PAPER",
        "",
        "Trinity",
        "active",
        "David Lowe",
        datetime.now().date().isoformat(),
        "Physics layer is tree-node-primary; axioms are evidence.",
    ]
    _build_heart_detail_sheet(wb, "HEART_PHYSICS_LAYER", seed)


def build_heart_cross_domain_sheet(wb):
    seed = [
        "LAYER-XDOM",
        "Cross-Domain Layer",
        "AA-XDM",
        "Cross-Domain Coherence",
        "cross-domain coherence, semantic entropy, somatic entropy, transfer",
        "How does coherence propagate across psychology, education, economy, theology, and governance?",
        "Captures domain transfer logic, coherence factor use, and cross-domain validation loops.",
        "Q6-B",
        "B",
        "QT3",
        "M2;M3;M4",
        "BC2;BC5",
        "DC-EC;DC-LI",
        "GSH-Q6",
        "C;K;R",
        "L03;L06;L08",
        "dual_pair",
        "PT-Shannon-1948;PT-Landauer-1961",
        "dataset;experiment;published_theory;axiom",
        "cross-domain coherence;semantic entropy;somatic entropy;social coherence;trans-domain invariants",
        "Is coherence metric comparable across domains? Are transfer assumptions explicit and testable?",
        "04_THEOPYHISCS/Cross-Domain Coherence Project",
        "MASTER_COHERENCE_ANALYSIS;00_CROSS_DOMAIN_ROADMAP",
        "",
        "Trinity",
        "active",
        "David Lowe",
        datetime.now().date().isoformat(),
        "Seeded from Cross-Domain Coherence Project corpus.",
    ]
    _build_heart_detail_sheet(wb, "HEART_CROSS_DOMAIN_LAYER", seed)


def build_heart_ai_sheet(wb):
    seed = [
        "LAYER-AI",
        "00_AI Layer",
        "AA-AI",
        "AI Governance",
        "ai prompts, yaml schema, tagging, trust hierarchy",
        "How do AI agents classify, govern, and safely transform the vault?",
        "Defines AI prompt standards, metadata policies, and workflow guardrails.",
        "Q1-B",
        "B",
        "QT4",
        "M1;M3",
        "BC1;BC3",
        "DC-SR;DC-LI",
        "GSH-Q1",
        "K;C",
        "L04;L05",
        "none",
        "PT-Turing-1936;PT-Wheeler-1990",
        "axiom;published_theory;experiment",
        "yaml schema;tagging;ai instructions;governance;workflow;trust hierarchy",
        "Are prompts constrained? Is canonical content protected? Are ignored tags persisted?",
        "00_AI",
        "00_AI_BOOTSTRAP;03_YAML_SCHEMA;04_TAGGING_SYSTEM",
        "",
        "Trinity",
        "active",
        "David Lowe",
        datetime.now().date().isoformat(),
        "AI layer must never rewrite canonical axioms without explicit approval.",
    ]
    _build_heart_detail_sheet(wb, "HEART_AI_LAYER", seed)


def build_heart_system_engine_sheet(wb):
    seed = [
        "LAYER-SYSENG",
        "00_SYSTEM + Engine Room Layer",
        "AA-SYS",
        "System Runtime",
        "engine room, runtime, validation, launchers, quality gates",
        "How is the system executed, validated, and governed in production?",
        "Maps engine modules, launchers, validators, and operational governance.",
        "Q2-A",
        "A",
        "QT1",
        "M1;M2;M4",
        "BC1;BC2;BC7",
        "DC-EC;DC-LI",
        "GSH-Q2",
        "K;C;T",
        "L01;L04;L06",
        "none",
        "PT-Shannon-1948;PT-Landauer-1961",
        "dataset;experiment;published_theory",
        "engine room;vault health;analytics;link integrity;yaml lint;runtime",
        "Do launchers, validators, and dashboards agree? Are quality gates blocking bad writes?",
        "00_SYSTEM;00_SYSTEM/00_ENGINE",
        "UNIFIED_SCORING_ARCHITECTURE;ENGINE_HEALTH_CHECK_2026-02-17",
        "",
        "Trinity",
        "active",
        "David Lowe",
        datetime.now().date().isoformat(),
        "System layer binds governance to runtime behavior.",
    ]
    _build_heart_detail_sheet(wb, "HEART_SYSTEM_ENGINE_LAYER", seed)


def build_prompts_sheet(wb):
    ws = ensure_sheet(wb, "TAG_AI_PROMPTS")
    headers = ["Prompt_ID", "Prompt_Name", "Use_Case", "Prompt_Text"]
    ws.append(headers)

    prompt_1 = dedent(
        """
        You are the Theophysics Tag Classifier (tree-primary).
        Task:
        1) classify this note with short tag codes (2-3 chars where possible),
        2) bind tags to node IDs (Qx-branch) when available,
        3) avoid noisy/redundant tags,
        4) respect ignore_forever tags.

        Return YAML ONLY:
        suggested_tags:
          required: [CODE1, CODE2]
          optional: [CODE3]
        node_binding:
          primary_node: Qx-A
          question_type: QT1
          modes: [M1]
          death_conditions: [DC-SR]
          boundary_conditions: [BC1]
        governance:
          ignore_forever_hits: []
          duplicates_detected: []
          confidence: 0.0-1.0
        """
    ).strip()

    prompt_2 = dedent(
        """
        You are the Theophysics Tag Curator.
        Propose up to 5 new tags max.
        For each new tag return:
        - Tag_Code (2-3 letters preferred)
        - Tag_Label
        - Tag_Family
        - Tag_Scope
        - Why it is not redundant with existing tags
        Reject tags already in ignore_forever.
        """
    ).strip()

    prompt_3 = dedent(
        """
        You are the Theophysics Metadata Filler.
        Fill folder-specific metadata module fields on demand.
        Priority modules: AXIOMS, TAGS, IMAGES, PHILOSOPHY, LOGOS_PAPERS, COHERENCE.
        Keep canonical equations and axioms unchanged.
        Return YAML ONLY.
        """
    ).strip()

    prompt_img_1 = dedent(
        """
        You are the Theophysics Image Classifier.
        Classify the image for IMG_REGISTRY with:
        - image_type, purpose, audience_level
        - aliases, keywords, search_phrases, negative_keywords
        - definition_1line, explanation_long
        - node/mode/death-condition binding
        - papers/notes usage candidates
        Return YAML only.
        """
    ).strip()

    prompt_img_2 = dedent(
        """
        You are the Theophysics Image Retrieval Assistant.
        Given a query, return top matching Image_ID rows from IMG_REGISTRY with reason scores.
        Respect negative_keywords and ignore deprecated assets.
        Return YAML only.
        """
    ).strip()

    prompt_core_1 = dedent(
        """
        You are the Tree-Primary Node Mapper.
        For the provided content, return:
        - Node_ID (Qx-Branch)
        - AA_Code (short simple label)
        - Topic (plain-language)
        - Keywords (compact comma list)
        - Question_Type, Modes, BCs, DCs
        - Published theories and supporting axioms
        Return YAML only.
        """
    ).strip()

    prompt_core_2 = dedent(
        """
        You are the Axiom Evidence Mapper.
        For each axiom, map it to:
        - Supporting_Node
        - AA_Code
        - Topic
        - Keywords
        - Evidence_Class and Evidence_Weight (1-5)
        - Proof_Status
        Return YAML only.
        """
    ).strip()

    prompt_ax_1 = dedent(
        """
        You are the Tree-Primary Axiom Formalizer.
        Primary unit is TREE NODE, not standalone axiom.
        For each axiom row:
        1) bind to earliest relevant Q-level + branch,
        2) fill AA_Code, Topic, Keywords in simple language,
        3) map published theories + unresolved question left open,
        4) add defeat condition and propagation test honesty.
        Keep output concise, evidential, and non-poetic.
        Return tabular rows matching AXIOM_FORMALIZATION_188 columns.
        """
    ).strip()

    rows = [
        ["PROMPT-TAG-01", "Tag Classification", "Classify tags for a note/folder/node", prompt_1],
        ["PROMPT-TAG-02", "Tag Creation", "Propose new short-code tags safely", prompt_2],
        ["PROMPT-TAG-03", "Module Fill", "Fill metadata modules on demand", prompt_3],
        ["PROMPT-IMG-01", "Image Classification", "Classify image metadata for registry", prompt_img_1],
        ["PROMPT-IMG-02", "Image Retrieval", "Find best-matching images by intent", prompt_img_2],
        ["PROMPT-CORE-01", "Node Mapper", "Map content to tree node with AA/topic/keywords", prompt_core_1],
        ["PROMPT-CORE-02", "Axiom Mapper", "Map axioms to evidence rows with AA/topic/keywords", prompt_core_2],
        ["PROMPT-AX-01", "Axiom Formalization", "Formalize axioms with tree-primary mapping", prompt_ax_1],
    ]
    for r in rows:
        ws.append(r)

    style_header(ws)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:D{ws.max_row}"
    ws.column_dimensions["D"].width = 120
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=4, max_col=4):
        row[0].alignment = Alignment(vertical="top", wrap_text=True)
    autosize(ws, max_width=80)
    ws.column_dimensions["D"].width = 120


def build_yaml_template_sheet(wb):
    ws = ensure_sheet(wb, "TAG_YAML_TEMPLATE")
    ws.append(["Section", "YAML_Snippet"])

    snippet = dedent(
        """
        tags:
          controlled:
            pillar: []
            corpus: []
            node: []
            mode: []
            death_condition: []
            boundary_condition: []
            gsh: []
            theory: []
            simulation: []
            project: []
          short_codes: []
          governance:
            approved: []
            pending: []
            rejected: []
            ignore_forever: []
          ai:
            classifier_prompt_id: PROMPT-TAG-01
            creator_prompt_id: PROMPT-TAG-02
            module_prompt_id: PROMPT-TAG-03
        """
    ).strip()

    ws.append(["Tag Block", snippet])
    image_snippet = dedent(
        """
        media:
          image_registry_id: ""
          aliases: []
          short_codes: []
          image_type: diagram
          purpose: explain
          audience_level: intermediate
          definition_1line: ""
          explanation_long: ""
          keywords: []
          search_phrases: []
          negative_keywords: []
          usage:
            papers: []
            notes: []
            placements: []
          node_binding:
            primary_node: ""
            question_type: QT2
            modes: []
            death_conditions: []
            boundary_conditions: []
            gsh: ""
          rights:
            license: owned
            creator: ""
            source_url: ""
          accessibility:
            alt_text: ""
            contrast_status: unknown
          ai:
            classifier_prompt_id: PROMPT-IMG-01
            retrieval_prompt_id: PROMPT-IMG-02
        """
    ).strip()

    ws.append(["Image Block", image_snippet])
    ws.append(["Simplify Block", "aa_code: \"\"\ntopic: \"\"\nkeywords: []"])
    ws.append(["Short Code Rule", "Use 2-3 letter codes when possible. Keep codes unique globally."])
    ws.append(["Persistence Rule", "If Decision=ignore_forever in TAG_ASSIGNMENTS, never suggest that tag again."])
    ws.append(["Carry Rule", "Global approved tags auto-apply to all folder profiles with Auto_Apply_Global_Tags=yes."])

    style_header(ws)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:B{ws.max_row}"
    ws.column_dimensions["A"].width = 28
    ws.column_dimensions["B"].width = 125
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=2, max_col=2):
        row[0].alignment = Alignment(vertical="top", wrap_text=True)


def write_system_stamp(wb):
    ws = ensure_sheet(wb, "TAG_SYSTEM_INFO")
    ws.append(["Field", "Value"])
    ws.append(["system_name", "Tree-Primary Tag Core"])
    ws.append(["version", "1.0.0"])
    ws.append(["generated_on", datetime.now().isoformat(timespec="seconds")])
    ws.append(["principle", "Tree nodes are primary; axioms are evidentiary support within nodes."])
    ws.append(["notes", "Use TAG_AI_PROMPTS for copy/paste classification workflows. Includes image prompts."])
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws)


def build_workbook(workbook_path: Path):
    wb = load_workbook(workbook_path)

    build_enums_sheet(wb)
    build_tag_registry_sheet(wb)
    build_folder_profiles_sheet(wb)
    build_assignments_sheet(wb)
    build_image_registry_sheet(wb)
    build_image_usage_sheet(wb)
    build_tree_nodes_master_sheet(wb)
    build_axiom_evidence_map_sheet(wb)
    build_axiom_crossref_sheet(wb)
    build_axiom_formalization_sheet(wb)
    build_note_masters_sheet(wb)
    build_yaml_synth_queue_sheet(wb)
    build_heart_index_sheet(wb)
    build_heart_god_sheet(wb)
    build_heart_physics_sheet(wb)
    build_heart_cross_domain_sheet(wb)
    build_heart_ai_sheet(wb)
    build_heart_system_engine_sheet(wb)
    build_prompts_sheet(wb)
    build_yaml_template_sheet(wb)
    write_system_stamp(wb)

    wb.save(workbook_path)


def main():
    parser = argparse.ArgumentParser(description="Build tree-primary tag sheets in the vault workbook.")
    parser.add_argument(
        "--workbook",
        default=r"C:\Users\lowes\OneDrive\Desktop\Master Theophysics Obsidian VAULT.xlsx",
        help="Path to target workbook.",
    )
    args = parser.parse_args()

    path = Path(args.workbook)
    if not path.exists():
        raise FileNotFoundError(f"Workbook not found: {path}")

    build_workbook(path)
    print(f"Updated workbook: {path}")


if __name__ == "__main__":
    main()
