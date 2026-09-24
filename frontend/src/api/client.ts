import { currentIdentity } from '../state/identity';
import type {
  ContractItem,
  PropertyItem,
  RenewalConflict,
  RenewalRequest,
  StartRenewalPayload,
} from '../types/domain';

const API_BASE = '/api';

export class ApiError extends Error {
  code: string;
  data: { conflicts?: RenewalConflict[] } | null;

  constructor(code: string, message: string, data: { conflicts?: RenewalConflict[] } | null) {
    super(message);
    this.code = code;
    this.data = data;
  }
}

function authHeaders(): HeadersInit {
  return {
    'X-User-Role': currentIdentity.role,
    'X-User-Name': encodeURIComponent(currentIdentity.name),
  };
}

export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { ...authHeaders(), ...(options.headers ?? {}) },
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new ApiError(payload.code, payload.message, payload.data ?? null);
  }
  return payload as T;
}

function post<T>(path: string, body: Record<string, unknown> = {}): Promise<T> {
  return request<T>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

export function getProperties(): Promise<PropertyItem[]> {
  return request<PropertyItem[]>('/properties/');
}

export function getContracts(): Promise<ContractItem[]> {
  return request<ContractItem[]>('/contracts/');
}

export function startRenewal(
  contractId: number,
  payload: StartRenewalPayload,
): Promise<RenewalRequest> {
  return post<RenewalRequest>('/renewals/', { contractId, ...payload });
}

export function renewalAction(
  renewalId: number,
  action: 'accept' | 'counter' | 'reject' | 'confirm' | 'cancel',
  body: Record<string, unknown> = {},
): Promise<RenewalRequest> {
  return post<RenewalRequest>(`/renewals/${renewalId}/${action}/`, body);
}

export function createRepair(ticket: { faultType: string; description: string }) {
  return post<{ id: number; status: string }>('/repairs/', ticket);
}
