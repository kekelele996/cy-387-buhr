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

export interface RenewalEvent {
  id: number;
  actorRole: '房东' | '租客';
  action: string;
  rent: number | null;
  note: string;
  createdAt: string;
}

export interface RenewalConflict {
  contractId: number;
  tenantName: string;
  startDate: string;
  endDate: string;
}

export interface Renewal {
  id: number;
  startDate: string;
  endDate: string;
  rent: number;
  expectedRent: number;
  status: '待房东处理' | '待租客确认' | '已续租' | '已取消';
  newContractId: number | null;
  createdAt: string;
  events: RenewalEvent[];
}

export interface ContractItem {
  id: number;
  propertyId: number;
  community: string;
  tenantName: string;
  landlordName: string;
  rent: number;
  startDate: string;
  endDate: string;
  status: '生效中' | '已到期' | '已续租' | '已取消';
  renewedFromId: number | null;
  renewal: Renewal | null;
}

export interface RenewalCreatePayload {
  startDate: string;
  endDate: string;
  expectedRent: number;
}
