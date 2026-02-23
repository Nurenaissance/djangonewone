
import { sendTextMessage, fastURL, djangoURL, sendNodeMessage } from "../mainwebhook/snm.js"
import { normalizePhone } from "../normalize.js";
import { userSessions, messageCache } from "../server.js";
import { findNextNodesFromEdges, findNodeById } from "./edge-navigation.js";
import axios from "axios";

const fallback_messages = {
    as: "দয়া করে সঠিক ইনপুট দিন",
    bh: "कृपया सही इनपुट दें",
    bn: "দয়া করে সঠিক ইনপুট দিন",
    gu: "કૃપા કરીને સahi ઇનપુટ આપો",
    hi: "कृपया सही इनपुट दें",
    kn: "ದಯವಿಟ್ಟು ಸರಿಯಾದ ಇನ್‌ಪುಟ್ ನೀಡಿರಿ",
    mr: "कृपया योग्य इनपुट द्या",
    or: "ଦୟାକରି ସଠିକ୍ ଇନପୁଟ୍ ଦିଅନ୍ତୁ"
}

export async function executeFallback(userSession) {
    // TEMPORARILY SIMPLIFIED LOGGING FOR HJIQOHE DEBUGGING
    var fallback_count = userSession.fallback_count
    const userPhoneNumber = userSession.userPhoneNumber
    const business_phone_number_id = userSession.business_phone_number_id
    const sessionKey = userPhoneNumber + business_phone_number_id

    // If flow is already completed, don't do anything - the restart handler will take care of it
    if (userSession.flowCompleted) {
        console.log(`[executeFallback] Flow already completed for ${userPhoneNumber}, skipping`);
        return;
    }

    if (fallback_count > 0) {
        const fallback_msg = fallback_messages?.[userSession.language] || userSession.fallback_msg
        const access_token = userSession.accessToken
        const response = await sendTextMessage(userPhoneNumber, business_phone_number_id, fallback_msg, access_token)
        fallback_count = fallback_count - 1;
        userSession.fallback_count = fallback_count
        await userSessions.set(sessionKey, userSession);
    }
    else {
        if (userSession.isTrigger) {
            // For trigger flows, mark as completed and delete session
            console.log(`[executeFallback] Trigger flow completed for ${userPhoneNumber}`);
            await userSessions.delete(sessionKey);
        }
        else {
            // For regular flows, reset to start instead of marking complete (original behavior)
            userSession.currNode = userSession.startNode
            userSession.nextNode = userSession.adjList[userSession.currNode]
            userSession.fallback_count = userSession.max_fallback_count || 1
            await userSessions.set(sessionKey, userSession);
            await sendNodeMessage(userPhoneNumber, business_phone_number_id);
        }
    }
}

export async function addContact(phone, name, bpid) {
    phone = normalizePhone(phone);
    try {
        const c_data = {
            name: name,
            phone: phone
        }
        await axios.post(`${djangoURL}/contacts_by_tenant/`, c_data, {
            headers: { 'bpid': bpid }
        })
    } catch (error) {
        console.error('Error Occured while adding contact: ', error.message)
    }
}

export async function addDynamicModelInstance(modelName, updateData, tenant) {
    const url = `${djangoURL}/dynamic-model-data/${modelName}/`;
    const data = updateData;
    try {
        const response = await axios.post(url, data, {
            headers: {
                'Content-Type': 'application/json',
                'X-Tenant-Id': tenant
            },
        });
        console.log('Data updated successfully:', response.data);
        return response.data;
    } catch (error) {
        if (error.response) {
            console.error(`Failed to add dynamic model instance: ${error.response.status}`, JSON.stringify(error.response.data, null, 5));
        } else if (error.request) {
            console.error('No response received:', error.request);
        } else {
            console.error('Error in setting up the request:', error.message);
        }
        return null;
    }
}

