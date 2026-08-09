"use client";

import type { User } from "@supabase/supabase-js";
import { createContext, ReactNode, useContext, useEffect, useMemo, useState } from "react";
import { hasSupabaseConfig, supabase } from "../lib/supabase";

interface AuthValue {
  user: User | null;
  loading: boolean;
  configured: boolean;
  signIn: (email: string, password: string) => Promise<string | null>;
  signUp: (email: string, password: string) => Promise<string | null>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(hasSupabaseConfig);

  useEffect(() => {
    if (!supabase) return;
    void supabase.auth.getUser().then(({ data }) => {
      setUser(data.user);
      setLoading(false);
    });
    const { data } = supabase.auth.onAuthStateChange((_event, session) => setUser(session?.user ?? null));
    return () => data.subscription.unsubscribe();
  }, []);

  const value = useMemo<AuthValue>(() => ({
    user,
    loading,
    configured: hasSupabaseConfig,
    async signIn(email, password) {
      if (!supabase) throw new Error("Supabase is not configured.");
      const { error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) throw error;
      return null;
    },
    async signUp(email, password) {
      if (!supabase) throw new Error("Supabase is not configured.");
      const { data, error } = await supabase.auth.signUp({ email, password });
      if (error) throw error;
      return data.session ? null : "Check your inbox to confirm your email, then sign in.";
    },
    async signOut() {
      await supabase?.auth.signOut();
    },
  }), [loading, user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used within AuthProvider");
  return value;
}
