-- allow authenticated users to receive and send broadcasts on private channels
create policy "Allow authenticated broadcast read" on "realtime"."messages"
    for select to authenticated using (true);

create policy "Allow authenticated broadcast write" on "realtime"."messages"
    for insert to authenticated with check (true);
