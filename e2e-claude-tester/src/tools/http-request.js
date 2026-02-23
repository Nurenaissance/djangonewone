/**
 * Generic HTTP request tool — foundation for all API interactions.
 */

import config from '../config.js';

export async function httpRequest({ url, method = 'GET', headers = {}, body = null, timeout }) {
  const controller = new AbortController();
  const timeoutMs = timeout || config.test.timeout;
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  const start = Date.now();

  try {
    const opts = {
      method,
      headers: { 'Content-Type': 'application/json', ...headers },
      signal: controller.signal,
    };
    if (body && method !== 'GET') {
      opts.body = typeof body === 'string' ? body : JSON.stringify(body);
    }

    const res = await fetch(url, opts);
    const responseTime_ms = Date.now() - start;

    let responseBody;
    const text = await res.text();
    try {
      responseBody = JSON.parse(text);
    } catch {
      responseBody = text;
    }

    // Truncate large payloads to keep AI context small
    const bodyStr = JSON.stringify(responseBody);
    if (bodyStr && bodyStr.length > 4000) {
      responseBody = bodyStr.slice(0, 4000) + '... [truncated]';
    }

    return { status: res.status, body: responseBody, responseTime_ms, success: res.ok };
  } catch (err) {
    return {
      status: 0,
      body: null,
      responseTime_ms: Date.now() - start,
      success: false,
      error: err.name === 'AbortError' ? `Request timed out after ${timeoutMs}ms` : err.message,
    };
  } finally {
    clearTimeout(timer);
  }
}
