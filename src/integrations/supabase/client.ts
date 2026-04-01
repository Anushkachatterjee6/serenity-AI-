// This file is modified for Streamlit compatibility.
import { createClient } from '@supabase/supabase-js';
import type { Database } from './types';

let _supabase: any = null;

export const getSupabase = () => {
  if (_supabase) return _supabase;

  const url = (window as any).VITE_SUPABASE_URL || "";
  const key = (window as any).VITE_SUPABASE_PUBLISHABLE_KEY || "";

  // If we don't have keys yet, we return a dummy object to prevent crash
  if (!url || !key) return null;

  _supabase = createClient<Database>(url, key, {
    auth: {
      storage: localStorage,
      persistSession: true,
      autoRefreshToken: true,
    }
  });

  return _supabase;
};

// Export a proxy or the client itself for easier migration
export const supabase = new Proxy({}, {
  get: (target, prop) => {
    const client = getSupabase();
    if (!client) {
      console.warn("Supabase accessed before keys were ready.");
      return undefined;
    }
    return (client as any)[prop];
  }
}) as any;