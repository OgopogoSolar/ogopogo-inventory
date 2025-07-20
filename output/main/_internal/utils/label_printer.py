"""
Universal Label Printing Library (utils/label_printer.py)

• Reads a WDFX/XML template and substitutes placeholders %%%Name%%%.
• Sends draw commands (rectangles, lines, text, barcodes, QR codes) to DTPWeb.
• Supports “rotated” tables by transposing only the internal grid (rows↔columns)
  while keeping the outer frame correct, and by repositioning each cell’s text
  based on the orientation (0°, 90°, 180°, 270°).  Coordinates assume a
  top-left origin.
"""

from __future__ import annotations
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from dtpweb import DTPWeb, LPA_QREccLevel

__all__ = ["print_label"]


def _get(node: ET.Element, tag: str, caster, default=None):
    """
    Helper to find <tag> under node, cast its text, or return default.
    """
    el = node.find(tag)
    if el is not None and el.text is not None:
        try:
            return caster(el.text)
        except Exception:
            return default
    return default


def print_label(template_path: str | Path, placeholders: dict[str, str]):
    """
    Load the XML template at template_path, substitute placeholders,
    and send drawing commands to the first available DTPWeb printer.
    """
    # 1) Read & fill template
    xml = Path(template_path).read_text(encoding="utf-8")
    xml_filled = re.sub(
        r"%%%\s*(.*?)\s*%%%",
        lambda m: str(placeholders.get(m.group(1).strip(), "")),
        xml,
    )
    root = ET.fromstring(xml_filled)

    # 2) Global label settings
    label_width = _get(root, "labelWidth", float, 0.0)
    label_height = _get(root, "labelHeight", float, 0.0)
    # offsets to apply to every element
    offset_x = _get(root, "offsetX", float, 0.0) - 2.0
    offset_y = _get(root, "offsetY", float, 0.0) - 1.0
    print_speed = _get(root, "printSpeed", int)
    print_darkness = _get(root, "printDarkness", int)

    page = root.find("Page")
    if page is None:
        raise RuntimeError("Template missing <Page> node")

    # 3) Initialize printer
    api = DTPWeb()
    if not api.check_plugin():
        raise RuntimeError("DTPWeb plugin not running")
    printers = api.get_printers()
    if not printers:
        raise RuntimeError("No printers found")
    api.open_printer(**printers[0])
    api.start_job(width=label_width, height=label_height)

    # 4) Draw each element
    for node in page:
        tag = node.tag.lower()
        # collect common parameters
        params: dict[str, object] = {}
        for name, caster in [
            ("x", float),
            ("y", float),
            ("width", float),
            ("height", float),
            ("rotation", int),
            ("orientation", int),
            ("lineWidth", float),
            ("fontSize", int),
            ("fontHeight", float),
            ("charSpace", float),
            ("lineSpace", float),
            ("autoReturn", int),
            ("fontStyle", str),
            ("fontName", str),
            ("leadingIndent", float),
            ("horizontalAlignment", int),
            ("verticalAlignment", int),
        ]:
            val = _get(node, name, caster)
            if val is not None:
                # apply the global offsets to x/y
                if name == "x":
                    params["x"] = val + offset_x
                elif name == "y":
                    params["y"] = val + offset_y
                else:
                    params[name] = val

        if tag == "table":
            # --- parse the row and column size lists ---
            raw_rows = node.findtext("rowHeight") or ""
            raw_cols = node.findtext("colWidth") or ""
            rowHeights = [float(r) for r in raw_rows.split(",") if r.strip()]
            colWidths = [float(c) for c in raw_cols.split(",") if c.strip()]
            lw = float(node.findtext("lineWidth"))

            # --- remember original table dimensions ---
            orig_w = params.get("width", 0.0)
            orig_h = params.get("height", 0.0)

            # --- decide if we transpose internal grid (90° or 270°) ---
            orientation = int(params.get("orientation", 0))
            transpose = orientation in (90, 270)
            if transpose:
                rowHeights, colWidths = colWidths, rowHeights

            # --- draw the outer frame with rotation intact ---
            params["lineWidth"] = lw
            if lw > 0:
                api.draw_rect(**params)

            base_x = params.get("x", 0.0)
            base_y = params.get("y", 0.0)
            # lw = params.get("lineWidth", 0.0)
            tbl_w = orig_w
            tbl_h = orig_h

            # --- draw internal horizontal grid lines (transposed or not) ---
            y_cur = base_y + lw / 2
            for rh in rowHeights[:-1]:
                y_cur += rh + lw
                line_args = {
                    "x1": base_x + lw / 2,
                    "y1": y_cur,
                    "x2": base_x + tbl_w - lw / 2,
                    "y2": y_cur,
                    "lineWidth": lw,
                    "orientation": orientation,
                }
                if lw > 0:
                    # only draw if lineWidth is positive
                    api.draw_line(**line_args)

            # --- draw internal vertical grid lines ---
            x_cur = base_x + lw / 2
            for cw in colWidths[:-1]:
                x_cur += cw + lw
                line_args = {
                    "x1": x_cur,
                    "y1": base_y + lw / 2,
                    "x2": x_cur,
                    "y2": base_y + tbl_h - lw / 2,
                    "lineWidth": lw,
                    "orientation": orientation,
                }
                if lw > 0:
                    api.draw_line(**line_args)

            # --- draw each cell’s text, repositioned per orientation ---
            cells = node.find("Cells")
            if cells is not None:
                texts = cells.findall("Text")
                cols = len(colWidths)

                for idx, cell in enumerate(texts):
                    content = (cell.findtext("content", "") or "").strip()
                    if not content:
                        continue

                    # determine row, column index
                    r, c = divmod(idx, cols)
                    # offset to the top-left of this cell (pre-rotation)
                    x_off = sum(colWidths[:c]) + (c + 1) * lw
                    y_off = sum(rowHeights[:r]) + (r + 1) * lw

                    # compute the final insertion point based on rotation about
                    # the table origin at (base_x, base_y)
                    if orientation == 0:
                        tx = base_x + x_off + lw/2
                        ty = base_y + y_off + lw/2
                    elif orientation == 90:
                        tx = base_x - (sum(colWidths[:c+1]) + (c + 2) * lw) + lw/2
                        ty = base_y + y_off + lw/2
                    else:  # 270° only. 180° is nonsence for tables
                        tx = base_x + x_off + lw/2
                        ty = base_y + (sum(rowHeights[:r+1]) + (r + 2) * lw) - lw/2

                    # prepare text args
                    text_args: dict[str, object] = {
                        "text": content,
                        "x": tx,
                        "y": ty,
                        "orientation": orientation,
                    }
                    # optional font overrides per cell
                    if cell.find("fontSize") is not None:
                        text_args["fontSize"] = int(cell.findtext("fontSize"))
                    if cell.find("fontHeight") is not None:
                        text_args["fontHeight"] = float(cell.findtext("fontHeight"))
                    # fontStyle默认0x00
                    if cell.find("fontStyle") is not None:
                        text_args["fontStyle"] = cell.findtext("fontStyle", "0x00")
                    if cell.find("verticalAlignment") is not None:
                        text_args["verticalAlignment"] = int(
                            cell.findtext("verticalAlignment", 0)
                        )
                    if cell.find("horizontalAlignment") is not None:
                        text_args["horizontalAlignment"] = int(
                            cell.findtext("horizontalAlignment", 0)
                        )
                    if cell.find("autoReturn") is not None:
                        text_args["autoReturn"] = int(
                            cell.findtext("autoReturn", 0)
                        )
                    api.draw_text(**text_args)
        elif tag == "qrcode":
            # (unchanged: draws QR, PDF417, or DataMatrix)
            code_type = _get(node, "type", int, 0)
            draw_args = dict(params)
            if code_type == 2:
                draw_args["data"] = node.findtext("data", "")
            else:
                draw_args["text"] = node.findtext("content", "")
            if code_type == 0:
                ecc = node.findtext("eccLevel")
                if ecc is not None:
                    draw_args["eccLevel"] = {
                        "0": LPA_QREccLevel.EccLevel_L.value,
                        "1": LPA_QREccLevel.EccLevel_M.value,
                        "2": LPA_QREccLevel.EccLevel_Q.value,
                        "3": LPA_QREccLevel.EccLevel_H.value,
                    }.get(ecc, LPA_QREccLevel.EccLevel_L.value)
                api.draw_qrcode(**draw_args)
            elif code_type == 1:
                draw_args["eccLevel"] = node.findtext("eccLevel", 0)
                api.draw_pdf417(**draw_args)
            else:
                api.draw_datamatrix(**draw_args)

        elif tag == "barcode":
            api.draw_barcode(**params)

        elif tag == "text":
            txt = node.findtext("content", "") or node.text or ""
            params["text"] = txt
            api.draw_text(**params)

    # 5) Finalize print job
    commit_opts: dict[str, int] = {}
    if print_speed is not None:
        commit_opts["speed"] = print_speed
    if print_darkness is not None:
        commit_opts["darkness"] = print_darkness
    api.commit_job(**commit_opts)
    api.close_printer()
