from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from decimal import Decimal
from core.models import DailyUpload, BalanceRow


CATEGORY_ORDER = ['Liquid', 'Treasury', 'WK', 'Investments']
TYPE_ORDER = ['Fiat', 'Stablecoin', 'Crypto', 'Shitcoin', 'No Liquid']

STABLECOIN_GROUPS = ['USDC', 'USDT']
CRYPTO_GROUPS = ['BTC', 'ETH']


def _is_ripio(row_qs):
    return row_qs.exclude(from_field='User').exclude(category='User')


def _build_table(upload):
    rows = _is_ripio(BalanceRow.objects.filter(upload=upload))

    table = []
    for cat in CATEGORY_ORDER:
        cat_rows = rows.filter(category__iexact=cat)
        if not cat_rows.exists():
            continue

        liquid_rows = cat_rows.exclude(type__iexact='No Liquid')
        cat_total_usd = liquid_rows.aggregate(t=Sum('usd'))['t'] or Decimal('0')

        table.append({
            'level': 'category',
            'label': cat.upper(),
            'usd': cat_total_usd,
        })

        for typ in TYPE_ORDER:
            type_rows = cat_rows.filter(type__iexact=typ)
            if not type_rows.exists():
                continue

            type_usd = type_rows.aggregate(t=Sum('usd'))['t'] or Decimal('0')
            table.append({
                'level': 'type',
                'label': typ.upper(),
                'usd': type_usd,
                'is_no_liquid': typ.lower() == 'no liquid',
            })

            if typ.lower() == 'stablecoin':
                shown_groups = STABLECOIN_GROUPS
            elif typ.lower() == 'crypto':
                shown_groups = CRYPTO_GROUPS
            else:
                shown_groups = None

            if shown_groups is not None:
                for grp in shown_groups:
                    grp_rows = type_rows.filter(asset_group__iexact=grp)
                    if not grp_rows.exists():
                        continue
                    grp_usd = grp_rows.aggregate(t=Sum('usd'))['t'] or Decimal('0')
                    grp_balance = grp_rows.aggregate(t=Sum('total_balance'))['t'] or Decimal('0')
                    first = grp_rows.first()
                    table.append({
                        'level': 'asset',
                        'label': grp,
                        'usd': grp_usd,
                        'amount': grp_balance,
                        'price': first.price if first else None,
                        'is_no_liquid': False,
                    })
                # Others
                others = type_rows.exclude(asset_group__in=shown_groups)
                if others.exists():
                    others_usd = others.aggregate(t=Sum('usd'))['t'] or Decimal('0')
                    table.append({
                        'level': 'asset',
                        'label': 'Others',
                        'usd': others_usd,
                        'amount': None,
                        'price': None,
                        'is_no_liquid': False,
                    })

    return table


