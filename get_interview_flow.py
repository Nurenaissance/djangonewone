#!/usr/bin/env python
"""
Fetch the interviewdrishtee automation structure for tenant ehgymjv
"""
import os
import sys
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'simplecrm.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from node_temps.models import NodeTemplate
from tenant.models import Tenant

TENANT_ID = 'ehgymjv'

def main():
    print("="*70)
    print("Fetching Interview Automation")
    print("="*70)

    try:
        tenant = Tenant.objects.get(id=TENANT_ID)
        print(f"\n[OK] Tenant: {tenant.organization}")
    except Tenant.DoesNotExist:
        print(f"[ERROR] Tenant {TENANT_ID} not found!")
        return

    # Get all NodeTemplates for this tenant
    templates = NodeTemplate.objects.filter(tenant=tenant)

    if templates.count() == 0:
        print(f"\n[ERROR] No NodeTemplates found for tenant {TENANT_ID}")
        return

    print(f"\nFound {templates.count()} NodeTemplate(s):")

    # List all templates
    for i, template in enumerate(templates):
        print(f"\n  [{i+1}] Name: {template.name}")
        print(f"      ID: {template.id}")
        print(f"      Trigger: {template.trigger}")
        print(f"      Category: {template.category}")
        print(f"      Created: {template.date_created}")

    # Find interview template
    interview_template = None
    for template in templates:
        if 'interview' in template.name.lower():
            interview_template = template
            break

    if not interview_template:
        print(f"\n[WARN] No template with 'interview' in name found, using first template")
        interview_template = templates.first()

    print(f"\n{'='*70}")
    print(f"ANALYZING: {interview_template.name}")
    print("="*70)

    # Parse node_data
    if interview_template.node_data:
        try:
            node_data = interview_template.node_data if isinstance(interview_template.node_data, dict) else json.loads(interview_template.node_data)

            # Extract nodes and edges
            nodes = node_data.get('nodes', [])
            edges = node_data.get('edges', [])

            print(f"\nTotal nodes: {len(nodes)}")
            print(f"Total edges: {len(edges)}")

            # Find askQuestion nodes
            ask_nodes = []
            for node in nodes:
                if node.get('type') == 'askQuestion':
                    data = node.get('data', {})
                    ask_nodes.append({
                        'id': node.get('id'),
                        'message': data.get('message', ''),
                        'variable': data.get('variable', ''),
                        'optionType': data.get('optionType', ''),
                        'dataType': data.get('dataType', '')
                    })

            print(f"\nFound {len(ask_nodes)} askQuestion nodes:\n")

            for i, node in enumerate(ask_nodes):
                print(f"{i+1}. Variable: '{node['variable']}'")
                print(f"   Data Type: {node['dataType']}")
                print(f"   Option Type: {node['optionType']}")
                msg_preview = node['message'][:100] if node['message'] else 'N/A'
                print(f"   Message: {msg_preview}...")
                print()

            # Create mapping guide
            print("="*70)
            print("VARIABLE MAPPING FOR IMPORT SCRIPT")
            print("="*70)
            print("\nBased on the variables found, update the import script to map:")
            print()
            for i, node in enumerate(ask_nodes):
                var = node['variable']
                dtype = node['dataType']
                print(f"  Variable '{var}' ({dtype}) -> InterviewResponse.{var}")

        except Exception as e:
            print(f"\n[ERROR] Error parsing node_data: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*70)

if __name__ == "__main__":
    main()
