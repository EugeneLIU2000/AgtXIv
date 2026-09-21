# -*- coding: utf-8 -*-
"""SPEAKING-SCRIPT-v1.md - the existing prose, re-ordered and re-numbered.

Nothing here is rewritten. Every per-frame block and every table row is moved
verbatim from SPEAKING-SCRIPT.md into its new position, and only the frame
number in front of it changes. The front region was never scripted, so those
frames get their meter and nothing else - that is a gap, and it says so.
"""
import json, re

O=json.load(open('order-v1.json'))
ORDER, METER, ACTS, PROV = O['order'], O['meter'], O['acts'], O['provenance']
new_of_old={p:k for k,p in enumerate(PROV) if isinstance(p,int)}

S=open('SPEAKING-SCRIPT.md',encoding='utf-8').read().split('\n')

# THE NUMBER IN THE OLD SCRIPT IS NOT TRUSTED. It carries at least one stale
# index - a row labelled "11" holds frame 39's copy, left over from the deck's
# 41-frame era - and moving copy by a wrong number puts it under a picture it
# does not describe. So every block and row is re-keyed by its METER text,
# which is the only part of the heading that came from the deck itself.
V0=json.loads('['+re.search(r'const METER=\[(.*?)\], MAXW=',
              open('chain-build.html',encoding='utf-8').read(), re.S).group(1)+']')
def norm(t): return re.sub(r'[^A-Z0-9]','', t.upper())
BY_METER={}
for k,m in enumerate(V0): BY_METER.setdefault(norm(m),[]).append(k)
def resolve(declared, meter_text, what):
    hit=BY_METER.get(norm(meter_text),[])
    if len(hit)==1:
        if hit[0]!=declared:
            print(f'  ! {what}: old script says frame {declared}, its meter is frame {hit[0]}'
                  f' - using {hit[0]}')
        return hit[0]
    return declared if declared < len(V0) else None

# ---- harvest the per-frame prose ----------------------------------------
blocks={}           # old frame -> its ### block, body only
rows={}             # old frame -> its | ... | table row
cur=None; buf=[]
for ln in S:
    m=re.match(r'^### 帧 (\d+) — (.*)$', ln)
    if m:
        if cur is not None: blocks[cur]='\n'.join(buf).strip()
        cur=resolve(int(m.group(1)), re.sub(r'^⚠️暖 — |^— ','',m.group(2)), f'heading {m.group(1)}')
        buf=[]; continue
    if cur is not None and re.match(r'^##+ ', ln):
        blocks[cur]='\n'.join(buf).strip(); cur=None; buf=[]
    if cur is not None: buf.append(ln)
    r=re.match(r'^\| \*\*(\d+)\*\*( ?[^|]*)\| (.*?) \| (.*) \|$', ln)
    if r:
        k=resolve(int(r.group(1)), r.group(3), f'table row {r.group(1)}')
        if k is not None: rows[k]=(r.group(2).strip(), r.group(4))
if cur is not None: blocks[cur]='\n'.join(buf).strip()

APPENDIX='\n'.join(S[next(k for k,l in enumerate(S) if l.startswith('## 10. 专题')):])

# ---- the new document ---------------------------------------------------
NOTE_NEW={k:json.load(open(f'{k}.json'))['note'][0] for k in ('title','hinge','roadmap')}
KEY_OF_NEWFRAME={}
for k,p in enumerate(PROV):
    if isinstance(p,str): KEY_OF_NEWFRAME[k]=p

acts=[]
for k,a in enumerate(ACTS):
    if not acts or acts[-1][0]!=a: acts.append((a,[k]))
    else: acts[-1][1].append(k)

BUDGET={'I':2,'II':6,'III':7,'IV':3,'V':6,'VI':7,'VII':10,'VIII':4,'IX':8}
out=[]
w=out.append
w('# chain-build-v1.html — 逐帧讲解与完整演讲稿')
w('')
w('> **这份稿子对应 `chain-build-v1.html`（67 帧），不是 `chain-build.html`（69 帧）。**')
w('> v1 把同样的图重新排了顺序：测量数字那一段被拆成三块分别放进了三个不同的幕，')
w('> 导入开场里 5 帧重复的 build step 被删掉，新增 3 帧（标题 / 铰链 / 路线图）。')
w('> 每一段讲稿文字都是从旧稿原样搬过来的，只有帧号变了；对照表见 §2。')
w('')
w('**对象：** `slides/chain-build/chain-build-v1.html`，67 帧，9 幕')
w('**语言：** 讲解用中文；**讲稿正文是英文**，因为 deck 上的 meter 和 speaker notes 都是英文。')
w('')
w('**三条贯穿全场的规矩**（deck 自己定的，讲的时候别破）：')
w('')
w('- **一个例子，永不离开**：arXiv:2607.26154v1。')
w('- **暖色 `#8C4A2F` 只有一个意思：NOT FROM THIS PAPER。**')
w('- **虚线环 = root，下面什么都没有；实心 = 形式化顺序能到达。**')
w('')
w('---')
w('')
w('## 1. 全局结构与时间预算')
w('')
w('| 幕 | 帧 | 内容 | 建议时长 |')
w('|---|---|---|---:|')
tot=0
for a,ks in acts:
    roman=a.split(' ')[0]; mins=BUDGET.get(roman,4); tot+=mins
    w(f'| **{a}** | {ks[0]}–{ks[-1]} | {len(ks)} 帧 | {mins} min |')
