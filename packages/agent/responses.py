"""Explain execution boundaries without turning them into tax conclusions."""
import re
from packages.agent import dialogue


def scope_reply(doc, text='', locale='zh', *, lookup=False):
    facts = dialogue.values(doc)
    en = locale == 'en'
    reasons = []
    if facts.get('recipient_type') == 'individual':
        reasons.append('you said the recipient is an individual' if en else '你说明这笔收入由个人收取')
    income = facts.get('income_type')
    if dialogue.resolved(income) and income != 'dividend':
        label = {'interest': '利息', 'royalty': '特许权使用费', 'disposal_gain': '处置收益'}.get(income, income)
        reasons.append(f'the income type is {income}' if en else f'你提供的收入类型是{label}')
    region = facts.get('analysis_jurisdiction')
    if dialogue.resolved(region) and region.casefold() not in ('hk', '香港', '中国香港', '中國香港', 'hong kong', 'hong kong sar'):
        reasons.append(f'the tax jurisdiction is {region}' if en else f'你要判断的税务地区是{region}')
    context = ('; '.join(reasons) + '. ') if en else ('；'.join(reasons) + '。')
    if not reasons:
        excerpt = re.sub(r'[<>\[\]\n\r`]', '', text.strip())[:100]
        context = (f'For your question, "{excerpt}": ' if en else f'关于你问的“{excerpt}”：') if excerpt else (
            'For the question you just asked, ' if en else '针对你刚才的问题，')
    if en:
        return context + ('The connected sources do not cover this research request. ' if lookup else
                          'The current case-analysis tool covers corporate foreign dividends in Hong Kong. ' ) + \
            'This is a limit of this tool, not a finding about whether you owe tax or qualify for an exemption. ' + \
            ('Specify a section or official case to check within the connected Hong Kong FSIE library; another jurisdiction needs its own official sources.' if lookup else
             'I can help look up the scope of Hong Kong FSIE separately, without applying the corporate case rules to your situation. You can also clarify or correct the facts above.')
    return context + ('当前接入的资料不能支持这项查询。' if lookup else
                      '当前个案分析工具处理的是香港企业境外股息，不能直接把这套企业分析规则套到你的情况。') + \
        '这是工具的覆盖限制，不代表已经判断你要缴税或可以免税。' + \
        ('你可以给出要核对的香港 FSIE 条文或官方案例；涉及其他地区的部分，需要对应地区的官方依据。' if lookup else
         '我们可以先单独查香港 FSIE 的适用范围；如果刚才的主体、收入类型或地区需要更正，也可以直接告诉我。')


def scope_question(doc, locale='zh'):
    en = locale == 'en'
    revision = doc.get('revision', 0) + 1
    return {'id': f'boundary:scope:{revision}', 'kind': 'mode', 'field': None,
            'text': 'Would you like to look up the scope of Hong Kong FSIE first?' if en else '要先查香港 FSIE 的适用范围吗？',
            'why': 'This checks the published rules; it does not run the corporate case analysis.' if en else '先核对官方规定，再决定怎样继续，不套用企业个案分析。',
            'example': 'Check the scope / correct the facts / pause' if en else '查适用范围 / 更正刚才的信息 / 暂停',
            'attempt': 1, 'based_on_revision': revision}
