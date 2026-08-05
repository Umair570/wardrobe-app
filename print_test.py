import json

with open("test_grey_out.txt", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()
    for line in lines:
        if "Vol" in line or "CHOSEN" in line:
            print(line.strip())