w(f'| Q&A | — | | 4 min |')
w(f'| | | | **{tot+4} min** |')
w('')
w('新顺序的三处关键改动，讲之前先记住：')
w('')
w('1. **旧帧 28–29（一个结果 / 6 行对 7,765 行）挪到了最前面**，紧跟危机曲线——')
w('   它们是那条曲线的实测版本，放在开头才起动机作用，放在中间只是一堆数字。')
w('2. **旧帧 30–32（0 人复核 / 46 条有条件 / 编译通过但答案为空）挪到了最后**，')
w('   放在链条长完之后。这三帧是**局限**，局限只有在听众已经看见东西之后才像诚实，')
w('   在之前只像免责声明。')
w('3. **旧帧 18–22（learn backwards / reasoning forwards）挪到了链条前面。**')
w('   backwards 就是 query closure，forwards 就是一层层长出来的那个 build——')
w('   放在这里它不再是插叙，而是预告了接下来 11 帧要干什么。')
w('')
w('---')
w('')
w('## 2. 帧号对照表（v1 → v0）')
w('')
w('| v1 | v0 | 幕 | meter |')
w('|---:|---:|---|---|')
for k in range(len(ORDER)):
    p=PROV[k]
    old = str(p) if isinstance(p,int) else '**新**'
    w(f'| {k} | {old} | {ACTS[k].split(" · ")[0]} | {METER[k]} |')
w('')
w('v0 里被删掉的 5 帧：**0**（源文件 slide 1，两个空占位符）、**4**（slide 5，'
  'slide 6 是同一帧多一张图）、**6**（slide 7，slide 8 是同一帧多一个 context window 框）、'
  '**18**（slide 19，slide 20 是同一帧多一张图）、**20**（slide 21，slide 22 同理）。'
  '删的都是同一张源幻灯片的重复 build step，没有删掉任何内容。')
w('')
w('---')
w('')

for a,ks in acts:
    w(f'## {a}（帧 {ks[0]}–{ks[-1]}）')
    w('')
    for k in ks:
        p=PROV[k]
        w(f'### 帧 {k} — {METER[k]}')
        w('')
        if k in KEY_OF_NEWFRAME:
            w('> **新增帧。** deck 内置 speaker note：')
            w('')
            for para in NOTE_NEW[KEY_OF_NEWFRAME[k]].split('\n\n'):
                w('> '+para.strip().replace('\n',' '))
                w('>')
            w('')
        elif p in blocks:
            body=blocks[p]
            body=re.sub(r'帧 (\d+)', lambda m: f'帧 {new_of_old[int(m.group(1))]}'
                        if int(m.group(1)) in new_of_old else m.group(0), body)
            w(body); w('')
        elif p in rows:
            warm, text = rows[p]
            w((f'{warm} ' if warm else '')+text); w('')
        else:
            w('*（导入开场帧，旧稿未覆盖——照着幻灯片讲即可。）*'); w('')
    w('---'); w('')

w('## 附录（从旧稿原样搬运）')
w('')
w('> ⚠️ **下面这几节里的「帧 N」是 v0 编号，没有改。** 需要换算时查 §2 的对照表。')
w('')
w(APPENDIX)

open('SPEAKING-SCRIPT-v1.md','w',encoding='utf-8').write('\n'.join(out))
covered=sum(1 for k in range(len(ORDER)) if isinstance(PROV[k],int) and (PROV[k] in blocks or PROV[k] in rows))
print(f'SPEAKING-SCRIPT-v1.md  {len(out)} lines')
print(f'  {len(blocks)} prose blocks + {len(rows)} table rows harvested from the old script')
print(f'  {covered+len(KEY_OF_NEWFRAME)} of {len(ORDER)} frames have copy; '
      f'{len(ORDER)-covered-len(KEY_OF_NEWFRAME)} are unscripted imported-opening frames')