export async function replacePlaceholders(message, userSession = {}, contact = null, tenant = null) {
    // TEMPORARILY SIMPLIFIED LOGGING FOR HJIQOHE DEBUGGING
    const placeholders = [...message.matchAll(/{{\s*[\w._\[\]]+\s*}}/g)] || [];

    if (userSession && !contact) contact = userSession.userPhoneNumber
    if (userSession && !tenant) tenant = userSession.tenant

    if (placeholders && placeholders.length > 0) {
        for (const placeholder of placeholders) {
            let key = placeholder[0].slice(2, -2).trim();
            const keys = key.split('.')
            if (keys[0] == 'contact') {
                let contactData = messageCache.get(contact)
                if (!contactData) {
                    const response = await axios.get(`${djangoURL}/contacts-by-phone/${contact}`, { headers: { 'X-Tenant-Id': tenant } })
                    // Fix: API returns an object, not an array
                    contactData = Array.isArray(response.data) ? response.data[0] : response.data;
                    messageCache.set(contact, contactData)
                }
                if (keys.length > 1) {
                    // Support nested paths like contact.customField.name or contact.name
                    let replacementValue = contactData;
                    const fieldPath = keys.slice(1).filter(k => k !== ''); // Remove empty strings from trailing dots

                    for (const field of fieldPath) {
                        if (replacementValue && replacementValue[field] !== undefined) {
                            replacementValue = replacementValue[field];
                        } else {
                            // If path not found, try direct field access (fallback)
                            replacementValue = contactData?.[field] || '';
                            break;
                        }
                    }

                    // Ensure we have a string value
                    replacementValue = replacementValue !== null && replacementValue !== undefined ? String(replacementValue) : '';
                    message = message.replace(placeholder[0], replacementValue);
                }
            }
            else if (keys[0] == 'api') {
                const data_source = userSession.api.GET
                const nestedKeyPath = keys.slice(1).join('.');
                const replacementValue = await getNestedValue(data_source, nestedKeyPath) || '';

                message = message.replace(placeholder[0], replacementValue);
            }
        }
    }
    return message;
}

async function getNestedValue(obj, keyPath) {
    if (!obj || !keyPath || typeof keyPath !== 'string') {
        return undefined; // Return undefined if obj or keyPath is invalid
    }

    // Split the key path into parts (e.g., "responseData1.user.name" -> ["responseData1", "user", "name"])
    const keys = keyPath.split('.');

    // Traverse the object to get the value
    let current = obj;
    for (const key of keys) {
        if (current[key] === undefined) {
            return undefined; // Key not found
        }
        current = current[key];
    }

    return current;
}

export async function updateStatus(status, message_id, business_phone_number_id, user_phone, broadcastGroup, tenant, timestamp) {
    // TEMPORARILY SIMPLIFIED LOGGING FOR HJIQOHE DEBUGGING
    let isRead = false;
    let isDelivered = false;
    let isSent = false;
    let isReplied = false;
    let isFailed = false;
    try {
        if (status === "replied") {
            isReplied = true;
        } else if (status === "read") {
            isRead = true;
        } else if (status === "delivered") {
            isDelivered = true;
        } else if (status === "sent") {
            isSent = true;
        } else if (status === "failed") {
            isFailed = true;
        }

        // Prepare data to send
        const data = {
            business_phone_number_id: business_phone_number_id,
            is_failed: isFailed,
            is_replied: isReplied,
            is_read: isRead,
            is_delivered: isDelivered,
            is_sent: isSent,
            user_phone: user_phone,
            message_id: message_id,
            bg_id: broadcastGroup?.id,
            bg_name: broadcastGroup?.name,
            template_name: broadcastGroup?.template_name,
            timestamp: timestamp
        };
        // Send POST request with JSON payload
        const response = await axios.post(`${fastURL}/set-status/`, data, {
            headers: {
                "X-Tenant-Id": tenant,
                "Content-Type": "application/json"
            }
        });
    } catch (error) {
        console.error("Error updating status:", error.response ? error.response.data : error.message);
    }
}

