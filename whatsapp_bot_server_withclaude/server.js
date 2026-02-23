import express from "express";
import cors from 'cors';
import session from "express-session";
import dotenv from "dotenv";
import { createServer } from "http";
import { Server } from "socket.io";
import { createAdapter } from '@socket.io/redis-adapter';
import { createClient } from 'redis';
import NodeCache from 'node-cache';
import setupRoutes from './routes/index.js';
import { clearInactiveSessions } from './utils.js';
import { setupAggregationJobs } from './analytics/aggregation.js';
import "./setupAuth.js";
import sessionManager from './sessionManager.js';
import {
  apiRateLimiter,
  skipRateLimitForServices,
  conditionalRateLimit,
  cleanupRateLimiter
} from './middleware/rateLimiter.js';

// Initialize cache and other shared resources
export const messageCache = new NodeCache({ stdTTL: 600 });
export const userSessions = sessionManager; // Redis-based session manager
// nurenConsumerMap moved to Redis - see helpers/agentMapping.js

// Load environment variables
// Use override: true to force .env file to override system environment variables
dotenv.config({ override: true });

// Debug: Log OpenAI API Key on startup
const apiKey = process.env.OPENAI_API_KEY;
if (apiKey) {
  // Strip quotes if present
  const cleanKey = apiKey.replace(/^["'](.*)["']$/, '$1');
  const keyPreview = `${cleanKey.substring(0, 10)}...${cleanKey.substring(cleanKey.length - 10)}`;
  console.log('\n🔑 ============ OPENAI API KEY DEBUG ============');
  console.log(`🔑 API Key loaded: ${keyPreview}`);
  console.log(`📏 Key length: ${cleanKey.length}`);
  console.log(`📍 Key starts with: ${cleanKey.substring(0, 15)}...`);
  console.log('🔑 ============================================\n');
} else {
  console.log('⚠️  WARNING: OPENAI_API_KEY not found in environment!\n');
}

// Server setup
const PORT = process.env.PORT || 8080;



const app = express();
const httpServer = createServer(app);
const allowedOrigins = [
  'http://localhost:8080',
  'http://localhost:5174',
  'http://localhost:5173',
  'https://whatsappbotserver.azurewebsites.net',
  'https://nuren.ai/',
  'https://nuren.ai',
  'https://nurenaiautomatic-b7hmdnb4fzbpbtbh.canadacentral-01.azurewebsites.net'
];

// Socket.io setup
export const io = new Server(httpServer, {
  cors: {
    origin: allowedOrigins,
    methods: ['GET', 'POST']
  }
});

// Redis adapter for Socket.IO multi-instance support
async function setupSocketIORedisAdapter() {
  try {
    const pubClient = createClient({ url: process.env.REDIS_URL || 'redis://localhost:6379' });
    const subClient = pubClient.duplicate();
    await Promise.all([pubClient.connect(), subClient.connect()]);
    io.adapter(createAdapter(pubClient, subClient));
    console.log('Socket.IO Redis adapter connected');
  } catch (err) {
    console.warn('Socket.IO Redis adapter failed, using default (single-instance):', err.message);
  }
}
setupSocketIORedisAdapter();

// Middleware setup
app.use(
  express.json({
    verify: (req, res, buf, encoding) => {
      req.rawBody = buf?.toString(encoding || "utf8");
    },
  }),
);

app.use(cors());

app.use((req, res, next) => {
  const origin = req.headers.origin;

  if (typeof origin === 'string' && allowedOrigins.includes(origin)) {
    res.setHeader('Access-Control-Allow-Origin', origin);
  }
  
  if (req.method === 'OPTIONS') {
    res.setHeader('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS, PATCH');
    return res.status(204).end();
  }
  
  res.setHeader('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS, PATCH');
  
  next();
});

app.use(session({
  secret: 'my_whatsapp_nuren_adarsh',
  resave: false,
  saveUninitialized: true,
  cookie: { secure: true }
}));

// Rate limiting middleware
// Skip rate limiting for internal service-to-service calls
app.use(skipRateLimitForServices);
// Apply rate limiting to all routes (will be skipped for service calls)
app.use(conditionalRateLimit(apiRateLimiter));

// Setup routes
setupRoutes(app);

// Socket.io connection handling
io.on('connection', (socket) => {
  console.log('a user connected');

  // Campaign room management for real-time progress updates
  socket.on('join:campaign', ({ batchId }) => {
    if (batchId) {
      socket.join(`campaign:${batchId}`);
      console.log(`Socket ${socket.id} joined campaign room: ${batchId}`);
    }
  });

  socket.on('leave:campaign', ({ batchId }) => {
    if (batchId) {
      socket.leave(`campaign:${batchId}`);
      console.log(`Socket ${socket.id} left campaign room: ${batchId}`);
    }
  });

  socket.on('disconnect', () => {
    console.log('user disconnected');
  });
});

// Session cleanup
setInterval(clearInactiveSessions, 60 * 60 * 1000);

// Setup analytics aggregation cron jobs
try {
  setupAggregationJobs();
  console.log('✅ Analytics aggregation jobs initialized');
} catch (error) {
  console.error('❌ Failed to initialize analytics aggregation jobs:', error);
}

// Start server
httpServer.listen(PORT, () => {
  console.log(`Server is listening on port: ${PORT}`);
});

// Graceful shutdown handling
async function gracefulShutdown(signal) {
  console.log(`\n${signal} received. Starting graceful shutdown...`);

  try {
    // Close HTTP server
    await new Promise((resolve, reject) => {
      httpServer.close((err) => {
        if (err) reject(err);
        else resolve();
      });
    });
    console.log('✅ HTTP server closed');

    // Close Socket.IO
    io.close();
    console.log('✅ Socket.IO closed');

    // Disconnect session manager
    await sessionManager.disconnect();

    // Cleanup rate limiter
    await cleanupRateLimiter();

    console.log('✅ Graceful shutdown complete');
    process.exit(0);
  } catch (error) {
    console.error('❌ Error during shutdown:', error);
    process.exit(1);
  }
}

// Handle shutdown signals
process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));