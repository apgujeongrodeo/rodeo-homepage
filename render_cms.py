import html,json,re
from collections import defaultdict
from pathlib import Path
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
    return f'<details><summary>{esc(row["title"])}</summary><div class="reading">{picture(row)}{paragraphs(row["body"])}</div></details>'
def service(row):
    title=esc(row['title'])
    return (f'<article class="detail-card"><h2>{title}</h2>'
            f'<p><strong>이런 분께</strong> {esc(row["audience"])}</p>'
            f'<p><strong>함께 확인</strong> {esc(row["check"])}</p>'
            f'<p><strong>상담 준비</strong> {esc(row["prepare"])}</p>'
            f'<a class="btn" href="{inquiry(row["title"])}">{title} 문의</a></article>')
def project(row):
    poster=asset(row.get('poster'))
    button=f'<a class="btn alt" href="{poster}" target="_blank" rel="noopener">기존 매물 포스터 열기</a>' if poster else ''
    return (f'<article class="split detail-card">{picture(row)}<div><h2>{esc(row["title"])}</h2>'
            f'{paragraphs(row["body"])}<div class="actions">{button}'
            f'<a class="btn" href="{inquiry(row["category"])}">비슷한 조건 상담하기</a></div></div></article>')
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
for name, renderer, rows in [('services',service,services),('insights',insight,read_rows('insights')),('projects',project,read_rows('projects'))]:
    path=ROOT/'dist'/name/'index.html'
    updates[path]=render_section(path.read_text(encoding='utf8'),'\n'+ '\n'.join(map(renderer,rows))+'\n')
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