export async function validateInput(inputVariable, message) {
    try {
        const prompt = `Question being asked is: ${inputVariable}?\n
Response being given is: ${message}\n
Does the response answer the question? reply in yes or no. nothing else `

        const api_key = process.env.OPENAI_API_KEY;

        const data = {
            model: "gpt-4o-mini",
            messages: [
                {
                    role: "system",
                    content: "you are a helpful assisstant who replies in yes or no only"
                },
                {
                    role: "user",
                    content: prompt
                }
            ]
        }
        const response = await axios.post('https://api.openai.com/v1/chat/completions', data, {
            headers: {
                'Authorization': `Bearer ${api_key}`,
                'Content-Type': 'application/json',
            }
        });

        const validationResult = response.data.choices[0].message.content;
        return validationResult
    } catch (error) {
        console.error('Error validating input:', error);
        return false;
    }
}

export async function getTenantFromBpid(bpid) {
    try {
        var response = await axios.get(`${djangoURL}/get-tenant/?bpid=${bpid}`, {
        })
        // console.log("Tenant Response: ", response.data)
        const tenant = response.data.tenant
        return tenant
    } catch (error) {
        console.error(`Error getting tenant for ${bpid}: `, error)
    }
}

/**
 * Save message - NON-BLOCKING by default to prevent webhook delays
 * The Django backend can be slow (cold starts, DB issues), so we don't wait for it
 *
 * @param {boolean} options.blocking - Set to true to wait for save (default: false)
 */
export async function saveMessage(userPhoneNumber, business_phone_number_id, formattedConversation, tenant, timestamp, retryCount = 0, options = {}) {
    const { blocking = false, messageId = null } = typeof options === 'object' ? options : {};

    // If non-blocking, fire and forget
    if (!blocking) {
        saveMessageInternal(userPhoneNumber, business_phone_number_id, formattedConversation, tenant, timestamp, 0, messageId)
            .catch(err => console.error(`❌ [Background] Failed to save message for ${userPhoneNumber}:`, err.message));
        return { queued: true };
    }

    // Blocking mode - wait for result
    return saveMessageInternal(userPhoneNumber, business_phone_number_id, formattedConversation, tenant, timestamp, retryCount, messageId);
}

