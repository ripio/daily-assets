from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from decimal import Decimal
from core.models import DailyUpload, BalanceRow


TYPE_ORDER = ['Stablecoin', 'Crypto', 'Fiat', 'Shitcoin', 'No Liquid']


def _get_user_rows(upload):
    from django.db.models import Q
    return BalanceRow.objects.filter(upload=upload).filter(
        Q(from_field='User') | Q(category='User')
    )


@login_required
def index(request):
    uploads = DailyUpload.objects.all()
    upload_dates = list(uploads.values_list('date', flat=True))

    date_str = request.GET.get('date')
    search = request.GET.get('q', '').strip()

    current_upload = None
    if date_str:
        try:
            current_upload = DailyUpload.objects.get(date=date_str)
        except DailyUpload.DoesNotExist:
            pass
    elif uploads.exists():
        current_upload = uploads.first()

    kpi_by_type = {}
    top_accounts = []
    type_breakdown = []
    detail_rows = []

    if current_upload:
        user_rows = _get_user_rows(current_upload)
        total_usd = user_rows.aggregate(t=Sum('usd'))['t'] or Decimal('0')

        for typ in TYPE_ORDER:
            t_rows = user_rows.filter(type__iexact=typ)
            t_usd = t_rows.aggregate(t=Sum('usd'))['t'] or Decimal('0')
            if t_usd > 0:
                kpi_by_type[typ] = t_usd

        top_accounts = list(
            user_rows.values('account_name')
            .annotate(total=Sum('usd'))
            .order_by('-total')[:10]
        )

        if total_usd > 0:
            for typ in TYPE_ORDER:
                t_rows = user_rows.filter(type__iexact=typ)
                t_usd = t_rows.aggregate(t=Sum('usd'))['t'] or Decimal('0')
                if t_usd > 0:
                    pct = (t_usd / total_usd * 100)
                    type_breakdown.append({'type': typ, 'usd': t_usd, 'pct': pct})

        detail_qs = user_rows
        if search:
            from django.db.models import Q
            detail_qs = detail_qs.filter(
                Q(account_name__icontains=search) |
                Q(asset__icontains=search) |
                Q(type__icontains=search) |
                Q(workspace__icontains=search)
            )
        detail_rows = list(detail_qs.values(
            'account_name', 'asset', 'asset_group', 'type', 'workspace',
            'total_balance', 'price', 'usd'
        ).order_by('-usd')[:500])

    return render(request, 'usuarios/index.html', {
        'current_upload': current_upload,
        'upload_dates': [str(d) for d in upload_dates],
        'kpi_by_type': kpi_by_type,
        'top_accounts': top_accounts,
        'type_breakdown': type_breakdown,
        'detail_rows': detail_rows,
        'search': search,
    })
