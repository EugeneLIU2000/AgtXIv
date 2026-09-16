"""Read-only projections over explicit, validated supplied records.

No ranking, score, majority vote, latest-label substitution, or state mutation.
This is a local record reader, not a publication/knowledge query service.
"""
from __future__ import annotations

from .contracts import AXES, RecordSet, detached, exact_ref, kind, ref_key

AXIS_LABELS = {
    'source_fidelity':'来源忠实性', 'mathematical_correctness':'数学正确性',
    'formal_alignment':'形式对齐', 'semantic_applicability':'科学适用性',
    'empirical_support':'经验支持', 'computational_reproducibility':'计算复现性',
}


def project_axes(records: RecordSet, target_ref: dict, *, require_artifacts: bool = True) -> dict:
    """Retain every assessment of this exact target in the supplied set.

    ``apparent_disagreement`` flags different assessed conclusions for further
    inspection; it does not assert that different conditional scopes conflict.
    Newer timestamps never overwrite earlier assessments.
    """
    report = records.validate(require_artifacts=require_artifacts)
    report.require_valid()
    target = records.resolve(target_ref)
    supplied = records.records
    assessments = sorted((r for r in supplied if kind(r)=='axis-assessment' and target_ref in r['payload']['target_refs']),
                         key=lambda r: ref_key(exact_ref(r)))
    frontiers = sorted((r for r in supplied if kind(r)=='frontier-item' and target_ref in r['payload']['target_refs']),
                       key=lambda r: ref_key(exact_ref(r)))
    axes = []
    for axis in AXES:
        selected = [r for r in assessments if r['payload']['axis']==axis]
        conclusions = {r['payload']['result'] for r in selected} - {'NOT_ASSESSED'}
        axes.append({'axis':axis,'label_zh':AXIS_LABELS[axis],
            'coverage':'HAS_SUPPLIED_ASSESSMENTS' if selected else 'NO_SUPPLIED_ASSESSMENT',
            'apparent_disagreement':len(conclusions)>1,
            'assessments':[{'record_ref':exact_ref(r),'data_class':r['data_class'],**detached(r['payload'])} for r in selected]})
    return {'projection_version':'agtxiv.v3.axis-view/0.0.0',
        'scope':'EXACT_TARGET_IN_SUPPLIED_RECORD_SET','target_ref':exact_ref(target),
        'supplied_record_refs':sorted([exact_ref(r) for r in supplied],key=ref_key),
        'axes':axes,'frontier_refs':[exact_ref(r) for r in frontiers],
        'authority_checked':report.authority_checked,'artifact_bytes_checked':report.byte_artifacts_checked,
        'limitations':list(report.limitations)+[
            'This view does not claim all existing assessments were supplied.',
            'Different assessed conclusions are displayed together without a combined truth status.',
        ]}


def render_axes_markdown(view: dict) -> str:
    """Reader-facing Chinese text with exact record IDs and retained conditions."""
    labels={'SUPPORTED':'有支持证据','PARTIALLY_SUPPORTED':'有部分支持证据','COUNTEREVIDENCE':'有反对证据',
        'INCONCLUSIVE':'尚不能判断','NOT_ASSESSED':'尚未评估','APPLICABLE':'适用',
        'NOT_APPLICABLE':'不适用','UNDETERMINED':'适用性待定','COMPLETED':'已完成本次检查',
        'FAILED':'检查失败','BLOCKED':'检查受阻','DEFERRED':'暂缓检查'}
    origins={'SYNTHETIC':'人工样例，不是真实科学评估','RESEARCH':'研究材料，权威边界待核实','OBSERVED':'实际记录，不等于科学认可'}
    methods={'SOURCE_REVIEW':'原文对应审阅','ARGUMENT_REVIEW':'论证审阅',
        'KERNEL_AND_ALIGNMENT':'形式检查与命题对齐','FORMAL_ALIGNMENT':'形式含义对齐',
        'SEMANTIC_REVIEW':'科学适用性审阅','EMPIRICAL_REVIEW':'经验数据审阅',
        'REPRODUCTION_REVIEW':'计算复现审阅','COUNTEREXAMPLE_REVIEW':'反例审阅','UNASSESSED':'尚无评估方法'}
    lines = ['# 主张的六轴证据', '',
        f'目标：`{view["target_ref"]["record_id"]}`，修订 {view["target_ref"]["revision"]}。',
        '', '这份视图只读取本次提供的记录。每个维度分别列出证据，不生成整篇正确率。',
        '', ('已按调用方提供的身份凭据核验；不代表机构资格认证。' if view['authority_checked'] else '身份与权限未核验。'),
        ('所提供字节与记录哈希、长度匹配；尚不说明出版来源已核实。' if view['artifact_bytes_checked'] else '所提供字节尚未核对。'), '']
    for axis in view['axes']:
        lines.extend(['## '+axis['label_zh'],''])
        if not axis['assessments']:
            lines.extend(['未提供该维度的评估；这不等于不适用。',''])
        for assessment in axis['assessments']:
            lines.append(f'- `{assessment["record_ref"]["record_id"]}`：{labels[assessment["result"]]}；{labels[assessment["applicability"]]}；{labels[assessment["execution"]]}。')
            lines.append(f'  材料性质：{origins[assessment["data_class"]]}。方法：{methods[assessment["method"]]}。记录修订：{assessment["record_ref"]["revision"]}。')
            lines.append('  '+assessment['rationale'].replace('\n',' '))
            for field,label in [('support_refs','支持依据'),('counterevidence_refs','反对依据')]:
                if assessment[field]:
                    lines.append('  '+label+'：'+', '.join('`'+r['record_id']+'`（修订 '+str(r['revision'])+'）' for r in assessment[field])+'。')
            for condition in assessment['conditions']:
                lines.append('  保留条件：'+condition['statement'].replace('\n',' '))
        if axis['apparent_disagreement']:
            lines.append('\n存在不同评估结论，需结合各自条件与证据阅读；这里保留每一份评估。')
        lines.append('')
    if view['frontier_refs']:
        lines.extend(['未解决问题记录：'+', '.join('`'+r['record_id']+'`' for r in view['frontier_refs']), ''])
    lines.append('本地契约校验不证明数学或科学结论正确，也不授予发布、认证或知识准入资格。')
    return '\n'.join(lines)+'\n'
