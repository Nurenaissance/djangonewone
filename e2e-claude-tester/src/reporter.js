/**
 * Reporter — writes results.json and generates GitHub Actions Summary markdown.
 */

import { writeFileSync, readFileSync, existsSync } from 'fs';
import { join } from 'path';
import { fileURLToPath } from 'url';
import { getResults } from './tools/report-result.js';

const __dirname = fileURLToPath(new URL('.', import.meta.url));
const RESULTS_PATH = join(__dirname, '..', 'results.json');

/**
 * Write accumulated results to results.json.
 */
export function writeResults() {
  const results = getResults();
  writeFileSync(RESULTS_PATH, JSON.stringify(results, null, 2));
  console.log(`Results written to ${RESULTS_PATH}`);
  return results;
}

/**
 * Generate markdown summary from results.json (for GitHub Actions Summary).
 */
export function generateSummary(resultsData) {
  const data = resultsData || JSON.parse(readFileSync(RESULTS_PATH, 'utf-8'));
  const { tests, summary, startedAt, finishedAt } = data;

  const statusIcon = (s) => (s === 'pass' ? '✅' : s === 'fail' ? '❌' : '⏭️');

  let md = `## E2E Test Results\n\n`;
  md += `**${summary.passed}/${summary.total} passed**`;
  if (summary.failed > 0) md += ` | ${summary.failed} failed`;
  if (summary.skipped > 0) md += ` | ${summary.skipped} skipped`;
  md += `\n\n`;
  md += `| Status | Test | Service | Duration | Reason |\n`;
  md += `|--------|------|---------|----------|--------|\n`;

  for (const t of tests) {
    const dur = t.duration_ms ? `${t.duration_ms}ms` : '-';
    const reason = (t.reason || '').replace(/\|/g, '\\|').slice(0, 120);
    md += `| ${statusIcon(t.status)} | ${t.test_name} | ${t.service} | ${dur} | ${reason} |\n`;
  }

  md += `\n_Started: ${startedAt} | Finished: ${finishedAt}_\n`;
  return md;
}

/**
 * CLI mode: read results.json and output summary.
 */
if (process.argv[2] === 'summary') {
  if (!existsSync(RESULTS_PATH)) {
    console.error('No results.json found. Run tests first.');
    process.exit(1);
  }
  const data = JSON.parse(readFileSync(RESULTS_PATH, 'utf-8'));
  console.log(generateSummary(data));
}
