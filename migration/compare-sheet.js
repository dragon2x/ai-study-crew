// 시트 「AI Study Crew Data」 스냅샷(sheet-study.txt, Drive 커넥터로 읽음)과 API 로 받은 study.json 을 주차별로 대조
const fs = require('fs');
const api = JSON.parse(fs.readFileSync(__dirname + '/study.json', 'utf8')).study;
const sheet = {};
for (const line of fs.readFileSync(__dirname + '/sheet-study.txt', 'utf8').split('\n')) {
  const c = line.split(' | ').map(s => s.replace(/^\| |\|$/g, '').trim());
  if (c.length < 4) continue;
  const [weekId, , av, sub] = c;
  const a = JSON.parse(av), s = JSON.parse(sub);
  let votes = 0; for (const d in a) votes += Object.values(a[d]).filter(Boolean).length;
  const nsub = Object.values(s).filter(Boolean).length;
  if (votes || nsub) sheet[weekId] = { votes, nsub, a, s };
}
const cnt = (w) => { const x = api[w]; if (!x) return [0, 0]; let v = 0; for (const d in x.availability) v += Object.values(x.availability[d]).filter(Boolean).length; return [v, Object.values(x.submittedMembers).filter(Boolean).length]; };
let ok = true, tv = 0, ts = 0;
for (const w of Object.keys(sheet).sort()) {
  const [v, n] = cnt(w); tv += sheet[w].votes; ts += sheet[w].nsub;
  const same = JSON.stringify(sheet[w].a) === JSON.stringify(api[w]?.availability) && JSON.stringify(sheet[w].s) === JSON.stringify(api[w]?.submittedMembers);
  if (v !== sheet[w].votes || n !== sheet[w].nsub || !same) ok = false;
  console.log(w, `sheet ${sheet[w].votes}/${sheet[w].nsub}`, `api ${v}/${n}`, same ? '내용 동일' : '★ 다름');
}
for (const w of Object.keys(api)) if (!sheet[w]) { ok = false; console.log(w, 'API 에만 있음'); }
console.log('시트 합계 votes', tv, 'submitted', ts, '/ 주차', Object.keys(sheet).length, '→', ok ? '모두 일치' : '불일치 있음');
