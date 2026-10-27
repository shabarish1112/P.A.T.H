import { test, expect } from '@playwright/test';
import { mkdir } from 'node:fs/promises';

test.use({ channel: 'msedge' });

for (const width of [1440, 390]) {
  test(`public analysis and optional accounts at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 950 });
    let signedIn = false;
    const account = {
      id: 'member-test',
      email: 'member@example.com',
      role: 'member',
      is_active: true,
    };
    const result = {
      analysis_id: 'a'.repeat(32),
      model: 'if',
      rows_accepted: 12,
      rows_received: 12,
      rows_rejected: 0,
      issues: [],
      expires_at: '2027-01-01T00:00:00Z',
      alerts: [
        {
          rank: 1,
          transaction_id: 'PUBLIC-1',
          agency: 'Example agency',
          vendor: 'Example vendor',
          amount_paise: 100000,
          score: 0.9,
          risk: 'High',
        },
      ],
    };
    await page.route('**/api/**', async (route) => {
      const path = new URL(route.request().url()).pathname;
      if (!path.startsWith('/api/')) return route.continue();
      const data = { access_token: 'mock-access', user: account };
      if (path === '/api/auth/refresh')
        return route.fulfill({
          status: signedIn ? 200 : 401,
          json: signedIn ? data : { detail: 'No session' },
        });
      if (path === '/api/auth/signup') {
        signedIn = true;
        return route.fulfill({ status: 201, json: data });
      }
      if (path === '/api/auth/me') return route.fulfill({ json: { user: account } });
      if (path === '/api/auth/logout') {
        signedIn = false;
        return route.fulfill({ json: { message: 'Logged out' } });
      }
      if (path === '/api/public/limits')
        return route.fulfill({ json: { max_upload_mb: 4, max_rows: 4000 } });
      if (path.startsWith('/api/public/analyses/')) return route.fulfill({ json: result });
      if (path === '/api/public/analyze') return route.fulfill({ status: 201, json: result });
      return route.fulfill({ status: 404, json: {} });
    });
    await page.goto('/');
    await expect(page.getByRole('heading', { name: /Find the unusual/ })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Create account', exact: true })).toBeVisible();
    await expect
      .poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth))
      .toBe(true);
    await mkdir('.local', { recursive: true });
    await page.screenshot({ path: `.local/public-${width}.png`, fullPage: true });
    await page.getByLabel('Transaction CSV').setInputFiles({
      name: 'sample.csv',
      mimeType: 'text/csv',
      buffer: Buffer.from('synthetic'),
    });
    await page.getByRole('button', { name: 'Upload and analyze' }).click();
    await expect(page.getByText('PUBLIC-1')).toBeVisible();
    await page.reload();
    await expect(page.getByText('PUBLIC-1')).toBeVisible();
    const downloaded = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Download results (JSON)' }).click();
    expect((await downloaded).suggestedFilename()).toBe('path-analysis.json');
    await page.getByRole('link', { name: 'Create account', exact: true }).click();
    await page.getByLabel('Email', { exact: true }).fill('member@example.com');
    await page.getByLabel('Password', { exact: true }).fill('VeryStrongPassword!123');
    await page.getByLabel('Confirm password', { exact: true }).fill('VeryStrongPassword!123');
    await page.getByRole('button', { name: 'Create account', exact: true }).click();
    await expect(page.getByRole('heading', { name: /Find the unusual/ })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Log out' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Staff workspace' })).toHaveCount(0);
    await page.getByRole('button', { name: 'Log out' }).click();
    await expect(page.getByRole('link', { name: 'Log in', exact: true })).toBeVisible();
  });
}
