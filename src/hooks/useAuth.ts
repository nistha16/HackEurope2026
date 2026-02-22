"use client";

import * as React from "react";
import { getUser, setUser, clearUser, type StoredUser } from "@/lib/auth";

export function useAuth() {
  const [user, setUserState] = React.useState<StoredUser | null>(null);

  React.useEffect(() => {
    setUserState(getUser());
  }, []);

  function login(email: string, isPremium = false) {
    const u: StoredUser = { email, isPremium };
    setUser(u);
    setUserState(u);
  }

  function upgradeToPremium(email: string) {
    const u: StoredUser = { email, isPremium: true };
    setUser(u);
    setUserState(u);
  }

  function logout() {
    clearUser();
    setUserState(null);
  }

  return { user, login, upgradeToPremium, logout };
}
