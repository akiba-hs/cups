#!/usr/bin/env python3

import sys
from pathlib import Path


REPLACEMENTS = {
    '*PCFileName: "sp410.tspl.ppd"': '*PCFileName: "TDP245TS.PPD"',
    '*Product: "(SP410)"': '*Product: "(XPrinter TDP-245 compatible)"',
    '*Manufacturer: "iDPRT"': '*Manufacturer: "XPrinter-compatible"',
    '*ModelName: "SP410"': '*ModelName: "XPrinter TDP-245 compatible"',
    '*NickName: "iDPRT SP410, 1.4.7"': '*NickName: "XPrinter TDP-245 compatible (TSPL)"',
    '*DefaultPageSize: w100h150': '*DefaultPageSize: 20x30mmRotated.Fullbleed',
    '*DefaultPageRegion: w100h150': '*DefaultPageRegion: 20x30mmRotated.Fullbleed',
    '*DefaultImageableArea: w100h150': '*DefaultImageableArea: 20x30mmRotated.Fullbleed',
    '*DefaultPaperDimension: w100h150': '*DefaultPaperDimension: 20x30mmRotated.Fullbleed',
    '*DefaultPaperType: None': '*DefaultPaperType: 1',
}

INSERT_AFTER = {
    '*PageSize w50h12/2"x0.5"(50.8mm x 12.7mm): "<</PageSize[142 36]/ImagingBBox null>>setpagedevice"': [
        '*PageSize 20x30mmRotated.Fullbleed/30 x 20 mm: "<</PageSize[85.04 56.69]/ImagingBBox null>>setpagedevice"',
        '*PageSize 20x30mm.Fullbleed/20 x 30 mm: "<</PageSize[56.69 85.04]/ImagingBBox null>>setpagedevice"',
    ],
    '*PageRegion w50h12/2"x0.5"(50.8mm x 12.7mm): "<</PageSize[142 36]/ImagingBBox null>>setpagedevice"': [
        '*PageRegion 20x30mmRotated.Fullbleed/30 x 20 mm: "<</PageSize[85.04 56.69]/ImagingBBox null>>setpagedevice"',
        '*PageRegion 20x30mm.Fullbleed/20 x 30 mm: "<</PageSize[56.69 85.04]/ImagingBBox null>>setpagedevice"',
    ],
    '*ImageableArea w50h12/2"x0.5"(50.8mm x 12.7mm): "0 0 142 36"': [
        '*ImageableArea 20x30mmRotated.Fullbleed/30 x 20 mm: "0 0 85.04 56.69"',
        '*ImageableArea 20x30mm.Fullbleed/20 x 30 mm: "0 0 56.69 85.04"',
    ],
    '*PaperDimension w50h12/2"x0.5"(50.8mm x 12.7mm): "142 36"': [
        '*PaperDimension 20x30mmRotated.Fullbleed/30 x 20 mm: "85.04 56.69"',
        '*PaperDimension 20x30mm.Fullbleed/20 x 30 mm: "56.69 85.04"',
    ],
}


FIXED_REPLACEMENTS = {
    '*PCFileName: "TDP245TS.PPD"': '*PCFileName: "TDP2430.PPD"',
    '*Product: "(XPrinter TDP-245 compatible)"': '*Product: "(XPrinter TDP-245 30x20 fixed)"',
    '*ModelName: "XPrinter TDP-245 compatible"': '*ModelName: "XPrinter TDP-245 30x20 fixed"',
    '*NickName: "XPrinter TDP-245 compatible (TSPL)"': '*NickName: "XPrinter TDP-245 30x20 fixed (TSPL)"',
}

