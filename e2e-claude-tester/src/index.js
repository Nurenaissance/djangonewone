#!/usr/bin/env node
/**
 * E2E Claude Tester — Entry point.
 *
 * Usage:
 *   GITHUB_TOKEN=ghp_xxx node src/index.js
 *
 * Environment variables:
 *   CHANGED_FILES  — newline-separated list of changed files (from git diff)
 *   DIFF_SUMMARY   — short diff stats summary
 *   TEST_SCOPE     — 'auto' | 'all' | 'health-only'
 *   FORCE_ALL_TESTS — 'true' to run all tests regardless of diff
 *   (see config.js for full list)
 */

import config from './config.js';
import { analyzeChangedFiles } from './diff-analyzer.js';
import { getTestsForServices } from './test-registry.js';
import { runTestSession } from './claude-client.js';
import { writeResults, generateSummary } from './reporter.js';

async function main() {
  console.log('=== E2E Claude Tester ===\n');

  // 1. Analyze what changed
  const changedFilesStr = process.env.CHANGED_FILES || '';
  const diffResult = analyzeChangedFiles(changedFilesStr);
  console.log(`Affected services: ${diffResult.affectedServices.join(', ')}`);
  if (diffResult.reason) console.log(`Reason: ${diffResult.reason}`);

  // 2. Determine which tests to run
  const scope = config.test.scope;
  let relevantTests;

  if (scope === 'health-only') {
    relevantTests = getTestsForServices(diffResult.affectedServices).filter((t) => t.category === 'health');
  } else {
    relevantTests = getTestsForServices(diffResult.affectedServices, config.test.forceAll);
  }

  console.log(`Tests selected: ${relevantTests.length}`);

  if (relevantTests.length === 0) {
    console.log('No tests to run. Exiting.');
    process.exit(0);
  }

  // 3. Run the AI test session
  const context = {
    affectedServices: diffResult.affectedServices,
    relevantTests,
    changedFiles: diffResult.changedFiles,
    diffSummary: process.env.DIFF_SUMMARY || '',
  };

  await runTestSession(context);

  // 4. Write results
  const results = writeResults();
  console.log('\n' + generateSummary(results));

  // 5. Exit code
  if (results.summary.failed > 0) {
    console.log(`\n${results.summary.failed} test(s) failed.`);
    process.exit(1);
  }

  console.log('\nAll tests passed.');
  process.exit(0);
}

main().catch((err) => {
  console.error('Fatal error:', err);
  process.exit(1);
});
