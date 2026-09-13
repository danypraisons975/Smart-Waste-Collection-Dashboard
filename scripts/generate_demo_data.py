from pathlib import Path
import csv

output = Path(__file__).resolve().parents[1] / "data" / "demo_collection_history.csv"
rows = []
ready_pattern = [12, 10, 8, 6, 9, 7, 11, 12, 8, 5, 10, 9, 12, 7, 6, 11, 8, 9, 5, 12, 10, 7, 8, 11, 6, 9, 12, 8, 7, 10, 11]
delay_pattern = [-5, 12, 35, 70, 20, 45, 5, -8, 28, 88, 18, 25, -3, 48, 62, 10, 32, 18, 95, -6, 15, 52, 30, 8, 68, 22, -4, 35, 46, 16, 12]
for index, (ready, delay) in enumerate(zip(ready_pattern, delay_pattern), start=1):
    total = 12
    minutes = 8 * 60 + 30 + delay
    collection_time = "" if index == 19 else f"{minutes // 60:02d}:{minutes % 60:02d}"
    rows.append({"day": f"D{index}", "collection_time": collection_time, "total_houses": total, "houses_ready": ready})
with output.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
print(f"Wrote {len(rows)} synthetic demo rows to {output}")
