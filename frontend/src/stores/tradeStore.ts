import { create } from 'zustand';
import type { Position, Trade, AccountOverview } from '../types';
import { tradeApi, accountApi } from '../services/api';

interface TradeState {
  userId: number | null;
  positions: Position[];
  trades: Trade[];
  overview: AccountOverview | null;
  loading: boolean;
  error: string | null;

  setUserId: (userId: number) => void;
  fetchPositions: () => Promise<void>;
  fetchTrades: () => Promise<void>;
  fetchOverview: () => Promise<void>;
  buyStock: (stockCode: string, stockName: string, price: number, quantity: number) => Promise<boolean>;
  sellStock: (stockCode: string, stockName: string, price: number, quantity: number) => Promise<boolean>;
}

export const useTradeStore = create<TradeState>((set, get) => ({
  userId: null,
  positions: [],
  trades: [],
  overview: null,
  loading: false,
  error: null,

  setUserId: (userId: number) => {
    set({ userId });
    // 自动加载数据
    get().fetchPositions();
    get().fetchTrades();
    get().fetchOverview();
  },

  fetchPositions: async () => {
    const { userId } = get();
    if (!userId) return;

    set({ loading: true, error: null });
    try {
      const response = await tradeApi.getPositions(userId);
      set({ positions: response.data, loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
    }
  },

  fetchTrades: async () => {
    const { userId } = get();
    if (!userId) return;

    set({ loading: true, error: null });
    try {
      const response = await tradeApi.getHistory(userId);
      set({ trades: response.data, loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
    }
  },

  fetchOverview: async () => {
    const { userId } = get();
    if (!userId) return;

    set({ loading: true, error: null });
    try {
      const response = await accountApi.getAccountOverview(userId);
      set({ overview: response.data, loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
    }
  },

  buyStock: async (stockCode, stockName, price, quantity) => {
    const { userId } = get();
    if (!userId) return false;

    set({ loading: true, error: null });
    try {
      await tradeApi.buy(userId, {
        stock_code: stockCode,
        stock_name: stockName,
        price,
        quantity,
      });
      // 刷新数据
      await get().fetchPositions();
      await get().fetchTrades();
      await get().fetchOverview();
      set({ loading: false });
      return true;
    } catch (error: any) {
      set({ error: error.response?.data?.detail || error.message, loading: false });
      return false;
    }
  },

  sellStock: async (stockCode, stockName, price, quantity) => {
    const { userId } = get();
    if (!userId) return false;

    set({ loading: true, error: null });
    try {
      await tradeApi.sell(userId, {
        stock_code: stockCode,
        stock_name: stockName,
        price,
        quantity,
      });
      // 刷新数据
      await get().fetchPositions();
      await get().fetchTrades();
      await get().fetchOverview();
      set({ loading: false });
      return true;
    } catch (error: any) {
      set({ error: error.response?.data?.detail || error.message, loading: false });
      return false;
    }
  },
}));
