import csv
import io
from decimal import Decimal, InvalidOperation

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction

from core.forms import UploadCSVForm
from core.models import DailyUpload, BalanceRow


EXPECTED_COLUMNS = {
    'Workspace', 'Account Name', 'Account ID', 'Asset',
    'Total Balance', 'From', 'Category', 'Type', 'Asset Group', 'Price', 'USD'
}

TYPE_NORMALIZE = {
    'crypto crypto': 'Crypto',
}


def _require_admin(request):
    if not request.user.is_authenticated:
        return False
    profile = getattr(request.user, 'profile', None)
    return profile and profile.is_admin()


def _clean_decimal(value):
    if value is None:
        return None
    s = str(value).strip().replace(',', '')
    if s == '' or s == '-':
        return None
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


def _parse_csv(file_obj):
    raw = file_obj.read()
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        text = raw.decode('latin-1')

    reader = csv.DictReader(io.StringIO(text))
    headers = set(reader.fieldnames or [])
    missing = EXPECTED_COLUMNS - headers
    if missing:
        raise ValueError(f'Columnas faltantes: {", ".join(sorted(missing))}')

    rows = []
    for row in reader:
        rows.append({
            'workspace': row.get('Workspace', '').strip(),
            'account_name': row.get('Account Name', '').strip(),
            'account_id': row.get('Account ID', '').strip(),
            'asset': row.get('Asset', '').strip(),
            'total_balance': _clean_decimal(row.get('Total Balance')),
            'from_field': row.get('From', '').strip(),
            'category': row.get('Category', '').strip(),
            'type': TYPE_NORMALIZE.get(row.get('Type', '').strip().lower(), row.get('Type', '').strip()),
            'asset_group': row.get('Asset Group', '').strip(),
            'price': _clean_decimal(row.get('Price')),
            'usd': _clean_decimal(row.get('USD')),
        })
    return rows


def _do_import(upload, rows):
    objs = [BalanceRow(upload=upload, **r) for r in rows]
    BalanceRow.objects.bulk_create(objs, batch_size=500)
    upload.row_count = len(objs)
    upload.save(update_fields=['row_count'])


@login_required
def index(request):
    if not _require_admin(request):
        messages.error(request, 'No tenés permisos para subir archivos.')
        return redirect('dashboard')

    form = UploadCSVForm()
    pending_date = None

    if request.method == 'POST':
        action = request.POST.get('action', 'upload')

        if action == 'upload':
            form = UploadCSVForm(request.POST, request.FILES)
            if form.is_valid():
                date = form.cleaned_data['date']
                file = form.cleaned_data['file']
                existing = DailyUpload.objects.filter(date=date).first()
                if existing:
                    request.session['pending_csv_date'] = str(date)
                    return render(request, 'upload/index.html', {
                        'form': form,
                        'pending_replace': existing,
                    })
                try:
                    rows = _parse_csv(file)
                except ValueError as e:
                    messages.error(request, str(e))
                    return render(request, 'upload/index.html', {'form': form})

                with transaction.atomic():
                    upload = DailyUpload.objects.create(
                        date=date, file=file, uploaded_by=request.user
                    )
                    _do_import(upload, rows)

                total_usd = sum(r['usd'] or Decimal('0') for r in rows)
                messages.success(
                    request,
                    f'Importadas {len(rows)} filas para {date}. Total USD: ${total_usd:,.2f}'
                )
                return redirect('upload')

    uploads = DailyUpload.objects.select_related('uploaded_by').all()
    return render(request, 'upload/index.html', {'form': form, 'uploads': uploads})


@login_required
def confirm_replace(request, pk):
    if not _require_admin(request):
        messages.error(request, 'No tenés permisos.')
        return redirect('dashboard')

    existing = get_object_or_404(DailyUpload, pk=pk)
    if request.method == 'POST':
        file = request.FILES.get('file')
        if not file:
            messages.error(request, 'Falta el archivo.')
            return redirect('upload')
        try:
            rows = _parse_csv(file)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('upload')

        with transaction.atomic():
            existing.rows.all().delete()
            if existing.file:
                try:
                    existing.file.delete(save=False)
                except Exception:
                    pass
            existing.file = file
            existing.uploaded_by = request.user
            existing.save()
            _do_import(existing, rows)

        total_usd = sum(r['usd'] or Decimal('0') for r in rows)
        messages.success(request, f'Reemplazado. {len(rows)} filas para {existing.date}. Total: ${total_usd:,.2f}')
    return redirect('upload')


@login_required
def delete_upload(request, pk):
    if not _require_admin(request):
        messages.error(request, 'No tenés permisos.')
        return redirect('dashboard')

    upload = get_object_or_404(DailyUpload, pk=pk)
    if request.method == 'POST':
        with transaction.atomic():
            upload.rows.all().delete()
            if upload.file:
                try:
                    upload.file.delete(save=False)
                except Exception:
                    pass
            upload.delete()
        messages.success(request, f'Upload del {upload.date} eliminado.')
    return redirect('upload')
