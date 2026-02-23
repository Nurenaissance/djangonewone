import pkg from 'pg';
const { Pool } = pkg;
import dotenv from 'dotenv';

dotenv.config();

// PostgreSQL connection pool - OPTIMIZED FOR AZURE
const pool = new Pool({
  host: process.env.ANALYTICS_DB_HOST || process.env.DB_HOST || 'localhost',
  port: process.env.ANALYTICS_DB_PORT || process.env.DB_PORT || 5432,
  database: process.env.ANALYTICS_DB_NAME || process.env.DB_NAME || 'analytics',
  user: process.env.ANALYTICS_DB_USER || process.env.DB_USER,
  password: process.env.ANALYTICS_DB_PASSWORD || process.env.DB_PASSWORD,
  max: 2, // REDUCED: Only 2 connections to prevent Azure slot exhaustion
  min: 0, // No minimum idle connections
  idleTimeoutMillis: 5000, // Release idle connections after 5s
  connectionTimeoutMillis: 10000, // Wait up to 10s for connection
  allowExitOnIdle: true, // Allow pool to close when all connections are idle
  // SSL configuration for Azure PostgreSQL
  ssl: process.env.DB_HOST?.includes('azure.com') || process.env.ANALYTICS_DB_HOST?.includes('azure.com')
    ? { rejectUnauthorized: false }
    : false,
});

// Test connection on startup
pool.on('connect', () => {
  console.log('✅ Analytics database connected');
});

pool.on('error', (err) => {
  console.error('❌ Unexpected error on idle client', err);
  // Don't exit on connection errors - let pool handle reconnection
});

pool.on('remove', () => {
  console.log('🔌 Connection removed from pool');
});

// Log pool stats periodically to monitor connection usage
setInterval(() => {
  console.log('📊 Pool Stats:', {
    total: pool.totalCount,
    idle: pool.idleCount,
    waiting: pool.waitingCount
  });
}, 60000); // Every 60 seconds

// Query helper
export async function query(text, params) {
  const start = Date.now();
  try {
    const res = await pool.query(text, params);
    const duration = Date.now() - start;
    if (duration > 1000) {
      console.warn(`⚠️ Slow query (${duration}ms):`, text.substring(0, 100));
    }
    return res;
  } catch (error) {
    console.error('❌ Database query error:', error);
    throw error;
  }
}

// Transaction helper
export async function transaction(callback) {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    const result = await callback(client);
    await client.query('COMMIT');
    return result;
  } catch (error) {
    await client.query('ROLLBACK');
    throw error;
  } finally {
    client.release();
  }
}

export default pool;
