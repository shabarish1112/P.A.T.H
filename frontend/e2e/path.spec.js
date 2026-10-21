import { expect, test } from '@playwright/test';

const email = process.env.E2E_EMAIL;
const password = process.env.E2E_PASSWORD;

test.beforeEach(async ({ page }) => {
  if (!email || !password) throw new Error('E2E_EMAIL and E2E_PASSWORD are required');
  await page.goto('/login');
  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Password').fill(password);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByRole('heading', { name: 'Executive Dashboard' })).toBeVisible();
});

test('admin research workflow', async ({ page }) => {
  await page.getByRole('link', { name: /Datasets/ }).click();
  await expect(page.getByRole('heading', { name: 'Dataset Management' })).toBeVisible();
  await page.getByLabel('CSV file').setInputFiles('../data/public_fund_demo.csv');
  await page.getByLabel(/Confirm replacement/).check();
  await page.getByRole('button', { name: 'Upload and validate' }).click();
  await expect(page.getByText(/accepted/)).toBeVisible({ timeout: 120_000 });

  await page.getByRole('link', { name: /ML Control/ }).click();
  await page.getByRole('button', { name: 'Run model' }).click();
  await expect(page.getByText('completed', { exact: true })).toBeVisible({ timeout: 120_000 });

  await page.getByRole('link', { name: /Anomaly Explorer/ }).click();
  const firstRow = page.locator('tbody tr').first();
  await expect(firstRow).toBeVisible();
  await firstRow.click();
  await expect(page.getByText('PATH Insight')).toBeVisible();
  await page.getByLabel('Status').selectOption('Escalated');
  await page.getByLabel('Review note').fill('E2E human validation action.');
  await page.getByRole('button', { name: 'Record decision' }).click();
  await expect(page.getByText(/recorded in the audit trail/)).toBeVisible();

  await page.getByRole('link', { name: /Access & Audit/ }).click();
  await expect(page.getByRole('heading', { name: 'Access & Audit' })).toBeVisible();
  await expect(page.getByText('review.update')).toBeVisible();
  await page.getByRole('button', { name: 'Logout' }).click();
  await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible();
});

test('unauthorized route redirects to login', async ({ browser }) => {
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.goto('/transactions');
  await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible();
  await context.close();
});
