/**
 * AI test orchestrator — tool-use conversation loop via OpenAI SDK → GitHub Models.
 */

import OpenAI from 'openai';
import config from './config.js';
import toolDefinitions from './tool-definitions.js';
import { executeTool } from './tool-executor.js';

const SYSTEM_PROMPT = `You are an automated E2E tester for a WhatsApp Business Automation platform with 3 backend services:
- **Node.js** (bot server): Handles WhatsApp webhooks, campaign management, session handling
- **FastAPI**: Contacts API, notifications, scheduled events, health monitoring
- **Django**: User authentication, CRM, tenant management, admin

## Your testing protocol:

1. **Always check health first** using check_health with service="all". If a service is unhealthy, skip tests that depend on it and report them as "skip".

2. **Webhook tests**: When you call simulate_webhook, the bot server should respond with HTTP 200. A 200 means the webhook was received and acknowledged — this is a PASS. The bot processes messages asynchronously, so you won't see the bot's reply in the webhook response.

3. **Campaign API tests**: These validate error handling. We expect specific HTTP error codes (400, 404) for invalid inputs. Getting the expected error code = PASS.

4. **Auth tests**: Only run if TEST_USERNAME/TEST_PASSWORD are configured. A successful login returns a JWT token.

5. **Never send real WhatsApp messages**. All webhook simulations go to our own bot server with test data.

6. **Call report_test_result for EVERY test** you run, with a clear pass/fail/skip status and human-readable reason.

7. **Be cost-conscious**: Don't repeat tests. Don't make unnecessary API calls. Be systematic and efficient.

8. **Adapt based on results**: If health checks reveal issues, adjust your testing strategy. If a webhook returns 500, investigate with a different payload before marking as fail.

## Test execution order:
1. Health checks (all services)
2. Webhook tests (text → button → list → image → status → flow)
3. Campaign API validation
4. Auth flow tests
5. FastAPI endpoint tests

After all tests, provide a brief summary of results.`;

/**
 * Run the AI-powered test session.
 * @param {object} context - { affectedServices, relevantTests, changedFiles, diffSummary }
 * @returns {object} Final results from the AI session
 */
export async function runTestSession(context) {
  if (!config.ai.token) {
    console.error('GITHUB_TOKEN not set — cannot connect to GitHub Models.');
    process.exit(1);
  }

  const client = new OpenAI({
    baseURL: config.ai.baseURL,
    apiKey: config.ai.token,
  });

  const userMessage = buildUserMessage(context);
  console.log('\n--- AI Test Session Starting ---');
  console.log(`Model: ${config.ai.model}`);
  console.log(`Affected services: ${context.affectedServices.join(', ')}`);
  console.log(`Tests to run: ${context.relevantTests.length}`);
  console.log('');

  const messages = [
    { role: 'system', content: SYSTEM_PROMPT },
    { role: 'user', content: userMessage },
  ];

  let turns = 0;
  let totalToolCalls = 0;

  while (turns < config.ai.maxTurns) {
    turns++;

    let response;
    try {
      response = await client.chat.completions.create({
        model: config.ai.model,
        messages,
        tools: toolDefinitions,
        temperature: 0.1,
        max_tokens: 4096,
      });
    } catch (err) {
      console.error(`AI API error on turn ${turns}:`, err.message);
      if (turns < 3) {
        // Retry once on early failures
        await new Promise((r) => setTimeout(r, 2000));
        continue;
      }
      break;
    }

    const choice = response.choices[0];
    const assistantMessage = choice.message;
    messages.push(assistantMessage);

    // If the AI produced a final text response (no tool calls), we're done
    if (!assistantMessage.tool_calls || assistantMessage.tool_calls.length === 0) {
      console.log('\n--- AI Summary ---');
      console.log(assistantMessage.content || '(no summary)');
      break;
    }

    // Process tool calls
    for (const toolCall of assistantMessage.tool_calls) {
      totalToolCalls++;
      if (totalToolCalls > config.ai.maxToolCalls) {
        console.warn(`Tool call limit (${config.ai.maxToolCalls}) reached — stopping.`);
        messages.push({ role: 'tool', tool_call_id: toolCall.id, content: JSON.stringify({ error: 'Tool call limit reached' }) });
        continue;
      }

      const { name, arguments: args } = toolCall.function;
      console.log(`  [Tool ${totalToolCalls}] ${name}(${truncate(args, 100)})`);

      const result = await executeTool(name, args);
      messages.push({ role: 'tool', tool_call_id: toolCall.id, content: result });
    }

    // Safety: if we hit max turns, tell the AI to wrap up
    if (turns === config.ai.maxTurns - 1) {
      messages.push({ role: 'user', content: 'You are running out of turns. Please call report_test_result for any remaining tests and provide your final summary.' });
    }
  }

  console.log(`\nSession complete: ${turns} turns, ${totalToolCalls} tool calls`);
  return { turns, totalToolCalls };
}

function buildUserMessage(context) {
  let msg = `## Test Session Context\n\n`;
  msg += `**Affected services:** ${context.affectedServices.join(', ')}\n`;
  msg += `**Test scope:** ${config.test.scope}\n\n`;

  if (context.changedFiles && context.changedFiles.length > 0) {
    msg += `### Changed files (${context.changedFiles.length}):\n`;
    for (const f of context.changedFiles.slice(0, 30)) {
      msg += `- ${f}\n`;
    }
    if (context.changedFiles.length > 30) msg += `- ... and ${context.changedFiles.length - 30} more\n`;
    msg += '\n';
  }

  if (context.diffSummary) {
    msg += `### Diff summary:\n${context.diffSummary}\n\n`;
  }

  msg += `### Tests to run (${context.relevantTests.length}):\n`;
  for (const t of context.relevantTests) {
    msg += `- [${t.category}] ${t.name} (services: ${t.services.join(', ')})\n`;
  }

  msg += `\nPlease begin testing. Start with health checks, then proceed through the test list. Call report_test_result for each test.`;
  return msg;
}

function truncate(str, max) {
  if (!str) return '';
  return str.length > max ? str.slice(0, max) + '...' : str;
}
