import axios from 'axios';

const API_BASE = '/api/broker';

export interface BrokerAccount {
  id: number;
  user_id: number;
  broker_type: string;
  account: string;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
}

export interface BrokerAccountCreate {
  broker_type: string;
  account: string;
  password: string;
}

export const brokerApi = {
  list: () => axios.get<BrokerAccount[]>(`${API_BASE}/accounts`),
  create: (data: BrokerAccountCreate) => axios.post<BrokerAccount>(`${API_BASE}/accounts`, data),
  update: (id: number, data: Partial<BrokerAccountCreate & { is_active: boolean }>) =>
    axios.put<BrokerAccount>(`${API_BASE}/accounts/${id}`, data),
  delete: (id: number) => axios.delete(`${API_BASE}/accounts/${id}`),
  login: (id: number) => axios.post(`${API_BASE}/accounts/${id}/login`),
};
