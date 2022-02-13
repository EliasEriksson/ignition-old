pre_models = (
    f"""
    create or replace function gen_token(table_ regclass) returns text as
    $$
    declare
        row_byte bytea;
    begin
        row_byte = int8send((select count(*) from table_));
        return encode(sha256(gen_random_bytes(32) || row_byte), 'base64');
    end;
    $$ language 'plpgsql';
    """
)

post_models = (
    f"""
    create extension if not exists pgcrypto;
    
    create or replace function update_expiration() returns trigger as
    $$
    BEGIN
        new.expires = now() + interval '1h';
        return new;
    end
    $$ language 'plpgsql';
    
    create or replace function update_expiration_of_row(row_id integer) returns void as
    $$
    begin
        update tokens set expires=now() + interval '1h' where tokens.id = row_id;
    end;
    $$ language 'plpgsql';
    
    create trigger update_expirations
        before update of value
        on tokens
        for row
    execute procedure update_expiration();
    
    
    """
)
