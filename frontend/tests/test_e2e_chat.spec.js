import { test, expect } from '@playwright/test';

test.describe('E2E Chat Flow', () => {
  test('chat input is present', async ({ page }) => {
    await page.goto('http://localhost:5173');
    const chatInput = page.getByPlaceholder('Ask a question about the videos...');
    await expect(chatInput).toBeVisible();
  });

  test('send button is disabled when input empty', async ({ page }) => {
    await page.goto('http://localhost:5173');
    const sendButton = page.getByRole('button', { name: 'Send' });
    await expect(sendButton).toBeDisabled();
  });
});
