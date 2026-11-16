import json, urllib.request, re, html, datetime, pathlib, sys
PATH = pathlib.Path(__file__).resolve().parent / 'ratings.json'
DATA = json.loads(PATH.read_text(encoding='utf8')) if PATH.exists() else {}
HEADERS = {'User-Agent':'AyushPortfolioRatingUpdater/1.0 (public profile statistics)'}
NOW = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
def get(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers={**HEADERS, **(headers or {})})
    with urllib.request.urlopen(req, timeout=25) as response:
        return response.read().decode('utf8')
def leetcode():
    query='query userContestRankingInfo($username: String!) { userContestRanking(username: $username) { rating topPercentage badge { name } } }'
    body=json.dumps({'query':query,'variables':{'username':'Ayush_Pandey_'}}).encode()
    result=json.loads(get('https://leetcode.com/graphql/',body,{'Content-Type':'application/json','Referer':'https://leetcode.com/'}))['data']['userContestRanking']
    if not result or result['rating'] is None: raise ValueError('Missing contest ranking')
    badge=(result.get('badge') or {}).get('name')
    return {'rating':round(result['rating']),'percentile':result.get('topPercentage'),'badge':badge}
def atcoder():
    history=json.loads(get('https://atcoder.jp/users/Ayush216/history/json'))
    rated=[x for x in history if x.get('IsRated')]
    if not rated: raise ValueError('Missing rating history')
    result={'rating':int(rated[-1]['NewRating'])}
    try:
        page=get('https://atcoder.jp/users/Ayush216?lang=en')
        match=re.search(r'\b(\d+)\s*(Kyu|Dan)\b',html.unescape(re.sub(r'<[^>]*>',' ',page)),re.I)
        if match: result['badge']=match.group(1)+' '+match.group(2).lower()
    except Exception as exc: print('AtCoder rank unavailable:',exc)
    return result
def codechef():
    page=get('https://www.codechef.com/users/ayush216')
    rating=re.search(r'<div\s+class=["\']rating-number["\'][^>]*>\s*(\d+)',page,re.I)
    stars=re.search(r'<div\s+class=["\']rating-star["\'][^>]*>(.*?)</div>',page,re.I|re.S)
    if not rating: raise ValueError('Rating not found in profile')
    result={'rating':int(rating.group(1))}
    if stars:
        count=html.unescape(re.sub(r'<[^>]*>','',stars.group(1))).count('★')
        if 1 <= count <= 7: result['stars']=count
    return result
success=0
for name,fetch in [('leetcode',leetcode),('atcoder',atcoder),('codechef',codechef)]:
    try:
        value=fetch(); value['updated_at']=NOW; DATA[name]=value; success+=1
        print(name, 'updated:',value)
    except Exception as exc: print(name,'refresh failed; preserving previous data:',str(exc),file=sys.stderr)
if not DATA: raise SystemExit('No rating data available')
PATH.write_text(json.dumps(DATA,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
if not success: print('All requests failed; previous data retained',file=sys.stderr)
