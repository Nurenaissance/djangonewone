#!/usr/bin/env python
"""
Fetch the interviewdrishtee automation structure for tenant ehgymjv
to understand the flow and question order
"""
import os
import sys
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'simplecrm.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from wabits.models import WAbits
from tenant.models import Tenant

TENANT_ID = 'ehgymjv'
FLOW_NAME = 'interviewdrishtee'

def main():
    print("="*70)
    print("Fetching Interview Automation Structure")
    print("="*70)

    try:
        tenant = Tenant.objects.get(id=TENANT_ID)
        print(f"\n[OK] Tenant: {tenant.organization}")
    except Tenant.DoesNotExist:
        print(f"[ERROR] Tenant {TENANT_ID} not found!")
        return

    # Get automation/wabits entry
    print("\nSearching for automations...")
    all_automations = WAbits.objects.filter(tenant=tenant)

    if all_automations.count() == 0:
        print(f"[ERROR] No automations found for tenant {TENANT_ID}")
        return

    print(f"Found {all_automations.count()} automation(s)")

    # List all automations
    for i, auto in enumerate(all_automations):
        print(f"\n  [{i+1}] ID: {auto.id}")
        print(f"      Created: {auto.created_at}")

        # Try to extract name from flow_json
        if auto.flow_json:
            try:
                flow_data = auto.flow_json if isinstance(auto.flow_json, dict) else json.loads(auto.flow_json)
                name = flow_data.get('name', 'No name field')
                trigger = flow_data.get('trigger', 'No trigger field')
                print(f"      Name: {name}")
                print(f"      Trigger: {trigger}")
            except:
                print(f"      (Could not parse flow_json)")

    # Use the first automation (or the one matching interview)
    automation = None
    for auto in all_automations:
        try:
            flow_data = auto.flow_json if isinstance(auto.flow_json, dict) else json.loads(auto.flow_json)
            if 'interview' in flow_data.get('name', '').lower():
                automation = auto
                break
        except:
            pass

    if not automation:
        automation = all_automations.first()

    print(f"\n[OK] Using automation ID: {automation.id}")

    # Parse flow data
    if automation.flow_json:
        print("\n" + "="*70)
        print("FLOW DATA STRUCTURE")
        print("="*70)

        try:
            flow_data = json.loads(automation.flow_json) if isinstance(automation.flow_json, str) else automation.flow_json

            # Extract nodes
            if 'nodes' in flow_data:
                nodes = flow_data['nodes']
                print(f"\nTotal nodes: {len(nodes)}")
                print("\nNode sequence:")

                # Find askQuestion nodes
                ask_question_nodes = []
                for i, node in enumerate(nodes):
                    node_id = node.get('id', 'unknown')
                    node_type = node.get('type', 'unknown')
                    node_data = node.get('data', {})

                    if node_type == 'askQuestion':
                        message = node_data.get('message', '')
                        variable = node_data.get('variable', '')
                        option_type = node_data.get('optionType', '')
                        data_type = node_data.get('dataType', '')

                        ask_question_nodes.append({
                            'index': i,
                            'id': node_id,
                            'message': message,
                            'variable': variable,
                            'optionType': option_type,
                            'dataType': data_type
                        })

                        print(f"\n  [{i}] Node ID: {node_id}")
                        print(f"      Type: {node_type}")
                        print(f"      Variable: {variable}")
                        print(f"      Message: {message[:100] if message else 'N/A'}...")
                        print(f"      Option Type: {option_type}")
                        print(f"      Data Type: {data_type}")

                print("\n" + "="*70)
                print("ASK QUESTION NODES SUMMARY")
                print("="*70)
                for node in ask_question_nodes:
                    print(f"\n{node['index']+1}. Variable: '{node['variable']}'")
                    print(f"   Data Type: {node['dataType']}")
                    print(f"   Question: {node['message'][:80] if node['message'] else 'N/A'}...")

        except Exception as e:
            print(f"\n[ERROR] Error parsing flow_json: {e}")
            print(f"\nRaw flow_json type: {type(automation.flow_json)}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*70)

if __name__ == "__main__":
    main()
