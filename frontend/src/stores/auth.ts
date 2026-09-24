import { create } from "zustand";

interface AuthState {
  token: string | null;
  username: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

export const useAuth = create<AuthState>((set) => ({
  token: localStorage.getItem("token"),
  username: localStorage.getItem("username"),
  login: async (username, password) => {
    const { default: api } = await import("../lib/api");
    const { data } = await api.post("/auth/login/json", { username, password });
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("username", data.user.username);
    set({ token: data.access_token, username: data.user.username });
  },
  logout: () => {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    set({ token: null, username: null });
  },
}));
