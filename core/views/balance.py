from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from decimal import Decimal
from core.models import DailyUpload, BalanceRow


CATEGORY_ORDER = ['Liquid', 'Treasury', 'WK', 'Investments']
TYPE_ORDER = ['Fiat', 'Stablecoin', 'Crypto', 'Shitcoin']  # No Liquid excluded — added at bottom
STABLECOIN_GROUPS = ['USDC', 'USDT']
CRYPTO_GROUPS = ['BTC', 'ETH']


def _is_ripio(qs):
    return qs.exclude(from_field='User').exclude(category='User')


def _ckey(cat, typ):
    return f"{cat.lower()}_{typ.lower().replace(' ', '_')}"


def _build_table(upload):
    rows = _is_ripio(BalanceRow.objects.filter(upload=upload))
    table = []

    for cat in CATEGORY_ORDER:
        cat_rows = rows.filter(category__iexact=cat)
        if not cat_rows.exists():
            continue

        cat_key = f"cat_{cat.lower()}"
        cat_total = cat_rows.exclude(type__iexact='No Liquid').aggregate(t=Sum('usd'))['t'] or Decimal('0')

        table.append({
            'level': 'category',
            'label': cat.upper(),
            'usd': cat_total,
            'cat_key': cat_key,
        })

        for typ in TYPE_ORDER:
            type_rows = cat_rows.filter(type__iexact=typ)
            if not type_rows.exists():
                continue

            type_usd = type_rows.aggregate(t=Sum('usd'))['t'] or Decimal('0')
            shown = STABLECOIN_GROUPS if typ.lower() == 'stablecoin' else (CRYPTO_GROUPS if typ.lower() == 'crypto' else None)
            ck = _ckey(cat, typ) if shown else ''

            table.append({
                'level': 'type', 'label': typ.upper(), 'usd': type_usd,
                'is_no_liquid': False, 'has_children': shown is not None,
                'collapse_key': ck, 'cat_key': cat_key,
            })

            if shown:
                for grp in shown:
                    gr = type_rows.filter(asset_group__iexact=grp)
                    if not gr.exists():
                        continue
                    first = gr.first()
                    table.append({
                        'level': 'asset', 'label': grp,
                        'usd': gr.aggregate(t=Sum('usd'))['t'] or Decimal('0'),
                        'amount': gr.aggregate(t=Sum('total_balance'))['t'] or Decimal('0'),
                        'price': first.price if first else None,
                        'is_no_liquid': False, 'collapse_key': ck, 'cat_key': cat_key,
                    })
                others = type_rows.exclude(asset_group__in=shown)
                if others.exists():
                    table.append({
                        'level': 'asset', 'label': 'Others',
                        'usd': others.aggregate(t=Sum('usd'))['t'] or Decimal('0'),
                        'amount': None, 'price': None,
                        'is_no_liquid': False, 'collapse_key': ck, 'cat_key': cat_key,
                    })

        # No Liquid dentro de la categoría (collapsable con la cat)
        nl = cat_rows.filter(type__iexact='No Liquid')
        if nl.exists():
            table.append({
                'level': 'type', 'label': 'NO LIQUID',
                'usd': nl.aggregate(t=Sum('usd'))['t'] or Decimal('0'),
                'is_no_liquid': True, 'has_children': False,
                'collapse_key': '', 'cat_key': cat_key,
            })

    # Filas de resumen global al fondo (siempre visibles)
    subtotal = rows.exclude(type__iexact='No Liquid').aggregate(t=Sum('usd'))['t'] or Decimal('0')
    nl_total = rows.filter(type__iexact='No Liquid').aggregate(t=Sum('usd'))['t'] or Decimal('0')
    table.append({'level': 'subtotal',      'label': 'SUBTOTAL',      'usd': subtotal})
    table.append({'level': 'nl_total',      'label': 'NO LIQUID',     'usd': nl_total})
    table.append({'level': 'grand_total',   'label': 'TOTAL GENERAL', 'usd': subtotal + nl_total})

    return table


