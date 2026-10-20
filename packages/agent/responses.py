"""Explain execution boundaries without turning them into tax conclusions."""
from packages.agent import dialogue


def scope_reply(doc, text='', locale='zh', *, lookup=False, scope_reason=None):
    facts = dialogue.values(doc)
    en = locale == 'en'
    if scope_reason == 'equity_disposal':
        return (
            'You are asking about a gain from selling shares, rather than a dividend paid by the company. '
            'The current calculation tool only implements foreign-dividend rules; it cannot estimate tax on this sale. '
            'That does not establish that FSIE is inapplicable or that the gain is tax-free. '
            'We still need to establish who owns the shares and receives the proceeds, the transaction details, and the relevant tax jurisdictions. '
            'Acting as a company representative does not by itself mean you are investing personally.' if en else
            '你描述的是股票涨价后出售、赚取买卖差价，与公司向股东派发股息不同。'
            '目前的计算工具只实现了境外股息规则，不能据此估算这笔卖股交易的税额；这不代表已判断它不适用 FSIE 或可以免税。'
            '还需要核对股票及出售所得归谁、交易安排和需要分析的税务地区。你说自己是公司代理人，并不等于你在做个人投资。'
        )
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
        context = '目前还不能把这笔交易直接按境外股息分析。' if not en else 'This transaction cannot yet be analyzed as a foreign dividend. '
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


def scope_question(doc, locale='zh', scope_reason=None):
    en = locale == 'en'
    revision = doc.get('revision', 0) + 1
    if scope_reason == 'equity_disposal':
        return {'id': f'boundary:scope:{revision}', 'kind': 'mode', 'field': None,
                'scope_reason': scope_reason,
                'text': 'Would you like to check the official rules on share disposal gains first?' if en else '要先查股权处置收益的官方规定吗？',
                'why': 'This is a source lookup, not a tax calculation.' if en else '先查相关依据，不套用股息计算规则。',
                'example': 'Check disposal rules / correct the facts / pause' if en else '查处置收益规定 / 更正刚才的信息 / 暂停',
                'attempt': 1, 'based_on_revision': revision}
    return {'id': f'boundary:scope:{revision}', 'kind': 'mode', 'field': None,
            'text': 'Would you like to look up the scope of Hong Kong FSIE first?' if en else '要先查香港 FSIE 的适用范围吗？',
            'why': 'This checks the published rules; it does not run the corporate case analysis.' if en else '先核对官方规定，再决定怎样继续，不套用企业个案分析。',
            'example': 'Check the scope / correct the facts / pause' if en else '查适用范围 / 更正刚才的信息 / 暂停',
            'attempt': 1, 'based_on_revision': revision}
