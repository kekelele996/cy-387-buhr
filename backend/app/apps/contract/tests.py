from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from app.apps.contract import services
from app.apps.contract.models import Contract, RenewalEvent, RenewalRequest
from app.apps.properties.models import Property

TENANT_HEADERS = {'HTTP_X_USER_ROLE': 'tenant', 'HTTP_X_USER_NAME': '%E9%99%88%E6%99%A8'}
LANDLORD_HEADERS = {'HTTP_X_USER_ROLE': 'landlord', 'HTTP_X_USER_NAME': '%E5%AE%8B%E6%88%BF%E4%B8%9C'}


class RenewalFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.house = Property.objects.create(
            community='海棠公寓', region='滨江区', layout='两室一厅', area=76,
            rent=5200, deposit=5200, payment='月付', facilities=[], status='已签约',
            landlord_phone='13800000001',
        )
        self.contract = Contract.objects.create(
            property=self.house, tenant_name='陈晨', landlord_name='宋房东', rent=5200, deposit=5200,
            start_date=date(2025, 10, 1), end_date=date(2026, 9, 30), status='有效',
        )
        self.other = Contract.objects.create(
            property=self.house, tenant_name='林悦', landlord_name='宋房东', rent=5400, deposit=5400,
            start_date=date(2026, 10, 1), end_date=date(2027, 9, 30), status='有效',
        )
        self.free_house = Property.objects.create(
            community='梧桐里', region='西湖区', layout='一室一厅', area=48,
            rent=3900, deposit=3900, payment='季付', facilities=[], status='已签约',
            landlord_phone='13800000002',
        )
        self.free_contract = Contract.objects.create(
            property=self.free_house, tenant_name='陈晨', landlord_name='宋房东', rent=3900, deposit=3900,
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31), status='有效',
        )

    def start(self, contract_id, start, end, rent, headers=None):
        response = self.client.post(
            '/api/renewals/',
            {'contractId': contract_id, 'newStartDate': start, 'newEndDate': end, 'proposedRent': rent},
            format='json', **(headers or TENANT_HEADERS),
        )
        return response

    def test_start_creates_pending_landlord_with_event(self):
        response = self.start(self.contract.id, '2026-10-01', '2027-09-30', 5300)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['status'], '待房东处理')
        event = RenewalEvent.objects.get(renewal_id=response.data['id'], action='发起续租')
        self.assertEqual(event.actor_role, '租客')
        self.assertEqual(event.actor_name, '陈晨')

    def test_overlapping_term_is_rejected_on_accept_and_explains_conflict(self):
        rid = self.start(self.contract.id, '2026-10-01', '2027-09-30', 5300).data['id']
        response = self.client.post(f'/api/renewals/{rid}/accept/', **LANDLORD_HEADERS)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['code'], 'RENEWAL_CONFLICT')
        self.assertEqual(response.data['data']['conflicts'][0]['id'], self.other.id)
        # 状态不变，冲突进入处理流水
        self.assertEqual(RenewalRequest.objects.get(pk=rid).status, '待房东处理')
        self.assertTrue(RenewalEvent.objects.filter(renewal_id=rid, action='租期冲突').exists())

    def test_counter_then_confirm_generates_next_contract(self):
        rid = self.start(self.free_contract.id, '2027-01-01', '2027-12-31', 4000).data['id']
        response = self.client.post(f'/api/renewals/{rid}/counter/', {'proposedRent': 4100},
                                    format='json', **LANDLORD_HEADERS)
        self.assertEqual(response.data['status'], '待租客确认')

        response = self.client.post(f'/api/renewals/{rid}/confirm/', **TENANT_HEADERS)
        self.assertEqual(response.data['status'], '已续租')
        new_id = response.data['createdContractId']
        self.assertTrue(new_id)

        self.contract.refresh_from_db()
        self.free_contract.refresh_from_db()
        new_contract = Contract.objects.get(pk=new_id)
        self.assertEqual(self.free_contract.status, '已续租')
        self.assertEqual(self.free_contract.renewed_contract_id, new_id)
        self.assertEqual(new_contract.rent, 4100)
        self.assertEqual(new_contract.status, '有效')

    def test_finalized_renewal_cannot_change_again(self):
        rid = self.start(self.free_contract.id, '2027-01-01', '2027-12-31', 4000).data['id']
        self.client.post(f'/api/renewals/{rid}/reject/', **LANDLORD_HEADERS)
        response = self.client.post(f'/api/renewals/{rid}/accept/', **LANDLORD_HEADERS)
        self.assertEqual(response.data['code'], 'RENEWAL_STATE_INVALID')

    def test_renewed_contract_cannot_start_again(self):
        services.landlord_accept(
            RenewalRequest.objects.create(
                contract=self.free_contract, property=self.free_house,
                tenant_name='陈晨', landlord_name='宋房东',
                new_start_date=date(2027, 1, 1), new_end_date=date(2027, 12, 31),
                proposed_rent=4000, current_rent=3900, status='待房东处理',
            ).id, '房东', '宋房东',
        )
        response = self.start(self.free_contract.id, '2028-01-01', '2028-12-31', 4200)
        self.assertEqual(response.data['code'], 'RENEWAL_STATE_INVALID')

    def test_role_guard(self):
        rid = self.start(self.contract.id, '2026-10-01', '2027-09-30', 5300).data['id']
        response = self.client.post(f'/api/renewals/{rid}/counter/', {'proposedRent': 5000},
                                    format='json', **TENANT_HEADERS)
        self.assertEqual(response.data['code'], 'RENEWAL_FORBIDDEN')

    def test_abutting_terms_do_not_conflict(self):
        rid = self.start(self.contract.id, '2027-10-01', '2028-09-30', 5300).data['id']
        response = self.client.post(f'/api/renewals/{rid}/accept/', **LANDLORD_HEADERS)
        self.assertEqual(response.data['status'], '已续租')