def _build_table_comparison(upload_a, upload_b):
    rows_a = _is_ripio(BalanceRow.objects.filter(upload=upload_a))
    rows_b = _is_ripio(BalanceRow.objects.filter(upload=upload_b))
    table = []

    for cat in CATEGORY_ORDER:
        cat_a = rows_a.filter(category__iexact=cat)
        cat_b = rows_b.filter(category__iexact=cat)
        if not cat_a.exists() and not cat_b.exists():
            continue

        cat_key = f"cat_{cat.lower()}"
        liq_a = cat_a.exclude(type__iexact='No Liquid').aggregate(t=Sum('usd'))['t'] or Decimal('0')
        liq_b = cat_b.exclude(type__iexact='No Liquid').aggregate(t=Sum('usd'))['t'] or Decimal('0')

        table.append({
            'level': 'category', 'label': cat.upper(),
            'usd': liq_a, 'usd_prev': liq_b, 'var_usd': liq_a - liq_b,
            'cat_key': cat_key,
        })

        for typ in TYPE_ORDER:
            ta = cat_a.filter(type__iexact=typ)
            tb = cat_b.filter(type__iexact=typ)
            if not ta.exists() and not tb.exists():
                continue

            usd_a = ta.aggregate(t=Sum('usd'))['t'] or Decimal('0')
            usd_b = tb.aggregate(t=Sum('usd'))['t'] or Decimal('0')
            shown = STABLECOIN_GROUPS if typ.lower() == 'stablecoin' else (CRYPTO_GROUPS if typ.lower() == 'crypto' else None)
            ck = _ckey(cat, typ) if shown else ''

            table.append({
                'level': 'type', 'label': typ.upper(),
                'usd': usd_a, 'usd_prev': usd_b, 'var_usd': usd_a - usd_b,
                'is_no_liquid': False, 'has_children': shown is not None,
                'collapse_key': ck, 'cat_key': cat_key,
            })

            if shown:
                for grp in shown:
                    ga = ta.filter(asset_group__iexact=grp)
                    gb = tb.filter(asset_group__iexact=grp)
                    if not ga.exists() and not gb.exists():
                        continue
                    usd_a2 = ga.aggregate(t=Sum('usd'))['t'] or Decimal('0')
                    usd_b2 = gb.aggregate(t=Sum('usd'))['t'] or Decimal('0')
                    bal_a = ga.aggregate(t=Sum('total_balance'))['t'] or Decimal('0')
                    bal_b = gb.aggregate(t=Sum('total_balance'))['t'] or Decimal('0')
                    fa = ga.first()
                    fb = gb.first()
                    table.append({
                        'level': 'asset', 'label': grp,
                        'usd': usd_a2, 'usd_prev': usd_b2, 'var_usd': usd_a2 - usd_b2,
                        'amount': bal_a, 'amount_prev': bal_b, 'var_amount': bal_a - bal_b,
                        'price': fa.price if fa else None,
                        'price_prev': fb.price if fb else None,
                        'is_no_liquid': False, 'collapse_key': ck, 'cat_key': cat_key,
                    })
                oa = ta.exclude(asset_group__in=shown)
                ob = tb.exclude(asset_group__in=shown)
                if oa.exists() or ob.exists():
                    uo_a = oa.aggregate(t=Sum('usd'))['t'] or Decimal('0')
                    uo_b = ob.aggregate(t=Sum('usd'))['t'] or Decimal('0')
                    table.append({
                        'level': 'asset', 'label': 'Others',
                        'usd': uo_a, 'usd_prev': uo_b, 'var_usd': uo_a - uo_b,
                        'amount': None, 'amount_prev': None, 'var_amount': None,
                        'price': None, 'price_prev': None,
                        'is_no_liquid': False, 'collapse_key': ck, 'cat_key': cat_key,
                    })

        # No Liquid dentro de la categoría
        nl_a = cat_a.filter(type__iexact='No Liquid')
        nl_b = cat_b.filter(type__iexact='No Liquid')
        if nl_a.exists() or nl_b.exists():
            nl_usd_a = nl_a.aggregate(t=Sum('usd'))['t'] or Decimal('0')
            nl_usd_b = nl_b.aggregate(t=Sum('usd'))['t'] or Decimal('0')
            table.append({
                'level': 'type', 'label': 'NO LIQUID',
                'usd': nl_usd_a, 'usd_prev': nl_usd_b, 'var_usd': nl_usd_a - nl_usd_b,
                'is_no_liquid': True, 'has_children': False,
                'collapse_key': '', 'cat_key': cat_key,
            })

    # Resumen global al fondo
    sub_a = rows_a.exclude(type__iexact='No Liquid').aggregate(t=Sum('usd'))['t'] or Decimal('0')
    sub_b = rows_b.exclude(type__iexact='No Liquid').aggregate(t=Sum('usd'))['t'] or Decimal('0')
    nl_a_tot = rows_a.filter(type__iexact='No Liquid').aggregate(t=Sum('usd'))['t'] or Decimal('0')
    nl_b_tot = rows_b.filter(type__iexact='No Liquid').aggregate(t=Sum('usd'))['t'] or Decimal('0')
    gt_a = sub_a + nl_a_tot
    gt_b = sub_b + nl_b_tot
    table.append({'level': 'subtotal',    'label': 'SUBTOTAL',      'usd': sub_a, 'usd_prev': sub_b, 'var_usd': sub_a - sub_b})
    table.append({'level': 'nl_total',    'label': 'NO LIQUID',     'usd': nl_a_tot, 'usd_prev': nl_b_tot, 'var_usd': nl_a_tot - nl_b_tot})
    table.append({'level': 'grand_total', 'label': 'TOTAL GENERAL', 'usd': gt_a, 'usd_prev': gt_b, 'var_usd': gt_a - gt_b})

    return table


@login_required
def index(request):
    uploads = DailyUpload.objects.all()
    upload_dates = list(uploads.values_list('date', flat=True))

    date_str = request.GET.get('date')
    compare_str = request.GET.get('compare')
    current_upload = compare_upload = None

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
    if current_upload:
        table = _build_table_comparison(current_upload, compare_upload) if compare_upload else _build_table(current_upload)

    return render(request, 'dashboard/balance.html', {
        'current_upload': current_upload,
        'compare_upload': compare_upload,
        'upload_dates': [str(d) for d in upload_dates],
        'table': table,
        'comparing': compare_upload is not None,
    })