def _build_table_comparison(upload_a, upload_b):
    """Build table with comparison columns between two uploads."""
    rows_a = _is_ripio(BalanceRow.objects.filter(upload=upload_a))
    rows_b = _is_ripio(BalanceRow.objects.filter(upload=upload_b))

    table = []
    for cat in CATEGORY_ORDER:
        cat_a = rows_a.filter(category__iexact=cat)
        cat_b = rows_b.filter(category__iexact=cat)
        if not cat_a.exists() and not cat_b.exists():
            continue

        liq_a = cat_a.exclude(type__iexact='No Liquid').aggregate(t=Sum('usd'))['t'] or Decimal('0')
        liq_b = cat_b.exclude(type__iexact='No Liquid').aggregate(t=Sum('usd'))['t'] or Decimal('0')

        table.append({
            'level': 'category',
            'label': cat.upper(),
            'usd': liq_a,
            'usd_prev': liq_b,
            'var_usd': liq_a - liq_b,
        })

        for typ in TYPE_ORDER:
            type_a = cat_a.filter(type__iexact=typ)
            type_b = cat_b.filter(type__iexact=typ)
            if not type_a.exists() and not type_b.exists():
                continue

            usd_a = type_a.aggregate(t=Sum('usd'))['t'] or Decimal('0')
            usd_b = type_b.aggregate(t=Sum('usd'))['t'] or Decimal('0')
            table.append({
                'level': 'type',
                'label': typ.upper(),
                'usd': usd_a,
                'usd_prev': usd_b,
                'var_usd': usd_a - usd_b,
                'is_no_liquid': typ.lower() == 'no liquid',
            })

            if typ.lower() == 'stablecoin':
                shown_groups = STABLECOIN_GROUPS
            elif typ.lower() == 'crypto':
                shown_groups = CRYPTO_GROUPS
            else:
                shown_groups = None

            if shown_groups is not None:
                for grp in shown_groups:
                    ga = type_a.filter(asset_group__iexact=grp)
                    gb = type_b.filter(asset_group__iexact=grp)
                    if not ga.exists() and not gb.exists():
                        continue
                    usd_a2 = ga.aggregate(t=Sum('usd'))['t'] or Decimal('0')
                    usd_b2 = gb.aggregate(t=Sum('usd'))['t'] or Decimal('0')
                    bal_a = ga.aggregate(t=Sum('total_balance'))['t'] or Decimal('0')
                    bal_b = gb.aggregate(t=Sum('total_balance'))['t'] or Decimal('0')
                    first_a = ga.first()
                    first_b = gb.first()
                    price_a = first_a.price if first_a else None
                    price_b = first_b.price if first_b else None
                    table.append({
                        'level': 'asset',
                        'label': grp,
                        'usd': usd_a2,
                        'usd_prev': usd_b2,
                        'var_usd': usd_a2 - usd_b2,
                        'amount': bal_a,
                        'amount_prev': bal_b,
                        'var_amount': bal_a - bal_b,
                        'price': price_a,
                        'price_prev': price_b,
                        'var_price': (price_a - price_b) if (price_a and price_b) else None,
                        'is_no_liquid': False,
                    })
                others_a = type_a.exclude(asset_group__in=shown_groups)
                others_b = type_b.exclude(asset_group__in=shown_groups)
                if others_a.exists() or others_b.exists():
                    uo_a = others_a.aggregate(t=Sum('usd'))['t'] or Decimal('0')
                    uo_b = others_b.aggregate(t=Sum('usd'))['t'] or Decimal('0')
                    table.append({
                        'level': 'asset',
                        'label': 'Others',
                        'usd': uo_a,
                        'usd_prev': uo_b,
                        'var_usd': uo_a - uo_b,
                        'amount': None,
                        'amount_prev': None,
                        'var_amount': None,
                        'price': None,
                        'price_prev': None,
                        'var_price': None,
                        'is_no_liquid': False,
                    })

    return table


def _btc_chart_data():
    uploads = DailyUpload.objects.order_by('date')
    labels, btc_amounts, btc_prices = [], [], []
    for up in uploads:
        ripio_rows = _is_ripio(BalanceRow.objects.filter(upload=up))
        btc_rows = ripio_rows.filter(asset_group__iexact='BTC')
        total_btc = btc_rows.aggregate(t=Sum('total_balance'))['t'] or Decimal('0')
        first_btc = btc_rows.first()
        price = float(first_btc.price) if first_btc and first_btc.price else None
        labels.append(str(up.date))
        btc_amounts.append(float(total_btc))
        btc_prices.append(price)
    return {'labels': labels, 'amounts': btc_amounts, 'prices': btc_prices}


@login_required
def index(request):
    uploads = DailyUpload.objects.all()
    upload_dates = list(uploads.values_list('date', flat=True))

    date_str = request.GET.get('date')
    compare_str = request.GET.get('compare')

    current_upload = None
    compare_upload = None

    if date_str:
        try:
            current_upload = DailyUpload.objects.get(date=date_str)
        except DailyUpload.DoesNotExist:
            pass
    elif uploads.exists():
        current_upload = uploads.first()

    if compare_str:
        try:
            compare_upload = DailyUpload.objects.get(date=compare_str)
        except DailyUpload.DoesNotExist:
            pass

    table = []
    kpi = {}
    if current_upload:
        ripio_rows = _is_ripio(BalanceRow.objects.filter(upload=current_upload))
        total_with = ripio_rows.aggregate(t=Sum('usd'))['t'] or Decimal('0')
        total_without = ripio_rows.exclude(type__iexact='No Liquid').aggregate(t=Sum('usd'))['t'] or Decimal('0')
        kpi = {
            'total_with_no_liquid': total_with,
            'total_without_no_liquid': total_without,
        }
        if compare_upload:
            table = _build_table_comparison(current_upload, compare_upload)
        else:
            table = _build_table(current_upload)

    btc_chart = _btc_chart_data()

    return render(request, 'dashboard/index.html', {
        'current_upload': current_upload,
        'compare_upload': compare_upload,
        'upload_dates': [str(d) for d in upload_dates],
        'table': table,
        'kpi': kpi,
        'btc_chart': btc_chart,
        'comparing': compare_upload is not None,
    })
