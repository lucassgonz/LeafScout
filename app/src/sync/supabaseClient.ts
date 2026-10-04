import 'react-native-url-polyfill/auto';
import { createClient } from '@supabase/supabase-js';

// Public anon/publishable key — meant to be embedded in a client app (it's
// what Row Level Security policies exist to constrain, see
// supabase/schema.sql's "anon insert" policies). Never put a service_role
// key here.
const SUPABASE_URL = 'https://chbhhzypwvkqmojvtcmx.supabase.co';
const SUPABASE_PUBLISHABLE_KEY = 'sb_publishable_jIN1bAGM9fXpu6tyAkJBkQ_piWQaDS1';

export const supabase = createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, {
  auth: { persistSession: false }, // no farmer auth yet — anonymous inserts only
});
