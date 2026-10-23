import { test, expect } from '@playwright/test';

test('PDF chip, consent, message and reload retain the attachment', async ({ page }) => {
  await page.route('**/api/attachments?*', route => route.fulfill({ json: {name:'case.pdf', page_count:2, pages:[{page:1,text:'Hong Kong company receives CNY 2000000.'}], empty_pages:[2]} }));
  await page.goto('/');
  await page.getByRole('button', {name:'Switch to English'}).click();
  await page.locator('input[type=file]').setInputFiles({name:'case.pdf', mimeType:'application/pdf', buffer:Buffer.from('%PDF-fixture')});
  await expect(page.locator('.composer .attachment-chip')).toContainText('case.pdf');
  await expect(page.locator('.composer details')).toHaveCount(0);
  await page.getByRole('textbox', {name:'Enter your tax question'}).fill('Please summarize my PDF.');
  await page.getByRole('button', {name:'Send message'}).click();
  await page.getByRole('checkbox').check();
  const message = page.waitForRequest(r => r.url().endsWith('/messages') && r.method()==='POST');
  await page.getByRole('button', {name:'Send message'}).click();
  expect((await message).postDataJSON().text).toContain('2000000');
  await expect(page.locator('.message.user')).toContainText('case.pdf');
  await expect(page.locator('.composer .attachment-chip')).toHaveCount(0);
  await page.reload();
  await expect(page.locator('.message.user')).toContainText('case.pdf');
  await expect(page.locator('.message.user details, .message.user pre')).toHaveCount(0);
  await expect(page.locator('.message.user .sent-attachment')).toContainText('case.pdf');
});

test('unreadable PDF reports an error and does not attach an empty file', async ({page}) => {
  await page.route('**/api/attachments?*', route => route.fulfill({status:422,json:{detail:'pdf_no_text'}}));
  await page.goto('/');
  await page.getByRole('button', {name:'Switch to English'}).click();
  await page.locator('input[type=file]').setInputFiles({name:'scan.pdf',mimeType:'application/pdf',buffer:Buffer.from('%PDF-fixture')});
  await expect(page.getByRole('alert')).toContainText('Apply OCR first');
  await expect(page.locator('.composer .attachment-chip')).toHaveCount(0);
  await expect(page.getByRole('button', {name:'Send message'})).toBeDisabled();
});

for (const [name, kind, label] of [['case.docx', 'word', 'Document body / tables'], ['case.xlsx', 'excel', 'Worksheet: Dividends']]) {
  test(`paperclip uploads and shows ${name}`, async ({ page }) => {
    await page.route('**/api/attachments?*', route => route.fulfill({json:{name, kind, page_count:1, pages:[{page:1,label,text:'Amount: 2000000'}], empty_pages:[],warnings:[]}}));
    await page.goto('/');
    await page.getByRole('button', {name:'Switch to English'}).click();
    const clip = page.getByRole('button', {name:'Attach file',exact:true});
    await expect(clip).toHaveText('');
    await expect(clip.locator('svg')).toHaveCount(1);
    await page.locator('input[type=file]').setInputFiles({name,mimeType:'application/octet-stream',buffer:Buffer.from('fixture')});
    await expect(page.locator('.composer .attachment-chip')).toContainText(name);
    await expect(page.locator('.composer details, .composer pre')).toHaveCount(0);
    await expect(page.locator('.composer .attachment-chip')).toHaveText(name);
    if (kind === 'word') await page.screenshot({path:'/tmp/taxrora-attachment-preview.png',fullPage:true});
    await page.getByRole('button',{name:'Remove attachment'}).click();
    await expect(page.locator('.composer .attachment-chip')).toHaveCount(0);
  });
}

test('image upload displays thumbnail above sent text and survives reload', async ({page}) => {
  const {readFileSync} = await import('node:fs');
  const bytes = readFileSync('../../tests/chat/fixtures/attachment.jpg');
  const thumb = 'data:image/jpeg;base64,' + bytes.toString('base64');
  await page.route('**/api/attachments?*', route => route.fulfill({json:{name:'receipt.jpg',kind:'image',thumbnail:thumb,page_count:1,pages:[{page:1,text:'Dividend 2000000'}],empty_pages:[],warnings:['image_ocr_only']}}));
  await page.goto('/');
  await page.getByRole('button',{name:'Switch to English'}).click();
  await page.locator('input[type=file]').setInputFiles({name:'receipt.jpg',mimeType:'image/jpeg',buffer:bytes});
  await expect(page.locator('.composer img')).toBeVisible();
  await page.getByRole('textbox',{name:'Enter your tax question'}).fill('Read this image.');
  await page.getByRole('button',{name:'Send message'}).click();
  await page.getByRole('checkbox').check();
  await page.getByRole('button',{name:'Send message'}).click();
  await expect(page.locator('.message.user .sent-image-thumbnail')).toBeVisible();
  await expect(page.locator('.composer img')).toHaveCount(0);
  await page.reload();
  const img = page.locator('.message.user .sent-image-thumbnail');
  await expect(img).toBeVisible();
  await expect(page.getByText('[Taxrora attachment]', {exact:false})).toHaveCount(0);
  expect(await img.evaluate((e:HTMLImageElement) => e.naturalWidth)).toBeGreaterThan(0);
  const card = await page.locator('.message.user .sent-attachment').boundingBox();
  const text = await page.locator('.message.user .user-message-content > p').boundingBox();
  expect(card!.y + card!.height).toBeLessThanOrEqual(text!.y);
  await expect(page.locator('.message.user details, .message.user pre')).toHaveCount(0);
  await page.screenshot({path:'/tmp/taxrora-image-message.png',fullPage:true});
});
