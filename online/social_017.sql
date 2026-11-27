
-- Closed-alpha social systems and isolated authoritative combat test.
create table c3_private.c3_parties (
 id uuid primary key default gen_random_uuid(),
 leader_id uuid not null references c3_private.c3_characters(id) on delete cascade
);
create table c3_private.c3_party_members (
 character_id uuid primary key references c3_private.c3_characters(id) on delete cascade,
 party_id uuid not null references c3_private.c3_parties(id) on delete cascade
);
create index c3_party_member_party_idx on c3_private.c3_party_members(party_id);
create table c3_private.c3_party_invites (
 id uuid primary key default gen_random_uuid(),
 party_id uuid not null references c3_private.c3_parties(id) on delete cascade,
 target_id uuid not null references c3_private.c3_characters(id) on delete cascade,
 expires_at timestamptz not null default now()+interval '60 seconds',
 unique(party_id,target_id)
);
create table c3_private.c3_chat (
 id bigint generated always as identity primary key,
 sender_id uuid not null references c3_private.c3_characters(id) on delete cascade,
 channel text not null check(channel in ('world','party')),
 party_id uuid references c3_private.c3_parties(id) on delete cascade,
 body text not null check(char_length(body) between 1 and 200),
 sent_at timestamptz not null default now(),
 check((channel='world' and party_id is null) or (channel='party' and party_id is not null))
);
create index c3_chat_sender_idx on c3_private.c3_chat(sender_id,sent_at desc);
create index c3_chat_channel_idx on c3_private.c3_chat(channel,party_id,id desc);
create table c3_private.c3_training_target (
 id integer primary key check(id=1),
 hp integer not null check(hp between 0 and 300),
 respawn_at timestamptz,
 defeats bigint not null default 0
);
insert into c3_private.c3_training_target(id,hp) values(1,300);
create table c3_private.c3_training_stats (
 character_id uuid primary key references c3_private.c3_characters(id) on delete cascade,
 last_hit timestamptz not null default '-infinity',
 damage bigint not null default 0,
 finishing_hits bigint not null default 0
);
alter table c3_private.c3_parties enable row level security;
alter table c3_private.c3_party_members enable row level security;
alter table c3_private.c3_party_invites enable row level security;
alter table c3_private.c3_chat enable row level security;
alter table c3_private.c3_training_target enable row level security;
alter table c3_private.c3_training_stats enable row level security;
revoke all on c3_private.c3_parties,c3_private.c3_party_members,c3_private.c3_party_invites,c3_private.c3_chat,c3_private.c3_training_target,c3_private.c3_training_stats from public,anon,authenticated;

