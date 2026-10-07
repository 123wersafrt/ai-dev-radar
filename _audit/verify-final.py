# -*- coding: utf-8 -*-
"""最终全量验收：所有前景/背景配对"""
import sys
sys.path.insert(0, 'C:/Users/15082/.workbuddy/skills/color-contrast-audit')
sys.stdout.reconfigure(encoding='utf-8')
from check import delta_e00, apca_lc
lc = lambda f, b: abs(apca_lc(f, b))

BG, PANEL, CARD, CARD2 = '#0f0d0b', '#191612', '#231f1a', '#2e2924'
LINE, LINE2 = '#423b34', '#544b41'
TX, TX2, TX3, TX4 = '#f3eee5', '#cec4b4', '#ab9e8c', '#a09484'
AMBER, AMBER2 = '#e8a951', '#f7cd7f'
RED, RED_LG, GREEN, GREEN_LG = '#ef8a6b', '#f5b39c', '#8cbd72', '#b3d89b'

pairs = []
def add(name, fg, bg, kind, need):
    pairs.append((name, fg, bg, kind, need))

# 文字层
for nm, c, need in [('tx',TX,75),('tx2',TX2,60),('tx3',TX3,45),('tx4',TX4,40)]:
    add(f'{nm} on card', c, CARD, 'Lc', need)
    add(f'{nm} on card2', c, CARD2, 'Lc', need)
    add(f'{nm} on bg', c, BG, 'Lc', need)
    add(f'{nm} on panel', c, PANEL, 'Lc', need)
# 强调色
add('amber on card', AMBER, CARD, 'Lc', 45)
add('amber on card2', AMBER, CARD2, 'Lc', 45)
add('amber2 on card', AMBER2, CARD, 'Lc', 60)
add('amber2 on card2', AMBER2, CARD2, 'Lc', 60)
add('amber2 on bg', AMBER2, BG, 'Lc', 60)
# 状态色（色条/色点）
for nm, c in [('red',RED),('green',GREEN)]:
    add(f'{nm} on card', c, CARD, 'Lc', 45)
    add(f'{nm} on card2', c, CARD2, 'Lc', 45)
# 大字
for nm, c in [('red-lg',RED_LG),('green-lg',GREEN_LG)]:
    add(f'{nm} on card', c, CARD, 'Lc', 60)
# 标签文字（在 card2 底上）
add('tag high 文字', RED_LG, CARD2, 'Lc', 60)
add('tag mid 文字', AMBER2, CARD2, 'Lc', 60)
add('tag low 文字', GREEN_LG, CARD2, 'Lc', 60)
# 涨跌幅 pill
add('up pill 内部', '#f8d5c8', '#43221b', 'Lc', 75)
add('down pill 内部', '#c9e4bd', '#22341f', 'Lc', 75)
add('up pill 底vs card', '#43221b', CARD, 'ΔE', 8)
add('down pill 底vs card', '#22341f', CARD, 'ΔE', 8)
# 描边
add('line vs card', LINE, CARD, 'ΔE', 8)
add('line vs bg', LINE, BG, 'ΔE', 8)
add('line vs panel', LINE, PANEL, 'ΔE', 8)
add('line2 vs card2', LINE2, CARD2, 'ΔE', 8)
# 并列语义色
add('amber vs red', AMBER, RED, 'ΔE', 8)
add('amber vs green', AMBER, GREEN, 'ΔE', 8)
add('red vs green', RED, GREEN, 'ΔE', 8)
add('red-lg vs green-lg', RED_LG, GREEN_LG, 'ΔE', 8)

fails = []
for name, fg, bg, kind, need in pairs:
    v = lc(fg, bg) if kind == 'Lc' else delta_e00(fg, bg)
    ok = v >= need
    if not ok: fails.append((name, v, need))
    print(f'  [{"PASS" if ok else "FAIL"}] {name:22} {kind} {v:6.1f} 需{need}')

print()
print('=' * 66)
print(f'合计 {len(pairs)} 项，通过 {len(pairs)-len(fails)} 项，不达标 {len(fails)} 项')
if fails:
    for n, v, need in fails: print(f'  ✗ {n}  {v:.1f} < {need}')
print('=' * 66)
