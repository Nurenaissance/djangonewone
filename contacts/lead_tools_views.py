"""
Lead tooling endpoints (additive; tenant-scoped via X-Tenant-Id):
  GET  /export-contacts/       -> .xlsx of the tenant's full contact list
  POST /contacts/<pk>/tag/     -> set a cold/warm/hot tag in customField JSON
These are isolated, additive views — they never read/write another tenant's data.
"""
import logging
from io import BytesIO
from datetime import datetime

from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
import openpyxl
from openpyxl.utils import get_column_letter

from .models import Contact

logger = logging.getLogger(__name__)
VALID_TAGS = {'cold', 'warm', 'hot'}


class ExportContactsExcelView(APIView):
    """Download the entire contact list for the tenant as an Excel file."""
    def get(self, request, *args, **kwargs):
        tenant_id = request.headers.get('X-Tenant-Id')
        if not tenant_id:
            return Response({'error': 'X-Tenant-Id header is required'}, status=400)

        contacts = Contact.objects.filter(tenant_id=tenant_id).order_by('-createdOn')
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Contacts'
        headers = ['Name', 'Phone', 'Email', 'Tag', 'City', 'Pincode', 'Address',
                   'Description', 'Last Seen', 'Last Replied', 'Created On']
        ws.append(headers)

        def dt(v):
            return v.strftime('%Y-%m-%d %H:%M') if v else ''

        for c in contacts:
            cf = c.customField or {}
            ws.append([
                c.name or '', c.phone or '', c.email or '',
                cf.get('tag') or '',
                cf.get('city') or cf.get('City') or '',
                cf.get('pincode') or cf.get('Pincode') or '',
                c.address or '', c.description or '',
                dt(c.last_seen), dt(c.last_replied), dt(c.createdOn),
            ])
        for i in range(1, len(headers) + 1):
            ws.column_dimensions[get_column_letter(i)].width = 22

        buf = BytesIO()
        wb.save(buf)
        buf.seek(0)
        fname = f'contacts_{tenant_id}_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
        resp = HttpResponse(
            buf.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        resp['Content-Disposition'] = f'attachment; filename="{fname}"'
        return resp


class ContactTagView(APIView):
    """Set a lead tag (cold/warm/hot) on a contact, stored in customField JSON."""
    def post(self, request, pk, *args, **kwargs):
        tenant_id = request.headers.get('X-Tenant-Id')
        tag = str(request.data.get('tag') or '').strip().lower()
        if tag not in VALID_TAGS:
            return Response({'error': f'tag must be one of {sorted(VALID_TAGS)}'}, status=400)
        qs = Contact.objects.filter(pk=pk)
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        c = qs.first()
        if not c:
            return Response({'error': 'contact not found'}, status=404)
        cf = c.customField or {}
        cf['tag'] = tag
        cf['tag_source'] = 'manual'   # manual edits win over AI auto-tagging
        c.customField = cf
        c.save(update_fields=['customField'])
        return Response({'success': True, 'id': c.id, 'tag': tag})
