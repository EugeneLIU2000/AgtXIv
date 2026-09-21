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
# derived from the order, not hard-coded - a new frame added to build_v1.py's
# ARC must not silently fall out of the script.
NOTE_NEW={k:json.load(open(f'{k}.json'))['note'][0]
          for k in {p for p in PROV if isinstance(p,str)}}
KEY_OF_NEWFRAME={}
for k,p in enumerate(PROV):
    if isinstance(p,str): KEY_OF_NEWFRAME[k]=p

acts=[]
for k,a in enumerate(ACTS):
    if not acts or acts[-1][0]!=a: acts.append((a,[k]))
    else: acts[-1][1].append(k)

BUDGET={'I':1,'II':4,'III':6,'IV':4,'V':8,'VI':5,'VII':6,'VIII':5,'IX':2}
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
w('这一版相对 v0 的改动，讲之前先记住：')
w('')
w('1. **危机曲线之后只有一句话**，然后直接进 LLM 机制——旧稿里那两帧'
  '（一个孤立的定理 / 6 行对 7,765 行）开了一个此处不打算展开的论证，已删。')
w('2. **「please help me …」三帧挪到了 trust 四象限之前**，'
  '因为 learn backwards / reason forwards 正是后面 closure 与 build 两个方向的引子。')
w('3. **How formalization works 之后加了三帧 Lean**：一段能读的代码、'
  'kernel 接受或拒绝、以及库（Mathlib / Quantumlib / 本文 66 个文件）。'
  '**这三帧是给物理听众的，讲慢一点。**')
w('4. **旧的测量段（213 support groups / 46 conditional / 8.6 GB …）整段删除。**'
  '这是一场关于可能性的报告，不是 schema 的技术汇报。'
  '其中最该说的那几句诚实话，现在集中在倒数第二帧「IN CLOSING」上。')
w('5. **最后两帧是新的**：结论，然后一帧只有一个问题的讨论页。')
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
