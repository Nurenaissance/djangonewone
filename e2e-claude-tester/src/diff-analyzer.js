/**
 * Maps git diff changed files to affected services.
 */

const SERVICE_PATHS = {
  'whatsapp_bot_server_withclaude/': 'nodejs',
  'fastAPIWhatsapp_withclaude/': 'fastapi',
  'whatsapp_latest_final_withclaude/': 'django',
  'whatsappBusinessAutomation_withclaude/': 'frontend',
  'e2e-claude-tester/': 'e2e',
  '.github/workflows/': 'ci',
  'shared_utils/': 'shared',
};

/**
 * @param {string} changedFilesStr - Newline-separated list of changed file paths (from git diff --name-only)
 * @returns {{ affectedServices: string[], changedFiles: string[], serviceFiles: Record<string, string[]> }}
 */
export function analyzeChangedFiles(changedFilesStr) {
  if (!changedFilesStr || !changedFilesStr.trim()) {
    return { affectedServices: ['nodejs', 'fastapi', 'django'], changedFiles: [], serviceFiles: {}, reason: 'No diff info — testing all backend services' };
  }

  const files = changedFilesStr.trim().split('\n').filter(Boolean);
  const serviceFiles = {};
  const affectedSet = new Set();

  for (const file of files) {
    for (const [prefix, service] of Object.entries(SERVICE_PATHS)) {
      if (file.startsWith(prefix) || file.includes(prefix)) {
        affectedSet.add(service);
        if (!serviceFiles[service]) serviceFiles[service] = [];
        serviceFiles[service].push(file);
      }
    }
  }

  // If only CI or e2e files changed, still test all backends
  const affectedServices = [...affectedSet].filter((s) => !['ci', 'e2e'].includes(s));
  if (affectedServices.length === 0) {
    return { affectedServices: ['nodejs', 'fastapi', 'django'], changedFiles: files, serviceFiles, reason: 'No service-specific changes — testing all backends' };
  }

  return { affectedServices, changedFiles: files, serviceFiles };
}
