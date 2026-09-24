export interface PropertyItem {
  id: number;
  community: string;
  region: string;
  layout: string;
  area: number;
  rent: number;
  deposit: number;
  payment: string;
  facilities: string[];
  status: string;
  landlordPhone: string;
}

export interface RepairTicket {
  id: number;
  faultType: string;
  description: string;
  status: string;
}

export type ContractStatus = '有效' | '已续租' | '已到期' | '已退租';

export type RenewalStatus = '待房东处理' | '待租客确认' | '已续租' | '已取消';

export interface RenewalEvent {
  id: number;
  actorRole: '房东' | '租客';
  actorName: string;
  action: string;
  note: string;
  time: string;
}

export interface RenewalRequest {
  id: number;
  contractId: number;
  propertyId: number;
  tenantName: string;
  landlordName: string;
  newStartDate: string;
  newEndDate: string;
  proposedRent: number;
  currentRent: number;
  status: RenewalStatus;
  message: string;
  createdContractId: number | null;
  events: RenewalEvent[];
  createdAt: string;
  updatedAt: string;
}

export interface ContractItem {
  id: number;
  propertyId: number;
  community: string;
  layout: string;
  tenantName: string;
  landlordName: string;
  rent: number;
  deposit: number;
  startDate: string;
  endDate: string;
  status: ContractStatus;
  renewedContractId: number | null;
  renewal: RenewalRequest | null;
}

export interface RenewalConflict {
  id: number;
  tenantName: string;
  startDate: string;
  endDate: string;
  rent: number;
}

export interface StartRenewalPayload {
  newStartDate: string;
  newEndDate: string;
  proposedRent: number;
  message?: string;
}
