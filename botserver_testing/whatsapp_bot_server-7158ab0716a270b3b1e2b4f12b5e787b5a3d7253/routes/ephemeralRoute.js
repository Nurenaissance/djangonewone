import express from 'express';

const router = express.Router();

/**
 * POST /api/ephemeral
 * Create an ephemeral session key for OpenAI Realtime API
 */
router.post('/api/ephemeral', async (req, res) => {
  try {
    // Get the API key and strip any quotes
    let apiKey = process.env.OPENAI_API_KEY;

    if (!apiKey) {
      console.error('❌ OPENAI_API_KEY not configured in environment');
      console.error('📍 Environment variable name: OPENAI_API_KEY');
      console.error('📍 Looking in file: .env');
      return res.status(500).json({ error: "OpenAI API key not configured" });
    }

    // Strip surrounding quotes if present (common .env issue)
    apiKey = apiKey.replace(/^["'](.*)["']$/, '$1');

    // Debug logging (hide middle part of key for security)
    const keyPreview = apiKey ? `${apiKey.substring(0, 10)}...${apiKey.substring(apiKey.length - 10)}` : 'undefined';
    console.log('🔑 Using OpenAI API Key:', keyPreview);
    console.log('📏 Key length:', apiKey?.length || 0);
    console.log('📍 Key source: process.env.OPENAI_API_KEY from .env file');
    console.log('📡 Fetching ephemeral key from OpenAI...');

    // OpenAI Realtime API - create ephemeral client secret
    // Docs: https://platform.openai.com/docs/api-reference/realtime-sessions
    const result = await fetch("https://api.openai.com/v1/realtime/client_secrets", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        expires_after: {
          anchor: "created_at",
          seconds: 600 // 10 minutes
        },
        session: {
          type: "realtime",
          model: "gpt-4o-realtime-preview-2024-12-17",
          voice: "alloy", // Options: alloy, echo, fable, onyx, nova, shimmer
        }
      }),
    });

    if (!result.ok) {
      const errorData = await result.json().catch(() => ({}));
      console.error("❌ OpenAI API Error:", result.status, errorData);

      if (result.status === 401) {
        return res.status(401).json({ error: "Invalid OpenAI API key" });
      }
      if (result.status === 403) {
        return res.status(403).json({ error: "API key lacks Realtime API access" });
      }
      if (result.status === 429) {
        return res.status(429).json({ error: "Rate limit exceeded" });
      }

      return res.status(result.status).json({
        error: "OpenAI API request failed",
        details: errorData
      });
    }

    const data = await result.json();

    // OpenAI returns: { value: "ek_xxx...", expires_at: timestamp }
    if (!data.value) {
      console.error("❌ Unexpected response structure:", data);
      return res.status(500).json({
        error: "Invalid response from OpenAI",
        raw: data
      });
    }

    const ephemeralKey = data.value;
    console.log('✅ Ephemeral key created successfully');
    console.log(`🔑 Ephemeral key preview: ${ephemeralKey.substring(0, 10)}...`);
    console.log(`⏰ Expires at: ${data.expires_at ? new Date(data.expires_at * 1000).toISOString() : 'N/A'}`);

    return res.status(200).json({ key: ephemeralKey });

  } catch (error) {
    console.error("❌ Ephemeral Key Error:", error);
    return res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/ephemeral
 * Also handle GET requests (for easier testing)
 */
router.get('/api/ephemeral', async (req, res) => {
  try {
    // Get the API key and strip any quotes
    let apiKey = process.env.OPENAI_API_KEY;

    if (!apiKey) {
      console.error('❌ OPENAI_API_KEY not configured in environment');
      console.error('📍 Environment variable name: OPENAI_API_KEY');
      console.error('📍 Looking in file: .env');
      return res.status(500).json({ error: "OpenAI API key not configured" });
    }

    // Strip surrounding quotes if present (common .env issue)
    apiKey = apiKey.replace(/^["'](.*)["']$/, '$1');

    // Debug logging (hide middle part of key for security)
    const keyPreview = apiKey ? `${apiKey.substring(0, 10)}...${apiKey.substring(apiKey.length - 10)}` : 'undefined';
    console.log('🔑 Using OpenAI API Key (GET):', keyPreview);
    console.log('📏 Key length:', apiKey?.length || 0);
    console.log('📍 Key source: process.env.OPENAI_API_KEY from .env file');
    console.log('📡 Fetching ephemeral key from OpenAI (GET)...');

    const result = await fetch("https://api.openai.com/v1/realtime/client_secrets", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        expires_after: {
          anchor: "created_at",
          seconds: 600 // 10 minutes
        },
        session: {
          type: "realtime",
          model: "gpt-4o-realtime-preview-2024-12-17",
          voice: "alloy",
        }
      }),
    });

    if (!result.ok) {
      const errorData = await result.json().catch(() => ({}));
      console.error("❌ OpenAI API Error:", result.status, errorData);

      if (result.status === 401) {
        return res.status(401).json({ error: "Invalid OpenAI API key" });
      }
      if (result.status === 403) {
        return res.status(403).json({ error: "API key lacks Realtime API access" });
      }
      if (result.status === 429) {
        return res.status(429).json({ error: "Rate limit exceeded" });
      }

      return res.status(result.status).json({
        error: "OpenAI API request failed",
        details: errorData
      });
    }

    const data = await result.json();

    if (!data.value) {
      console.error("❌ Unexpected response structure:", data);
      return res.status(500).json({
        error: "Invalid response from OpenAI",
        raw: data
      });
    }

    const ephemeralKey = data.value;
    console.log('✅ Ephemeral key created successfully (GET)');
    console.log(`🔑 Ephemeral key preview: ${ephemeralKey.substring(0, 10)}...`);
    console.log(`⏰ Expires at: ${data.expires_at ? new Date(data.expires_at * 1000).toISOString() : 'N/A'}`);

    return res.status(200).json({ key: ephemeralKey });

  } catch (error) {
    console.error("❌ Ephemeral Key Error:", error);
    return res.status(500).json({ error: error.message });
  }
});

export default router;
