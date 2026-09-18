// pull-study.js 가 받은 study.json 을 Realtime Database 구조(study/{weekId}/{availability,submitted})로 변환
const fs = require('fs');
const src = JSON.parse(fs.readFileSync(__dirname + '/study.json', 'utf8'));
const study = {}; let votes = 0, subs = 0;
for (const [weekId, d] of Object.entries(src.study)) {
  const availability = {};
  for (const [day, byName] of Object.entries(d.availability || {})) {
    if (!['wed', 'thu', 'fri'].includes(day)) throw new Error(weekId + ' 이상한 요일 ' + day);
    for (const [name, v] of Object.entries(byName)) if (v) { (availability[day] ||= {})[name] = true; votes++; }
  }
  const submitted = {};
  for (const [name, v] of Object.entries(d.submittedMembers || {})) if (v) { submitted[name] = true; subs++; }
  study[weekId] = { availability, submitted };
}
fs.writeFileSync(__dirname + '/rtdb-study.json', JSON.stringify(study, null, 2));
console.log('weeks', Object.keys(study).length, 'votes', votes, 'submitted', subs, 'members(api)', JSON.stringify(src.members));
