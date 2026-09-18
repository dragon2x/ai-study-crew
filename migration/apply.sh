#!/bin/bash
# 대표님이 직접 실행하는 묶음: ① 보안 규칙 게시 ② 투표 데이터(study) 적재 ③ 멤버 목록(members) 적재 — 2026-09-18
export MSYS_NO_PATHCONV=1
P=ai-study-crew-lunch-aec4d
echo "== ① 규칙 게시 =="
(cd /c/Users/UOU/ai-study-crew-lunch && firebase deploy --only database --project $P) || { echo "규칙 게시 실패"; exit 1; }
echo "== ② study 적재 =="
firebase database:set --project $P -f /study "C:/Users/UOU/ai-study-crew/migration/rtdb-study.json" || { echo "study 적재 실패"; exit 1; }
echo "== ③ members 적재 =="
firebase database:set --project $P -f /members "C:/Users/UOU/ai-study-crew/migration/rtdb-members.json" || { echo "members 적재 실패"; exit 1; }
echo "== 확인 =="
curl -s "https://$P-default-rtdb.asia-southeast1.firebasedatabase.app/members.json"; echo
curl -s "https://$P-default-rtdb.asia-southeast1.firebasedatabase.app/study.json?shallow=true"; echo
echo "끝"
