from datetime import date

from django.db import migrations


def seed_demo_data(apps, schema_editor):
    Property = apps.get_model('properties', 'Property')
    Contract = apps.get_model('contract', 'Contract')

    p1 = Property.objects.create(
        community='海棠公寓', region='滨江区', layout='两室一厅', area=76,
        rent=5200, deposit=5200, payment='月付',
        facilities=['空调', '洗衣机', '宽带'], status='已签约', landlord_phone='13800000001',
    )
    p2 = Property.objects.create(
        community='梧桐里', region='西湖区', layout='一室一厅', area=48,
        rent=3900, deposit=3900, payment='季付',
        facilities=['冰箱', '宽带'], status='已签约', landlord_phone='13800000002',
    )
    Property.objects.create(
        community='江湾城', region='滨江区', layout='三室两厅', area=98,
        rent=6800, deposit=6800, payment='季付',
        facilities=['空调', '冰箱', '洗衣机', '宽带'], status='待出租', landlord_phone='13800000003',
    )

    # 陈晨即将到期的合同（续约演示起点）
    Contract.objects.create(
        property=p1, tenant_name='陈晨', landlord_name='宋房东', rent=5200, deposit=5200,
        start_date=date(2025, 10, 1), end_date=date(2026, 9, 30), status='有效',
    )
    # 同一套房已被口头答应给另一位租客：新租期若覆盖该区间会报冲突
    Contract.objects.create(
        property=p1, tenant_name='林悦', landlord_name='宋房东', rent=5400, deposit=5400,
        start_date=date(2026, 10, 1), end_date=date(2027, 9, 30), status='有效',
    )
    # 陈晨在另一套房源的在租合同：续租无冲突，演示完整成功流程
    Contract.objects.create(
        property=p2, tenant_name='陈晨', landlord_name='宋房东', rent=3900, deposit=3900,
        start_date=date(2026, 1, 1), end_date=date(2026, 12, 31), status='有效',
    )
    Contract.objects.create(
        property=p2, tenant_name='陈晨', landlord_name='宋房东', rent=3700, deposit=3700,
        start_date=date(2024, 1, 1), end_date=date(2024, 12, 31), status='已到期',
    )


def remove_demo_data(apps, schema_editor):
    Property = apps.get_model('properties', 'Property')
    Property.objects.filter(community__in=['海棠公寓', '梧桐里', '江湾城']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0001_initial'),
        ('contract', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_demo_data, remove_demo_data),
    ]
