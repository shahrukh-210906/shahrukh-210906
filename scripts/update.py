"""Fetch the public GitHub calendar and render self-contained animated SVG."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from datetime import date, timedelta
import json, html, re

ROOT=Path(__file__).resolve().parents[1]
USERNAME='shahrukh-210906'
class Calendar(HTMLParser):
    def __init__(self):
        super().__init__(); self.cells={}; self.tips={}; self.tip=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if a.get('data-date') and 'data-level' in a:
            self.cells[a['id']]={'date':a['data-date'],'level':int(a['data-level'])}
        if tag=='tool-tip': self.tip=a.get('for')
    def handle_data(self,data):
        if self.tip: self.tips[self.tip]=self.tips.get(self.tip,'')+data
    def handle_endtag(self,tag):
        if tag=='tool-tip': self.tip=None
def parse(source):
    p=Calendar(); p.feed(source); days=[]
    for ident,cell in p.cells.items():
        tip=p.tips.get(ident,''); match=re.search(r'([\d,]+) contribution',tip)
        if not tip or (not match and not tip.startswith('No contributions')):
            raise ValueError('GitHub calendar tooltip format changed')
        days.append(dict(cell,count=int(match[1].replace(',','')) if match else 0))
    days.sort(key=lambda d:d['date'])
    if len(days)<350: raise ValueError('Incomplete contribution calendar; preserving previous graph')
    return days
def render(days):
    first=date.fromisoformat(days[0]['date']); start=first-timedelta(days=(first.weekday()+1)%7)
    palette=['#161b22','#0e4429','#006d32','#26a641','#39d353']; total=sum(d['count'] for d in days)
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="860" height="230" viewBox="0 0 860 230" role="img">',f'<title>{total:,} contributions · {USERNAME} · {days[0]["date"]} to {days[-1]["date"]}</title>', '<style>text{font-family:Consolas,monospace}.day{animation:enter .4s both}@keyframes enter{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:translateY(0)}}@media(prefers-reduced-motion:reduce){.day{animation:none}}</style><rect width="860" height="230" rx="14" fill="#0d1117"/><rect x=".5" y=".5" width="859" height="229" rx="14" fill="none" stroke="#30363d"/>', '<text x="26" y="30" fill="#8b949e" font-size="12">PUBLIC CONTRIBUTIONS / LAST YEAR</text>']
    for label,row in [('Mon',1),('Wed',3),('Fri',5)]: parts.append(f'<text x="24" y="{65+row*16}" fill="#8b949e" font-size="10">{label}</text>')
    months=set()
    for d in days:
        current=date.fromisoformat(d['date']); offset=(current-start).days; col,row=divmod(offset,7); x=62+col*14.5; y=54+row*16
        if current.day<=7 and current.month not in months:
            months.add(current.month); parts.append(f'<text x="{x}" y="46" fill="#8b949e" font-size="10">{current:%b}</text>')
        parts.append(f'<rect class="day" style="animation-delay:{(col+row)*.018:.3f}s" x="{x}" y="{y}" width="11" height="12" rx="2" fill="{palette[min(d["level"],4)]}"><title>{d["date"]}: {d["count"]} contributions</title></rect>')
    parts.append(f'<text x="26" y="202" fill="#c9d1d9" font-size="13">{total:,} contributions in the last year</text><text x="600" y="202" fill="#8b949e" font-size="10">Less</text>')
    for i,c in enumerate(palette): parts.append(f'<rect x="{634+i*17}" y="191" width="12" height="12" rx="2" fill="{c}"/>')
    parts.append('<text x="727" y="202" fill="#8b949e" font-size="10">More</text></svg>')
    return ''.join(parts)
if __name__=='__main__':
    import sys
    source=Path(sys.argv[1]).read_text(encoding='utf-8') if len(sys.argv)>1 else urlopen(Request(f'https://github.com/users/{USERNAME}/contributions',headers={'User-Agent':'profile-art'}),timeout=30).read().decode()
    days=parse(source)
    (ROOT/'data').mkdir(exist_ok=True)
    (ROOT/'data/contributions.json').write_text(json.dumps({'username':USERNAME,'days':days},indent=2)+'\n',encoding='utf-8')
    (ROOT/'contrib-heatmap.svg').write_text(render(days),encoding='utf-8')
    print(f'Rendered {len(days)} days, {sum(d["count"] for d in days)} contributions')
