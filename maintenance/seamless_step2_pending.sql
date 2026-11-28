-- PENDING: apply only after the actual Godot candidate passes.
-- Keep existing authentication, character ownership, region names and coordinates.
-- Expand field validation only to the connecting road.
begin;
do $migration$
declare f record; definition text; changed integer:=0;
 old_condition text:='(p_region=''field'' and p_x between -40 and 40 and p_z between -30 and 30)';
 new_condition text:='(p_region=''field'' and ((p_x between -40 and 40 and p_z between -30 and 30)
 or (p_x between 18 and 113 and abs(p_z)<=3)
 or (abs(p_x-110)<=3 and p_z between -3 and 47)
 or (p_x between 107 and 183 and abs(p_z-44)<=3)
 or (abs(p_x-180)<=2.4 and p_z>39 and p_z<=47)))';
begin
 for f in select p.oid from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='c3_private' and p.proname in ('c3_save','c3_world_tick') loop
  definition:=pg_get_functiondef(f.oid);
  if strpos(definition,old_condition)=0 then raise exception 'Unexpected existing position validator; no changes made'; end if;
  execute replace(definition,old_condition,new_condition);
  changed:=changed+1;
 end loop;
 if changed<>2 then raise exception 'Expected two existing functions'; end if;
end $migration$;
-- No direct table permissions or extra RPC functions are added.
commit;
