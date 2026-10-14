import { test, expect } from "@playwright/test";

test("case facts use the full workspace, guided steps and explicit review", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "打开案例信息" }).click();
  await expect(page.locator(".app-shell")).toHaveClass(/panel-workspace/);
  await expect(page.locator(".main-workspace")).toBeHidden();
  await expect(page.getByRole("heading", { name: "收款主体" })).toBeVisible();
  await expect(page.getByRole("button", { name: "法规资料库" })).toBeVisible();
  await expect(page.getByRole("button", { name: "法规资料", exact: true })).toHaveCount(0);
  await page.screenshot({ path: "test-results/facts-wizard.png", fullPage: true, animations: "disabled" });

  await page.getByRole("combobox", { name: "收款主体", exact: true }).selectOption({ label: "公司" });
  await page.getByRole("button", { name: /02 收入情况/ }).click();
  await expect(page.getByRole("heading", { name: "收入情况" })).toBeVisible();
  await page.getByRole("button", { name: /08 核对提交/ }).click();
  await expect(page.getByRole("heading", { name: "核对后再提交" })).toBeVisible();
  await expect(page.locator(".facts-review-list")).toContainText("收款主体");
  await page.getByRole("button", { name: "保存事实" }).click();
  await expect(page.getByRole("button", { name: "保存事实" })).toBeDisabled();
  await expect(page.getByRole("button", { name: "确认事实并分析" })).toBeEnabled();

  await page.getByRole("button", { name: "关闭详情" }).click();
  await page.getByRole("button", { name: "法规资料库" }).click();
  await expect(page.locator(".app-shell")).toHaveClass(/panel-workspace/);
  await expect(page.getByRole("heading", { name: "法规与来源" })).toBeVisible();
  const sourcesPanel = await page.locator(".panel-slot").boundingBox();
  expect(sourcesPanel!.width).toBeGreaterThan(900);
  await page.getByRole("button", { name: "关闭详情" }).click();
  await page.getByRole("button", { name: "结构分析", exact: true }).click();
  const structurePanel = await page.locator(".panel-slot").boundingBox();
  expect(structurePanel!.width).toBeGreaterThan(900);
});

test("case facts fill the phone workspace without a side drawer", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page.getByRole("button", { name: "打开案例信息" }).click();
  const panel = await page.locator(".panel-slot").boundingBox();
  expect(panel).not.toBeNull();
  expect(panel!.x).toBe(0);
  expect(panel!.width).toBe(390);
  await expect(page.locator(".overlay-backdrop")).toHaveCount(0);
});