FIXED_PAGE_SIZE = '*PageSize 20x30mmRotated.Fullbleed/30 x 20 mm: "<</PageSize[85.04 56.69]/ImagingBBox null>>setpagedevice"'
FIXED_PAGE_REGION = '*PageRegion 20x30mmRotated.Fullbleed/30 x 20 mm: "<</PageSize[85.04 56.69]/ImagingBBox null>>setpagedevice"'
FIXED_IMAGEABLE_AREA = '*ImageableArea 20x30mmRotated.Fullbleed/30 x 20 mm: "0 0 85.04 56.69"'
FIXED_PAPER_DIMENSION = '*PaperDimension 20x30mmRotated.Fullbleed/30 x 20 mm: "85.04 56.69"'


def generate_general(source: Path) -> list[str]:
    lines = source.read_text().splitlines()
    out: list[str] = []
    seen_replacements = set()
    seen_anchors = set()

    for original_line in lines:
        line = REPLACEMENTS.get(original_line, original_line)
        if original_line in REPLACEMENTS:
            seen_replacements.add(original_line)

        out.append(line)

        extras = INSERT_AFTER.get(original_line)
        if extras:
            seen_anchors.add(original_line)
            out.extend(extras)

    missing_replacements = sorted(set(REPLACEMENTS) - seen_replacements)
    missing_anchors = sorted(set(INSERT_AFTER) - seen_anchors)
    if missing_replacements or missing_anchors:
        missing = "\n".join(missing_replacements + missing_anchors)
        raise SystemExit(f"PPD patch anchors not found:\n{missing}")

    return out


def generate_fixed(lines: list[str]) -> list[str]:
    out: list[str] = []
    inside_pagesize = False
    inside_pageregion = False
    inside_papertype = False

    for original_line in lines:
        line = FIXED_REPLACEMENTS.get(original_line, original_line)

        if line.startswith("*CustomPageSize") or line.startswith("*ParamCustomPageSize"):
            continue

        if line == "*OpenUI *PageSize/Media Size: PickOne":
            inside_pagesize = True
            out.append(line)
            continue
        if inside_pagesize:
            if line.startswith("*DefaultPageSize:"):
                out.append("*DefaultPageSize: 20x30mmRotated.Fullbleed")
                continue
            if (
                line.startswith("*OrderDependency: 10 AnySetup *PageSize")
                or line == FIXED_PAGE_SIZE
                or line == "*CloseUI: *PageSize"
            ):
                out.append(line)
                if line == "*CloseUI: *PageSize":
                    inside_pagesize = False
                continue
            continue

        if line == "*OpenUI *PageRegion/Media Size: PickOne":
            inside_pageregion = True
            out.append(line)
            continue
        if inside_pageregion:
            if line.startswith("*DefaultPageRegion:"):
                out.append("*DefaultPageRegion: 20x30mmRotated.Fullbleed")
                continue
            if (
                line.startswith("*OrderDependency: 10 AnySetup *PageRegion")
                or line == FIXED_PAGE_REGION
                or line == "*CloseUI: *PageRegion"
            ):
                out.append(line)
                if line == "*CloseUI: *PageRegion":
                    inside_pageregion = False
                continue
            continue

        if line.startswith("*DefaultImageableArea:"):
            out.append("*DefaultImageableArea: 20x30mmRotated.Fullbleed")
            continue
        if line.startswith("*ImageableArea "):
            if line == FIXED_IMAGEABLE_AREA:
                out.append(line)
            continue

        if line.startswith("*DefaultPaperDimension:"):
            out.append("*DefaultPaperDimension: 20x30mmRotated.Fullbleed")
            continue
        if line.startswith("*PaperDimension "):
            if line == FIXED_PAPER_DIMENSION:
                out.append(line)
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
    fixed = False
    args = sys.argv[1:]
    if args and args[0] == "--fixed-30x20-gap2":
        fixed = True
        args = args[1:]

    if len(args) != 2:
        print(
            f"usage: {Path(sys.argv[0]).name} [--fixed-30x20-gap2] SOURCE_PPD DEST_PPD",
            file=sys.stderr,
        )
        return 2

    source = Path(args[0])
    dest = Path(args[1])

    out = generate_general(source)
    if fixed:
        out = generate_fixed(out)
    dest.write_text("\n".join(out) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
