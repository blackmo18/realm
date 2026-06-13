"""
realm_lib.py — stdlib-only helpers for manifest_write.py.
No external dependencies. Python 3.9+.
"""

import json
import os
import re
import tempfile
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# realm-state.json
# ---------------------------------------------------------------------------

def load_state(project_root: str) -> dict:
    path = os.path.join(project_root, ".realm", "realm-state.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: dict, project_root: str) -> None:
    path = os.path.join(project_root, ".realm", "realm-state.json")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
        f.write("\n")
    os.replace(tmp, path)


# ---------------------------------------------------------------------------
# manifest-draft.md parsing
# ---------------------------------------------------------------------------

@dataclass
class DraftNode:
    rel_path: str
    status: str          # "new" | "update"
    links: str           # raw links line value (may be empty)
    body: str            # full text after the "---" separator line


@dataclass
class DraftMeta:
    slug: str
    phase_run: str
    mode: str
    gap_summary: str


@dataclass
class Draft:
    meta: DraftMeta
    nodes: List[DraftNode] = field(default_factory=list)
    session_log: Optional[DraftNode] = None


def parse_draft(text: str) -> Draft:
    """Parse manifest-draft.md into a Draft dataclass."""
    lines = text.splitlines()

    # --- parse ## Meta block ---
    meta_slug = ""
    meta_phase_run = ""
    meta_mode = ""
    meta_gap_summary = ""

    in_meta = False
    for line in lines:
        stripped = line.strip()
        if stripped == "## Meta":
            in_meta = True
            continue
        if in_meta:
            if stripped.startswith("##"):
                break
            if stripped.startswith("slug:"):
                meta_slug = stripped[len("slug:"):].strip()
            elif stripped.startswith("phase-run:"):
                meta_phase_run = stripped[len("phase-run:"):].strip()
            elif stripped.startswith("mode:"):
                meta_mode = stripped[len("mode:"):].strip()
            elif stripped.startswith("gap-summary:"):
                meta_gap_summary = stripped[len("gap-summary:"):].strip()

    meta = DraftMeta(
        slug=meta_slug,
        phase_run=meta_phase_run,
        mode=meta_mode,
        gap_summary=meta_gap_summary,
    )

    draft = Draft(meta=meta)

    # --- collect ### sections ---
    # Each ### <rel_path> block: header line, then key:value lines, then ---, then body
    section_re = re.compile(r'^### (.+)$')
    i = 0
    in_session_section = False

    while i < len(lines):
        line = lines[i]

        # detect ## Session Log Entry boundary
        if line.strip() == "## Session Log Entry":
            in_session_section = True
            i += 1
            continue

        m = section_re.match(line)
        if not m:
            i += 1
            continue

        rel_path = m.group(1).strip()
        i += 1

        # collect key:value header lines until "---" separator
        status = "new"
        links = ""
        while i < len(lines):
            hline = lines[i].strip()
            if hline == "---":
                i += 1
                break
            if hline.startswith("status:"):
                status = hline[len("status:"):].strip()
            elif hline.startswith("links:"):
                links = hline[len("links:"):].strip()
            i += 1

        # collect body until next ### or ## or EOF
        body_lines = []
        while i < len(lines):
            peek = lines[i]
            if peek.startswith("### ") or peek.startswith("## "):
                break
            body_lines.append(peek)
            i += 1

        body = "\n".join(body_lines).strip()
        node = DraftNode(rel_path=rel_path, status=status, links=links, body=body)

        if in_session_section:
            draft.session_log = node
        else:
            draft.nodes.append(node)

    return draft


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------

def split_frontmatter(body: str) -> Tuple[str, str]:
    """Split YAML frontmatter from body content.

    Returns (yaml_text, content) where yaml_text is the raw key:value block
    (without the --- delimiters) and content is everything after the closing ---.
    If no frontmatter, returns ("", body).
    """
    lines = body.splitlines()
    if not lines or lines[0].strip() != "---":
        return "", body

    end = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end = idx
            break

    if end is None:
        return "", body

    yaml_text = "\n".join(lines[1:end])
    content = "\n".join(lines[end + 1:]).lstrip("\n")
    return yaml_text, content


def parse_yaml_min(yaml_text: str) -> Dict[str, object]:
    """Minimal YAML parser: flat key:value + simple list values.

    Handles:
      key: value
      key: [a, b, c]
      key:
        - item
    Returns a flat dict. Values are str or List[str].
    """
    result: Dict[str, object] = {}
    lines = yaml_text.splitlines()
    current_key = None
    current_list: Optional[List[str]] = None

    for line in lines:
        # list item under a block key
        if current_list is not None:
            stripped = line.strip()
            if stripped.startswith("- "):
                current_list.append(stripped[2:].strip())
                continue
            else:
                result[current_key] = current_list
                current_list = None
                current_key = None

        if ":" not in line:
            continue

        colon = line.index(":")
        key = line[:colon].strip()
        raw_val = line[colon + 1:].strip()

        if raw_val == "":
            current_key = key
            current_list = []
        elif raw_val.startswith("[") and raw_val.endswith("]"):
            items = [v.strip() for v in raw_val[1:-1].split(",") if v.strip()]
            result[key] = items
        else:
            result[key] = raw_val

    if current_key is not None and current_list is not None:
        result[current_key] = current_list

    return result


# ---------------------------------------------------------------------------
# Node type → vault directory
# ---------------------------------------------------------------------------

_TYPE_DIR = {
    "decision": "decisions",
    "function": "functions",
    "class": "classes",
    "system": "systems",
    "discovery": "discoveries",
}


def node_type_dir(node_type: str) -> str:
    return _TYPE_DIR.get(node_type.lower(), node_type.lower() + "s")


# ---------------------------------------------------------------------------
# Wikilink extraction
# ---------------------------------------------------------------------------

_WIKILINK_RE = re.compile(r'\[\[([^\]]+)\]\]')


def extract_wikilinks(text: str) -> List[str]:
    return _WIKILINK_RE.findall(text)
