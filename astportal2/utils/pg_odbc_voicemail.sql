--
-- First, let's create our large object type, called "lo"
--
CREATE FUNCTION loin (cstring) RETURNS lo AS 'oidin' LANGUAGE internal IMMUTABLE STRICT;
CREATE FUNCTION loout (lo) RETURNS cstring AS 'oidout' LANGUAGE internal IMMUTABLE STRICT;
CREATE FUNCTION lorecv (internal) RETURNS lo AS 'oidrecv' LANGUAGE internal IMMUTABLE STRICT;
CREATE FUNCTION losend (lo) RETURNS bytea AS 'oidrecv' LANGUAGE internal IMMUTABLE STRICT;

CREATE TYPE lo ( INPUT = loin, OUTPUT = loout, RECEIVE = lorecv, SEND = losend, INTERNALLENGTH = 4, PASSEDBYVALUE );
CREATE CAST (lo AS oid) WITHOUT FUNCTION AS IMPLICIT;
CREATE CAST (oid AS lo) WITHOUT FUNCTION AS IMPLICIT;

--
-- If we're not already using plpgsql, then let's use it!
--
CREATE TRUSTED LANGUAGE plpgsql;

--
-- Next, let's create a trigger to cleanup the large object table
-- whenever we update or delete a row from the voicemessages table
--

CREATE FUNCTION vm_lo_cleanup() RETURNS "trigger"
AS $$
declare
msgcount INTEGER;
begin
--    raise notice 'Starting lo_cleanup function for large object with oid %',old.recording;
-- If it is an update action but the BLOB (lo) field was not changed, dont do anything
if (TG_OP = 'UPDATE') then
if ((old.recording = new.recording) or (old.recording is NULL)) then
raise notice 'Not cleaning up the large object table, as recording has not changed';
return new;
end if;
end if;
if (old.recording IS NOT NULL) then
SELECT INTO msgcount COUNT(*) AS COUNT FROM voicemessages WHERE recording = old.recording;
if (msgcount > 0) then
raise notice 'Not deleting record from the large object table, as object is still referenced';
return new;
else
perform lo_unlink(old.recording);
if found then
raise notice 'Cleaning up the large object table';
return new;
else
raise exception 'Failed to cleanup the large object table';
return old;
end if;
end if;
else
raise notice 'No need to cleanup the large object table, no recording on old row';
return new;
end if;
end$$
LANGUAGE plpgsql;

--
-- Now, let's create our voicemessages table
-- This is what holds the voicemail from Asterisk
--

CREATE TABLE voicemessages
(
uniqueid serial PRIMARY KEY,
msgnum int4,
msg_id varchar(40),
dir varchar(80),
context varchar(80),
macrocontext varchar(80),
callerid varchar(40),
origtime varchar(40),
duration varchar(20),
flag varchar(8),
mailboxuser varchar(80),
mailboxcontext varchar(80),
recording lo,
label varchar(30),
"read" bool DEFAULT false
);

--
-- Let's not forget to make the voicemessages table use the trigger
--

CREATE TRIGGER vm_cleanup AFTER DELETE OR UPDATE ON voicemessages FOR EACH ROW EXECUTE PROCEDURE vm_lo_cleanup();
