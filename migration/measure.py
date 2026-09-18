# 로컬 서버(http://127.0.0.1:8766)에 올린 투표 사이트 index.html 의 체감 속도·동작을 잰다.
#  ① 열자마자 표 표시(캐시 없음/있음)  ② 두 창 실시간 반영  ③ 「입력 완료」 후 표시까지
#  ④ 참석 불가 저장  ⑤ 멤버 추가·삭제 후 다른 창 반영·표 제거  ⑥ 콘솔 오류
# 시험 저장은 TEST_MEMBER 로 하고 끝나면 원래대로 되돌린다. 시험 멤버는 TEST_NEW 로 추가했다가 지운다.
import sys, time, json, urllib.request, urllib.parse
from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8766/index.html'
RTDB = 'https://ai-study-crew-lunch-aec4d-default-rtdb.asia-southeast1.firebasedatabase.app'
TEST_MEMBER = '황성욱'
TEST_NEW = '시험멤버'

INIT_JS = """
window.__t0 = performance.now();
window.__firstData = null;
const obs = new MutationObserver(() => {
  const el = document.getElementById('scheduleTableContainer');
  if (el && el.querySelector('.check-yes') && window.__firstData === null) window.__firstData = performance.now() - window.__t0;
});
document.addEventListener('DOMContentLoaded', () => {
  if (document.querySelector('#scheduleTableContainer .check-yes') && window.__firstData === null) window.__firstData = performance.now() - window.__t0;
  obs.observe(document.body, { childList: true, subtree: true, characterData: true });
});
"""

def week_id():
    import datetime as dt
    today = dt.date.today(); mon = today - dt.timedelta(days=today.weekday())
    y, w, _ = mon.isocalendar(); return f"{y}-W{w:02d}"

def q(path): return '/'.join(urllib.parse.quote(p) for p in path.split('/'))
def rest(path):
    with urllib.request.urlopen(f"{RTDB}/{q(path)}.json", timeout=20) as r: return json.loads(r.read().decode())

def open_page(ctx, clear_cache):
    page = ctx.new_page()
    page.on('dialog', lambda d: d.accept())
    page.add_init_script(INIT_JS)
    if clear_cache:
        page.goto(URL); page.evaluate("localStorage.clear()")
    page.goto(URL)
    page.wait_for_function("window.__firstData !== null", timeout=15000)
    return page, page.evaluate("window.__firstData")

def row_text(page, name):
    return page.evaluate("(n) => { const tr=[...document.querySelectorAll('.schedule-table tbody tr')].find(t=>t.querySelector('td strong')?.textContent===n); return tr ? tr.innerText.split(String.fromCharCode(10)).join(' ').split(String.fromCharCode(9)).join(' ') : null }", name)

