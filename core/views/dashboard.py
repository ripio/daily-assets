import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from decimal import Decimal
from core.models import DailyUpload, BalanceRow


CHART_COLORS_TYPE = {
    'Fiat':       '#AED6F1',
    'Stablecoin': '#A9DFBF',
    'Crypto':     '#A9C4E8',
    'Shitcoin':   '#D7BDE2',
}

TYPE_NORMALIZE = {
    'crypto crypto': 'Crypto',
}

TYPE_CHART_COLORS = {
    'Fiat':       '#AED6F1',
    'Stablecoin': '#A9DFBF',
    'Crypto':     '#A9C4E8',
    'Shitcoin':   '#D7BDE2',
    'Unknown':    '#D5D8DC',
}
TYPE_ORDER = ['Fiat', 'Stablecoin', 'Crypto', 'Shitcoin']

ASSET_PALETTE = [
    '#0b5394', '#3d85c6', '#1a56a0', '#4a90d9', '#9fc5e8',
    '#27AE60', '#e67e22', '#e74c3c', '#9b59b6', '#d0e2f3',
]


def _is_ripio(qs):
    return qs.exclude(from_field='User').exclude(category='User')


def _portfolio_chart_data():
    uploads = list(DailyUpload.objects.order_by('date'))
    if not uploads:
        return {'labels': [], 'series': [], 'prices': []}

    labels = [str(up.date) for up in uploads]
    btc_prices = []
    date_type_data = []

    for up in uploads:
        ripio = _is_ripio(BalanceRow.objects.filter(upload=up))
        first_btc = ripio.filter(asset_group__iexact='BTC').first()
        btc_prices.append(float(first_btc.price) if first_btc and first_btc.price else None)

        by_type = ripio.exclude(type__iexact='No Liquid').values('type').annotate(total=Sum('usd'))
        merged: dict = {}
        for r in by_type:
            canonical = TYPE_NORMALIZE.get((r['type'] or '').lower(), r['type'] or 'Unknown')
            merged[canonical] = merged.get(canonical, 0.0) + float(r['total'] or 0)
        date_type_data.append(merged)

    all_types = [t for t in TYPE_ORDER if any(t in d for d in date_type_data)]
    for d in date_type_data:
        for t in d:
            if t not in all_types:
                all_types.append(t)

    series = [
        {
            'label': typ,
            'data': [d.get(typ, 0.0) for d in date_type_data],
            'color': TYPE_CHART_COLORS.get(typ, 'rgba(180,180,180,0.7)'),
        }
        for typ in all_types
    ]
    return {'labels': labels, 'series': series, 'prices': btc_prices}


def _chart_data(upload):
    rows = _is_ripio(BalanceRow.objects.filter(upload=upload))

    # Donut: by type (exclude No Liquid, normalize type aliases)
    raw_types = rows.exclude(type__iexact='No Liquid').values('type').annotate(total=Sum('usd'))
    merged: dict = {}
    for r in raw_types:
        canonical = TYPE_NORMALIZE.get((r['type'] or '').lower(), r['type'] or 'Unknown')
        merged[canonical] = merged.get(canonical, 0.0) + float(r['total'] or 0)
    by_type_sorted = sorted(merged.items(), key=lambda x: -x[1])
    type_labels = [k for k, _ in by_type_sorted]
    type_data   = [v for _, v in by_type_sorted]
    type_colors = [CHART_COLORS_TYPE.get(k, '#ccc') for k in type_labels]

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
        'btc_chart': json.dumps(_portfolio_chart_data()),
        'chart_data': chart_data_json,
    })
