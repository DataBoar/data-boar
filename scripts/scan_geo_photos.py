"""Scan pCloud photos for GPS coordinates near Caju/Porto do Rio."""

import sys
from pathlib import Path

try:
    from PIL import Image
    from PIL.ExifTags import TAGS, GPSTAGS
except ImportError:
    print("PIL not available")
    sys.exit(1)

CAJU_LAT = -22.878
CAJU_LON = -43.224
RADIUS_KM = 3.0


def get_gps(filepath):
    try:
        img = Image.open(filepath)
        exif = img._getexif()
        if not exif:
            return None
        gps_info = {}
        for tag_id, value in exif.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag == "GPSInfo":
                for gps_tag_id, gps_value in value.items():
                    gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                    gps_info[gps_tag] = gps_value
        if not gps_info:
            return None
        lat = dms_to_dd(gps_info.get("GPSLatitude"), gps_info.get("GPSLatitudeRef"))
        lon = dms_to_dd(gps_info.get("GPSLongitude"), gps_info.get("GPSLongitudeRef"))
        if lat is not None and lon is not None:
            return (lat, lon)
    except Exception:
        pass
    return None


def dms_to_dd(dms, ref):
    if dms is None or ref is None:
        return None
    d, m, s = [float(x) for x in dms]
    dd = d + m / 60 + s / 3600
    if ref in ("S", "W"):
        dd = -dd
    return dd


def haversine_km(lat1, lon1, lat2, lon2):
    import math

    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.asin(math.sqrt(a))


def main():
    folder = (
        Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"P:\Automatic Upload\iPhoneL")
    )
    year_start = sys.argv[2] if len(sys.argv) > 2 else "2022"

    hits = []
    scanned = 0
    no_gps = 0

    for f in sorted(folder.glob("*.jpeg")):
        if not f.name.startswith(("2022", "2023", "2024", "2025", "2026")):
            if f.name < year_start:
                continue
        scanned += 1
        if scanned % 200 == 0:
            print(f"  ...scanned {scanned}...", file=sys.stderr)
        coords = get_gps(f)
        if coords is None:
            no_gps += 1
            continue
        lat, lon = coords
        dist = haversine_km(lat, lon, CAJU_LAT, CAJU_LON)
        if dist <= RADIUS_KM:
            hits.append((f.name, lat, lon, dist))

    print(
        f"\nScanned: {scanned} | No GPS: {no_gps} | Hits near Caju (<{RADIUS_KM}km): {len(hits)}"
    )
    for name, lat, lon, dist in hits:
        print(f"  {name}  ({lat:.4f}, {lon:.4f})  {dist:.1f}km")


if __name__ == "__main__":
    main()