wk = week_id()
before = rest(f"study/{wk}")
errors = []
with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context()
    a, cold = open_page(ctx, clear_cache=True)
    print(f"① 첫 방문(캐시 없음) 표 표시: {cold:.0f} ms")
    a.close()
    a, warm = open_page(ctx, clear_cache=False)
    print(f"① 재방문(캐시 있음) 표 표시: {warm:.0f} ms")
    a.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
    b, _ = open_page(ctx, clear_cache=False)
    b.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
    time.sleep(1)

    # ③ A 창에서 TEST_MEMBER 가 수·금 선택 → 입력 완료 → A 표 갱신까지 / ② B 창 반영까지
    a.click(f".member-card:has-text('{TEST_MEMBER}')")
    a.click(".date-card:nth-child(1)"); a.click(".date-card:nth-child(3)")
    t0 = time.time(); a.click("#submitBtn")
    a.wait_for_function(f"() => {{ const r = [...document.querySelectorAll('.schedule-table tbody tr')].find(t=>t.querySelector('td strong')?.textContent==='{TEST_MEMBER}'); return r && r.querySelectorAll('.check-yes').length===2 }}", timeout=10000)
    print(f"③ 입력 완료 → 내 창 표시: {(time.time()-t0)*1000:.0f} ms")
    t0 = time.time()
    b.wait_for_function(f"() => {{ const r = [...document.querySelectorAll('.schedule-table tbody tr')].find(t=>t.querySelector('td strong')?.textContent==='{TEST_MEMBER}'); return r && r.querySelectorAll('.check-yes').length===2 }}", timeout=10000)
    print(f"② 다른 창 반영: {(time.time()-t0)*1000:.0f} ms  (B 창 행: {row_text(b, TEST_MEMBER)})")
    d = rest(f"study/{wk}"); print("   DB:", {k: d['availability'][k].get(TEST_MEMBER) for k in d.get('availability', {})}, "submitted:", d.get('submitted', {}).get(TEST_MEMBER))

    # ④ 참석 불가 저장
    a.click(f".member-card:has-text('{TEST_MEMBER}')"); a.click("#unavailableCard"); t0 = time.time(); a.click("#submitBtn")
    b.wait_for_function(f"() => {{ const r = [...document.querySelectorAll('.schedule-table tbody tr')].find(t=>t.querySelector('td strong')?.textContent==='{TEST_MEMBER}'); return r && r.querySelectorAll('.check-yes').length===0 && r.querySelectorAll('.check-no').length===3 }}", timeout=10000)
    print(f"④ 참석 불가 저장 → 다른 창 반영: {(time.time()-t0)*1000:.0f} ms  (B 창 행: {row_text(b, TEST_MEMBER)})")
    d = rest(f"study/{wk}"); print("   DB availability 에 있음:", any(TEST_MEMBER in d['availability'].get(k, {}) for k in d.get('availability', {})), "/ submitted:", d.get('submitted', {}).get(TEST_MEMBER))

    # ⑤ 멤버 추가 → B 창 반영 → 시험멤버로 표 저장 → 삭제 → B 창에서 사라지고 DB 표도 제거
    a.click("button:has-text('멤버 관리')"); a.fill("#newMemberInput", TEST_NEW); t0 = time.time(); a.click("button:has-text('추가')")
    b.wait_for_selector(f".member-card:has-text('{TEST_NEW}')", timeout=10000)
    print(f"⑤ 멤버 추가 → 다른 창 반영: {(time.time()-t0)*1000:.0f} ms")
    a.click("#manageModal button:has-text('닫기')")
    a.click(f".member-card:has-text('{TEST_NEW}')"); a.click(".date-card:nth-child(2)"); a.click("#submitBtn")
    b.wait_for_function(f"() => {{ const r = [...document.querySelectorAll('.schedule-table tbody tr')].find(t=>t.querySelector('td strong')?.textContent==='{TEST_NEW}'); return r && r.querySelectorAll('.check-yes').length===1 }}", timeout=10000)
    print("   시험멤버 표 저장 확인(DB):", rest(f"study/{wk}/availability/thu/{TEST_NEW}"), rest(f"study/{wk}/submitted/{TEST_NEW}"))
    a.click("button:has-text('멤버 관리')"); t0 = time.time()
    a.click(f".modal-member-item:has-text('{TEST_NEW}') button")
    b.wait_for_function(f"() => ![...document.querySelectorAll('.member-card .member-name')].some(e=>e.textContent==='{TEST_NEW}') && ![...document.querySelectorAll('.schedule-table td strong')].some(e=>e.textContent==='{TEST_NEW}')", timeout=10000)
    print(f"   멤버 삭제 → 다른 창 반영: {(time.time()-t0)*1000:.0f} ms")
    time.sleep(1)
    print("   삭제 후 DB 표 남음?:", rest(f"study/{wk}/availability/thu/{TEST_NEW}"), rest(f"study/{wk}/submitted/{TEST_NEW}"), "/ members:", rest("members"))
    time.sleep(1)
    print("⑥ 콘솔 오류:", errors if errors else "없음")
    browser.close()

# 되돌리기: TEST_MEMBER 의 표를 시험 전 상태로
import urllib.request as u
def put(path, val):
    req = u.Request(f"{RTDB}/{q(path)}.json", data=json.dumps(val).encode(), method='PUT', headers={'Content-Type': 'application/json'})
    with u.urlopen(req, timeout=20) as r: return r.status
for k in ['wed', 'thu', 'fri']:
    put(f"study/{wk}/availability/{k}/{TEST_MEMBER}", (before.get('availability') or {}).get(k, {}).get(TEST_MEMBER))
put(f"study/{wk}/submitted/{TEST_MEMBER}", (before.get('submitted') or {}).get(TEST_MEMBER))
after = rest(f"study/{wk}")
print("되돌리기 후 DB == 시험 전:", after == before)
