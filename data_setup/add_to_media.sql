use recap_db;

/* ALTER TABLE media
ADD addedby int;

alter table media
ADD CONSTRAINT fk_addedby
foreign key (addedby)
references users(user_id)
on update restrict
on delete cascade;
 */
-- UPDATE media SET addedby = 5 WHERE addedby IS NULL;