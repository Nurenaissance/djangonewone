import express from 'express';
import sessionManager from '../sessionManager.js';

const router = express.Router();

/**
 * Health check endpoint
 * Checks server status and component health WITHOUT sending real WhatsApp messages
 */
router.get("/health", async (req, res) => {
    const startTime = Date.now();
    const checks = {
        server: 'healthy',
        redis: 'unknown',
        sessions: 'unknown',
        timestamp: new Date().toISOString()
    };

    try {
        // Check Redis connectivity via session manager
        try {
            if (sessionManager.isConnected) {
                // Verify with a ping-like operation
                const sessionCount = await sessionManager.size();
                checks.redis = 'healthy';
                checks.sessions = {
                    status: 'healthy',
                    activeCount: sessionCount
                };
            } else {
                checks.redis = 'unhealthy';
                checks.sessions = { status: 'degraded', reason: 'Redis not connected' };
            }
        } catch (redisError) {
            checks.redis = 'unhealthy';
            checks.sessions = { status: 'unhealthy', error: redisError.message };
        }

        // Calculate overall health
        const isHealthy = checks.server === 'healthy' && checks.redis === 'healthy';
        checks.status = isHealthy ? 'healthy' : 'degraded';
        checks.responseTime = `${Date.now() - startTime}ms`;

        res.status(isHealthy ? 200 : 503).json(checks);
    } catch (error) {
        checks.status = 'unhealthy';
        checks.error = error.message;
        checks.responseTime = `${Date.now() - startTime}ms`;
        res.status(503).json(checks);
    }
});

/**
 * Detailed health check with all components
 */
router.get("/health/detailed", async (req, res) => {
    const startTime = Date.now();
    const checks = {
        server: { status: 'healthy', uptime: process.uptime() },
        memory: {},
        redis: {},
        sessions: {},
        timestamp: new Date().toISOString()
    };

    try {
        // Memory usage
        const memUsage = process.memoryUsage();
        checks.memory = {
            status: 'healthy',
            heapUsed: `${Math.round(memUsage.heapUsed / 1024 / 1024)}MB`,
            heapTotal: `${Math.round(memUsage.heapTotal / 1024 / 1024)}MB`,
            rss: `${Math.round(memUsage.rss / 1024 / 1024)}MB`
        };

        // Redis/Sessions check
        try {
            if (sessionManager.isConnected) {
                const sessionCount = await sessionManager.size();
                checks.redis = { status: 'healthy' };
                checks.sessions = {
                    status: 'healthy',
                    activeCount: sessionCount
                };
            } else {
                checks.redis = { status: 'unhealthy', reason: 'Not connected' };
                checks.sessions = { status: 'degraded' };
            }
        } catch (redisError) {
            checks.redis = { status: 'unhealthy', error: redisError.message };
            checks.sessions = { status: 'unhealthy' };
        }

        // Calculate overall status
        const componentStatuses = [
            checks.server.status,
            checks.memory.status,
            checks.redis.status,
            checks.sessions.status
        ];

        if (componentStatuses.every(s => s === 'healthy')) {
            checks.status = 'healthy';
        } else if (componentStatuses.some(s => s === 'unhealthy')) {
            checks.status = 'unhealthy';
        } else {
            checks.status = 'degraded';
        }

        checks.responseTime = `${Date.now() - startTime}ms`;

        const statusCode = checks.status === 'healthy' ? 200 :
                          checks.status === 'degraded' ? 200 : 503;
        res.status(statusCode).json(checks);
    } catch (error) {
        checks.status = 'unhealthy';
        checks.error = error.message;
        checks.responseTime = `${Date.now() - startTime}ms`;
        res.status(503).json(checks);
    }
});

/**
 * Liveness probe - simple check that server is responding
 */
router.get("/health/live", (req, res) => {
    res.status(200).json({ status: 'alive', timestamp: new Date().toISOString() });
});

/**
 * Readiness probe - check if server is ready to accept traffic
 */
router.get("/health/ready", async (req, res) => {
    try {
        // Check Redis is connected
        if (!sessionManager.isConnected) {
            return res.status(503).json({
                status: 'not_ready',
                reason: 'Redis not connected',
                timestamp: new Date().toISOString()
            });
        }

        res.status(200).json({
            status: 'ready',
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        res.status(503).json({
            status: 'not_ready',
            error: error.message,
            timestamp: new Date().toISOString()
        });
    }
});

export default router;