async function saveMessageInternal(userPhoneNumber, business_phone_number_id, formattedConversation, tenant, timestamp, retryCount = 0, messageId = null) {
    const MAX_RETRIES = 3;
    const RETRY_DELAYS = [2000, 4000, 8000]; // Increased delays for slow backend

    // Validate required parameters
    if (!userPhoneNumber || !business_phone_number_id || !formattedConversation || !tenant) {
        console.error("❌ saveMessage: Missing required parameters", {
            userPhoneNumber: !!userPhoneNumber,
            business_phone_number_id: !!business_phone_number_id,
            formattedConversation: !!formattedConversation,
            tenant: !!tenant
        });
        throw new Error("Missing required parameters for saveMessage");
    }

    // Ensure formattedConversation is an array
    if (!Array.isArray(formattedConversation)) {
        formattedConversation = [formattedConversation];
    }

    // Filter out undefined/null entries
    formattedConversation = formattedConversation.filter(conv => conv != null);

    if (formattedConversation.length === 0) {
        console.warn("⚠️ saveMessage: Empty conversation array, skipping save");
        return { skipped: true, reason: "empty conversation" };
    }

    try {
        const body = {
            contact_id: userPhoneNumber,
            business_phone_number_id: business_phone_number_id,
            conversations: formattedConversation,
            tenant: tenant,
            time: timestamp || new Date().toISOString(),
            ...(messageId && { message_id: messageId })
        };

        const response = await axios.post(
            `${djangoURL}/whatsapp_convo_post/${userPhoneNumber}/?source=whatsapp`,
            body,
            {
                headers: {
                    'Content-Type': 'application/json',
                    'X-Tenant-Id': tenant
                },
                timeout: 30000 // Increased to 30 seconds for slow backend
            }
        );
        console.log(`✅ Message saved for ${userPhoneNumber}`);
        return response.data;
    } catch (error) {
        const isRetryable =
            error.code === 'ECONNABORTED' || // Timeout
            error.code === 'ECONNRESET' ||   // Connection reset
            error.code === 'ETIMEDOUT' ||    // Timeout
            error.message?.includes('socket hang up') || // Socket closed
            (error.response?.status >= 500 && error.response?.status < 600) || // Server errors
            error.response?.status === 429;  // Rate limited

        if (isRetryable && retryCount < MAX_RETRIES) {
            const delay = RETRY_DELAYS[retryCount] || 8000;
            console.warn(`⚠️ saveMessage failed (attempt ${retryCount + 1}/${MAX_RETRIES}), retrying in ${delay}ms...`);
            console.warn(`   Error: ${error.message}`);

            await new Promise(resolve => setTimeout(resolve, delay));
            return saveMessageInternal(userPhoneNumber, business_phone_number_id, formattedConversation, tenant, timestamp, retryCount + 1, messageId);
        }

        console.error(`❌ Error saving conversation for ${userPhoneNumber} (final attempt):`, error.message);
        if (error.response) {
            console.error("Response status:", error.response.status);
            console.error("Response data:", JSON.stringify(error.response.data));
        }
        throw error; // Re-throw so caller knows it failed
    }
}

export async function sendNotification(notif, tenant) {
    try {
        await axios.post(`${fastURL}/notifications`, notif,
            {
                headers: {
                    'X-Tenant-Id': tenant
                }
            }
        )
        // console.log("Response Sending Notification: ", res.data)
    }
    catch (error) {
        console.error(`Error sending notification: ${error}`)
    }
}

export async function updateLastSeen(type, time, phone, bpid) {
    try {
        await axios.patch(`${djangoURL}/update-last-seen/${phone}/${type}`, { time: time }, { headers: { bpid: bpid } })
    } catch (error) {
        // Silent fail for non-critical operation
    }
}

