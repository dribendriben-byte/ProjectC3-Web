-- Separate authoritative PvE ledger; existing client saves cannot write it.
create table c3_private.c3_raid_mobs (
 id integer primary key,
 name text not null,
 x real not null, z real not null,
 max_hp integer not null check(max_hp>0),
 hp integer not null check(hp>=0 and hp<=max_hp),
 generation bigint not null default 1,
 respawn_at timestamptz,
 xp_reward integer not null check(xp_reward>0),
 token_reward integer not null check(token_reward>0)
);
insert into c3_private.c3_raid_mobs(id,name,x,z,max_hp,hp,xp_reward,token_reward) values
 (1,'Каменный дозорный',-9,3,240,240,120,12),
 (2,'Страж заставы',-13,6,480,480,240,24);
create table c3_private.c3_raid_wallet (
 character_id uuid primary key references c3_private.c3_characters(id) on delete cascade,
 raid_xp bigint not null default 0 check(raid_xp>=0),
 tokens bigint not null default 0 check(tokens>=0),
 kills bigint not null default 0 check(kills>=0)
);
create table c3_private.c3_raid_cooldown (
 character_id uuid primary key references c3_private.c3_characters(id) on delete cascade,
 last_hit timestamptz not null default '-infinity'
);
create table c3_private.c3_raid_contribution (
 mob_id integer not null references c3_private.c3_raid_mobs(id) on delete cascade,
 generation bigint not null,
 character_id uuid not null references c3_private.c3_characters(id) on delete cascade,
 damage integer not null check(damage>0),
 last_hit timestamptz not null,
 primary key(mob_id,generation,character_id)
);
create table c3_private.c3_raid_award (
 mob_id integer not null references c3_private.c3_raid_mobs(id) on delete cascade,
 generation bigint not null,
 character_id uuid not null references c3_private.c3_characters(id) on delete cascade,
 xp integer not null check(xp>=0),
 tokens integer not null check(tokens>=0),
 awarded_at timestamptz not null default now(),
 primary key(mob_id,generation,character_id)
);
alter table c3_private.c3_raid_mobs enable row level security;
alter table c3_private.c3_raid_wallet enable row level security;
alter table c3_private.c3_raid_cooldown enable row level security;
alter table c3_private.c3_raid_contribution enable row level security;
alter table c3_private.c3_raid_award enable row level security;
revoke all on c3_private.c3_raid_mobs,c3_private.c3_raid_wallet,c3_private.c3_raid_cooldown,c3_private.c3_raid_contribution,c3_private.c3_raid_award from public,anon,authenticated;

create function c3_private.c3_raid(p_action text,p_mob integer default null)
returns jsonb language plpgsql security definer set search_path='' as $$
declare
 cid uuid; m c3_private.c3_raid_mobs%rowtype;
 loc c3_private.c3_presence%rowtype;
 t timestamptz:=clock_timestamp(); hit integer:=0;
 n integer; eligible uuid[]; won boolean:=false;
 my_xp integer:=0; my_tokens integer:=0;
 response jsonb;
