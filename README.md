# AI Study Crew · 일정 조율

주간 모임 요일(수·목·금) 투표 사이트. GitHub Pages 로 배포된다: https://dragon2x.github.io/ai-study-crew/

- 데이터는 Firebase Realtime Database `study/{weekId}` 에 저장한다 (2026-09-18 Google Apps Script 에서 이전). 프로젝트는 점심 앱과 같은 `ai-study-crew-lunch-aec4d`.
- **보안 규칙은 점심 앱 저장소 `ai-study-crew-lunch/database.rules.json` 에 있다** (한 프로젝트 한 규칙).
- 멤버 목록 `members` 는 점심 앱과 공유한다.
- `migration/` 은 이전 때 쓴 스크립트(받아 둔 데이터 json 은 커밋하지 않는다).