create function c3_private.c3_social(p_action text,p_payload jsonb default '{}'::jsonb)
returns jsonb language plpgsql security definer set search_path='' as $$
declare cid uuid; pid uuid; target uuid; invited uuid; v_channel text; v_body text; hit integer; health integer; remaining timestamptz; kills bigint; done boolean; t timestamptz:=clock_timestamp(); response jsonb;
begin
 select c.id into cid from c3_private.c3_characters c join c3_private.c3_alpha_access a on a.user_id=c.owner_id where c.owner_id=auth.uid() and not c.banned;
 if cid is null then raise exception 'Character unavailable'; end if;
 if jsonb_typeof(p_payload) is distinct from 'object' or octet_length(p_payload::text)>2048 then raise exception 'Invalid request'; end if;
 if p_action not in ('state','chat','invite','accept','decline','leave','attack') or p_action is null then raise exception 'Invalid action'; end if;
 -- Small closed-alpha population: serialize mutations to avoid party/invite races.
 if p_action in ('invite','accept','decline','leave','chat') then
  perform pg_advisory_xact_lock(17431,1);
 end if;
 select m.party_id into pid from c3_private.c3_party_members m where m.character_id=cid;
 if p_action='invite' then
  target:=(p_payload->>'target')::uuid;
  if target is null or target=cid then raise exception 'Choose another player'; end if;
  if not exists(select 1 from c3_private.c3_characters c join c3_private.c3_presence p on p.character_id=c.id join c3_private.c3_alpha_access a on a.user_id=c.owner_id where c.id=target and not c.banned and p.seen_at>t-interval '15 seconds') then raise exception 'Player offline'; end if;
  if exists(select 1 from c3_private.c3_party_members m where m.character_id=target) then raise exception 'Player already in a party'; end if;
  if pid is null then
   insert into c3_private.c3_parties(leader_id) values(cid) returning id into pid;
   insert into c3_private.c3_party_members(character_id,party_id) values(cid,pid);
  end if;
  if not exists(select 1 from c3_private.c3_parties p where p.id=pid and p.leader_id=cid) then raise exception 'Leader only'; end if;
  if (select count(*) from c3_private.c3_party_members m where m.party_id=pid)>=4 then raise exception 'Party full'; end if;
  delete from c3_private.c3_party_invites where expires_at<t;
  if (select count(*) from c3_private.c3_party_invites i where i.party_id=pid)>=8 then raise exception 'Too many invitations'; end if;
  insert into c3_private.c3_party_invites(party_id,target_id) values(pid,target) on conflict(party_id,target_id) do nothing;
 elsif p_action in ('accept','decline') then
  invited:=(p_payload->>'invite')::uuid;
  select i.party_id into target from c3_private.c3_party_invites i where i.id=invited and i.target_id=cid and i.expires_at>t;
  if target is null then raise exception 'Invitation expired'; end if;
  if p_action='accept' then
   if pid is not null then raise exception 'Leave current party first'; end if;
   if (select count(*) from c3_private.c3_party_members m where m.party_id=target)>=4 then raise exception 'Party full'; end if;
   insert into c3_private.c3_party_members(character_id,party_id) values(cid,target);
   pid:=target;
   delete from c3_private.c3_party_invites where target_id=cid;
  else
   delete from c3_private.c3_party_invites where id=invited and target_id=cid;
  end if;
 elsif p_action='leave' then
  if pid is not null then
   delete from c3_private.c3_party_members where character_id=cid;
   if not exists(select 1 from c3_private.c3_party_members m where m.party_id=pid) then
    delete from c3_private.c3_parties where id=pid;
   else
    update c3_private.c3_parties p set leader_id=(select m.character_id from c3_private.c3_party_members m where m.party_id=pid order by m.character_id limit 1) where p.id=pid and p.leader_id=cid;
   end if;
   pid:=null;
  end if;
 elsif p_action='chat' then
  v_channel:=p_payload->>'channel'; v_body:=trim(p_payload->>'body');
  if v_channel is null or v_channel not in ('world','party') or (v_channel='party' and pid is null) or v_body is null or char_length(v_body) not between 1 and 200 then raise exception 'Invalid message'; end if;
  if exists(select 1 from c3_private.c3_chat c where c.sender_id=cid and c.sent_at>t-interval '2 seconds') then raise exception 'Chat cooldown: 2 seconds'; end if;
  insert into c3_private.c3_chat(sender_id,channel,party_id,body) values(cid,v_channel,case when v_channel='party' then pid else null end,v_body);
  delete from c3_private.c3_chat where sent_at<t-interval '48 hours';
 elsif p_action='attack' then
  -- Isolated shared training target, never modifies legacy XP/loot/equipment.
  if not exists(select 1 from c3_private.c3_presence p where p.character_id=cid and p.region='field' and p.seen_at>t-interval '12 seconds' and (p.x+5)*(p.x+5)+(p.z-1.7)*(p.z-1.7)<=64) then raise exception 'Training is near the starting outpost'; end if;
  insert into c3_private.c3_training_stats(character_id) values(cid) on conflict do nothing;
  perform 1 from c3_private.c3_training_stats where character_id=cid for update;
  if exists(select 1 from c3_private.c3_training_stats s where s.character_id=cid and s.last_hit>t-interval '1500 milliseconds') then raise exception 'Attack cooldown'; end if;
  select a.hp,a.respawn_at,a.defeats into health,remaining,kills from c3_private.c3_training_target a where a.id=1 for update;
  if health=0 and remaining>t then raise exception 'Target respawning'; end if;
  if health=0 then health:=300; end if;
  hit:=least(health,12+floor(random()*9)::integer);
  health:=health-hit;done:=health=0;
  update c3_private.c3_training_target set hp=health,respawn_at=case when done then t+interval '15 seconds' else null end,defeats=kills+case when done then 1 else 0 end where id=1;
  update c3_private.c3_training_stats set last_hit=t,damage=damage+hit,finishing_hits=finishing_hits+case when done then 1 else 0 end where character_id=cid;
 end if;
 -- Only the caller's party, addressed invites and recent public messages are returned.
 select jsonb_build_object(
 'me',cid,'party',pid,
 'leader',(select p.leader_id from c3_private.c3_parties p where p.id=pid),
 'members',coalesce((select jsonb_agg(jsonb_build_object('id',c.id,'name',c.name,'online',coalesce(p.seen_at>t-interval '15 seconds',false))) from c3_private.c3_party_members m join c3_private.c3_characters c on c.id=m.character_id left join c3_private.c3_presence p on p.character_id=c.id where m.party_id=pid and not c.banned),'[]'::jsonb),
 'invites',coalesce((select jsonb_agg(jsonb_build_object('id',i.id,'from',c.name)) from c3_private.c3_party_invites i join c3_private.c3_parties p on p.id=i.party_id join c3_private.c3_characters c on c.id=p.leader_id where i.target_id=cid and i.expires_at>t and not c.banned),'[]'::jsonb),
 'players',coalesce((select jsonb_agg(to_jsonb(v)) from (select c.id,c.name from c3_private.c3_presence p join c3_private.c3_characters c on c.id=p.character_id join c3_private.c3_alpha_access a on a.user_id=c.owner_id where c.id<>cid and not c.banned and p.seen_at>t-interval '15 seconds' limit 40) v),'[]'::jsonb),
 'messages',coalesce((select jsonb_agg(to_jsonb(v) order by v.id) from (select m.id,c.name,m.channel,m.body,m.sent_at from c3_private.c3_chat m join c3_private.c3_characters c on c.id=m.sender_id where m.sent_at>t-interval '48 hours' and not c.banned and (m.channel='world' or (m.channel='party' and m.party_id=pid)) order by m.id desc limit 60) v),'[]'::jsonb),
 'training',(select jsonb_build_object('hp',case when a.hp=0 and a.respawn_at<=t then 300 else a.hp end,'max_hp',300,'respawn_at',a.respawn_at,'defeats',a.defeats,'damage',coalesce(s.damage,0),'finishing_hits',coalesce(s.finishing_hits,0),'last_damage',hit) from c3_private.c3_training_target a left join c3_private.c3_training_stats s on s.character_id=cid where a.id=1)
 ) into response;
 return response;
end $$;
revoke all on function c3_private.c3_social(text,jsonb) from public,anon,authenticated;
grant execute on function c3_private.c3_social(text,jsonb) to authenticated;
create function public.c3_social(p_action text,p_payload jsonb default '{}'::jsonb) returns jsonb language sql security invoker set search_path='' as $$select c3_private.c3_social(p_action,p_payload)$$;
revoke all on function public.c3_social(text,jsonb) from public,anon,authenticated;
grant execute on function public.c3_social(text,jsonb) to authenticated;
