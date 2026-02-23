/**
 * report_test_result tool — the AI calls this for each individual test to record pass/fail/skip.
 */

// Shared results accumulator (mutated by the tool, read by reporter)
const results = {
  tests: [],
  startedAt: new Date().toISOString(),
  finishedAt: null,
};

export function reportTestResult({ test_name, status, reason, service, duration_ms }) {
  const entry = {
    test_name,
    status, // 'pass' | 'fail' | 'skip'
    reason: reason || '',
    service: service || 'unknown',
    duration_ms: duration_ms || 0,
    timestamp: new Date().toISOString(),
  };
  results.tests.push(entry);
  return { recorded: true, total_tests: results.tests.length, entry };
}

export function getResults() {
  results.finishedAt = new Date().toISOString();
  const passed = results.tests.filter((t) => t.status === 'pass').length;
  const failed = results.tests.filter((t) => t.status === 'fail').length;
  const skipped = results.tests.filter((t) => t.status === 'skip').length;
  return { ...results, summary: { total: results.tests.length, passed, failed, skipped } };
}
