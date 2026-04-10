#!/usr/bin/env python3

import sys
from pathlib import Path


def format_mm(value: float) -> str:
    text = f"{value:.3f}".rstrip("0").rstrip(".")
    return text or "0"


def mm_to_points(value_mm: float) -> str:
    value_pt = value_mm * 72.0 / 25.4
    return f"{value_pt:.2f}"


def parse_mm(arg: str, name: str) -> float:
    try:
        value = float(arg)
    except ValueError as exc:
        raise SystemExit(f"{name} must be a number in millimeters, got: {arg}") from exc

    if value <= 0:
        raise SystemExit(f"{name} must be greater than zero, got: {arg}")
    return value


def build_fixed_ppd(source: Path, width_mm: float, height_mm: float, gap_mm: float) -> list[str]:
    if gap_mm != 2.0:
        raise SystemExit(
            "gap_mm other than 2 is not supported by the current raster-tspl driver path; "
            "use gap_mm=2"
        )

    width_text = format_mm(width_mm)
    height_text = format_mm(height_mm)
    gap_text = format_mm(gap_mm)
    page_id = f"w{width_text.replace('.', '_')}h{height_text.replace('.', '_')}mm.Fixed"
    page_label = f"{width_text} x {height_text} mm"
    page_size = f"[{mm_to_points(width_mm)} {mm_to_points(height_mm)}]"
    imageable = f"0 0 {mm_to_points(width_mm)} {mm_to_points(height_mm)}"
    paper_dimension = f"{mm_to_points(width_mm)} {mm_to_points(height_mm)}"

    replacements = {
        '*PCFileName: "sp410.tspl.ppd"': '*PCFileName: "TDP24FIX.PPD"',
        '*Product: "(SP410)"': f'*Product: "(XPrinter fixed {width_text}x{height_text} gap {gap_text})"',
        '*Manufacturer: "iDPRT"': '*Manufacturer: "XPrinter-compatible"',
        '*ModelName: "SP410"': f'*ModelName: "XPrinter fixed {width_text}x{height_text} gap {gap_text}"',
        '*NickName: "iDPRT SP410, 1.4.7"': (
            f'*NickName: "XPrinter fixed {width_text} x {height_text} mm gap {gap_text} (TSPL)"'
        ),
    }

    fixed_page_size = (
        f'*PageSize {page_id}/{page_label}: "<</PageSize{page_size}/ImagingBBox null>>setpagedevice"'
    )
    fixed_page_region = (
        f'*PageRegion {page_id}/{page_label}: "<</PageSize{page_size}/ImagingBBox null>>setpagedevice"'
    )
    fixed_imageable_area = f'*ImageableArea {page_id}/{page_label}: "{imageable}"'
    fixed_paper_dimension = f'*PaperDimension {page_id}/{page_label}: "{paper_dimension}"'

    lines = source.read_text().splitlines()
    out: list[str] = []
    inside_pagesize = False
    inside_pageregion = False
    inside_resolution = False
    inside_papertype = False

    for original_line in lines:
        line = replacements.get(original_line, original_line)

        if line.startswith("*CustomPageSize") or line.startswith("*ParamCustomPageSize"):
            continue

        if line == "*OpenUI *PageSize/Media Size: PickOne":
            inside_pagesize = True
            out.append(line)
            continue
        if inside_pagesize:
            if line.startswith("*DefaultPageSize:"):
                out.append(f"*DefaultPageSize: {page_id}")
                continue
            if line.startswith("*OrderDependency: 10 AnySetup *PageSize"):
                out.append(line)
                out.append(fixed_page_size)
                continue
            if line == "*CloseUI: *PageSize":
                out.append(line)
                inside_pagesize = False
                continue
            continue

        if line == "*OpenUI *PageRegion/Media Size: PickOne":
            inside_pageregion = True
            out.append(line)
            continue
        if inside_pageregion:
            if line.startswith("*DefaultPageRegion:"):
                out.append(f"*DefaultPageRegion: {page_id}")
                continue
            if line.startswith("*OrderDependency: 10 AnySetup *PageRegion"):
                out.append(line)
                out.append(fixed_page_region)
                continue
            if line == "*CloseUI: *PageRegion":
                out.append(line)
                inside_pageregion = False
                continue
            continue

        if line.startswith("*DefaultImageableArea:"):
            out.append(f"*DefaultImageableArea: {page_id}")
            continue
        if line.startswith("*ImageableArea "):
            if not out or out[-1] != fixed_imageable_area:
                out.append(fixed_imageable_area)
            continue

        if line.startswith("*DefaultPaperDimension:"):
            out.append(f"*DefaultPaperDimension: {page_id}")
            continue
        if line.startswith("*PaperDimension "):
            if not out or out[-1] != fixed_paper_dimension:
                out.append(fixed_paper_dimension)
            continue

        if line == "*OpenUI *Resolution/Resolution: PickOne":
            inside_resolution = True
            out.append(line)
            continue
        if inside_resolution:
            if line.startswith("*DefaultResolution:"):
                out.append("*DefaultResolution: 203dpi")
                continue
            if (
                line.startswith("*OrderDependency: 100 AnySetup *Resolution")
                or line == '*Resolution 203dpi/203 DPI: "<</HWResolution[203 203]/cupsBitsPerColor 1/cupsRowCount 0/cupsRowFeed 0/cupsRowStep 0/cupsColorSpace 3>>setpagedevice"'
                or line == "*CloseUI: *Resolution"
            ):
                out.append(line)
                if line == "*CloseUI: *Resolution":
                    inside_resolution = False
                continue
            continue

        if line == "*OpenUI *PaperType/Type: PickOne":
            inside_papertype = True
            out.append(line)
            continue
        if inside_papertype:
            if line.startswith("*DefaultPaperType:"):
                out.append("*DefaultPaperType: 1")
                continue
            if (
                line.startswith("*OrderDependency: 120 AnySetup *PaperType")
                or line == '*PaperType 1/Label with Gaps: ""'
                or line == "*CloseUI: *PaperType"
            ):
                out.append(line)
                if line == "*CloseUI: *PaperType":
                    inside_papertype = False
                continue
            continue

        out.append(line)

    return out


def main() -> int:
    if len(sys.argv) != 6:
        print(
            f"usage: {Path(sys.argv[0]).name} SOURCE_PPD DEST_PPD WIDTH_MM HEIGHT_MM GAP_MM",
            file=sys.stderr,
        )
        return 2

    source = Path(sys.argv[1])
    dest = Path(sys.argv[2])
    width_mm = parse_mm(sys.argv[3], "width_mm")
    height_mm = parse_mm(sys.argv[4], "height_mm")
    gap_mm = parse_mm(sys.argv[5], "gap_mm")

    out = build_fixed_ppd(source, width_mm, height_mm, gap_mm)
    dest.write_text("\n".join(out) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
