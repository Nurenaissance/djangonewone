import express from 'express';
import { getSession, triggerFlowById } from '../helpers/misc.js';
import { messageCache, userSessions } from '../server.js';

const router = express.Router();

router.post("/trigger-flow", async (req, res) => {
    try {
        const business_phone_number_id = req.body.business_phone_number_id;
        const userPhoneNumber = req.body.userPhoneNumber;
        const userName = req.body.userName;
        const id = req.body.id;
        
        // Validate required fields
        if (!business_phone_number_id || !userPhoneNumber || !userName || !id) {
            return res.status(400).json({ 
                "Error": "Missing required fields: business_phone_number_id, userPhoneNumber, userName, id" 
            });
        }
        
        const contact = {
            wa_id: userPhoneNumber,
            profile: { name: userName.trim() }
        };
        
        const userSession = await getSession(business_phone_number_id, contact);
        await triggerFlowById(userSession, id);
        res.status(200).json({ "message": "trigger flow successfully set" });
    } catch (error) {
        console.log("Error Occurred setting trigger flow:", error.response?.data || error.message);
        res.status(500).json({ "Error": "Error Occurred setting trigger flow" });
    }
});

// Clear flow cache for a business phone number - call this when flow is updated from frontend
router.post("/clear-cache", async (req, res) => {
    try {
        const { business_phone_number_id } = req.body;

        if (!business_phone_number_id) {
            return res.status(400).json({
                "error": "Missing required field: business_phone_number_id"
            });
        }

        // Clear the tenant/flow data cache for this bpid
        const deleted = messageCache.del(business_phone_number_id);

        console.log(`[clear-cache] Cache cleared for bpid: ${business_phone_number_id}, was cached: ${deleted > 0}`);

        res.status(200).json({
            "message": "Cache cleared successfully",
            "business_phone_number_id": business_phone_number_id,
            "was_cached": deleted > 0
        });
    } catch (error) {
        console.error("Error clearing cache:", error.message);
        res.status(500).json({ "error": "Error clearing cache" });
    }
});

// Clear user session - forces user to get fresh flow data on next message
router.post("/clear-session", async (req, res) => {
    try {
        const { business_phone_number_id, userPhoneNumber } = req.body;

        if (!business_phone_number_id || !userPhoneNumber) {
            return res.status(400).json({
                "error": "Missing required fields: business_phone_number_id, userPhoneNumber"
            });
        }

        const sessionKey = userPhoneNumber + business_phone_number_id;
        await userSessions.delete(sessionKey);

        console.log(`[clear-session] Session cleared for user: ${userPhoneNumber}, bpid: ${business_phone_number_id}`);

        res.status(200).json({
            "message": "User session cleared successfully",
            "userPhoneNumber": userPhoneNumber,
            "business_phone_number_id": business_phone_number_id
        });
    } catch (error) {
        console.error("Error clearing session:", error.message);
        res.status(500).json({ "error": "Error clearing session" });
    }
});

// Clear ALL caches for a bpid - both flow cache and all user sessions for that bpid
router.post("/refresh-flow", async (req, res) => {
    try {
        const { business_phone_number_id } = req.body;

        if (!business_phone_number_id) {
            return res.status(400).json({
                "error": "Missing required field: business_phone_number_id"
            });
        }

        // Clear flow data cache
        const cacheDeleted = messageCache.del(business_phone_number_id);

        console.log(`[refresh-flow] Flow cache cleared for bpid: ${business_phone_number_id}`);
        console.log(`[refresh-flow] New flow data will be fetched on next user message`);

        res.status(200).json({
            "message": "Flow refreshed - new conversations will use updated flow",
            "business_phone_number_id": business_phone_number_id,
            "cache_cleared": cacheDeleted > 0,
            "note": "Existing user sessions will continue with old flow until they restart or session expires"
        });
    } catch (error) {
        console.error("Error refreshing flow:", error.message);
        res.status(500).json({ "error": "Error refreshing flow" });
    }
});

export default router; 
