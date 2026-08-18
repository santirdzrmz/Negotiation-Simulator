"""
analyze_tournament.py
---------------------
Reads the CSV produced by tournament.py and prints:
  - Tournament scores, standard error, utility-on-agreement, agreement rate
  - Payoff matrix with symmetric Nash equilibria marked
  - Per-domain-type breakdown (size × competitiveness)

Usage:
    python analyze_tournament.py <results_file.csv>

If no file is given, the most recent CSV in the current folder is used.
"""

import csv
import math
import sys
import os
import glob
from collections import defaultdict


def load_results(file_name: str):
    rows = []
    with open(file_name, newline='') as f:
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            if len(row) < 6:
                continue
            if row[0] in ("sep=", "Agent1"):
                continue
            agent1, agent2, domain, agreement, util1_s, util2_s = row[:6]
            try:
                util1 = float(util1_s)
                util2 = float(util2_s)
            except ValueError:
                continue
            rows.append({
                "agent1":    agent1,
                "agent2":    agent2,
                "domain":    domain,
                "agreement": agreement.strip().upper() == "YES",
                "util1":     util1,
                "util2":     util2,
            })
    return rows


def mean(lst):
    return sum(lst) / len(lst) if lst else float('nan')

def stderr(lst):
    if len(lst) < 2:
        return float('nan')
    m = mean(lst)
    variance = sum((x - m) ** 2 for x in lst) / (len(lst) - 1)
    return math.sqrt(variance / len(lst))


def get_agent_order(rows):
    seen, order = set(), []
    for r in rows:
        for n in (r["agent1"], r["agent2"]):
            if n not in seen:
                order.append(n)
                seen.add(n)
    return order


def build_payoff_matrix(rows, agents):
    """Returns payoff[a][b] = list of utilities a got when playing against b."""
    payoff = defaultdict(lambda: defaultdict(list))
    for r in rows:
        payoff[r["agent1"]][r["agent2"]].append(r["util1"])
        payoff[r["agent2"]][r["agent1"]].append(r["util2"])
    return payoff


def find_symmetric_nash(agents, payoff):
    """
    A symmetric Nash equilibrium is a strategy X such that, when the opponent
    plays X, no other strategy Y yields strictly higher utility than X itself.

    Formally: payoff[X][X] >= payoff[Y][X]  for all Y.
    """
    nash = []
    for x in agents:
        x_vs_x = mean(payoff[x][x])
        is_ne = True
        for y in agents:
            if y == x:
                continue
            y_vs_x = mean(payoff[y][x])
            if y_vs_x > x_vs_x + 1e-9:
                is_ne = False
                break
        if is_ne:
            nash.append(x)
    return nash


def domain_type(domain_name: str) -> str:
    """Map a domain name to a human-readable category."""
    n = domain_name.lower()
    if "small" in n and "coop" in n:   return "Small / Cooperative"
    if "small" in n and "comp" in n:   return "Small / Competitive"
    if "med"   in n and "coop" in n:   return "Medium / Cooperative"
    if "med"   in n and "comp" in n:   return "Medium / Competitive"
    if "large" in n and "coop" in n:   return "Large / Cooperative"
    if "large" in n and "comp" in n:   return "Large / Competitive"
    return "Other"


