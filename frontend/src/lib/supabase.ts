import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env['VITE_SUPABASE_URL'] as string;
const supabaseKey = import.meta.env['VITE_SUPABASE_ANON_KEY'] as string;

if (!supabaseUrl || !supabaseKey) {
  console.warn("Supabase credentials not found in environment variables");
}

export const supabase = createClient(
  supabaseUrl || "https://dummy.supabase.co",
  supabaseKey || "dummy-key"
);
