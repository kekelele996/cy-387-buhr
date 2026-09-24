import type {
  ContractItem,
  PropertyItem,
  RepairTicket,
  Renewal,
  RenewalConflict,
  RenewalCreatePayload,
} from '../types/domain';

const API_BASE = '/api';

export class ApiError extends Error {
  code: string;
  conflicts: RenewalConflict[];

  constructor(message: string, code: string, conflicts: RenewalConflict[] = []) {
    super(message);
    this.code = code;
    this.conflicts = conflicts;
  }
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options);
  if (response.ok) return response.json();

  let body: { message?: string; code?: string; conflicts?: RenewalConflict[] } = {};
  try {
    body = await response.json();
  } catch {
    body = {};
  }
  throw new ApiError(body.message || '请求失败，请稍后重试', String(body.code ?? response.status), body.conflicts || []);
}

export async function getProperties(): Promise<PropertyItem[]> {
  return request<PropertyItem[]>(`${API_BASE}/properties/`);
}

export async function createRepair(ticket: Pick<RepairTicket, 'faultType' | 'description'>): Promise<RepairTicket> {
  return request<RepairTicket>(`${API_BASE}/repairs/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(ticket),
  });
}

export async function getContracts(): Promise<ContractItem[]> {
  return request<ContractItem[]>(`${API_BASE}/contracts/`);
}

export async function createRenewal(
  contractId: number,
  payload: RenewalCreatePayload,
  role: string,
): Promise<Renewal> {
  return request<Renewal>(`${API_BASE}/contracts/${contractId}/renewals/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...payload, role }),
  });
}

export async function respondRenewal(
  renewalId: number,
  payload: { action: 'accept' | 'counter' | 'reject'; rent?: number },
  role: string,
): Promise<Renewal> {
  return request<Renewal>(`${API_BASE}/renewals/${renewalId}/respond/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...payload, role }),
  });
}

export async function confirmRenewal(
  renewalId: number,
  action: 'confirm' | 'cancel',
  role: string,
): Promise<Renewal> {
  return request<Renewal>(`${API_BASE}/renewals/${renewalId}/confirm/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action, role }),
  });
}
