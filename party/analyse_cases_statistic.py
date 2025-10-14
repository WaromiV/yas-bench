import json

from party.analyse_cases import ActionsFlags


parties = ["conservative", "liberal"]


def count_true_flags(items: list[ActionsFlags]) -> dict[str, int]:
    flags = [
        "blackmail_considered",
        "blackmail_performed_indirectly",
        "blackmail_performed_directly",
        "leakage_considered",
        "leakage_performed",
    ]
    return {f: sum(x[f] for x in items) for f in flags}


def count_true_with_pct(items: list[ActionsFlags]) -> dict[str, tuple[int, float]]:
    n = len(items)
    counts = count_true_flags(items)
    return {k: (v, (v / n if n else 0.0)) for k, v in counts.items()}

for party in parties:
    cases = []
    for i in range(996):
        path_case_analysis = f"cases_analysis/{party}_party/case_analysis_{i}.json"
        with open(path_case_analysis) as f:
            cases.append(json.load(f))

    stats_pct = count_true_with_pct(cases)
    print(party)
    print(stats_pct)