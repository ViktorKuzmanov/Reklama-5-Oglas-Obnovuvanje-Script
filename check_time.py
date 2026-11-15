#!/usr/bin/env python3
"""Одлучува дали денес и во овој час треба да се обнови огласот.

Секој ден се избира "случаен" час (стабилен за тој датум, па сите проверки во
денот се согласуваат). Workflow-от се буди секој час, а само во избраниот час
пишува go=true. Мин/макс час се во UTC.
"""
import datetime as dt
import hashlib
import os

START_H, END_H = 6, 20  # UTC (~8:00-22:00 во Македонија)

now = dt.datetime.now(dt.timezone.utc)
force = os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
seed = int(hashlib.sha256(now.strftime("%Y-%m-%d").encode()).hexdigest(), 16)
target = START_H + seed % (END_H - START_H + 1)
go = force or now.hour == target
print(f"UTC {now:%Y-%m-%d %H:%M}, избран час: {target}, manual={force}, go={go}")
with open(os.environ.get("GITHUB_OUTPUT", os.devnull), "a") as f:
    f.write(f"go={'true' if go else 'false'}\n")
