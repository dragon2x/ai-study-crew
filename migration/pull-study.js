// 기존 Apps Script 에서 주차별 투표 데이터(availability·submittedMembers·members)를 받아 study.json 으로 저장
// (점심 앱 migration/pull.js 를 본뜸. 2026-09-18 Firebase 이전용)
const URL = 'https://script.google.com/macros/s/AKfycbz2CCEL-5_-BHuSrVxEzSyQGmoFEfXyPGniQ_spVDmeBmtxoBajTboZuo_xK9ngyHIv7A/exec';
const fs = require('fs');
const weeks = [];
for (let w = 10; w <= 40; w++) weeks.push('2026-W' + String(w).padStart(2, '0'));
(async () => {
  const out = {}; let members = null;
  // 한꺼번에 부르면 Apps Script 가 HTML 오류 페이지를 줄 때가 있어 한 주씩, 실패하면 3번까지 다시 시도한다.
  async function load(weekId) {
    for (let i = 0; i < 3; i++) {
      try { const r = await fetch(URL + '?action=load&weekId=' + weekId); return await r.json(); }
      catch (e) { console.error(weekId, 'retry', i + 1, String(e).slice(0, 60)); await new Promise(r => setTimeout(r, 2000)); }
    }
    throw new Error(weekId + ' 3회 실패');
  }
  for (const weekId of weeks) {
    const t0 = Date.now();
    const j = await load(weekId);
    if (!j.success) { console.error(weekId, 'FAIL', j.error); continue; }
    if (j.members) members = j.members;
    const av = j.availability || {}, sub = j.submittedMembers || {};
    let votes = 0; for (const d in av) votes += Object.values(av[d]).filter(Boolean).length;
    const nsub = Object.values(sub).filter(Boolean).length;
    if (votes || nsub) out[weekId] = { availability: av, submittedMembers: sub };
    console.log(weekId, 'votes', votes, 'submitted', nsub, (Date.now() - t0) + 'ms');
  }
  fs.writeFileSync(__dirname + '/study.json', JSON.stringify({ members, study: out }, null, 2));
  let tv = 0, ts = 0;
  for (const w in out) { for (const d in out[w].availability) tv += Object.values(out[w].availability[d]).filter(Boolean).length; ts += Object.values(out[w].submittedMembers).filter(Boolean).length; }
  console.log('weeks:', Object.keys(out).sort().join(', '), '\ntotal votes:', tv, '\ntotal submitted:', ts, '\nmembers:', JSON.stringify(members));
})();
