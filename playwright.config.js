// Warstwa skryptowa testów: npm test (serwer lokalny startuje sam, przełącznik buduje się w pretest).
const { defineConfig } = require('@playwright/test');
module.exports = defineConfig({
  testDir: 'tests/e2e', timeout: 120000, fullyParallel: true, workers: process.env.CI ? 2 : 4, retries: process.env.CI ? 2 : 0,
  reporter: [['list'], ['json', { outputFile: 'tests/e2e/report/results.json' }]],
  use: { baseURL: 'http://localhost:8801', viewport: { width: 1456, height: 829 }, colorScheme: 'light' },
  webServer: { command: 'python3 -m http.server 8801', url: 'http://localhost:8801/README.md', reuseExistingServer: true, timeout: 20000 },
});
