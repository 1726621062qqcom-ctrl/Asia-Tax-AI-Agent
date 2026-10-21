import { test, expect } from '@playwright/test';
import { engineText, questionText } from '../src/engine-language';
import fields from '../src/engine-fields.json' with { type: 'json' };
import glossary from '../src/engine-glossary.json' with { type: 'json' };

test('every pinned field and source label has an English display value', () => {
  for (const text of [...Object.values(fields), ...Object.keys(glossary)]) {
    expect(engineText(text, 'en'), text).not.toMatch(/[\u3400-\u9fff]/);
  }
});

test('questions keep their meaning and hide internal addresses in both languages', () => {
  const q = { key: 'flow:up1.reinvested_in_cn', prompt: '请提供：分得利润是否在内地再投资（flow:up1.reinvested_in_cn）' };
  expect(questionText(q, 'en')).toBe('Please confirm: Are the distributed profits reinvested in mainland China?');
  expect(questionText(q, 'zh')).toBe('请提供：分得利润是否在内地再投资');
  expect(engineText('是/否', 'en')).toBe('Yes / No');
  expect(engineText('再投资协议', 'en')).toBe('Reinvestment agreement');
  expect(engineText('收款方是否为受益所有人', 'en')).toBe('Is the recipient the beneficial owner?');
  expect(engineText('股息', 'zh')).toBe('股息');
  expect(engineText('该笔支付在付款方是否可扣除', 'en')).toBe('Is the payment deductible for the payer?');
});
