# -*- coding: utf-8 -*-
"""
AI Dev Radar · 数据更新脚本
拉取最新数据 → 归一化 → 影响判断 → 生成 data.js

用法（需要本机代理，因为要访问 models.dev / GitHub / 官方状态页）：
    python refresh.py

数据源：
    - https://models.dev/api.json                      模型库 + 价格
    - tokencanopy/price  data/history/price_changes.csv 价格变化历史
    - OpenAI / Anthropic 官方状态页                     实时状态
"""
import json, csv, sys, os, re, urllib.request, collections

sys.stdout.reconfigure(encoding='utf-8')
csv.field_size_limit(10**9)
BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, 'raw')
os.makedirs(RAW, exist_ok=True)

# 代理为可选：
#   · 本地跑（国内网络）→ 需要代理，默认 127.0.0.1:7890
#   · GitHub Actions 跑（海外机房）→ 直连，用 RADAR_PROXY='' 关闭代理
PROXY = os.environ.get('RADAR_PROXY', 'http://127.0.0.1:7890').strip()
if PROXY:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY}))
    print(f'· 使用代理 {PROXY}')
else:
    opener = urllib.request.build_opener()
    print('· 直连模式（未使用代理）')
opener.addheaders = [('User-Agent', 'Mozilla/5.0 AI-Dev-Radar/1.0')]


def fetch(url, dst=None, label=''):
    """下载；成功返回 bytes，失败返回 None"""
    try:
        with opener.open(url, timeout=300) as r:
            data = r.read()
        if dst:
            open(dst, 'wb').write(data)
        print(f'  ✓ {label or url}  {len(data)/1024/1024:.2f} MB')
        return data
    except Exception as e:
        print(f'  ✗ {label or url}  失败: {e}')
        return None


# 严格模式：抓取失败即退出非零（供 CI 使用，避免静默沿用旧数据）
STRICT = os.environ.get('RADAR_STRICT', '').strip() in ('1', 'true', 'yes')


print('=' * 60)
print('[1/4] 拉取数据源')

models_path = os.path.join(RAW, 'models.json')
changes_path = os.path.join(RAW, 'price_changes.csv')

md = fetch('https://models.dev/api.json', models_path, 'models.dev 模型库')
if md is None:
    if STRICT:
        print('  ✗ 严格模式：models.dev 抓取失败，终止'); sys.exit(1)
    if os.path.exists(models_path):
        print('  · 使用本地缓存的 models.json')
        md = open(models_path, 'rb').read()

cd = fetch('https://raw.githubusercontent.com/tokencanopy/price/main/data/history/price_changes.csv',
           changes_path, 'tokencanopy 价格变化')
if cd is None:
    if STRICT:
        print('  ✗ 严格模式：价格变化数据抓取失败，终止'); sys.exit(1)
    if os.path.exists(changes_path):
        print('  · 使用本地缓存的 price_changes.csv')

if not os.path.exists(models_path) or not os.path.exists(changes_path):
    print('缺少必要数据源，退出'); sys.exit(1)

# 状态页
print('\n[2/4] 拉取官方状态页')
status_services = []
STATUS_SRC = [
    ('OpenAI', 'https://status.openai.com/api/v2/summary.json'),
    ('Claude', 'https://status.claude.com/api/v2/summary.json'),
]
for name, url in STATUS_SRC:
    raw = fetch(url, None, f'{name} 状态页')
    if not raw:
        continue
    try:
        s = json.loads(raw)
        comps = s.get('components', [])
        bad = [c for c in comps if c.get('status') not in ('operational', None)]
        st = 'ok' if not bad else ('degraded' if len(bad) < 3 else 'bad')
        status_services.append({
            'n': name, 'st': st,
            'label': (s.get('status') or {}).get('description') or '—',
            'comps': len(comps), 'bad': len(bad),
            'inc': [{'t': i.get('name'), 's': i.get('status'), 'd': (i.get('created_at') or '')[:10]}
                    for i in (s.get('incidents') or [])[:5]],
        })
    except Exception as e:
        print(f'  ✗ 解析 {name} 失败: {e}')

# ============ 归一化 ============
print('\n[3/4] 归一化 + 影响判断')

def nkey(s):
    s = (s or '').lower()
    s = re.sub(r'^[^/]+/', '', s)
    return re.sub(r'[^a-z0-9]', '', s)

MAJOR = ('openai','anthropic','google','deepseek','xai','meta','mistral','alibaba',
         'moonshot','zhipu','minimax','cohere','amazon','microsoft','nvidia',
         'openrouter','groq','together','fireworks','perplexity','baidu','tencent','stepfun','reka')

def impact(pct, plat, metric, up):
    a = abs(pct)
    if a >= 300:   s = 55
    elif a >= 100: s = 46
    elif a >= 50:  s = 36
    elif a >= 20:  s = 22
    elif a >= 10:  s = 11
    else:          s = 4
    s += 15 if up else 7
    pk = (plat or '').lower().replace(' ', '')
    if any(m in pk for m in MAJOR):
        s += 18
    if metric in ('input', 'output'):
        s += 6
    return ('high' if s >= 62 else 'mid' if s >= 42 else 'low'), s

