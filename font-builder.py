# Automated hybrid font builder for the custom Uni404se font.
# It merges 15 fonts with auto‐scaling and GPOS preservation.

import requests
import io
from fontTools.ttLib import TTFont, woff2
from fontTools.feaLib.builder import addOpenTypeFeatures
from fontTools import subset

BASE_FONT_URL = "https://fonts.bunny.net/space-grotesk/files/space-grotesk-latin-700-normal.woff2"
SECONDARY_FONTS = [
    "https://fonts.bunny.net/alfa-slab-one/files/alfa-slab-one-latin-400-normal.woff2",
    "https://fonts.bunny.net/amatic-sc/files/amatic-sc-latin-700-normal.woff2",
    "https://fonts.bunny.net/bebas-neue/files/bebas-neue-latin-400-normal.woff2",
    "https://fonts.bunny.net/bungee-shade/files/bungee-shade-latin-400-normal.woff2",
    "https://fonts.bunny.net/caveat/files/caveat-latin-700-normal.woff2",
    "https://fonts.bunny.net/chewy/files/chewy-latin-400-normal.woff2",
    "https://fonts.bunny.net/creepster/files/creepster-latin-400-normal.woff2",
    "https://fonts.bunny.net/dotgothic16/files/dotgothic16-latin-400-normal.woff2",
    "https://fonts.bunny.net/indie-flower/files/indie-flower-latin-400-normal.woff2",
    "https://fonts.bunny.net/luckiest-guy/files/luckiest-guy-latin-400-normal.woff2",
    "https://fonts.bunny.net/michroma/files/michroma-latin-400-normal.woff2",
    "https://fonts.bunny.net/permanent-marker/files/permanent-marker-latin-400-normal.woff2",
    "https://fonts.bunny.net/press-start-2p/files/press-start-2p-latin-400-normal.woff2",
    "https://fonts.bunny.net/special-elite/files/special-elite-latin-400-normal.woff2",
    "https://fonts.bunny.net/ultra/files/ultra-latin-400-normal.woff2",
]

def get_font_from_url(url):
    response = requests.get(url)
    stream = io.BytesIO(response.content)
    decompressed = io.BytesIO()

    woff2.decompress(stream, decompressed)

    decompressed.seek(0)

    return TTFont(decompressed)

base_font = get_font_from_url(BASE_FONT_URL)
feature_code = ""

for i, url in enumerate(SECONDARY_FONTS, start=1):
    ss_tag = f"ss{i:02d}"
    other_font = get_font_from_url(url)

    base_h = base_font["head"].unitsPerEm
    other_h = other_font["head"].unitsPerEm
    scale = base_h / other_h

    for char in ["four", "zero"]:
        new_name = f"{char}.{ss_tag}"
        base_font["glyf"][new_name] = other_font["glyf"][char]

        glyph = base_font["glyf"][new_name]

        if hasattr(glyph, "coordinates"):
            for j in range(len(glyph.coordinates)):
                x, y = glyph.coordinates[j]
                glyph.coordinates[j] = (int(x * scale), int(y * scale))

            glyph.xMin, glyph.yMin = int(glyph.xMin * scale), int(glyph.yMin * scale)
            glyph.xMax, glyph.yMax = int(glyph.xMax * scale), int(glyph.yMax * scale)

        orig_width = other_font["hmtx"][char][0]
        base_font["hmtx"][new_name] = (int(orig_width * scale), 0)

        if new_name not in base_font.getGlyphOrder():
            base_font.getGlyphOrder().append(new_name)

    feature_code += f"\nfeature {ss_tag} {{\n    sub four by four.{ss_tag};\n    sub zero by zero.{ss_tag};\n}} {ss_tag};\n"

    if "GPOS" in other_font:
        gpos_table = other_font["GPOS"].table

        if hasattr(gpos_table.LookupList, "Lookup"):
            for lookup in gpos_table.LookupList.Lookup:
                if lookup.LookupType == 2:
                    for sub in lookup.SubTable:
                        if hasattr(sub, "PairSet"):
                            for g1_gid, pair_set in zip(sub.Coverage.glyphs, sub.PairSet):
                                g1 = g1_gid if isinstance(g1_gid, str) else other_font.getGlyphName(g1_gid)

                                if g1 in ["four", "zero"]:
                                    for rec in pair_set.PairValueRecord:
                                        g2 = rec.SecondGlyph if isinstance(rec.SecondGlyph, str) else other_font.getGlyphName(rec.SecondGlyph)

                                        if g2 in ["four", "zero"]:
                                            val1 = rec.Value1

                                            if val1 and hasattr(val1, "XAdvance") and val1.XAdvance != 0:
                                                feature_code += f"\nfeature kern {{\n    pos {g1}.{ss_tag} {g2}.{ss_tag} {int(val1.XAdvance * scale)};\n}} kern;\n"

all_custom = []

for i in range(1, 16):
    all_custom.extend([f"four.ss{i:02d}", f"zero.ss{i:02d}"])

subset_options = subset.Options()
subset_options.ignore_missing_glyphs = True
subsetter = subset.Subsetter(options=subset_options)
subsetter.populate(glyphs=["four", "zero", ".notdef"] + all_custom)
subsetter.subset(base_font)

addOpenTypeFeatures(base_font, io.StringIO(feature_code))

for name_id in [0, 3, 5, 8, 9, 11, 13, 14]:
    base_font["name"].removeNames(nameID=name_id)

base_font["name"].setName("Uni404se", 1, 3, 1, 1033)
base_font["name"].setName("Bold", 2, 3, 1, 1033)
base_font["name"].setName("Uni404se Bold", 4, 3, 1, 1033)
base_font["name"].setName("Version 1.0.0", 5, 3, 1, 1033)
base_font["name"].setName("Placer", 8, 3, 1, 1033)
base_font["name"].setName("Placer", 9, 3, 1, 1033)
base_font["name"].setName("This Font Software is licensed under the SIL Open Font License, Version 1.1 and incorporates glyphs from other fonts, which are acknowledged in FONTLOG.md. This license is available with a FAQ at: https://openfontlicense.org", 13, 3, 1, 1033)
base_font["name"].setName("https://openfontlicense.org", 14, 3, 1, 1033)
base_font["name"].setName("Uni404se", 16, 3, 1, 1033)
base_font["name"].setName("Bold", 17, 3, 1, 1033)
base_font["head"].fontRevision = 1.000

base_font.save("Uni404se-Bold.ttf")

woff2.compress("Uni404se-Bold.ttf", "Uni404se-Bold.woff2")

print("✅ Uni404se-Bold font created successfully!")
