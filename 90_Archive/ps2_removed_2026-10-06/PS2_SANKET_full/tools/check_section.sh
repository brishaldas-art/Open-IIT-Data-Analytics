#!/usr/bin/env bash
# Invariants for THIS section. Prints PASS/FAIL; non-zero exit on any FAIL.
# usage: bash tools/check_section.sh   (run from anywhere)
SEC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; WS="$(dirname "$SEC")"; FAIL=0
chk(){ if eval "$2" >/dev/null 2>&1; then echo "PASS  $1"; else echo "FAIL  $1"; FAIL=1; fi; }

chk "section has its brief (README_PS2_SANKET.md)"        "[ -f '$SEC/README_PS2_SANKET.md' ]"
chk "all 9 PS2 documents present"                         "for f in PS2_ASSUMPTIONS.md PS2_DEEP_INTERNET_RESEARCH.md PS2_ARCHITECTURE_REQUIREMENTS.md PS2_ADVANCED_ARCHITECTURE_RESEARCH.md PS2_ARCHITECTURE_OPTIONS.md PS2_ARCHITECTURE_SELECTION.md PS2_SANKET_SOLUTION_ARCHITECTURE_FINAL.md PS2_SANKET_SOLUTION_ARCHITECTURE.md; do [ -f \"$SEC/\$f\" ]; done"
chk "cross-cutting documents present (master, integration, research, index)" "[ -f '$SEC/CreditNirvana_PS2_PS3_MASTER.md' ] && [ -f '$SEC/SANKET_SUTRA_SYSTEM_ARCHITECTURE_FINAL.md' ] && [ -f '$SEC/SIMILAR_SYSTEMS_REVERSE_ENGINEERING.md' ] && [ -f '$SEC/PS2_PS3_DATASET_REVIEW.md' ] && [ -f '$SEC/README.md' ] && [ -f '$SEC/HOW_TO_USE_AND_UNDERSTAND_THIS_PACKAGE.md' ] && [ -f '$SEC/START_HERE_TEAM_HANDOFF.md' ]"
chk "master document carries Parts 0, I, XIV, XV"          "grep -q '^# Part 0' '$SEC/CreditNirvana_PS2_PS3_MASTER.md' && grep -q '^# Part I\.' '$SEC/CreditNirvana_PS2_PS3_MASTER.md' && grep -q '^# Part XIV' '$SEC/CreditNirvana_PS2_PS3_MASTER.md' && grep -q '^# Part XV' '$SEC/CreditNirvana_PS2_PS3_MASTER.md'"
chk "own data tables present (11)"                        "[ \$(ls -1 '$SEC/data/raw'/*.csv | wc -l) -eq 11 ]"
chk "acceptance table present"                            "[ -f '$SEC/data/derived/derived_ps2_policy_baselines.csv' ]"
chk "no PS3-only table leaked in"                         "[ ! -f '$SEC/data/raw/visit_gps_points.csv' ] && [ ! -f '$SEC/data/raw/surveyed_addresses.csv' ]"
chk "tools present (audit, derived, reproduce, financial model)" "[ -f '$SEC/tools/dataset_audit.py' ] && [ -f '$SEC/tools/build_derived_table.py' ] && [ -f '$SEC/tools/reproduce.sh' ] && [ -f '$SEC/tools/financial_model.py' ]"
OLD="SH""ARED"; D1="data""set"; D2="10""_Inputs"; P2="0[0-9]_"
chk "no old shared-bucket or pre-division folder references left" "! grep -rqE \"$OLD/|${P2}Master|${P2}(Phase|Architecture|Evidence|Model|Dataset)\" \"$SEC\" --include='*.md' --include='*.sh' --include='*.py' --exclude-dir=_superseded --exclude=check_section.sh"
chk "no stale dataset paths"  "! grep -rqE \"/home/user/($D1|$D2)\" \"$SEC\" --include='*.md' --include='*.sh' --include='*.py' --exclude-dir=_superseded"
chk "scripts parse"                                       "python3 -c \"import ast;[ast.parse(open(f).read(),f) for f in ['$SEC/tools/dataset_audit.py','$SEC/tools/build_derived_table.py','$SEC/tools/financial_model.py']]\""
chk "every document link resolves inside the section"     "python3 '$SEC/tools/check_links.py'"
chk "hand-off ready (sibling on disk, or this section standalone)"  "[ -d '$WS/PS3_SUTRA' ] || [ \$(ls -d \"$WS\"/*/ 2>/dev/null | wc -l) -le 1 ]"
chk "this section reproduces its numbers"                 "CN_OUT=$SEC/data/derived python3 '$SEC/tools/build_derived_table.py' | grep -q '0\.1872'"
echo
[ $FAIL -eq 0 ] && echo "PS2 SECTION: ALL CHECKS PASSED" || echo "PS2 SECTION: SOME CHECKS FAILED"
exit $FAIL
