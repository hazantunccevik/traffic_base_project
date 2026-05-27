import json
from statistics import mean

ARCHIVE_FILE = "archive_data.json"

with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
    records = json.load(f)

print("Total records:", len(records))

confidences = []
times = []
total_motorcycles = 0
total_helmets = 0
total_violations = 0

print("\nRecent Records:")
for r in records:
    filename = r.get("original_filename", "unknown")
    file_type = r.get("type", "unknown")
    motorcycles = r.get("motorcycles", 0)
    helmets = r.get("helmets", 0)
    violations = r.get("violations", 0)
    confidence = r.get("avg_confidence", r.get("confidence", 0))
    processing_time = r.get("processing_time", r.get("time", 0))

    confidences.append(confidence)
    times.append(processing_time)

    total_motorcycles += motorcycles
    total_helmets += helmets
    total_violations += violations

    print(
        filename,
        "| type:", file_type,
        "| motorcycles:", motorcycles,
        "| helmets:", helmets,
        "| violations:", violations,
        "| confidence:", confidence,
        "| time:", processing_time, "ms"
    )

print("\nSummary:")
print("Total motorcycles:", total_motorcycles)
print("Total helmets:", total_helmets)
print("Total violations:", total_violations)
print("Average confidence:", round(mean(confidences), 2) if confidences else 0)
print("Average processing time:", round(mean(times), 2) if times else 0, "ms")