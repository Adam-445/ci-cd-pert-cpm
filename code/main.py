tasks = {
    "A": {"dur": 5, "pred": []},
    "B": {"dur": 10, "pred": ["A"]},
    "C": {"dur": 6, "pred": ["A"]},
    "D": {"dur": 12, "pred": ["B", "C"]},
}

ES, EF = {}, {}
for t in tasks:
    ES[t] = max([EF[p] for p in tasks[t]["pred"]], default=0)
    EF[t] = ES[t] + tasks[t]["dur"]

project_time = max(EF.values())
print("Project duration:", project_time, "\n")

number: str = "3"

print("Task  ES  EF")
for t in tasks:
    print(f"{t:>4} {ES[t]:>3} {EF[t]:>3}")
