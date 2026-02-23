/**
 * Winston Logger Configuration
 * Provides structured logging for the WhatsApp bot server
 */
import winston from 'winston';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const logsDir = path.join(__dirname, '..', 'logs');

// Ensure logs directory exists
if (!fs.existsSync(logsDir)) {
  fs.mkdirSync(logsDir, { recursive: true });
}

// Custom format for console (human readable)
const consoleFormat = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
  winston.format.errors({ stack: true }),
  winston.format.printf(({ timestamp, level, message, ...meta }) => {
    const metaStr = Object.keys(meta).length ? JSON.stringify(meta) : '';
    return `${timestamp} [${level.toUpperCase()}] ${message} ${metaStr}`;
  })
);

// Custom format for file (JSON for easy parsing)
const fileFormat = winston.format.combine(
  winston.format.timestamp(),
  winston.format.errors({ stack: true }),
  winston.format.json()
);

// Create logger instance
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  defaultMeta: { service: 'whatsapp-bot-server' },
  transports: [
    // Error logs (error level only)
    new winston.transports.File({
      filename: path.join(logsDir, 'error.log'),
      level: 'error',
      format: fileFormat,
      maxsize: 10 * 1024 * 1024, // 10MB
      maxFiles: 5,
      tailable: true
    }),
    // Combined logs (all levels)
    new winston.transports.File({
      filename: path.join(logsDir, 'combined.log'),
      format: fileFormat,
      maxsize: 10 * 1024 * 1024, // 10MB
      maxFiles: 5,
      tailable: true
    })
  ],
  // Handle exceptions and rejections
  exceptionHandlers: [
    new winston.transports.File({
      filename: path.join(logsDir, 'exceptions.log'),
      format: fileFormat
    })
  ],
  rejectionHandlers: [
    new winston.transports.File({
      filename: path.join(logsDir, 'rejections.log'),
      format: fileFormat
    })
  ]
});

// Add console transport for non-production
if (process.env.NODE_ENV !== 'production') {
  logger.add(new winston.transports.Console({
    format: consoleFormat
  }));
} else {
  // In production, use JSON format for console (easier to parse in Azure logs)
  logger.add(new winston.transports.Console({
    format: winston.format.combine(
      winston.format.timestamp(),
      winston.format.json()
    )
  }));
}

// Helper methods for common logging patterns
logger.webhook = (action, data = {}) => {
  logger.info(`[WEBHOOK] ${action}`, { category: 'webhook', ...data });
};

logger.message = (action, data = {}) => {
  logger.info(`[MESSAGE] ${action}`, { category: 'message', ...data });
};

logger.queue = (action, data = {}) => {
  logger.info(`[QUEUE] ${action}`, { category: 'queue', ...data });
};

logger.session = (action, data = {}) => {
  logger.info(`[SESSION] ${action}`, { category: 'session', ...data });
};

logger.analytics = (action, data = {}) => {
  logger.info(`[ANALYTICS] ${action}`, { category: 'analytics', ...data });
};

logger.api = (action, data = {}) => {
  logger.info(`[API] ${action}`, { category: 'api', ...data });
};

// Request logging middleware
export const requestLogger = (req, res, next) => {
  const start = Date.now();

  res.on('finish', () => {
    const duration = Date.now() - start;
    logger.api('Request completed', {
      method: req.method,
      url: req.originalUrl || req.url,
      status: res.statusCode,
      duration: `${duration}ms`,
      ip: req.ip || req.connection?.remoteAddress
    });
  });

  next();
};

export default logger;
