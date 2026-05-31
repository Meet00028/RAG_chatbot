import { test, expect } from '@playwright/test';

test.describe('E2E Ingest Flow', () => {
  test('page loads without errors', async ({ page }) => {
    await page.goto('http://localhost:5173');
    // Check for no console errors (basic check)
    const errors = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    await page.waitForLoadState('networkidle');
    expect(errors.length).toBe(0);
  });

  test('URL inputs are present and editable', async ({ page }) => {
    await page.goto('http://localhost:5173');
    const urlAInput = page.getByLabel('Video A (YouTube)');
    const urlBInput = page.getByLabel('Video B (Instagram)');
    await expect(urlAInput).toBeVisible();
    await expect(urlBInput).toBeVisible();
    await urlAInput.fill('https://www.youtube.com/watch?v=dQw4w9WgXcQ');
    await urlBInput.fill('https://www.instagram.com/reel/test/');
    await expect(urlAInput).toHaveValue('https://www.youtube.com/watch?v=dQw4w9WgXcQ');
  });

  test('analyze button is disabled when inputs are empty', async ({ page }) => {
    await page.goto('http://localhost:5173');
    const analyzeButton = page.getByRole('button', { name: 'Analyze Videos' });
    await expect(analyzeButton).toBeDisabled();
  });

  test('filling both URLs enables the button', async ({ page }) => {
    await page.goto('http://localhost:5173');
    const urlAInput = page.getByLabel('Video A (YouTube)');
    const urlBInput = page.getByLabel('Video B (Instagram)');
    const analyzeButton = page.getByRole('button', { name: 'Analyze Videos' });
    
    await urlAInput.fill('https://www.youtube.com/watch?v=dQw4w9WgXcQ');
    await expect(analyzeButton).toBeDisabled(); // Still missing urlB
    
    await urlBInput.fill('https://www.instagram.com/reel/test/');
    await expect(analyzeButton).toBeEnabled();
  });
});
