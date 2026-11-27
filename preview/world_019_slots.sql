-- v0.19 isolated world-preview characters. Existing c3_characters is untouched.
create table c3_private.c3_world_slots (
 id uuid primary key default gen_random_uuid(),
 owner_id uuid not null references auth.users(id) on delete cascade,
 slot smallint not null check(slot between 1 and 3),
 name text not null check(char_length(name) between 3 and 24),
 race text not null check(race in ('Человек','Эльф','Тёмный эльф','Орк','Гном')),
 discipline text not null,
 gender text not null check(gender in ('male','female')),
 face smallint not null check(face between 0 and 3),
 hair smallint not null check(hair between 0 and 3),
 hair_color smallint not null check(hair_color between 0 and 3),
 skin smallint not null check(skin between 0 and 3),
 progress jsonb not null default '{}'::jsonb,
 x real not null default -85.2, z real not null default 0,
 revision bigint not null default 0,
 updated_at timestamptz not null default now(),
 unique(owner_id,slot)
);
create unique index c3_world_slots_name_idx on c3_private.c3_world_slots(lower(name));
alter table c3_private.c3_world_slots enable row level security;
revoke all on c3_private.c3_world_slots from public,anon,authenticated;
create function c3_private.c3_world_slots_api(p_action text,p_payload jsonb default '{}'::jsonb)
returns jsonb language plpgsql security definer set search_path='' as $$
declare uid uuid:=auth.uid(); r text; d text; n text; g text;
 i smallint; f smallint; h smallint; hc smallint; sk smallint;
 cid uuid; rev bigint; xx real; zz real; state jsonb; result jsonb;
begin
 if uid is null or not exists(select 1 from c3_private.c3_alpha_access a where a.user_id=uid)
 or exists(select 1 from c3_private.c3_characters c where c.owner_id=uid and c.banned)
 then raise exception 'Character access unavailable'; end if;
 if jsonb_typeof(p_payload) is distinct from 'object' or octet_length(p_payload::text)>131072 then raise exception 'Invalid request'; end if;
 if p_action='create' then
  i:=(p_payload->>'slot')::smallint; n:=trim(p_payload->>'name'); r:=p_payload->>'race'; d:=p_payload->>'discipline'; g:=p_payload->>'gender';
  f:=(p_payload->>'face')::smallint; h:=(p_payload->>'hair')::smallint; hc:=(p_payload->>'hair_color')::smallint; sk:=(p_payload->>'skin')::smallint;
  if n is null or n !~ '^[[:alnum:]_-]{3,24}$' then raise exception 'Invalid character name'; end if;
  if r is null or d is null or not (
    (r='Человек' and d in ('Ратник','Ученик чар')) or
    (r='Эльф' and d in ('Страж','Ученик росы')) or
    (r='Тёмный эльф' and d in ('Воин тени','Ученик сумерек')) or
    (r='Орк' and d in ('Боец','Ученик духов')) or
    (r='Гном' and d='Подгорный боец')) then raise exception 'Invalid race/class'; end if;
  insert into c3_private.c3_world_slots(owner_id,slot,name,race,discipline,gender,face,hair,hair_color,skin)
  values(uid,i,n,r,d,g,f,h,hc,sk);
 elsif p_action='save' then
  cid:=(p_payload->>'id')::uuid; rev:=(p_payload->>'revision')::bigint; xx:=(p_payload->>'x')::real; zz:=(p_payload->>'z')::real; state:=p_payload->'progress';
  if cid is null or rev is null or xx is null or zz is null or not(xx between -150 and 150 and zz between -90 and 90)
   or jsonb_typeof(state) is distinct from 'object' then raise exception 'Invalid save'; end if;
  update c3_private.c3_world_slots set progress=state,x=xx,z=zz,revision=revision+1,updated_at=now()
  where owner_id=uid and id=cid and revision=rev returning revision into rev;
  if not found then raise exception 'Save conflict: reload your character'; end if;
  return jsonb_build_object('revision',rev);
 elsif p_action<>'list' or p_action is null then raise exception 'Invalid action'; end if;
 select coalesce(jsonb_agg(to_jsonb(s)-'owner_id' order by s.slot),'[]'::jsonb) into result from c3_private.c3_world_slots s where s.owner_id=uid;
 return result;
end $$;
revoke all on function c3_private.c3_world_slots_api(text,jsonb) from public,anon,authenticated;
grant execute on function c3_private.c3_world_slots_api(text,jsonb) to authenticated;
create function public.c3_world_slots_api(p_action text,p_payload jsonb default '{}'::jsonb)
returns jsonb language sql security invoker set search_path='' as $$select c3_private.c3_world_slots_api(p_action,p_payload)$$;
revoke all on function public.c3_world_slots_api(text,jsonb) from public,anon,authenticated;
grant execute on function public.c3_world_slots_api(text,jsonb) to authenticated;
