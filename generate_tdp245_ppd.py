#!/usr/bin/env python3

from pathlib import Path
import sys


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


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {Path(sys.argv[0]).name} SOURCE_PPD DEST_PPD", file=sys.stderr)
        return 2

    source = Path(sys.argv[1])
    dest = Path(sys.argv[2])

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

    dest.write_text("\n".join(out) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