raw_rows = []
with open(changes_path, encoding='utf-8') as f:
    for r in csv.DictReader(f):
        o, n = r['old_usd_per_1m'], r['new_usd_per_1m']
        if not o or not n:
            continue
        try:
            fo, fn = float(o), float(n)
        except ValueError:
            continue
        if fo == fn or fo <= 0:
            continue
        raw_rows.append((r['observed_at'][:10], r['platform'], r['model_key'],
                         r['model_name'], r['metric'], fo, fn))
print(f'  变化事件: {len(raw_rows)}')

dates = sorted({x[0] for x in raw_rows})
plats = sorted({x[1] for x in raw_rows})
metrics = ['input', 'output', 'cache_read', 'cache_write']
di = {d: i for i, d in enumerate(dates)}
pi = {p: i for i, p in enumerate(plats)}
mi = {m: i for i, m in enumerate(metrics)}
LI = {'high': 0, 'mid': 1, 'low': 2}

changes = []
for d, p, k, name, mt, fo, fn in raw_rows:
    pct = round((fn - fo) / fo * 100, 1)
    lvl, sc = impact(pct, p, mt, fn > fo)
    changes.append([di[d], pi[p], k, name, mi.get(mt, 0), round(fo, 5), round(fn, 5), pct, LI[lvl], sc, nkey(k)])
changes.sort(key=lambda x: (x[0], x[9]))

def kind_of(mid, name, family):
    s = (mid + ' ' + (name or '') + ' ' + (family or '')).lower().replace('_', '-')
    if 'embed' in s: return 1
    if 'rerank' in s: return 2
    if (re.search(r'(^|[^a-z])(asr|stt|tts)([^a-z]|$)', s)
        or any(k in s for k in ('whisper','voxtral','parakeet','canary','sensevoice','cosyvoice',
                                'sovits','speech','voice','audio','transcrib','kokoro','f5-tts'))): return 3
    if any(k in s for k in ('image','dall-e','dalle','flux','stable-diffusion','imagen','kolors',
                            'seedream','gpt-image','nano-banana','midjourney','sd3','sdxl')): return 4
    if any(k in s for k in ('video','veo','sora','wan2','kling','runway','hailuo','pika','seedance')): return 5
    if any(k in s for k in ('moderation','guard','safety','shieldgemma')): return 6
    return 0

KINDS = ['chat','embed','rerank','audio','image','video','guard']

models_raw = json.loads(md.decode('utf-8'))
provs, provnames, prov_i, mods = [], [], {}, []
for pid, p in models_raw.items():
    for mid, m in (p.get('models') or {}).items():
        c = m.get('cost') or {}
        if not c.get('input') and not c.get('output'):
            continue
        if pid not in prov_i:
            prov_i[pid] = len(provs); provs.append(pid); provnames.append(p.get('name') or pid)
        lim = m.get('limit') or {}
        mds = ','.join((m.get('modalities') or {}).get('input') or [])
        mods.append([prov_i[pid], mid, m.get('name') or mid,
                     c.get('input') or 0, c.get('output') or 0, c.get('cache_read') or 0,
                     lim.get('context') or 0, lim.get('output') or 0,
                     m.get('release_date') or '',
                     1 if m.get('reasoning') else 0, 1 if m.get('tool_call') else 0,
                     1 if m.get('open_weights') else 0, mds,
                     kind_of(mid, m.get('name'), m.get('family')), nkey(mid)])
mods.sort(key=lambda x: (x[13] != 0, x[3] if x[3] else 9e9))
print(f'  模型: {len(mods)}  provider: {len(provs)}')
print('  影响分布:', collections.Counter(x[8] for x in changes))

# ============ 输出 ============
print('\n[4/4] 生成 data.js')
payload = {
    'meta': {'built': __import__('datetime').date.today().isoformat(),
             'dateMin': dates[0], 'dateMax': dates[-1],
             'nChanges': len(changes), 'nModels': len(mods), 'nProvs': len(provs),
             'sources': ['models.dev', 'tokencanopy/price']},
    'dates': dates, 'plats': plats, 'metrics': metrics, 'kinds': KINDS,
    'provs': provs, 'provnames': provnames,
    'changes': changes, 'models': mods,
}
status = {'fetched': __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M'),
          'services': status_services}

dst = os.path.join(BASE, 'data.js')
with open(dst, 'w', encoding='utf-8') as f:
    f.write('window.__RADAR__=' + json.dumps(payload, ensure_ascii=False, separators=(',', ':')) + ';')
    f.write('\nwindow.__STATUS__=' + json.dumps(status, ensure_ascii=False, separators=(',', ':')) + ';')
print(f'  ✓ data.js  {os.path.getsize(dst)/1024/1024:.2f} MB')
print(f'  数据范围: {dates[0]} → {dates[-1]}')
print('\n完成。刷新 index.html 即可看到最新数据。')
