import { reactive } from 'vue';

export interface Identity {
  label: string;
  role: 'tenant' | 'landlord';
  name: string;
}

export const IDENTITIES: Identity[] = [
  { label: '租客 · 陈晨', role: 'tenant', name: '陈晨' },
  { label: '房东 · 宋房东', role: 'landlord', name: '宋房东' },
];

// 演示用登录身份：真实环境由 JWT 注入，此处用顶部身份切换模拟。
export const currentIdentity = reactive<Identity>({ ...IDENTITIES[0] });

export function switchIdentity(identity: Identity) {
  Object.assign(currentIdentity, identity);
}