export async function getSession(business_phone_number_id, contact, skipAddContact = false, retryCount = 0) {
    const MAX_RETRIES = 3;

    // Prevent infinite recursion
    if (retryCount >= MAX_RETRIES) {
        throw new Error(`Session initialization failed after ${MAX_RETRIES} attempts. Please check backend connectivity and service authentication.`);
    }

    try {
        // TEMPORARILY SIMPLIFIED LOGGING FOR HJIQOHE DEBUGGING
        const userPhoneNumber = contact?.wa_id
        // Better contact name handling - only use fallback if truly no name available
let userName = null;
if (contact?.profile?.name && contact.profile.name.trim() !== '') {
    userName = contact.profile.name.trim();
}
// Don't set a default "Nuren User" - let it be null if no name is available

        const key = String(userPhoneNumber) + String(business_phone_number_id);
        let userSession = await userSessions.get(key);

        if (!userSession) {
            // Only add contact if skipAddContact is false
            if (!skipAddContact) {
                addContact(userPhoneNumber, userName, business_phone_number_id)
            }
            try {
                let responseData = messageCache.get(business_phone_number_id)

                // Validate cached data - if it's missing critical fields, refetch
                if (responseData) {
                    const whatsappData = responseData?.whatsapp_data?.[0];
                    const hasValidData = whatsappData && (whatsappData.adj_list || whatsappData.nodes);
                    if (!hasValidData) {
                        messageCache.del(business_phone_number_id); // NodeCache uses del() not delete()
                        responseData = null;
                    }
                }

                // Service authentication headers
                const serviceHeaders = {
                    'bpid': business_phone_number_id,
                    'X-Service-Key': process.env.NODEJS_SERVICE_KEY || process.env.NODE_SERVICE_KEY
                };

                //Get tenant from Fast
                if (!responseData) {
                    try {
                        const response = await axios.get(`${fastURL}/whatsapp_tenant`, {
                            headers: serviceHeaders,
                            timeout: 10000
                        });
                        responseData = response.data
                        messageCache.set(business_phone_number_id, responseData)
                    } catch (error) {
                        // FastAPI fallback to Django
                    }
                }
                //Get tenant from Django
                if (!responseData) {
                    try {
                        const response = await axios.get(`${djangoURL}/whatsapp_tenant`, {
                            headers: serviceHeaders,
                            timeout: 10000
                        });
                        responseData = response.data
                        messageCache.set(business_phone_number_id, responseData)
                    } catch (error) {
                        // Django also failed
                    }
                }
                //Get tenant failed from both
                if (!responseData) {
                    throw new Error(`Both Backends failed!! FastAPI: ${fastURL}, Django: ${djangoURL}. Check: 1) Services are running 2) NODEJS_SERVICE_KEY is set 3) Network connectivity`);
                }

                // DUAL MODE DETECTION
                const whatsappData = responseData?.whatsapp_data[0];
                const flowVersion = whatsappData?.flow_version || 1;
                let multilingual = whatsappData.multilingual;
                let flowData, adjList, startNode, currNode, nextNode, nodes, edges, startNodeId;

                if (flowVersion === 2) {
                    // NEW MODE: Use nodes + edges
                    nodes = whatsappData.nodes;
                    edges = whatsappData.edges;
                    startNodeId = whatsappData.start_node_id;
                    currNode = startNodeId;
                    nextNode = findNextNodesFromEdges(edges, currNode);

                    // For compatibility with sendNodeMessage
                    flowData = nodes;  // Store nodes in flowData for now
                    adjList = null;    // No adjacency list
                    startNode = startNodeId;
                } else {
                    // LEGACY MODE: Use flow_data + adj_list
                    if (multilingual) flowData = responseData?.whatsapp_data;
                    else flowData = whatsappData.flow_data;

                    adjList = whatsappData?.adj_list;
                    startNode = whatsappData?.start !== null ? whatsappData?.start : 0;
                    currNode = startNode;
                    nextNode = adjList?.[currNode] || [];

                    nodes = null;
                    edges = null;
                    startNodeId = null;
                }

                if (!flowData && !nodes) console.error("[getSession] Flow Data missing for bpid:", business_phone_number_id)

                let triggers = {};
                responseData.triggers.forEach(element => {
                    triggers[element.trigger] = element.id;
                });

                userSession = {
                    type: "chatbot",
                    AIMode: false,
                    lastActivityTime: Date.now(),

                    // Mode detection
                    flowVersion: flowVersion,

                    // Legacy fields
                    flowData: flowData || [],
                    adjList: adjList || {},
                    startNode: startNode,

                    // New fields
                    nodes: nodes || null,
                    edges: edges || null,
                    startNodeId: startNodeId || null,

                    // Navigation
                    currNode: currNode,
                    nextNode: nextNode,

                    // Common fields
                    accessToken: whatsappData.access_token,
                    accountID: whatsappData.business_account_id,
                    flowName: whatsappData.flow_name || "",
                    business_phone_number_id: whatsappData.business_phone_number_id,
                    tenant: whatsappData.tenant_id,
                    userPhoneNumber: userPhoneNumber,
                    userName: userName,
                    inputVariable: null,
                    inputVariableType: null,
                    fallback_msg: whatsappData.fallback_message || "please provide correct input",
                    fallback_count: whatsappData.fallback_count != null ? whatsappData.fallback_count : 1,
                    max_fallback_count: whatsappData.fallback_count != null ? whatsappData.fallback_count : 1,
                    products: responseData.catalog_data,
                    language: "en",
                    multilingual: multilingual,
                    doorbell: whatsappData?.introductory_msg || null,
                    api: {
                        POST: {},
                        GET: {}
                    },
                    triggers: triggers,
                    isTrigger: false,
                    hop_nodes: whatsappData.hop_nodes || [],
                    agents: responseData.agents || [],
                    agentModeEnabled: whatsappData.agent_mode_enabled || false,
                    agentSystemPrompt: whatsappData.agent_system_prompt || null
                };

                const key = userPhoneNumber + business_phone_number_id
                await userSessions.set(key, userSession);
            } catch (error) {
                console.error(`Error fetching tenant data for user ${userPhoneNumber}:`, error.message);
                throw error;
            }
        } else {
            // DEBUG: Log what we retrieved from Redis
            console.log(`[getSession] Retrieved existing session: currNode=${userSession.currNode}, inputVariable="${userSession.inputVariable || 'null'}"`);

            userSession.lastActivityTime = Date.now()

            // Update nextNode based on mode
            if (userSession.currNode != null) {
                if (userSession.flowVersion === 2) {
                    // New mode: use edges
                    userSession.nextNode = findNextNodesFromEdges(userSession.edges, userSession.currNode);
                } else {
                    // Legacy mode: use adj_list
                    // Safety check: ensure adjList exists
                    if (!userSession.adjList) {
                        await userSessions.delete(userPhoneNumber + business_phone_number_id);
                        messageCache.del(business_phone_number_id); // Clear bad cached data
                        return await getSession(business_phone_number_id, contact, skipAddContact, retryCount + 1);
                    }
                    userSession.nextNode = userSession.adjList[userSession.currNode];
                }
            }
            else if (userSession.isTrigger) {
                await userSessions.delete(userPhoneNumber + business_phone_number_id);
                messageCache.del(business_phone_number_id); // Clear cached data for fresh trigger
                return await getSession(business_phone_number_id, contact, skipAddContact, retryCount + 1);
            }
            else {
                userSession.currNode = userSession.flowVersion === 2 ? userSession.startNodeId : userSession.startNode;

                if (userSession.flowVersion === 2) {
                    userSession.nextNode = findNextNodesFromEdges(userSession.edges, userSession.currNode);
                } else {
                    // Safety check: ensure adjList exists before accessing
                    if (!userSession.adjList) {
                        await userSessions.delete(userPhoneNumber + business_phone_number_id);
                        messageCache.del(business_phone_number_id); // Clear bad cached data
                        return await getSession(business_phone_number_id, contact, skipAddContact, retryCount + 1);
                    }
                    userSession.nextNode = userSession.adjList[userSession.currNode];
                }

                userSession.fallback_count = userSession.max_fallback_count || 1;
            }
        }
        return userSession;
    } catch (error) {
        console.error("Error in getSession: ", error);
        throw new Error(`Session initialization failed: ${error.message}`)
    }
}

