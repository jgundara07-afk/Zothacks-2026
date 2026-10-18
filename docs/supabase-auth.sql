-- Run in the Supabase SQL Editor, then enable this function as the
-- Authentication > Hooks > Before User Created Postgres hook.
-- This stops direct calls to Supabase Auth from bypassing the app's email policy.
create or replace function public.onething_before_user_created(event jsonb)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  address text := btrim(coalesce(event->'user'->>'email', ''));
  domain text;
begin
  domain := lower(split_part(address, '@', 2));
  if address !~ '^[A-Za-z0-9!#$%&''*+/=?^_`{|}~.-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$'
     or length(address) > 254
     or length(split_part(address, '@', 1)) > 64
     or split_part(address, '@', 1) like '.%'
     or split_part(address, '@', 1) like '%.'
     or split_part(address, '@', 1) like '%..%'
     or domain not in ('gmail.com','outlook.com','hotmail.com','live.com','yahoo.com',
                       'icloud.com','me.com','mac.com','proton.me','protonmail.com','uci.edu')
  then
    return jsonb_build_object('error', jsonb_build_object(
      'http_code', 400,
      'message', 'Use a Gmail, Outlook/Hotmail/Live, Yahoo, iCloud, Proton, or UC Irvine email address.'
    ));
  end if;
  return event;
end;
$$;

grant usage on schema public to supabase_auth_admin;
grant execute on function public.onething_before_user_created(jsonb) to supabase_auth_admin;
revoke execute on function public.onething_before_user_created(jsonb) from public, anon, authenticated;
