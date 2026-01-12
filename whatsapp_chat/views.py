from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json, requests
from dynamic_entities.views import create_dynamic_model, createDynamicModel
from django.db import DatabaseError, transaction
from dynamic_entities.views import DynamicModelListView
from django.db import connection
from .models import WhatsappTenantData
from .tasks import process_message_status
from rest_framework import generics
from tenant.models import Tenant
from django.utils import timezone
from node_temps.models import NodeTemplate
from django.forms.models import model_to_dict
from shop.models import Products
from helpers.tables import get_db_connection
from datetime import datetime, timedelta


def process_flow_v2(flow, tenant):
    """
    New simplified flow processor - stores nodes and edges directly
    without ID conversion or node expansion.

    This function processes flow data in the new v2 format, eliminating the complexity
    of ID conversion and node expansion used in the legacy convert_flow function.

    Args:
        flow (dict): Frontend flow with {nodes: [...], edges: [...]}
        tenant (object): Tenant object

    Returns:
        tuple: (nodes, edges, start_node_id, collected_fields)
            - nodes: List of node objects from frontend (unchanged)
            - edges: List of edge objects from frontend (unchanged)
            - start_node_id: String ID of the starting node
            - collected_fields: List of field definitions for dynamic model creation
    """
    try:
        print("Processing flow v2 (new mode)")
        nodes = flow.get('nodes', [])
        edges = flow.get('edges', [])
        fields = []
        start_node_id = None

        # Find start node from edges
        for edge in edges:
            if edge.get('source') == 'start':
                start_node_id = edge.get('target')
                break

        if not start_node_id:
            print("Warning: No start node found in edges")
            # Fallback: use first non-start node
            for node in nodes:
                if node.get('type') != 'start':
                    start_node_id = node.get('id')
                    break

        # Extract dynamic model fields from askQuestion nodes
        for node in nodes:
            node_type = node.get('type')
            if node_type == 'askQuestion':
                data = node.get('data', {})
                variable = data.get('variable')
                data_type = data.get('dataType', 'string')

                if variable:
                    # Map frontend dataType to database field type
                    field_type_mapping = {
                        'string': 'string',
                        'number': 'integer',
                        'integer': 'integer',
                        'text': 'text',
                        'boolean': 'boolean',
                        'date': 'date',
                        'bigint': 'bigint'
                    }

                    db_field_type = field_type_mapping.get(data_type.lower(), 'string')

                    fields.append({
                        'field_name': variable,
                        'field_type': db_field_type
                    })

        print(f"Flow v2 processed: {len(nodes)} nodes, {len(edges)} edges, start: {start_node_id}, fields: {len(fields)}")
        return nodes, edges, start_node_id, fields

    except Exception as e:
        print(f"Error in process_flow_v2: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None, None


# converts node template data into whatsapp tenant data (LEGACY)
def convert_flow(flow, tenant):
    """
        Converts a flow configuration into a structured node graph with adjacency list representation.
        
        Processes various node types (questions, messages, conditions, etc.) from an input flow format,
        creates normalized nodes with sequential IDs, and builds an adjacency list for graph traversal.
        
        Args:
            flow (dict): The input flow configuration containing nodes and edges
            tenant (object): Tenant object containing organization-specific configuration (e.g., catalog_id)
            
        Returns:
            tuple: (nodes, adjacency_list, start_node, collected_fields) 
                - nodes: List of processed node objects
                - adjacency_list: Adjacency list representation of node connections
                - start_node: ID of the starting node
                - collected_fields: List of variables collected from question nodes
                
        Raises:
            Exception: Catches and logs any processing errors, returns (None, None) on failure
    """
     
    fields = []

    # Extract tenant-specific catalog ID if available
    if tenant.catalog_id != None:
        catalog_id = tenant.catalog_id
    try:
        print("Received flow: ", flow)
        node_blocks = flow['nodes']
        edges = flow['edges']

        nodes = []
        adjList = []
        current_id = 0  # Sequential ID counter for new node format

        # Process each node in the input flow
        for node_block in node_blocks:

            # Skip start nodes as they're handled in edge processing
            if node_block['type'] == "start":
                continue;
            
            # Handle Question Nodes
            if node_block['type'] == 'askQuestion':
                data = node_block['data']
                base_node = {
                    "oldIndex": node_block["id"],
                    "id": current_id,
                    "body": data['question'] or "Choose Option:"
                }

                # Add optional delay if present
                delay = data.get('delay')
                if delay:
                    base_node['delay'] = delay

                # Collect variables for data capture
                if data['variable'] and data['dataType']: 
                    fields.append({
                        'field_name': data['variable'] or None,
                        'field_type': data['dataType'] or None
                    })
                    base_node.update({
                        'variable': data['variable'],
                        'variableType': data['variable']
                    })

                # Process different question response types
                if data['optionType'] == 'Buttons':
                    base_node["type"] = "Button"
                    if data.get('med_id'):
                        base_node["mediaID"] = data['med_id']
                    
                    nodes.append(base_node)
                    parent_id = current_id
                    current_id += 1
                    adjList.append([])  # Initialize adjacency list for parent

                    # Create child nodes for each button option
                    for option in data['options']:
                        btn_node = {
                            "id": current_id,
                            "body": option or "Choose Option:",
                            "type": "button_element"
                        }
                        nodes.append(btn_node)
                        adjList.append([])
                        adjList[parent_id].append(current_id)
                        current_id += 1
                
                elif data['optionType'] == 'Text':
                    base_node["type"] = "Text"
                    if data.get('med_id'):
                        base_node["mediaID"] = data['med_id']
                    nodes.append(base_node)
                    adjList.append([])
                    current_id += 1

                elif data['optionType'] == 'Lists':
                    base_node["type"] = "List"
                    nodes.append(base_node)
                    if data.get('listTitle'):
                        base_node["listTitle"] = data['listTitle']
                    parent_id = current_id
                    current_id += 1
                    adjList.append([])

                    # Create list item nodes
                    for option in data['options']:
                        if isinstance(option, dict):
                            body = option.get("title", "Choose Option:")
                            list_node = {
                                "id": current_id,
                                "body": body,
                                "type": "list_element"
                            }
                            if "description" in option and option["description"]:
                                list_node["description"] = option["description"]
                        else:
                            list_node = {
                                "id": current_id,
                                "body": option or "Choose Option:",
                                "type": "list_element"
                            }
                        nodes.append(list_node)
                        adjList.append([])
                        adjList[parent_id].append(current_id)
                        current_id += 1

            # Handle Message Nodes
            elif node_block['type'] == 'sendMessage':
                data = node_block['data']
                msg_node = {
                    "oldIndex": node_block["id"],
                    "id": current_id,
                }

                delay = data.get('delay')
                if delay:
                    msg_node['delay'] = delay

                content = data['fields']['content']
                msg_type = data["fields"]['type']

                # Process different media types
                if msg_type == "text":
                    msg_node.update({
                        "type": "string",
                        "body": content['text']
                    })
                elif msg_type == "Image":
                    msg_node.update({
                        "type": "image",
                        "body": {"caption": content["caption"], "id": content["med_id"]}
                    })
                    # Add localized captions
                    for key, value in content.items():
                        if key.startswith('caption') and '_' in key:  # Avoid overwriting the 'text' key
                            language = key.split('_')[-1]  # Get language code (hi, mr, etc.)
                            msg_node['body'][f'caption_{language}'] = value

                elif msg_type == "Location":
                    msg_node["type"] = "location"
                    msg_node["body"] = {
                        "latitude": content["latitude"],
                        "longitude": content["longitude"],
                        "name": content["loc_name"],
                        "address": content["address"]
                    }
                elif msg_type == "Audio":
                    msg_node["type"] = "audio"
                    msg_node["body"] = {"audioID" : content["audioID"]}

                elif msg_type == "Video":
                    msg_node["type"] = "video"
                    msg_node["body"] = {"videoID" : content["videoID"]}
                
                nodes.append(msg_node)
                adjList.append([])
                current_id += 1

            elif node_block['type'] == 'setCondition':
                data = node_block['data']
                cond_node = {
                    "oldIndex": node_block["id"],
                    "id": current_id,
                    "body": data['condition'],
                    "type": "Button"
                }

                # Add optional delay and localized conditions
                for key, value in data.items():
                        if key.startswith('condition') and '_' in key:  # Avoid overwriting the 'text' key
                            language = key.split('_')[-1]  # Get language code (hi, mr, etc.)
                            cond_node[f'body_{language}'] = value

                delay = data.get('delay')
                if delay:
                    cond_node['delay'] = delay
                
                nodes.append(cond_node)
                adjList.append([])
                parent_id = current_id
                current_id += 1

                node = {
                    "id": id,
                    "body": "Yes",
                    "type": "button_element"
                }
                
                for choice in ["Yes", "No"]:
                    choice_node = {
                        "id": current_id,
                        "body": choice,
                        "type": "button_element"
                    }
                    nodes.append(choice_node)
                    adjList.append([])
                    adjList[parent_id].append(current_id)
                    current_id += 1

            elif node_block['type'] == 'ai':
                data = node_block['data']
                ai_node = {
                    "oldIndex": node_block["id"],
                    "id": current_id,
                    "type": "AI",
                    "body": data['startMessage'],
                    "prompt": data['prompt']
                }
                delay = data.get('delay')
                if delay:
                    ai_node['delay'] = delay
                
                nodes.append(ai_node)
                adjList.append([])
                current_id += 1

            elif node_block['type'] == 'api':
                data = node_block['data']
                api_node = {
                    "oldIndex": node_block['id'],
                    "id": current_id,
                    "type": "api",
                }
                api_node['api'] = {
                    "method": data['method'],
                    "headers": data.get('headers', ''),
                    "endpoint": data['endpoint'],
                    "variable": data['variable']
                }
                delay = data.get('delay')
                if delay:
                    api_node['delay'] = delay

                nodes.append(api_node)
                adjList.append([])
                current_id += 1

            elif node_block['type'] == 'template':
                data = node_block['data']
                template_node = {
                    "oldIndex": node_block["id"],
                    "id": current_id,
                    "type": "template",
                    "name": data['template']
                }
                nodes.append(template_node)
                adjList.append([])
                current_id += 1

            elif node_block['type'] == 'customint':
                data = node_block['data']
                customint_node = {
                    "oldIndex": node_block["id"],
                    "id": current_id,
                    "type": "customint",
                    "body": data['uniqueId']
                }
                nodes.append(customint_node)
                adjList.append([])
                current_id += 1
            
            elif node_block['type'] == 'flowjson':
                data = node_block['data']
                flow_json = {
                    "oldIndex": node_block["id"],
                    "id": current_id,
                    "type": "flowjson",
                    "flowName": data.get('flowName', ''),
                    "header": data.get('header', ''),
                    "body": data.get('body', ''),
                    "footer": data.get('footer', ''),  
                    "cta": data.get('cta', '')
                }
                nodes.append(flow_json)
                adjList.append([])
                current_id += 1

        # Process edges to build adjacency list
        startNode = None
        for edge in edges:
            # Identify start node
            if edge['source'] == "start":
                startNodeIndex = int(edge['target'])
                print("start node index: ", startNodeIndex)
                for node in nodes:
                    if 'oldIndex' in node:
                        if int(node['oldIndex']) == startNodeIndex:
                            startNode = int(node['id'])

            # Build node connections
            else:
                source = int(edge['source'])
                target = int(edge['target'])

                # Handle conditional branches
                suffix = 0
                sourcehandle = edge['sourceHandle']
                if sourcehandle not in [None, "text"]:
                    if sourcehandle == "true":
                        suffix += 1
                    elif sourcehandle == "false":
                        suffix += 2
                    else:
                        suffix += int(sourcehandle[-1]) + 1
                
                # Map original IDs to new sequential IDs
                for node in nodes:
                    if 'oldIndex' in node:
                        if int(node['oldIndex']) == source:
                            print("source")
                            n_source = int(node['id']) + suffix
                        if int(node['oldIndex']) == target:
                            print("target")
                            n_target = int(node['id'])
                print(f"source: {source}, target: {target}")
                adjList[n_source].append(n_target)

        # Cleanup temporary IDs
        for node in nodes:
            node.pop('oldIndex', None)
        print(f"fields: {fields}, start: {startNode}")

        return nodes, adjList, startNode, fields

    except Exception as e:
        print(f"An error occurred in convert flow: {e}")
        return None, None
    
def reset_fastapi_cache(business_phone_number_id=None):
    try:
        headers = {}
        if business_phone_number_id:
            headers['bpid'] = str(business_phone_number_id)

        response = requests.post("https://fastapiyes-avaaadfjgzafe6ff.canadacentral-01.azurewebsites.net/reset-cache", headers=headers)
        
        try:
            print("Reset FastAPI cache:", response.status_code, response.json())
        except ValueError:
            print("Reset FastAPI cache non-JSON response:", response.status_code, response.text)
    except Exception as e:
        print("Error calling FastAPI:", e)


@csrf_exempt
def insert_whatsapp_tenant_data(request):
    try:
        # Parse JSON data from the request body
        data = json.loads(request.body.decode('utf-8'))
        print("Received data at insert data: ", data)
        tenant_id = request.headers.get('X-Tenant-Id')
        if not tenant_id:
            return JsonResponse({'status': 'error', 'mesage': 'no tenant id found in headers'}, status = 400)
        tenant = Tenant.objects.get(id=tenant_id)

        business_phone_number_id =request.headers.get('bpid')
        print("BPID:",business_phone_number_id)
        access_token = data.get('access_token')
        account_id = data.get('accountID')
        firstInsertFlag = data.get('firstInsert', False)  # flag to mark the insert of bpid, access token, account id
        hop_nodes = data.get('hop_nodes')


        if not business_phone_number_id:
            print("Business Phone Number not provided in request")
            
            # Fetch the first record matching the tenant_id
            record = WhatsappTenantData.objects.filter(tenant_id=tenant_id).first()
            
            if not record:
                return JsonResponse({'status': 'error', 'message': 'No WhatsApp tenant data found for this tenant'}, status=404)
            
            business_phone_number_id = record.business_phone_number_id
        
        if firstInsertFlag:
            try:
                print("First insert")
                if not all([business_phone_number_id, access_token, account_id]):
                    return JsonResponse({'status': 'error', 'message': 'Missing required fields'}, status=400)

                # query = '''
                # INSERT INTO whatsapp_tenant_data (business_phone_number_id, access_token, account_id, tenant_id)
                # VALUES (%s, %s, %s, %s)
                # '''
                # #insert fallback msg and count
                
                # with connection.cursor() as cursor:
                #     print("Executing query:", query, business_phone_number_id, access_token, account_id, tenant_id)
                #     cursor.execute(query, [business_phone_number_id, access_token, account_id, tenant_id])
                #     connection.commit()  # Commit the transaction
                # print("Query executed successfully")
                # return JsonResponse({'message': 'Data inserted successfully'})


                whatsapp_data = WhatsappTenantData.objects.create(
                    business_phone_number_id=business_phone_number_id,
                    access_token=access_token,
                    business_account_id=account_id,
                    tenant=tenant,
                    hop_nodes=hop_nodes  # New field added
                )
                reset_fastapi_cache(business_phone_number_id=business_phone_number_id)
                return JsonResponse({'status': 'success', 'bpid': whatsapp_data.business_phone_number_id})
                
            except Exception as e:
                print(f"An error occurred during first insert: {e}")
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

        else:
            node_template_id = data.get('node_template_id')
            use_v2 = data.get('use_flow_v2', False)  # Frontend flag for new mode

            node_template = NodeTemplate.objects.get(id = node_template_id)
            node_data = node_template.node_data
            flow_name = node_template.name
            fallback_count = node_template.fallback_count
            fallback_message = node_template.fallback_msg

            if node_data is not None:
                try:
                    print("Node Data: ", node_data)

                    # DUAL MODE DETECTION
                    if use_v2:
                        print("Using NEW flow system (v2)")
                        nodes, edges, start_node_id, dynamicModelFields = process_flow_v2(node_data, tenant)

                        if nodes is None:
                            return JsonResponse({'status': 'error', 'message': 'Flow v2 processing failed'}, status=500)

                        # Add phone_no field
                        dynamicModelFields.append({'field_name': 'phone_no', 'field_type': 'bigint'})

                        # Sanitize flow name and create dynamic model
                        flow_name_sanitized = DynamicModelListView.sanitize_model_name(model_name=flow_name)
                        print("new flow name: ", flow_name_sanitized)
                        createDynamicModel(flow_name_sanitized, dynamicModelFields, tenant_id)

                        # Update database with NEW MODE fields
                        whatsapp_data = WhatsappTenantData.objects.filter(tenant_id=tenant_id)
                        en_records = whatsapp_data.filter(language='en')
                        instance_to_update = en_records.order_by('id').first()

                        instance_to_update.nodes = nodes
                        instance_to_update.edges = edges
                        instance_to_update.start_node_id = start_node_id
                        instance_to_update.flow_version = 2
                        instance_to_update.fallback_count = fallback_count
                        instance_to_update.fallback_message = fallback_message
                        instance_to_update.flow_name = flow_name_sanitized
                        instance_to_update.hop_nodes = hop_nodes
                        instance_to_update.updated_at = timezone.now()
                        instance_to_update.introductory_msg = None
                        instance_to_update.multilingual = False

                        # Clear legacy fields
                        instance_to_update.flow_data = None
                        instance_to_update.adj_list = None
                        instance_to_update.start = None

                        instance_to_update.save()

                        whatsapp_data.exclude(id=instance_to_update.id).delete()
                        reset_fastapi_cache(business_phone_number_id=business_phone_number_id)

                        print(f"Flow v2 saved successfully: {flow_name_sanitized}")
                        return JsonResponse({
                            'status': 'success',
                            'message': 'Data successfully updated',
                            'flow_name': flow_name_sanitized,
                            'flow_version': 2
                        })

                    else:
                        print("Using LEGACY flow system (v1)")
                        flow_data, adj_list, start, dynamicModelFields = convert_flow(node_data, tenant)

                        dynamicModelFields.append({ 'field_name': 'phone_no', 'field_type': 'bigint'})

                        flow_name = DynamicModelListView.sanitize_model_name(model_name=flow_name)
                        print("new flow name: ", flow_name)
                        model_name= flow_name
                        fields = dynamicModelFields
                        print("model name: ", model_name, fields)
                        createDynamicModel(model_name, fields, tenant_id)

                        # Updating whatsapp_tenant_flow with flow_data and adj_list
                        whatsapp_data = WhatsappTenantData.objects.filter(tenant_id = tenant_id)
                        en_records = whatsapp_data.filter(language = 'en')

                        instance_to_update = en_records.order_by('id').first()

                        instance_to_update.flow_data = flow_data
                        instance_to_update.hop_nodes = hop_nodes
                        instance_to_update.adj_list = adj_list
                        instance_to_update.start = start
                        instance_to_update.flow_version = 1  # Mark as legacy
                        instance_to_update.fallback_count = fallback_count
                        instance_to_update.fallback_message = fallback_message
                        instance_to_update.flow_name = flow_name
                        instance_to_update.updated_at = timezone.now()
                        instance_to_update.introductory_msg = None
                        instance_to_update.multilingual = False
                        instance_to_update.save()

                        whatsapp_data.exclude(id=instance_to_update.id).delete()
                        reset_fastapi_cache(business_phone_number_id=business_phone_number_id)

                        print("Query executed successfully")
                        return JsonResponse({'status': 'success', 'message': 'data succesfully updated','flow_name':flow_name, 'flow_version': 1})

                except Exception as e:
                    print(f"An error occurred during update: {e}")
                    import traceback
                    traceback.print_exc()
                    return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            else:
                return JsonResponse({'message': 'No Node Data Present'}, status=400)
        
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        print(f"An unexpected error occurred at insert whatsapptenant data: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)    
    
@csrf_exempt
def get_whatsapp_tenant_data(request):
    try:
        tenant_id = request.headers.get('X-Tenant-Id')
        bpid = request.headers.get('bpid')
        
        print("TENANT AND BPID:", tenant_id, bpid)
        
        # Handle demo tenant mapping (like FastAPI)
        if tenant_id == "demo":
            tenant_id = 'ai'
        
        # Retrieve WhatsappTenantData for the specified tenant
        if tenant_id:
            # Get all whatsapp data for tenant (as array like FastAPI)
            whatsapp_data = WhatsappTenantData.objects.filter(tenant_id=tenant_id).order_by('id')
            if not whatsapp_data.exists():
                return JsonResponse({'error': 'WhatsappTenantData not found for tenant'}, status=404)
            whatsapp_data_json = []
            for wd in whatsapp_data:
                wd_dict = model_to_dict(wd)

                # Rename 'tenant' key to 'tenant_id' if it exists
                if 'tenant' in wd_dict:
                    wd_dict['tenant_id'] = wd_dict.pop('tenant')

                # Ensure flow_data is included in each whatsapp_data object (like FastAPI)
                if 'flow_data' not in wd_dict and hasattr(wd, 'flow_data'):
                    wd_dict['flow_data'] = wd.flow_data

                # Ensure flow_version is included (defaults to 1 for legacy)
                if 'flow_version' not in wd_dict:
                    wd_dict['flow_version'] = getattr(wd, 'flow_version', 1)

                # Include v2 fields if present
                if hasattr(wd, 'flow_version') and wd.flow_version == 2:
                    if 'nodes' not in wd_dict and hasattr(wd, 'nodes'):
                        wd_dict['nodes'] = wd.nodes
                    if 'edges' not in wd_dict and hasattr(wd, 'edges'):
                        wd_dict['edges'] = wd.edges
                    if 'start_node_id' not in wd_dict and hasattr(wd, 'start_node_id'):
                        wd_dict['start_node_id'] = wd.start_node_id

                whatsapp_data_json.append(wd_dict)
            
        elif bpid:
            # Get whatsapp data by business phone number ID
            whatsapp_data = WhatsappTenantData.objects.filter(business_phone_number_id=bpid)
            if not whatsapp_data.exists():
                return JsonResponse({'error': 'WhatsappTenantData not found for bpid'}, status=404)
            whatsapp_data_json = []
            for wd in whatsapp_data:
                wd_dict = model_to_dict(wd)

                # Rename 'tenant' key to 'tenant_id' if it exists
                if 'tenant' in wd_dict:
                    wd_dict['tenant_id'] = wd_dict.pop('tenant')

                # Ensure flow_data is included in each whatsapp_data object (like FastAPI)
                if 'flow_data' not in wd_dict and hasattr(wd, 'flow_data'):
                    wd_dict['flow_data'] = wd.flow_data

                # Ensure flow_version is included (defaults to 1 for legacy)
                if 'flow_version' not in wd_dict:
                    wd_dict['flow_version'] = getattr(wd, 'flow_version', 1)

                # Include v2 fields if present
                if hasattr(wd, 'flow_version') and wd.flow_version == 2:
                    if 'nodes' not in wd_dict and hasattr(wd, 'nodes'):
                        wd_dict['nodes'] = wd.nodes
                    if 'edges' not in wd_dict and hasattr(wd, 'edges'):
                        wd_dict['edges'] = wd.edges
                    if 'start_node_id' not in wd_dict and hasattr(wd, 'start_node_id'):
                        wd_dict['start_node_id'] = wd.start_node_id

                whatsapp_data_json.append(wd_dict)
            tenant_id = whatsapp_data.first().tenant_id
            
        else:
            return JsonResponse({'error': 'Either Tenant-ID or BPID header must be provided'}, status=400)
        
        # Get tenant data (assuming you have a Tenant model)
        try:
            tenant_data = Tenant.objects.get(id=tenant_id)
            # Assuming agents is a related field or property on Tenant model
            agents = getattr(tenant_data, 'agents', [])
            if hasattr(agents, 'all'):  # If it's a related manager
                agents = [model_to_dict(agent) for agent in agents.all()]
            else:
                agents = []
        except (Tenant.DoesNotExist, ImportError):
            # If Tenant model doesn't exist or agents field doesn't exist
            agents = []
        
        # Get node templates with triggers (assuming you have a NodeTemplate model)
        try:
            node_templates = NodeTemplate.objects.filter(
                tenant_id=tenant_id
            ).exclude(trigger__isnull=True).exclude(trigger='').values('id', 'name', 'trigger')
            
            triggers = [
                {"id": nt['id'], "name": nt['name'], "trigger": nt['trigger']}
                for nt in node_templates
            ]
        except (ImportError, Exception):
            # If NodeTemplate model doesn't exist, create empty triggers array
            triggers = []
        
        # Print data for debugging
        print("whatsapp_data:", whatsapp_data_json)
        print("agents:", agents)
        print("triggers:", triggers)
        
        # Return data in FastAPI-compatible structure
        response_data = {
            'whatsapp_data': whatsapp_data_json,  # Now an array like FastAPI
            'agents': agents,
            'triggers': triggers
        }
        
        return JsonResponse(response_data, safe=False)
    
    except DatabaseError as e:
        return JsonResponse({'error': 'Database error occurred', 'details': str(e)}, status=500)
    
    except Exception as e:
        print("Error occurred with tenant:", tenant_id)
        return JsonResponse({'error': 'An unexpected error occurred', 'details': str(e)}, status=500)
   
@csrf_exempt
def get_tenant(request):
    try:
        bpid = request.GET.get('bpid')
        if not bpid:
            print("no bpid---------------------------------")
            return JsonResponse({"error": "Missing 'bpid' parameter"}, status=400)
        
        whatsapp_data = WhatsappTenantData.objects.get(business_phone_number_id = bpid)
        res = whatsapp_data.tenant.id
        if res is None:
            print("no res---------------------------------")
            return JsonResponse({"error": f"No tenant found for bpid {bpid}"}, status=404)
        print("res----------------------", res)
        return JsonResponse({
            "tenant" : res
        })
    except Exception as e:
        print("Error in get_tenant: ", e)
        return JsonResponse({"error": "An error occurred while retrieving tenant", "details": str(e)}, status=500)

# @csrf_exempt
# def update_message_status(request):
#     try:
#         # Print the raw request body for debugging
#         # print("Received request:", request)
#         # print("Request body:", request.body.decode('utf-8'))
        
#         # Parse JSON data from the request body
#         data = json.loads(request.body)
#         tenant_id = request.headers.get('X-Tenant-Id')
#         print("tenant rcvd: ", tenant_id)
#         # print("Data Rcvd: ", data, tenant_id)
        
#         # Extract data from the JSON object
#         business_phone_number_id = data.get('business_phone_number_id')
#         isFailed = data.get('is_failed')
#         isReplied = data.get('is_replied')
#         isRead = data.get('is_read')
#         isDelivered = data.get('is_delivered')
#         isSent = data.get('is_sent')
#         phone_number = data.get('user_phone')
#         messageID = data.get('message_id')
#         broadcastGroup_id = data.get('bg_id')
#         broadcastGroup_name = data.get('bg_name')
#         template_name = data.get('template_name')
#         time = data.get('timestamp')
#         print("Time: ", time)

#         timestamp_seconds = time/ 1000

#         datetime_obj = datetime.fromtimestamp(timestamp_seconds)

#         # Format the datetime object as a string (PostgreSQL-compatible)
#         postgres_timestamp = datetime_obj.strftime('%Y-%m-%d %H:%M:%S')
        
#         with transaction.atomic():
#             with connection.cursor() as cursor:
#                 query = """
#                     INSERT INTO whatsapp_message_id (message_id, business_phone_number_id, sent, delivered, read, replied, failed, user_phone_number, broadcast_group, broadcast_group_name, template_name,tenant_id, last_seen)
#                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#                     ON CONFLICT (message_id)
#                     DO UPDATE SET
#                         sent = EXCLUDED.sent,
#                         delivered = EXCLUDED.delivered,
#                         read = EXCLUDED.read,
#                         failed = EXCLUDED.failed,
#                         replied = EXCLUDED.replied,
#                         last_seen = EXCLUDED.last_seen;
#                 """
#                 cursor.execute(query, [messageID, business_phone_number_id, isSent, isDelivered, isRead, isReplied, isFailed, phone_number, broadcastGroup_id, broadcastGroup_name, template_name, tenant_id, postgres_timestamp])
#             print("updated status for message id: ", messageID)
#             print(f"isSent: {isSent}, isDeli: {isDelivered}, isRead: {isRead}, isReplied: {isReplied} ", )

#         return JsonResponse({'message': 'Data inserted successfully'})
#     except json.JSONDecodeError as e:
#         print("JSON decode error:", e)
#         return JsonResponse({'error': 'Invalid JSON format'}, status=400)
#     except Exception as e:
#         print("Exception:", e)
#         return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def get_status(request):
    if request.method == 'GET':
        connection = get_db_connection()
        query = """
            SELECT *
            FROM whatsapp_message_id;
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()

            message_statuses = [
                {
                    "business_phone_number_id": row[0],
                    "is_sent": row[1],
                    "is_delivered": row[2],
                    "is_read": row[3],
                    "user_phone_number": row[4],
                    "message_id": row[5],
                    "broadcast_group": row[6],
                    "is_replied": row[7],
                    "is_failed": row[8]
                }
                for row in rows
            ]

            return JsonResponse({"message_statuses": message_statuses})

        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)


def send_template(name):
    print(f"Preparing to send template: {name}")
    
    bg_id = None
    template = {
        "name": "basic_template"
    }
    business_phone_number_id = 241683569037594
    phone_numbers = [919548265904]

    data = {
        "template": template,
        "business_phone_number_id": business_phone_number_id,
        "phone_numbers": phone_numbers
    }

    url = "https://localhost:8080/send-template"
    response = requests.post(url, json=data)

    if response.status_code == 200:
        print("Template sent successfully!")
    else:
        print(f"Failed to send template. Status code: {response.status_code}")

def check_for_schedule(scheduler):
    today = datetime.now().date()
    print(f"Checking schedule for today: {today}")

    scheduled_event = {
        "name": "basic_template",
        "scheduled_time": datetime(today.year, today.month, today.day, 17, 44)
    }

    print(f"Scheduled event time: {scheduled_event['scheduled_time']}")

    if scheduled_event['scheduled_time'].date() == today:
        time_diff = scheduled_event['scheduled_time'] - datetime.now()
        print(f"Time difference to scheduled event: {time_diff}")
        
        if time_diff.total_seconds() > 0:
            print(f"Scheduling event at {scheduled_event['scheduled_time']}")
            scheduler.add_job(send_template, 'date', run_date=scheduled_event['scheduled_time'], args=[scheduled_event['name']])
            print("Message Sent")
        else:
            print("The scheduled event time has already passed today.")
    else:
        print("No event scheduled for today.")

import json, os, openai
import logging
from datetime import datetime

from django.utils.timezone import make_aware
from celery import shared_task
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from contacts.models import Contact
# Configure logging
logger = logging.getLogger(__name__)

def convert_time(datetime_str):
    """
    Converts a date-time string from 'DD/MM/YYYY, HH:MM:SS.SSS'
    to PostgreSQL-compatible 'YYYY-MM-DD HH:MM:SS.SSS' format.
    
    Args:
        datetime_str (str): The date-time string to be converted.
    
    Returns:
        str: Converted date-time string in PostgreSQL format.
    """
    try:
        # Parse the input date-time string
        parsed_datetime = datetime.strptime(datetime_str, "%d/%m/%Y, %H:%M:%S.%f")
        aware_time = make_aware(parsed_datetime)
        postgres_format = aware_time.strftime("%Y-%m-%d %H:%M:%S.%f")
        return postgres_format
    except ValueError as e:
        print(f"Error converting datetime: {e}")
        return None
    

@csrf_exempt
@require_http_methods(["POST"])
def update_message_status(request):

    """
    View to queue message status updates for async processing
    
    :param request: HTTP request
    :return: JSON response with task status
    """
    try:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        
        required_fields = ['message_id', 'timestamp']
        if not all(data.get(field) for field in required_fields):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        raw_time = data['timestamp']
        data['timestamp'] = convert_time(raw_time)
        
        message_payload = {
            'message_id': data.get('message_id'),
            'data': data,
            'tenant_id': request.headers.get('X-Tenant-Id')
        }

        # Enqueue the task
        print("Message Payload: ", message_payload)
        task_1 = process_message_status.delay(message_payload)
        # task_2 = process_new_set_status.delay(message_payload)

        return JsonResponse({
            'message': 'Status update queued', 
            'task1_id': task_1.id,
            # 'task2_id': task_2.id
        }, status=202)

    except Exception as e:
        logger.error(f"Unexpected error in set-status: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

def check_task_status(request, task_id):
    """
    Check the status of a queued task
    
    :param request: HTTP request
    :param task_id: ID of the Celery task
    :return: JSON response with task status
    """
    try:
        from celery.result import AsyncResult
        
        task_result = AsyncResult(task_id)
        
        return JsonResponse({
            "task_id": task_id,
            "status": task_result.status,
            "result": task_result.result
        })
    
    except Exception as e:
        logger.error(f"Error checking task status: {e}")
        return JsonResponse({"error": "Could not retrieve task status"}, status=500)

@csrf_exempt
def new_set_status(request):
    try:
        data = json.loads(request.body)
        print("data receieved in new set status: ", data)
        

        connection = get_db_connection()
        cursor = connection.cursor()

        
        message_id = data.get('message_id')
        template_name, bg_group = get_template_name(message_id)

        key = bg_group or template_name
        print("Key : ", key)
        update_fields = []
        flag_to_column = {
            'is_sent': 'sent',
            'is_delivered': 'delivered',
            'is_read': 'read',
            'is_replied': 'replied',
            'is_failed': 'failed'
        }

        for flag, column in flag_to_column.items():
            if data.get(flag) is True:
                print("Column found: ", column)
                update_fields.append(f"{column} = {column} + 1")

        cursor.execute(f"SELECT 1 FROM new_set_status WHERE name = %s;", (key,))
        row_exists = cursor.fetchone()

        if row_exists:
            print("Row Exists: ", key)
            if update_fields:

                update_query = f"UPDATE new_set_status SET {', '.join(update_fields)} WHERE name = %s;"
                cursor.execute(update_query, (key,))
                message = "Record updated successfully."
            else:
                message = "No updates were made as no flags were set to True."
        else:
            print("Row does not exist: ", key)
            tenant_id = request.headers.get('X-Tenant-Id') # Assuming tenant_id is passed in the request
            insert_query = """
            INSERT INTO new_set_status (name, tenant_id, sent, delivered, read, replied, failed)
            VALUES (%s, %s, 1, 0, 0, 0, 0);
            """
            cursor.execute(insert_query, (key, tenant_id))
            message = "New record created successfully."

        connection.commit()
        cursor.close()
        connection.close()

        return JsonResponse({"status": "success", "message": message}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON in request body."}, status=400)
    except KeyError as e:
        return JsonResponse({"status": "error", "message": f"Missing key in request data: {e}"}, status=400)
    except Exception as e:
        print("An exception occurred:", e)
        return JsonResponse({"status": "error", "message": "An internal server error occurred."}, status=500)


def process_new_set_status(payload):
    try:

        with transaction.atomic():
            message_id = payload['message_id']
            data = payload['data']
            tenant_id = payload['tenant_id']

        template_name, bg_group = get_template_name(message_id)

        key = bg_group or template_name
        print("Key : ", key)

        if key is None:
            return
        
        update_fields = []
        flag_to_column = {
            'is_sent': 'sent',
            'is_delivered': 'delivered',
            'is_read': 'read',
            'is_replied': 'replied',
            'is_failed': 'failed'
        }

        for flag, column in flag_to_column.items():
            if data.get(flag) is True:
                print("Column found: ", column)
                update_fields.append(f"{column} = {column} + 1")

    
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT 1 FROM new_set_status WHERE name = %s;", (key,))
            row_exists = cursor.fetchone()

            if row_exists:
                print("Row Exists: ", key)
                if update_fields:

                    update_query = f"UPDATE new_set_status SET {', '.join(update_fields)} WHERE name = %s;"
                    cursor.execute(update_query, (key,))
                    message = "Record updated successfully."
                else:
                    message = "No updates were made as no flags were set to True."
            else:
                print("Row does not exist: ", key)
                insert_query = """
                INSERT INTO new_set_status (name, tenant_id, sent, delivered, read, replied, failed)
                VALUES (%s, %s, 1, 0, 0, 0, 0);
                """
                cursor.execute(insert_query, (key, tenant_id))
                message = "New record created successfully."

        print("Message: " ,message)
    except Exception as exc: 
        print("An Exception Occured in process_new_set_status: ", exc)


def get_template_name(message_id):
    print("rcvd message id: ", message_id)
    sql_query = """
    SELECT template_name, broadcast_group_name
    FROM whatsapp_message_id
    WHERE message_id = %s;
    """
    
    cursor = connection.cursor()
    cursor.execute(sql_query, (message_id,))
    
    result = cursor.fetchone()
    print("Result: ", result)
    if result:
        template_name, broadcast_group_name = result
        return template_name, broadcast_group_name
    else:
        return None, None

OPENAI_PROMPT = """
You are a helpful assisstant who is pro at translating Indian Languages. 

Translate the text provided in english into the languages provided. 
Keep the structure of Flow Data intact and return only the translated text in Json format. 

Also give the language code. code under 'code' and translation under 'translations'

IMPORTANT: Keep the body of 'list_element' type under 24 characters and 'button_element' type under 20 characters

Output Example:
{
"code": "en"
"fallback": (fallback message)
"translations": (flow data) (keys and values enclosed in double quotes)
}

KEEP THE FORMAT AS MENTIONED IN OUTPUT EXAMPLE
"""

@csrf_exempt
def translate_whatsapp_flow(request):
    try: 
        data = json.loads(request.body)
        tenant = request.headers.get('X-Tenant-Id')
        language_data = data.get('languages')
        languages = list(language_data.values())
        business_phone_number_id = request.headers.get('bpid')
        print("Languages: ", languages)

        whatsapp_tenant_data = WhatsappTenantData.objects.filter(tenant_id = tenant, language = "en").first()

        WhatsappTenantData.objects.filter(tenant_id=tenant).exclude(id = whatsapp_tenant_data.id).delete()

        # whatsapp_tenant_data = WhatsappTenantData.objects.filter(tenant_id = tenant).filter(language = "en").first()

        whatsapp_tenant_data.introductory_msg = data
        whatsapp_tenant_data.multilingual = True
        whatsapp_tenant_data.save()

        flow_data = whatsapp_tenant_data.flow_data
        fallback_msg = whatsapp_tenant_data.fallback_message
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        if not business_phone_number_id:
            print("Business Phone Number not provided in request")
            
            # Fetch the first record matching the tenant_id
            record = WhatsappTenantData.objects.filter(tenant_id=tenant).first()
            
            if not record:
                return JsonResponse({'status': 'error', 'message': 'No WhatsApp tenant data found for this tenant'}, status=404)
            
            business_phone_number_id = record.business_phone_number_id
        

        for lang in languages:
            print("Lang: ", lang)
            if (lang != "English"):
                PROMPT = f"Flow Data: {flow_data}, Fallback Message: {fallback_msg} , Language: {lang}"
                # print("Sending Data to transslation..", PROMPT)
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": OPENAI_PROMPT},
                        {"role": "user", "content": PROMPT}
                    ]
                )
                result = response.choices[0].message.content
                # print("raw Result: ", result)
                start = result.find('{')
                end = result.rfind('}')
                if start == -1 or end == -1:
                    raise ValueError("Invalid JSON format in OpenAI response")

                result = result[start:end + 1]
                # print("Result: ", result)
                result_json = json.loads(result)
                print("Flow: " ,result_json['translations'])
                # print("Language: ", result_json['code'])

                new_whatsapp_tenant_data = WhatsappTenantData(
                    tenant_id=whatsapp_tenant_data.tenant_id,
                    flow_data=result_json['translations'],  # Use the translated flow_data
                    language = result_json['code'],
                    business_phone_number_id = whatsapp_tenant_data.business_phone_number_id,
                    adj_list = whatsapp_tenant_data.adj_list,
                    access_token = whatsapp_tenant_data.access_token,
                    business_account_id = whatsapp_tenant_data.business_account_id,
                    start = whatsapp_tenant_data.start,
                    fallback_count = whatsapp_tenant_data.fallback_count,
                    fallback_message = result_json['fallback'],
                    flow_name = whatsapp_tenant_data.flow_name,
                    spreadsheet_link = whatsapp_tenant_data.spreadsheet_link,
                    introductory_msg = data,
                    multilingual = True
                    )

                # Save the new object to the database
                new_whatsapp_tenant_data.save()
        reset_fastapi_cache(business_phone_number_id=business_phone_number_id)
             
            # print("Result: ", result_json, type(result_json))

        return JsonResponse({'success': True, 'message': f"Flow translated for languages: {languages}"}, status = 200)
    except Exception as e:
        print("Exception: ", e)
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def test_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        name = data.get('body', '')
        print("POST req rcvd with data: ", data)
        return JsonResponse({'message': 'data rcvd succesfully'})
    
    elif request.method == 'GET':
        print("GET req rcvd: ", name)
        return JsonResponse({'data': f"Your name is {name}"})


@csrf_exempt
def reset_automation(request):
    """
    Reset automation flow data while preserving WhatsApp settings.

    Clears:
    - flow_data, nodes, edges, adj_list, start, start_node_id
    - flow_version, flow_name, hop_nodes

    Preserves:
    - business_phone_number_id, access_token, business_account_id
    - fallback_count, fallback_message, language, multilingual, introductory_msg
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST method allowed'}, status=405)

    try:
        # Get tenant ID from headers
        tenant_id = request.headers.get('X-Tenant-Id')
        if not tenant_id:
            return JsonResponse({'status': 'error', 'message': 'No tenant ID found in headers'}, status=400)

        # Verify tenant exists
        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Invalid tenant ID'}, status=404)

        # Get WhatsApp tenant data
        whatsapp_data = WhatsappTenantData.objects.filter(tenant_id=tenant_id).first()

        if not whatsapp_data:
            return JsonResponse({
                'status': 'error',
                'message': 'No automation found for this tenant'
            }, status=404)

        # Store business_phone_number_id for cache reset
        business_phone_number_id = whatsapp_data.business_phone_number_id

        # Clear flow fields only (preserve WhatsApp settings)
        whatsapp_data.flow_data = None
        whatsapp_data.nodes = None
        whatsapp_data.edges = None
        whatsapp_data.adj_list = None
        whatsapp_data.start = None
        whatsapp_data.start_node_id = None
        whatsapp_data.flow_version = 1  # Reset to default
        whatsapp_data.flow_name = None
        whatsapp_data.hop_nodes = None
        whatsapp_data.updated_at = timezone.now()

        # Save changes
        whatsapp_data.save()

        # Reset FastAPI cache
        reset_fastapi_cache(business_phone_number_id=business_phone_number_id)

        print(f"Automation reset successfully for tenant: {tenant_id}")

        return JsonResponse({
            'status': 'success',
            'message': 'Automation reset successfully. Flow data cleared and cache refreshed.',
            'cleared_fields': [
                'flow_data', 'nodes', 'edges', 'adj_list', 'start',
                'start_node_id', 'flow_version', 'flow_name', 'hop_nodes'
            ],
            'preserved_fields': [
                'business_phone_number_id', 'access_token', 'business_account_id',
                'fallback_count', 'fallback_message', 'language', 'multilingual', 'introductory_msg'
            ]
        }, status=200)

    except Exception as e:
        print(f"Error resetting automation: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to reset automation: {str(e)}'
        }, status=500)