export async function triggerFlowById(userSession, id) {
    try {
        const serviceHeaders = {
            'X-Service-Key': process.env.NODEJS_SERVICE_KEY || process.env.NODE_SERVICE_KEY
        };

        console.log(`[triggerFlowById] Flow ${id}`);
        const response = await axios.get(`${djangoURL}/flows/${id}/`, {
            headers: serviceHeaders,
            timeout: 10000
        });

        const apiData = response.data;

        // Django returns: data (array), adj_list (object), start (string), name (string)
        // Handle both Django format and alternative formats
        let flowData = apiData.data || apiData.flowData || apiData.flow_data || [];
        const adjList = apiData.adj_list || apiData.adjList || {};
        const startNode = apiData.start || apiData.startNode || apiData.start_node || "0";
        const flowName = apiData.name || apiData.flowName || apiData.flow_name || '';
        const fallback_msg = apiData.fallback_msg || apiData.fallback_message || "please provide correct input";
        const fallback_count = apiData.fallback_count != null ? apiData.fallback_count : 1;

        // Check if this is V2 node format (nodes have .data property with modern types)
        // V2 nodes use types like: askQuestion, sendMessage, start (with .data property containing optionType, variable, etc.)
        // V1 nodes use types like: Text, Button, List, string, image, customint (with body, variable at root level)
        // NOTE: "customint" exists in BOTH V1 and V2 - don't use it for detection
        let isV2NodeFormat = false;
        let nodesArray = [];

        if (Array.isArray(flowData)) {
            nodesArray = flowData;
            // Check first few nodes to detect format
            const sampleNode = flowData.find(n => n.type && n.type !== 'start');
            if (sampleNode) {
                // V2-exclusive types (these ONLY exist in V2)
                const v2ExclusiveTypes = ['askQuestion', 'sendMessage', 'setVariable', 'llmPrompt'];
                // V1-exclusive types (these ONLY exist in V1)
                const v1ExclusiveTypes = ['Text', 'Button', 'List', 'string', 'image', 'audio', 'video', 'location', 'template', 'AI', 'api', 'custom', 'flowjson'];

                // First check for V1-exclusive types (more reliable)
                const hasV1Type = flowData.some(n => v1ExclusiveTypes.includes(n.type));
                if (hasV1Type) {
                    isV2NodeFormat = false;
                }
                // Then check for V2-exclusive types
                else if (v2ExclusiveTypes.includes(sampleNode.type)) {
                    isV2NodeFormat = true;
                }
                // Check for V2-style .data property with V2-specific fields
                else if (sampleNode.data && (sampleNode.data.optionType || sampleNode.data.options || sampleNode.data.message)) {
                    isV2NodeFormat = true;
                }
                // Default to V1 for ambiguous cases
                else {
                    isV2NodeFormat = false;
                }
            }
        }

        if (isV2NodeFormat) {
            // HYBRID FORMAT: V2 nodes + V1 adjacency list
            // Convert adj_list to edges array for processNodeV2
            const edges = [];
            for (const [sourceId, targets] of Object.entries(adjList)) {
                if (Array.isArray(targets)) {
                    for (const targetId of targets) {
                        edges.push({
                            id: `${sourceId}-${targetId}`,
                            source: sourceId,
                            target: targetId
                        });
                    }
                }
            }

            const currNode = startNode;
            const nextNode = findNextNodesFromEdges(edges, currNode);

            userSession.flowVersion = 2;
            userSession.nodes = nodesArray;
            userSession.edges = edges;
            userSession.startNodeId = startNode;
            userSession.flowData = nodesArray;  // For compatibility
            userSession.adjList = adjList;      // Keep for reference
            userSession.startNode = startNode;
            userSession.currNode = currNode;
            userSession.nextNode = nextNode;
        } else {
            // TRUE V1 FORMAT: Convert array to object if needed
            if (Array.isArray(flowData)) {
                const flowDataObj = {};
                for (const node of flowData) {
                    if (node.id !== undefined) {
                        flowDataObj[node.id] = node;
                    }
                }
                flowData = flowDataObj;
            }

            const currNode = startNode;
            const nextNode = adjList?.[currNode] || [];

            userSession.flowVersion = 1;
            userSession.nodes = null;
            userSession.edges = null;
            userSession.startNodeId = null;
            userSession.flowData = flowData;
            userSession.adjList = adjList;
            userSession.startNode = startNode;
            userSession.currNode = currNode;
            userSession.nextNode = nextNode;
        }

        userSession.flowName = flowName;
        userSession.fallback_msg = fallback_msg;
        userSession.fallback_count = fallback_count;
        userSession.max_fallback_count = fallback_count;
        userSession.isTrigger = true;
        userSession.inputVariable = null;

        const { userPhoneNumber, business_phone_number_id } = userSession;

        // CRITICAL: Save session BEFORE calling sendNodeMessage
        const sessionKey = userPhoneNumber + business_phone_number_id;
        await userSessions.set(sessionKey, userSession);
        console.log(`[triggerFlowById] Flow ${id} ready, start=${userSession.currNode}, next=${JSON.stringify(userSession.nextNode)}`);

        await sendNodeMessage(userPhoneNumber, business_phone_number_id);
    } catch (error) {
        console.error(`[triggerFlowById] Error triggering flow ${id}:`, error.response?.data || error.message);
        throw error;
    }
}

