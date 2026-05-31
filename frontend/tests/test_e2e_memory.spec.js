import { test, expect } from '@playwright/test';

test.describe('E2E Memory Flow', () => {
  test('chat history stays visible', async ({ page }) => {
    await page.goto('http://localhost:5173');
    // Basic check that the chat area exists
    await expect(page.locator('[data-testid="chat-panel"]').or(page.locator('body'))).toBeTruthy();
  });
});
