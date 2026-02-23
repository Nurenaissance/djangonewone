/**
 * Auth tester — validates Django login + JWT verification against FastAPI.
 */

import config from '../config.js';
import { httpRequest } from './http-request.js';

export async function testAuth({ action }) {
  switch (action) {
    case 'login': {
      if (!config.auth.username || !config.auth.password) {
        return { action, pass: false, skipped: true, reason: 'TEST_USERNAME/TEST_PASSWORD not set' };
      }
      const result = await httpRequest({
        url: `${config.services.django}/login/`,
        method: 'POST',
        body: { username: config.auth.username, password: config.auth.password },
      });
      const hasToken = result.body && (result.body.token || result.body.access || result.body.access_token);
      return {
        action,
        status: result.status,
        has_token: !!hasToken,
        pass: result.status === 200 && !!hasToken,
        responseTime_ms: result.responseTime_ms,
      };
    }

    case 'verify_token': {
      // First login to get a token
      if (!config.auth.username || !config.auth.password) {
        return { action, pass: false, skipped: true, reason: 'TEST_USERNAME/TEST_PASSWORD not set' };
      }
      const loginRes = await httpRequest({
        url: `${config.services.django}/login/`,
        method: 'POST',
        body: { username: config.auth.username, password: config.auth.password },
      });
      if (loginRes.status !== 200 || !loginRes.body) {
        return { action, pass: false, reason: 'Login failed, cannot verify token', login_status: loginRes.status };
      }
      const token = loginRes.body.token || loginRes.body.access || loginRes.body.access_token;
      if (!token) {
        return { action, pass: false, reason: 'No token in login response' };
      }
      // Verify token on FastAPI protected endpoint
      const verifyRes = await httpRequest({
        url: `${config.services.fastapi}/contacts/`,
        method: 'GET',
        headers: { Authorization: `Bearer ${token}` },
      });
      return {
        action,
        login_status: loginRes.status,
        verify_status: verifyRes.status,
        pass: verifyRes.status !== 401 && verifyRes.status !== 403,
        responseTime_ms: loginRes.responseTime_ms + verifyRes.responseTime_ms,
      };
    }

    case 'full_flow': {
      const loginResult = await testAuth({ action: 'login' });
      if (!loginResult.pass) {
        return { action, pass: false, reason: 'Login step failed', login: loginResult };
      }
      const verifyResult = await testAuth({ action: 'verify_token' });
      return {
        action,
        pass: loginResult.pass && verifyResult.pass,
        login: loginResult,
        verify: verifyResult,
      };
    }

    default:
      return { error: `Unknown auth action: ${action}. Valid: login, verify_token, full_flow` };
  }
}
