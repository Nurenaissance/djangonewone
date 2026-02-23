#!/usr/bin/env node

/**
 * Quick script to fix missing await keywords for userSessions operations
 * Run with: node fix_async_sessions.js
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const filesToFix = [
    'mainwebhook/userWebhook.js',
    'routes/webhookRoute.js',
    'send-message.js',
    'webhooks/businessWebhook.js',
    'webhooks/campaignWebhook.js',
    'webhooks/manualWebhook.js',
    'routes/authRoute.js'
];

const replacements = [
    // Fix userSessions.get without await
    {
        pattern: /(\s+)(const|let|var)\s+(\w+)\s*=\s*userSessions\.get\(/g,
        replacement: '$1$2 $3 = await userSessions.get('
    },
    // Fix userSessions.set without await (with semicolon)
    {
        pattern: /(\s+)userSessions\.set\((.*?)\);/g,
        replacement: '$1await userSessions.set($2);'
    },
    // Fix userSessions.delete without await (with semicolon)
    {
        pattern: /(\s+)userSessions\.delete\((.*?)\);/g,
        replacement: '$1await userSessions.delete($2);'
    }
];

let totalFixed = 0;

for (const file of filesToFix) {
    const filePath = path.join(__dirname, file);

    if (!fs.existsSync(filePath)) {
        console.log(`⚠️  File not found: ${file}`);
        continue;
    }

    let content = fs.readFileSync(filePath, 'utf8');
    let fileFixed = 0;

    for (const { pattern, replacement } of replacements) {
        const matches = content.match(pattern);
        if (matches) {
            fileFixed += matches.length;
            content = content.replace(pattern, replacement);
        }
    }

    if (fileFixed > 0) {
        fs.writeFileSync(filePath, content, 'utf8');
        console.log(`✅ Fixed ${fileFixed} issues in ${file}`);
        totalFixed += fileFixed;
    } else {
        console.log(`✓  No issues found in ${file}`);
    }
}

console.log(`\n🎉 Total fixes applied: ${totalFixed}`);
console.log('\n⚠️  Manual review recommended for complex cases!');
