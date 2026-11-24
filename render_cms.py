import html,json,re
from collections import defaultdict
from pathlib import Path
from datetime import datetime, date, timedelta, timezone
from urllib.parse import urlencode
ROOT=Path(__file__).resolve().parent
def esc(value):
    return html.escape(str(value),quote=True)
def paragraphs(body):
    return ''.join(f'<p>{esc(p).replace(chr(10),"<br>")}</p>' for p in body.strip().split('\n\n') if p.strip())
def asset(value):
    if not value:
        return ''
    if not re.fullmatch(r'/[\w./% -]+', value) or value.startswith('//') or '..' in value.split('/'):
        raise ValueError(f'Invalid media path: {value}')
    if not (ROOT/'dist'/value.lstrip('/')).is_file():
        raise ValueError(f'Missing media: {value}')
    return esc(value)
def picture(row):
    src=asset(row.get('image'))
    if not src:
        return ''
    alt=esc(row.get('alt') or row['title'])
    caption=esc(row.get('caption',''))
    return f'<figure class="detail-figure"><img loading="lazy" src="{src}" alt="{alt}"><figcaption>{caption}</figcaption></figure>'
def inquiry(category):
    return esc('/contact/?'+urlencode({'service': category}))
def insight(row):
    published = row.get("published")
    meta = ""
    if published:
        stamp = date.fromisoformat(published[:10])
        today = datetime.now(timezone(timedelta(hours=9))).date()
        badge = '<b class="board-new">NEW</b>' if 0 <= (today-stamp).days <= 7 else ''
        meta = f'<time datetime="{stamp}">{stamp:%Y.%m.%d}</time>{badge}'
    source = row.get("source", "")
    source_link = f'<p><a href="{esc(source)}">원문 보기</a></p>' if re.fullmatch(r'https://[^\s]+', source) else ""
    return (f'<details class="board-post"><summary><span>{esc(row["title"])}</span>{meta}</summary>'
            f'<div class="reading">{picture(row)}{paragraphs(row["body"])}{source_link}</div></details>')

def insight_board(rows):
    sections = []
    categories = (("market", "로데오 상권 노트"), ("news", "부동산 NEWS"))
    for key, label in categories:
        posts = [row for row in rows if row.get("category", "market") == key]
        posts.sort(key=lambda row: row.get("published") or "", reverse=True)
        body = "".join(map(insight, posts))
        if not body:
            body = '<p class="board-empty">등록된 소식이 없습니다.</p>'
        sections.append(f'<section class="board-section" id="{key}"><h2>{label}</h2>{body}</section>')
    return "".join(sections)

def faq_board(rows):
    posts = [row for row in rows if row.get("category") == "faq"]
    return '<section class="board-section" id="faq"><h2>자주 묻는 질문</h2>' + "".join(map(insight, posts)) + '</section>'

def public_questions():
    snapshot = ROOT / "questions_snapshot.json"
    if not snapshot.exists():
        return '<p class="board-empty">최신 질문은 더 보기에서 확인할 수 있습니다.</p>'
    rows = json.loads(snapshot.read_text(encoding="utf8"))[:10]
    if not rows:
        return '<p class="board-empty">아직 공개 질문이 없습니다.</p>'
    posts = []
    for row in rows:
        url = row["url"]
        if not re.fullmatch(r"https://github\.com/apgujeongrodeo/rodeo-homepage/discussions/[0-9]+", url):
            continue
        stamp = datetime.fromisoformat(row["createdAt"].replace("Z", "+00:00")).astimezone(timezone(timedelta(hours=9))).date()
        posts.append(f'<li class="board-post"><a href="{esc(url)}">{esc(row["title"])}</a> '
                     f'<time datetime="{stamp}">{stamp:%Y.%m.%d}</time> '
                     f'<span class="board-replies">댓글 {int(row["comments"]["totalCount"])}</span></li>')
    return '<ul class="public-questions">' + "".join(posts) + '</ul>'

def service(row):
    title=esc(row['title'])
    return (f'<article class="detail-card"><h2>{title}</h2>'
            f'<p><strong>이런 분께</strong> {esc(row["audience"])}</p>'
            f'<p><strong>함께 확인</strong> {esc(row["check"])}</p>'
            f'<p><strong>상담 준비</strong> {esc(row["prepare"])}</p>'
            f'<a class="btn" href="{inquiry(row["title"])}">{title} 문의</a></article>')
