import { test, expect } from '@playwright/test';

test('case details batches facts and excludes dependent/professional questions', async ({ page }) => {
  let current: any;
  const question = (id: string, type: string, status = 'ready', kind = 'data') => ({
    id, key: `ULT.${id}`, kind, region: ['HK'], prompt: id, prompt_en: id,
    interview_status: status, answer_schema: {type}, why: [], source_hint: '', forms: [],
  });
  await page.route(/\/api\/cases$/, async route => {
    const response = await route.fetch();
    current = await response.json();
    if (Array.isArray(current)) { await route.fulfill({json: current}); return; }
    current.facts = {income_type: {value: 'dividend', origin:'user', status:'user_entered'}};
    current.domain_workflow = {mode:'assess_current',status:'active',pending_question_id:'Reinvested'};
    current.domain_outcome = {status:'needs_input', questions:[
      question('Reinvested','boolean'), question('Revenue','number'), question('Unknown amount','number'),
      question('Hidden detail','text','waiting'), question('Professional ruling','boolean','ready','ruling'),
    ]};
    await route.fulfill({json: current});
  });
  let calls = 0;
  await page.route('**/api/cases/*/domain-answers', async route => {
    calls++;
    const body = route.request().postDataJSON();
    expect(body.answers).toHaveLength(3);
    expect(body.answers.map((a:any) => a.value)).toEqual(['no','2000000','unknown']);
    expect(body.locale).toBe('en');
    await route.fulfill({json: {...current, revision: current.revision + 1,
      domain_outcome: {...current.domain_outcome, questions: []}}});
  });
  await page.goto('/');
  await page.getByRole('button', {name:'Switch to English'}).click();
  await page.getByRole('button', {name:'Open case details',exact:true}).click();
  const form = page.locator('.calculation-facts');
  await expect(form.getByLabel('Reinvested', {exact:true})).toBeVisible();
  await expect(form.getByText('Hidden detail', {exact:true})).toHaveCount(0);
  await expect(form.getByText('Professional ruling', {exact:true})).toHaveCount(0);
  await form.getByLabel('Reinvested', {exact:true}).selectOption('no');
  await form.getByLabel('Revenue', {exact:true}).fill('2000000');
  await form.locator('.fact-field').filter({hasText:'Unknown amount'}).getByRole('button', {name:'Unknown',exact:true}).click();
  await page.screenshot({path:'/tmp/taxrora-batch-facts.png',fullPage:true});
  await form.getByRole('button', {name:'Submit 3 items and recalculate'}).click();
  await expect(form).toContainText('There are no directly answerable questions now');
  expect(calls).toBe(1);
});
