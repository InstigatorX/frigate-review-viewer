#!/usr/bin/env python3
import sys
import json
import urllib.request
from datetime import datetime  # NEW: for fallback time formatting

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

            # data block (may be None)
            data_block = e.get("data") or {}

            # metadata can be null in JSON -> becomes None in Python
            md = data_block.get("metadata")
            if not isinstance(md, dict):
                md = {}  # normalize null / bad types to empty dict

            objs = ", ".join(data_block.get("objects") or [])

            start_time = e.get("start_time", "")
            end_time = e.get("end_time", "")
            eid = e.get("id", "")
            severity = e.get("severity", "")

            # --- Handle metadata present vs null/missing ---
            if md:  # metadata exists and is a non-empty dict
                title = md.get("title") or ""
                scene = md.get("scene") or ""
                time_str = md.get("time") or ""
                threat_level = md.get("potential_threat_level")
                if threat_level is None:
                    threat_level = ""
            else:
                # metadata is null or empty -> apply your rules
                # time_str: derive from start_time
                try:
                    ts = float(start_time)
                    dt = datetime.fromtimestamp(ts)
                    # Example format: "Sunday, 11:18 AM"
                    time_str = dt.strftime("%A, %I:%M %p")
                except Exception:
                    time_str = ""

                # threat: N/A
                threat_level = "N/A"

                # scene: "No GenAI available"
                scene = "No GenAI available"

                # title: something non-empty so link text isn't []
                title = "Security event"

            # raw thumb path from event (usually starts with /media/frigate/...)
            thumb_path = e.get("thumb_path", "")

            # Adjust timestamps (–5s / +10s padding)
            start_time_adj = start_time
            end_time_adj = end_time
            try:
                start_time_adj = float(start_time) - 5
                end_time_adj = float(end_time) + 10
            except Exception:
                # leave as-is if conversion fails
                pass

            # We will try to int-cast for URLs, but be defensive
            try:
                start_int = int(start_time_adj)
                end_int = int(end_time_adj)
            except Exception:
                # fallback: don't pad, and try to int original if possible
                try:
                    start_int = int(float(start_time))
                    end_int = int(float(end_time))
                except Exception:
                    # as a last resort, use 0/1 second window
                    start_int = 0
                    end_int = 1

            lines.append(f"{i}.   {time_str} - {cam}")
            lines.append(f"Threat:{threat_level}")
            lines.append(f"Severity:{severity}")
            lines.append(f"Objects:{objs}")
            lines.append(
                f"[{title}]("
                f"http://192.168.86.243:5000/vod/{cam}/start/{start_int}/end/{end_int}/index.m3u8)"
            )
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

                thumb_url = f"https://nvr.loebees.com:8971{thumb_rel}"
            else:
                # fallback: construct thumbnail path without random suffix
                thumb_url = (
                    f"http://192.168.86.244:5000/clips/review/"
                    f"thumb-{cam}-{start_time}.webp"
                )

            # inline markdown image
            lines.append(f"![Thumbnail]({thumb_url})")

            lines.append(
                f"[Video](http://192.168.86.243:5000/vod/{cam}/start/{start_int}/end/{end_int}/index.m3u8) "
                f"[Preview](http://192.168.86.244:5000/api/review/{eid}/preview)"
            )
            lines.append("")

    with open(f"/config/www/frigate_{ydate}.log", "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