def project(row, listing=False):
    poster=asset(row.get('poster'))
    button=f'<a class="btn alt" href="{poster}" target="_blank" rel="noopener">기존 매물 포스터 열기</a>' if poster else ''
    return (f'<article class="split detail-card">{picture(row)}<div><h2>{esc(row["title"])}</h2>'
            f'{paragraphs(row["body"])}<div class="actions">{button}'
            f'<a class="btn" href="{inquiry(row["category"])}">{("이 매물 상담하기" if listing else "비슷한 조건 상담하기")}</a></div></div></article>')
def read_rows(name):
    records=[(p.name,json.loads(p.read_text(encoding='utf-8-sig'))) for p in (ROOT/'content'/name).glob('*.json')]
    return [row for _,row in sorted(records,key=lambda item:(item[1].get('order') or 0,item[0]))]
def render_section(source,markup):
    before,mark,rest=source.partition('<!-- cms:start -->')
    _,end,after=rest.partition('<!-- cms:end -->')
    if not mark or not end:
        raise ValueError('CMS markers missing')
    return before+mark+markup+end+after
def render_history(rows):
    months = defaultdict(list)
    years = {2024, 2025, 2026}
    for row in rows:
        year, month = int(row["year"]), int(row["month"])
        if not 1982 <= year <= 2100 or not 1 <= month <= 12:
            raise ValueError("Invalid deal year or month")
        years.add(year)
        months[year, month].append(row)

    def deal(row):
        identity = " · ".join(esc(row[key]) for key in ("publicName", "publicAddress") if row.get(key))
        caption = f'<p>{identity}</p>' if identity else ""
        return (f'<article class="deal"><span>{esc(row["transaction"])} · {esc(row["use"])}'
                f' · {esc(row["industry"])}</span><h4>{esc(row["title"])}</h4>'
                f'<p>{esc(row["area"])}</p>{caption}</article>')

    panels = []
    for year in sorted(years, reverse=True):
        grid = []
        for month in range(12, 0, -1):
            entries = months[year, month]
            body = "".join(map(deal, entries)) if entries else '<p class="history-empty">공개 사례 없음</p>'
            grid.append(f'<div class="history-month"><h3>{month:02d}<span>월</span></h3>{body}</div>')
        panels.append(f'<details class="history-year"><summary><span>{year}</span><span class="history-toggle" aria-hidden="true"></span></summary>'
                      f'<div class="history-months">{"".join(grid)}</div></details>')
    return "".join(panels)

services=read_rows('services')
if len({r['title'] for r in services})!=len(services):
    raise ValueError('Service titles must be unique')
history_path=ROOT/'dist/about/index.html'
updates={history_path:render_section(history_path.read_text(encoding='utf8'),render_history(read_rows('deal-history')))}
for name, renderer, rows in [('services',service,services),('insights',insight,read_rows('insights')),('projects',project,read_rows('projects')),('listings',lambda row: project(row, listing=True),read_rows('listings')),('qa',insight,read_rows('insights'))]:
    path=ROOT/'dist'/name/'index.html'
    markup = insight_board(rows) if name == "insights" else "\n".join(map(renderer, rows))
    if name == "qa":
        markup = faq_board(rows)
    if name == "projects" and not rows:
        markup = '<p class="board-empty">공개할 계약 사례와 고객 인터뷰를 준비 중입니다.</p>'
    source = render_section(path.read_text(encoding='utf8'), "\n"+markup+"\n")
    if name == "qa":
        source = re.sub(r'(<!-- questions:start -->).*?(<!-- questions:end -->)',
                        lambda match: match[1]+public_questions()+match[2], source, flags=re.S)
    updates[path] = source
for name in ('index.html','contact/index.html'):
    path=ROOT/'dist'/name
    source=path.read_text(encoding='utf8')
    options='<option value="">선택해 주세요</option>'+''.join(f'<option>{esc(r["title"])}</option>' for r in services)
    updated,count=re.subn(r'(<select id="service" name="service" required>).*?(</select>)',lambda m:m[1]+options+m[2],source,flags=re.S)
    if count!=1:
        raise ValueError(f'Unexpected service selector in {name}')
    updates[path]=updated
for path,source in updates.items():
    path.write_text(source,encoding='utf8')

