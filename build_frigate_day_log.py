#!/usr/bin/env python3
import sys
import json
import urllib.request

def main():
    if len(sys.argv) != 4:
        print("Usage: build_frigate_day_log.py <ydate> <start> <end>")
        sys.exit(1)

    ydate, start, end = sys.argv[1], sys.argv[2], sys.argv[3]

    url = f"http://192.168.86.244:5000/api/review?after={start}&before={end}"

    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.load(resp)
    except Exception as e:
        # If anything goes wrong, write a simple error file
        with open(f"/config/www/frigate_{ydate}.log", "w") as f:
            f.write(f"{ydate} - Error fetching data: {e}")
        return

    # Your API returns a top-level list like: [ {event1}, {event2}, ... ]
    if isinstance(data, dict) and "events" in data:
        events = data["events"]
    elif isinstance(data, list):
        events = data
    else:
        events = []

    lines = []

    if not events:
        lines.append(f"{ydate} - No events.")
    else:
        lines.append(f"{ydate} - Frigate Events")
        lines.append("--------------------------------------------------")

        for i, e in enumerate(events, 1):
            cam = e.get("camera", "")
            md = (e.get("data") or {}).get("metadata") or {}
            objs = ", ".join((e.get("data") or {}).get("objects") or [])
            title = md.get("title", "")
            scene = md.get("scene", "")
            time_str = md.get("time", "")
            start_time = e.get("start_time", "")
            end_time = e.get("end_time", "")
            eid = e.get("id", "")
            threat_level = md.get("potential_threat_level", "")
            severity = e.get("severity", "")

            # raw thumb path from event (usually starts with /media/frigate/...)
            thumb_path = e.get("thumb_path", "")

            # Adjust timestamps (–5s / +10s padding)
            try:
                start_time_adj = float(start_time) - 5
                end_time_adj = float(end_time) + 10
            except Exception:
                start_time_adj = start_time
                end_time_adj = end_time

            lines.append(f"{i}.   {time_str} - {cam}")
            lines.append(f"Threat:{threat_level}")
            lines.append(f"Severity:{severity}")
            lines.append(f"Objects:{objs}")
            lines.append(f"[{title}](http://192.168.86.243:5000/vod/{cam}/start/{int(start_time_adj)}/end/{int(end_time_adj)}/index.m3u8)")
            lines.append(f"   {scene}")

            # --- Thumbnail as inline markdown image ---
            if thumb_path:
                # remove /media/frigate prefix
                if thumb_path.startswith("/media/frigate"):
                    thumb_rel = thumb_path[len("/media/frigate"):]
                else:
                    thumb_rel = thumb_path

                # ensure leading slash
                if not thumb_rel.startswith("/"):
                    thumb_rel = "/" + thumb_rel

                thumb_url = f"https://192.168.86.244:8971{thumb_rel}"
            else:
                # fallback: construct thumbnail path without random suffix
                thumb_url = (
                    f"http://192.168.86.244:5000/clips/review/"
                    f"thumb-{camera}-{start_time}.webp"
                )

            # inline markdown image
            lines.append(f"![Thumbnail]({thumb_url})")

            lines.append(f"[Video](http://192.168.86.243:5000/vod/{cam}/start/{int(start_time_adj)}/end/{int(end_time_adj)}/index.m3u8) [Preview](http://192.168.86.244:5000/api/review/{eid}/preview)")
            lines.append("")

    with open(f"/config/www/frigate_{ydate}.log", "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
