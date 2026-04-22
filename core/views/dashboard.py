import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from decimal import Decimal
from core.models import DailyUpload, BalanceRow


CHART_COLORS_TYPE = {
    'Fiat': '#3d85c6',
    'Stablecoin': '#0b5394',
    'Crypto': '#1a56a0',
    'Shitcoin': '#9fc5e8',
    'No Liquid': '#9ca3af',
}

ASSET_PALETTE = [
    '#0b5394', '#3d85c6', '#1a56a0', '#4a90d9', '#9fc5e8',
    '#27AE60', '#e67e22', '#e74c3c', '#9b59b6', '#d0e2f3',
]


def _is_ripio(qs):
    return qs.exclude(from_field='User').exclude(category='User')


def _btc_chart_data():
    uploads = DailyUpload.objects.order_by('date')
    labels, btc_amounts, btc_prices = [], [], []
    for up in uploads:
        ripio = _is_ripio(BalanceRow.objects.filter(upload=up))
        btc = ripio.filter(asset_group__iexact='BTC')
        total_btc = btc.aggregate(t=Sum('total_balance'))['t'] or Decimal('0')
        first = btc.first()
        labels.append(str(up.date))
        btc_amounts.append(float(total_btc))
        btc_prices.append(float(first.price) if first and first.price else None)
    return {'labels': labels, 'amounts': btc_amounts, 'prices': btc_prices}


def _chart_data(upload):
    rows = _is_ripio(BalanceRow.objects.filter(upload=upload))

    # Donut: by type
    by_type = list(rows.values('type').annotate(total=Sum('usd')).order_by('-total'))
    type_labels = [r['type'] or 'Unknown' for r in by_type]
    type_data = [float(r['total'] or 0) for r in by_type]
    type_colors = [CHART_COLORS_TYPE.get(r['type'], '#ccc') for r in by_type]

    # Donut: top asset groups (exclude No Liquid)
    by_asset = list(
        rows.exclude(type__iexact='No Liquid')
            .values('asset_group').annotate(total=Sum('usd'))
            .order_by('-total')[:10]
    )
    asset_labels = [r['asset_group'] or 'Unknown' for r in by_asset]
    asset_data = [float(r['total'] or 0) for r in by_asset]
    asset_colors = ASSET_PALETTE[:len(by_asset)]

    # Bar: by category
    by_cat = list(
        rows.exclude(type__iexact='No Liquid')
            .values('category').annotate(total=Sum('usd'))
            .order_by('-total')
    )
    cat_labels = [r['category'] or 'Other' for r in by_cat]
    cat_data = [float(r['total'] or 0) for r in by_cat]

    return {
        'type_labels': type_labels, 'type_data': type_data, 'type_colors': type_colors,
        'asset_labels': asset_labels, 'asset_data': asset_data, 'asset_colors': asset_colors,
        'cat_labels': cat_labels, 'cat_data': cat_data,
    }


@login_required
def index(request):
    uploads = DailyUpload.objects.all()
    upload_dates = list(uploads.values_list('date', flat=True))

    date_str = request.GET.get('date')
    current_upload = None

    if date_str:
        try:
            current_upload = DailyUpload.objects.get(date=date_str)
        except DailyUpload.DoesNotExist:
            pass
    elif uploads.exists():
        current_upload = uploads.first()

    kpi = {}
    chart_data_json = '{}'
    if current_upload:
        ripio = _is_ripio(BalanceRow.objects.filter(upload=current_upload))
        total_with = ripio.aggregate(t=Sum('usd'))['t'] or Decimal('0')
        total_without = ripio.exclude(type__iexact='No Liquid').aggregate(t=Sum('usd'))['t'] or Decimal('0')
        kpi = {
            'total_with_no_liquid': float(total_with),
            'total_without_no_liquid': float(total_without),
        }
        chart_data_json = json.dumps(_chart_data(current_upload))

    return render(request, 'dashboard/index.html', {
        'current_upload': current_upload,
        'upload_dates': [str(d) for d in upload_dates],
        'kpi': kpi,
        'btc_chart': json.dumps(_btc_chart_data()),
        'chart_data': chart_data_json,
    })