def analyze(rows):
    agents = get_agent_order(rows)
    payoff = build_payoff_matrix(rows, agents)

    utils_by_agent  = defaultdict(list)
    agree_by_agent  = defaultdict(list)
    util_on_agree   = defaultdict(list)

    for r in rows:
        for a, u in [(r["agent1"], r["util1"]), (r["agent2"], r["util2"])]:
            utils_by_agent[a].append(u)
            agree_by_agent[a].append(1 if r["agreement"] else 0)
            if r["agreement"]:
                util_on_agree[a].append(u)

    # ------------------------------------------------------------------ #
    # 1. Summary table
    # ------------------------------------------------------------------ #
    col_w = 20
    header = (f"{'Agent':<{col_w}} {'Score':>8} {'StdErr':>8} "
              f"{'UtilOnAgr':>10} {'AgreeRate':>10} {'N':>6}")
    print("\n" + "=" * len(header))
    print("TOURNAMENT RESULTS")
    print("=" * len(header))
    print(header)
    print("-" * len(header))

    scores = {}
    for a in agents:
        sc  = mean(utils_by_agent[a])
        se  = stderr(utils_by_agent[a])
        uoa = mean(util_on_agree[a])
        ar  = mean(agree_by_agent[a])
        n   = len(utils_by_agent[a])
        scores[a] = sc
        print(f"{a:<{col_w}} {sc:>8.4f} {se:>8.4f} {uoa:>10.4f} {ar:>10.4f} {n:>6}")

    print("=" * len(header))

    # ------------------------------------------------------------------ #
    # 2. Payoff matrix
    # ------------------------------------------------------------------ #
    col = 14
    nash_agents = find_symmetric_nash(agents, payoff)

    print(f"\nPAYOFF MATRIX  (row agent's mean utility vs column agent)")
    if nash_agents:
        print(f"  Symmetric Nash equilibria: {', '.join(nash_agents)}  [marked with *]")
    else:
        print("  No symmetric Nash equilibrium found.")

    header2 = " " * col + "".join(
        f"{(a[:col-2] + ('*' if a in nash_agents else ' ')):>{col}}"
        for a in agents
    )
    print(header2)
    print("-" * len(header2))
    for a in agents:
        marker  = "*" if a in nash_agents else " "
        row_str = f"{(a + marker):<{col}}"
        for b in agents:
            vals = payoff[a][b]
            cell = f"{mean(vals):.4f}" if vals else "—"
            # Bold diagonal with brackets
            if a == b:
                cell = f"[{cell}]"
            row_str += f"{cell:>{col}}"
        print(row_str)
    print()

    # ------------------------------------------------------------------ #
    # 3. Domain-type breakdown
    # ------------------------------------------------------------------ #
    print("DOMAIN-TYPE BREAKDOWN  (mean score per agent per domain category)")
    print("-" * 80)

    # Collect all domain categories present in the data
    categories = []
    seen_cats  = set()
    for r in rows:
        c = domain_type(r["domain"])
        if c not in seen_cats:
            categories.append(c)
            seen_cats.add(c)

    # Per agent × per category → list of utilities
    cat_utils = defaultdict(lambda: defaultdict(list))
    for r in rows:
        c = domain_type(r["domain"])
        cat_utils[r["agent1"]][c].append(r["util1"])
        cat_utils[r["agent2"]][c].append(r["util2"])

    cat_w = 22
    hdr = f"{'Agent':<{col_w}}" + "".join(f"{c[:cat_w-1]:>{cat_w}}" for c in categories)
    print(hdr)
    print("-" * len(hdr))
    for a in agents:
        row_str = f"{a:<{col_w}}"
        for c in categories:
            vals = cat_utils[a][c]
            row_str += f"{mean(vals):>{cat_w}.4f}" if vals else f"{'—':>{cat_w}}"
        print(row_str)
    print()

    # ------------------------------------------------------------------ #
    # 4. Ranking
    # ------------------------------------------------------------------ #
    ranked = sorted(agents, key=lambda a: scores[a], reverse=True)
    print("RANKING:")
    for i, a in enumerate(ranked, 1):
        ne_tag = "  ← Symmetric Nash Equilibrium" if a in nash_agents else ""
        print(f"  {i}. {a}  ({scores[a]:.4f}){ne_tag}")
    print()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_name = sys.argv[1]
    else:
        csv_files = sorted(glob.glob("*.csv"), key=os.path.getmtime, reverse=True)
        if not csv_files:
            print("No CSV file found. Run tournament.py first.")
            sys.exit(1)
        file_name = csv_files[0]
        print(f"Using most recent results file: {file_name}")

    rows = load_results(file_name)
    if not rows:
        print("No data rows found in the CSV.")
        sys.exit(1)

    print(f"Loaded {len(rows)} negotiation results.")
    analyze(rows)
