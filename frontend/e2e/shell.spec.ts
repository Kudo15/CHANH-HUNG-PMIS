import { expect, test } from '@playwright/test'

test('shows the local application shell', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { level: 1, name: 'CHÁNH HƯNG PMIS' })).toBeVisible()
})
