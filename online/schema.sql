-- Project C3 Web v0.10: CLOSED online alpha (not authoritative combat).
-- Run once in a dedicated Supabase project. No service-role key in browser.
begin;
create table public.c3_characters (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null unique references auth.users(id) on delete cascade,
  name text not null check (char_length(name) between 3 and 24),
  race text not null,
  discipline text not null,
  gender text not null check(gender in ('male','female')),
  appearance smallint not null default 0 check(appearance between 0 and 3),
  progress jsonb not null default '{}'::jsonb,
  region text not null default 'field' check(region in ('field','town')),
  x real not null default -5, z real not null default 1.7,
  banned boolean not null default false,
  updated_at timestamptz not null default now()
);
create unique index c3_unique_name on public.c3_characters(lower(name));
create table public.c3_gms (user_id uuid primary key references auth.users(id) on delete cascade);
create table public.c3_presence (
  character_id uuid primary key references public.c3_characters(id) on delete cascade,
  region text not null, x real not null, z real not null,
  heading real not null default 0, seen_at timestamptz not null default now()
);
create index c3_presence_region_seen on public.c3_presence(region, seen_at);
create table public.c3_gm_audit (
  id bigint generated always as identity primary key,
  gm_id uuid not null, character_id uuid not null,
  action text not null, detail jsonb not null, created_at timestamptz not null default now()
);
alter table public.c3_characters enable row level security;
alter table public.c3_gms enable row level security;
alter table public.c3_presence enable row level security;
alter table public.c3_gm_audit enable row level security;
revoke all on public.c3_characters, public.c3_gms, public.c3_presence, public.c3_gm_audit from anon, authenticated;

create function public.c3_my_character() returns jsonb language sql stable security definer set search_path='' as $$
  select to_jsonb(c) - 'owner_id' from public.c3_characters c where c.owner_id=auth.uid()
$$;
create function public.c3_create_character(p_name text,p_race text,p_discipline text,p_gender text,p_appearance smallint)
returns jsonb language plpgsql security definer set search_path='' as $$
declare c public.c3_characters;
begin
 if auth.uid() is null then raise exception 'Sign in required'; end if;
 if trim(p_name) !~ '^[[:alnum:]_-]{3,24}$' then raise exception 'Invalid name'; end if;
 if not ((p_race='Человек' and p_discipline in ('Ратник','Ученик чар')) or
 (p_race='Эльф' and p_discipline in ('Страж','Ученик росы')) or
 (p_race='Тёмный эльф' and p_discipline in ('Воин тени','Ученик сумерек')) or
 (p_race='Орк' and p_discipline in ('Боец','Ученик духов')) or
 (p_race='Гном' and p_discipline='Подгорный боец')) then raise exception 'Invalid race/class'; end if;
 insert into public.c3_characters(owner_id,name,race,discipline,gender,appearance)
 values(auth.uid(),trim(p_name),p_race,p_discipline,p_gender,p_appearance) returning * into c;
 return to_jsonb(c)-'owner_id';
end $$;
-- Client snapshot is for private testing only; replace with authoritative server rewards before public launch.
create function public.c3_save(p_progress jsonb,p_region text,p_x real,p_z real)
returns void language plpgsql security definer set search_path='' as $$
begin
 if jsonb_typeof(p_progress) is distinct from 'object' or octet_length(p_progress::text)>131072 then raise exception 'Invalid save'; end if;
 if p_region not in ('field','town') or p_x is null or p_z is null or
 not ((p_region='field' and p_x between -20 and 20 and p_z between -14 and 14) or
 (p_region='town' and p_x between 134 and 226 and p_z between -39 and 39)) then raise exception 'Invalid position'; end if;
 update public.c3_characters set progress=p_progress,region=p_region,x=p_x,z=p_z,updated_at=now()
 where owner_id=auth.uid() and not banned;
 if not found then raise exception 'Character unavailable'; end if;