/**
 * Trigger a flow by ID with a custom starting node
 * Used by HelloZestay to skip the welcome node when we already sent a personalized welcome
 */
export async function triggerFlowByIdWithStartNode(userSession, id, customStartNode) {
    try {
        const serviceHeaders = {
            'X-Service-Key': process.env.NODEJS_SERVICE_KEY || process.env.NODE_SERVICE_KEY
        };

        const response = await axios.get(`${djangoURL}/flows/${id}/`, {
            headers: serviceHeaders,
            timeout: 10000
        });

        const apiData = response.data;
        let flowData = apiData.data || apiData.flowData || apiData.flow_data || [];
        const adjList = apiData.adj_list || apiData.adjList || {};
        const flowName = apiData.name || apiData.flowName || apiData.flow_name || '';
        const fallback_msg = apiData.fallback_msg || apiData.fallback_message || "please provide correct input";
        const fallback_count = apiData.fallback_count != null ? apiData.fallback_count : 1;

        // Use custom start node if provided, otherwise use flow's default
        const startNode = customStartNode || apiData.start || apiData.startNode || apiData.start_node || "0";

        // Convert array flowData to object for V1 processing
        if (Array.isArray(flowData)) {
            const flowDataObj = {};
            for (const node of flowData) {
                if (node.id !== undefined) {
                    flowDataObj[node.id] = node;
                }
            }
            flowData = flowDataObj;
        }

        // Always use V1 format for HelloZestay (flow 209 is V1)
        let currNode = startNode;

        // Skip customint nodes at the start since HelloZestay already sent the welcome message
        // This prevents duplicate welcome messages from being sent via n8n
        const startNodeData = flowData[currNode] || flowData[String(currNode)];
        if (startNodeData?.type === 'customint') {
            const skipToNodes = adjList?.[currNode] || adjList?.[String(currNode)] || [];
            if (skipToNodes.length > 0) {
                console.log(`[triggerFlowByIdWithStartNode] Skipping customint node ${currNode} (welcome already sent), starting at ${skipToNodes[0]}`);
                currNode = skipToNodes[0];
            }
        }

        const nextNode = adjList?.[currNode] || adjList?.[String(currNode)] || [];

        userSession.flowVersion = 1;
        userSession.nodes = null;
        userSession.edges = null;
        userSession.startNodeId = null;
        userSession.flowData = flowData;
        userSession.adjList = adjList;
        userSession.startNode = startNode;
        userSession.currNode = currNode;
        userSession.nextNode = nextNode;
        userSession.flowName = flowName;
        userSession.fallback_msg = fallback_msg;
        userSession.fallback_count = fallback_count;
        userSession.max_fallback_count = fallback_count;
        userSession.isTrigger = true;
        userSession.inputVariable = null;

        console.log(`[triggerFlowByIdWithStartNode] Flow ${id}, start=${currNode}, next=${JSON.stringify(nextNode)}`);

        const { userPhoneNumber, business_phone_number_id } = userSession;
        const sessionKey = userPhoneNumber + business_phone_number_id;
        await userSessions.set(sessionKey, userSession);

        await sendNodeMessage(userPhoneNumber, business_phone_number_id);
    } catch (error) {
        console.error(`[triggerFlowByIdWithStartNode] Error:`, error.response?.data || error.message);
        throw error;
    }
}
