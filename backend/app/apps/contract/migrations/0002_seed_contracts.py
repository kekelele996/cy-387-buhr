from django.db import migrations

# 演示数据：两套房源、三份有效合同
# 海棠公寓下的两份合同租期不重叠，但若陈晨续租超过 2026-10-01，
# 会与周岚 2026-10-01 起租的合同冲突，用于验证租期重叠说明。
SEED_PROPERTIES = [
    {
        'community': '海棠公寓',
        'region': '滨江区',
        'layout': '两室一厅',
        'area': 76,
        'rent': 5200,
        'deposit': 5200,
        'payment': '月付',
        'facilities': ['空调', '洗衣机', '宽带'],
        'status': '已签约',
        'landlord_phone': '13800000001',
    },
    {
        'community': '梧桐里',
        'region': '西湖区',
        'layout': '一室一厅',
        'area': 48,
        'rent': 3900,
        'deposit': 3900,
        'payment': '季付',
        'facilities': ['冰箱', '宽带'],
        'status': '已签约',
        'landlord_phone': '13800000002',
    },
]

SEED_CONTRACTS = [
    {
        'property_index': 0,
        'tenant_name': '陈晨',
        'landlord_name': '宋房东',
        'rent': 5200,
        'start_date': '2025-10-01',
        'end_date': '2026-09-30',
    },
    {
        'property_index': 0,
        'tenant_name': '周岚',
        'landlord_name': '宋房东',
        'rent': 5300,
        'start_date': '2026-10-01',
        'end_date': '2027-09-30',
    },
    {
        'property_index': 1,
        'tenant_name': '林夏',
        'landlord_name': '何房东',
        'rent': 3900,
        'start_date': '2025-12-01',
        'end_date': '2026-11-30',
    },
]


def seed_data(apps, schema_editor):
    Property = apps.get_model('properties', 'Property')
    Contract = apps.get_model('contract', 'Contract')

    properties = []
    for item in SEED_PROPERTIES:
        property_obj, _ = Property.objects.get_or_create(
            community=item['community'],
            region=item['region'],
            defaults=item,
        )
        properties.append(property_obj)

    for item in SEED_CONTRACTS:
        Contract.objects.get_or_create(
            tenant_name=item['tenant_name'],
            start_date=item['start_date'],
            defaults={
                'property': properties[item['property_index']],
                'landlord_name': item['landlord_name'],
                'rent': item['rent'],
                'end_date': item['end_date'],
                'status': '生效中',
            },
        )


def remove_seed_data(apps, schema_editor):
    Property = apps.get_model('properties', 'Property')
    Contract = apps.get_model('contract', 'Contract')
    names = [item['tenant_name'] for item in SEED_CONTRACTS]
    Contract.objects.filter(tenant_name__in=names).delete()
    Property.objects.filter(community__in=[item['community'] for item in SEED_PROPERTIES]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('properties', '0001_initial'),
        ('contract', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_data, remove_seed_data),
    ]