begin
 select c.id into cid from c3_private.c3_characters c
 join c3_private.c3_alpha_access a on a.user_id=c.owner_id
 where c.owner_id=auth.uid() and not c.banned;
 if cid is null then raise exception 'Character unavailable'; end if;
 if p_action is null or p_action not in ('state','hit') then raise exception 'Invalid raid action'; end if;
 if p_action='hit' then
  select * into loc from c3_private.c3_presence p where p.character_id=cid;
  if not found or loc.region<>'field' or loc.seen_at<t-interval '8 seconds' then raise exception 'Position unavailable'; end if;
  insert into c3_private.c3_raid_cooldown(character_id) values(cid) on conflict do nothing;
  perform 1 from c3_private.c3_raid_cooldown where character_id=cid for update;
  if exists(select 1 from c3_private.c3_raid_cooldown c where c.character_id=cid and c.last_hit>t-interval '1500 milliseconds') then raise exception 'Attack cooldown'; end if;
  select * into m from c3_private.c3_raid_mobs where id=p_mob for update;
  if not found then raise exception 'Unknown target'; end if;
  if (loc.x-m.x)^2+(loc.z-m.z)^2>9 then raise exception 'Target out of range'; end if;
  if m.hp=0 then
   if m.respawn_at>t then raise exception 'Target respawning'; end if;
   m.hp:=m.max_hp;
   m.generation:=m.generation+1;
   delete from c3_private.c3_raid_contribution where mob_id=m.id and generation<m.generation;
  end if;
  -- Fixed alpha attack stats; no client-supplied damage, critical, gear, currency or level.
  hit:=least(m.hp,12+floor(random()*9)::integer);
  m.hp:=m.hp-hit;
  won:=m.hp=0;
  update c3_private.c3_raid_mobs set hp=m.hp,generation=m.generation,
   respawn_at=case when won then t+interval '25 seconds' else null end where id=m.id;
  update c3_private.c3_raid_cooldown set last_hit=t where character_id=cid;
  insert into c3_private.c3_raid_contribution(mob_id,generation,character_id,damage,last_hit)
   values(m.id,m.generation,cid,hit,t)
   on conflict(mob_id,generation,character_id) do update set damage=c3_private.c3_raid_contribution.damage+excluded.damage,last_hit=excluded.last_hit;
  if won then
   -- All recent contributing characters nearby, plus nearby current group members.
   -- Split a fixed reward budget; last hitter gets any rounding remainder.
   select array_agg(distinct c.id order by c.id) into eligible
   from c3_private.c3_characters c join c3_private.c3_alpha_access a on a.user_id=c.owner_id
   join c3_private.c3_presence p on p.character_id=c.id
   where not c.banned and p.region='field' and p.seen_at>=t-interval '8 seconds'
   and (p.x-m.x)^2+(p.z-m.z)^2<=100
   and (c.id=cid or exists(
    select 1 from c3_private.c3_raid_contribution d
    where d.mob_id=m.id and d.generation=m.generation and d.last_hit>=t-interval '60 seconds'
     and (d.character_id=c.id or exists(
      select 1 from c3_private.c3_party_members dm join c3_private.c3_party_members cm on cm.party_id=dm.party_id
      where dm.character_id=d.character_id and cm.character_id=c.id))));
   n:=cardinality(eligible);
   if n is null or n<1 then raise exception 'No reward recipient'; end if;
   my_xp:=m.xp_reward/n + m.xp_reward%n;
   my_tokens:=m.token_reward/n + m.token_reward%n;
   with awards as (
    insert into c3_private.c3_raid_award(mob_id,generation,character_id,xp,tokens)
    select m.id,m.generation,e,case when e=cid then my_xp else m.xp_reward/n end,
      case when e=cid then my_tokens else m.token_reward/n end from unnest(eligible) e
    returning character_id,xp,tokens
   )
   insert into c3_private.c3_raid_wallet(character_id,raid_xp,tokens,kills)
   select a.character_id,a.xp,a.tokens,case when a.character_id=cid then 1 else 0 end from awards a
   on conflict(character_id) do update set raid_xp=c3_private.c3_raid_wallet.raid_xp+excluded.raid_xp,
    tokens=c3_private.c3_raid_wallet.tokens+excluded.tokens,kills=c3_private.c3_raid_wallet.kills+excluded.kills;
  end if;
 end if;
 select jsonb_build_object(
 'mobs',coalesce((select jsonb_agg(jsonb_build_object('id',r.id,'name',r.name,'x',r.x,'z',r.z,
 'hp',case when r.hp=0 and r.respawn_at<=t then r.max_hp else r.hp end,'max_hp',r.max_hp,
 'generation',case when r.hp=0 and r.respawn_at<=t then r.generation+1 else r.generation end) order by r.id)
 from c3_private.c3_raid_mobs r),'[]'::jsonb),
 'wallet',coalesce((select jsonb_build_object('xp',w.raid_xp,'tokens',w.tokens,'kills',w.kills) from c3_private.c3_raid_wallet w where w.character_id=cid),'{"xp":0,"tokens":0,"kills":0}'::jsonb),
 'hit',hit,'mob',p_mob,'kill',won,'reward_xp',my_xp,'reward_tokens',my_tokens
 ) into response;
 return response;
end $$;
revoke all on function c3_private.c3_raid(text,integer) from public,anon,authenticated;
grant execute on function c3_private.c3_raid(text,integer) to authenticated;
create function public.c3_raid(p_action text,p_mob integer default null) returns jsonb language sql security invoker set search_path='' as $$select c3_private.c3_raid(p_action,p_mob)$$;
revoke all on function public.c3_raid(text,integer) from public,anon,authenticated;
grant execute on function public.c3_raid(text,integer) to authenticated;