end $$;
-- Shared presence only, no shared combat or PvP in this milestone.
create function public.c3_world_tick(p_region text,p_x real,p_z real,p_heading real)
returns jsonb language plpgsql security definer set search_path='' as $$
declare cid uuid; old_seen timestamptz;
begin
 select id into cid from public.c3_characters where owner_id=auth.uid() and not banned;
 if cid is null then raise exception 'Character unavailable'; end if;
 if p_heading is null or not(p_heading between -100 and 100) or
 not ((p_region='field' and p_x between -20 and 20 and p_z between -14 and 14) or
 (p_region='town' and p_x between 134 and 226 and p_z between -39 and 39)) then raise exception 'Invalid position'; end if;
 insert into public.c3_presence(character_id,region,x,z,heading) values(cid,p_region,p_x,p_z,p_heading)
 on conflict(character_id) do update set region=excluded.region,x=excluded.x,z=excluded.z,heading=excluded.heading,seen_at=now()
 where public.c3_presence.seen_at < now()-interval '750 milliseconds';
 return coalesce((select jsonb_agg(to_jsonb(v)) from (
 select c.id,c.name,c.race,c.discipline,p.x,p.z,p.heading
 from public.c3_presence p join public.c3_characters c on c.id=p.character_id
 where p.character_id<>cid and not c.banned and p.region=p_region and p.seen_at>now()-interval '12 seconds'
 and abs(p.x-p_x)<30 and abs(p.z-p_z)<30 order by p.seen_at desc limit 40
 ) v),'[]'::jsonb);
end $$;
create function public.c3_leave() returns void language sql security definer set search_path='' as $$
 delete from public.c3_presence where character_id in (select id from public.c3_characters where owner_id=auth.uid())
$$;
create function public.c3_is_gm() returns boolean language sql stable security definer set search_path='' as $$
 select exists(select 1 from public.c3_gms where user_id=auth.uid())
$$;
create function public.c3_gm_players() returns jsonb language plpgsql security definer set search_path='' as $$
begin
 if not public.c3_is_gm() then raise exception 'Forbidden'; end if;
 return coalesce((select jsonb_agg(to_jsonb(v)) from (
 select c.id,c.name,c.race,c.discipline,c.banned,c.updated_at,c.progress,c.region,c.x,c.z,
 coalesce(p.seen_at>now()-interval '12 seconds',false) as online
 from public.c3_characters c left join public.c3_presence p on p.character_id=c.id
 order by c.updated_at desc limit 200
 ) v),'[]'::jsonb);
end $$;
create function public.c3_gm_ban(p_id uuid,p_banned boolean)
returns void language plpgsql security definer set search_path='' as $$
begin
 if not public.c3_is_gm() then raise exception 'Forbidden'; end if;
 update public.c3_characters set banned=p_banned where id=p_id;
 if not found then raise exception 'Character not found'; end if;
 if p_banned then delete from public.c3_presence where character_id=p_id; end if;
 insert into public.c3_gm_audit(gm_id,character_id,action,detail)
 values(auth.uid(),p_id,'ban',jsonb_build_object('banned',p_banned));
end $$;
revoke execute on function public.c3_my_character(),public.c3_create_character(text,text,text,text,smallint),
 public.c3_save(jsonb,text,real,real),public.c3_world_tick(text,real,real,real),public.c3_leave(),
 public.c3_is_gm(),public.c3_gm_players(),public.c3_gm_ban(uuid,boolean) from public, anon;
grant execute on function public.c3_my_character(),public.c3_create_character(text,text,text,text,smallint),
 public.c3_save(jsonb,text,real,real),public.c3_world_tick(text,real,real,real),public.c3_leave(),
 public.c3_is_gm(),public.c3_gm_players(),public.c3_gm_ban(uuid,boolean) to authenticated;
commit;
-- GM access: run manually as database owner after your account is registered.
-- insert into public.c3_gms(user_id) select id from auth.users where email='YOUR_EMAIL';
