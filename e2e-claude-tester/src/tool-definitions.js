/**
 * OpenAI function-calling tool schemas for the AI test orchestrator.
 */

const toolDefinitions = [
  {
    type: 'function',
    function: {
      name: 'http_request',
      description: 'Make a generic HTTP request to any URL. Use for ad-hoc endpoint checks not covered by specialized tools.',
      parameters: {
        type: 'object',
        properties: {
          url: { type: 'string', description: 'Full URL to request' },
          method: { type: 'string', enum: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'], default: 'GET' },
          headers: { type: 'object', description: 'HTTP headers as key-value pairs', additionalProperties: { type: 'string' } },
          body: { description: 'Request body (object or string). Ignored for GET.' },
          timeout: { type: 'number', description: 'Timeout in ms (default 10000)' },
        },
        required: ['url'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'check_health',
      description: 'Check the health of backend services. Returns status, response time, and component health.',
      parameters: {
        type: 'object',
        properties: {
          service: {
            type: 'string',
            enum: ['nodejs', 'fastapi', 'django', 'all'],
            description: 'Which service to health-check. Use "all" to check all three at once.',
          },
        },
        required: ['service'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'simulate_webhook',
      description: 'Send a simulated WhatsApp webhook payload to the Node.js bot server. The server should respond with 200 (acknowledgment). This does NOT send real WhatsApp messages.',
      parameters: {
        type: 'object',
        properties: {
          message_type: {
            type: 'string',
            enum: ['text', 'button_reply', 'list_reply', 'nfm_reply', 'image', 'status_update'],
            description: 'Type of WhatsApp message to simulate.',
          },
          text: { type: 'string', description: 'Text content (for message_type=text)' },
          button_id: { type: 'string', description: 'Button ID (for button_reply)' },
          button_title: { type: 'string', description: 'Button display title (for button_reply)' },
          list_id: { type: 'string', description: 'List item ID (for list_reply)' },
          list_title: { type: 'string', description: 'List item title (for list_reply)' },
          nfm_response_json: { type: 'string', description: 'JSON string of form response (for nfm_reply)' },
          status_type: { type: 'string', enum: ['sent', 'delivered', 'read', 'failed'], description: 'Status type (for status_update)' },
          status_message_id: { type: 'string', description: 'Message ID for the status update' },
          caption: { type: 'string', description: 'Caption for image messages' },
        },
        required: ['message_type'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'test_campaign_api',
      description: 'Validate campaign API endpoints on the Node.js server. Tests error handling and parameter validation (read-only, never sends real messages).',
      parameters: {
        type: 'object',
        properties: {
          action: {
            type: 'string',
            enum: ['validate_status_endpoint', 'validate_list_endpoint', 'validate_stop_endpoint', 'validate_resume_endpoint'],
            description: 'Which campaign endpoint to validate.',
          },
        },
        required: ['action'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'test_auth',
      description: 'Test authentication flow: Django login endpoint and JWT token verification on FastAPI.',
      parameters: {
        type: 'object',
        properties: {
          action: {
            type: 'string',
            enum: ['login', 'verify_token', 'full_flow'],
            description: '"login" tests the Django login endpoint. "verify_token" logs in then verifies the JWT on FastAPI. "full_flow" runs both.',
          },
        },
        required: ['action'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'run_webhook_flow',
      description: 'Run a multi-step webhook conversation flow with delays between steps. Useful for testing greeting → menu → selection sequences.',
      parameters: {
        type: 'object',
        properties: {
          steps: {
            type: 'array',
            description: 'Array of webhook steps to execute in order.',
            items: {
              type: 'object',
              properties: {
                message_type: { type: 'string', enum: ['text', 'button_reply', 'list_reply', 'nfm_reply', 'image', 'status_update'] },
                text: { type: 'string' },
                button_id: { type: 'string' },
                button_title: { type: 'string' },
                list_id: { type: 'string' },
                list_title: { type: 'string' },
              },
              required: ['message_type'],
            },
          },
          delay_ms: { type: 'number', description: 'Delay between steps in ms (default 1500)' },
        },
        required: ['steps'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'report_test_result',
      description: 'Record the result of an individual test. Call this for EVERY test you run to build the final report.',
      parameters: {
        type: 'object',
        properties: {
          test_name: { type: 'string', description: 'Short descriptive name for the test (e.g. "Health Check - Node.js")' },
          status: { type: 'string', enum: ['pass', 'fail', 'skip'], description: 'Test outcome' },
          reason: { type: 'string', description: 'Human-readable explanation of why the test passed/failed/was skipped' },
          service: { type: 'string', description: 'Which service this test targets (nodejs, fastapi, django, frontend, cross-service)' },
          duration_ms: { type: 'number', description: 'How long the test took in milliseconds' },
        },
        required: ['test_name', 'status', 'reason'],
      },
    },
  },
];

export default toolDefinitions;
