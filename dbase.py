import psycopg2


def create_tables():
    with psycopg2.connect(database="vkinder", user="postgres", password="7") as conn:
        cur = conn.cursor()
        cur.execute("""
                CREATE TABLE IF NOT EXISTS users_id(
                id SERIAL PRIMARY KEY,
                user_vk_id INTEGER NOT NULL UNIQUE
                );
                
                CREATE TABLE IF NOT EXISTS viewed_profiles(
                Id SERIAL PRIMARY KEY,
                viewed_profile INTEGER NOT NULL UNIQUE,
                viewing_id INTEGER REFERENCES users_id(id)
                );
                """)
        conn.commit()


def write_db(viewing_id, viewed_profile):
    with psycopg2.connect(database="vkinder", user="postgres", password="7") as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_vk_id FROM users_id WHERE user_vk_id = %s", (viewing_id,))
        answer_viewing = cur.fetchone()
        if answer_viewing is None:
            cur.execute("""
                    INSERT INTO users_id(user_vk_id) VALUES (%s) RETURNING id;    
                    """, (viewing_id,))
            answer_returning_id = cur.fetchone()[0]
            cur.execute("""
                    INSERT INTO viewed_profiles(viewed_profile, viewing_id) VALUES (%s, %s);    
                    """, (viewed_profile, answer_returning_id))
            conn.commit()
        else:
            cur.execute("""
                    INSERT INTO viewed_profiles(viewed_profile, viewing_id) VALUES (%s, %s);    
                    """, (viewed_profile, 1))
            conn.commit()


def check_db(viewing_id, viewed_profile):
    with psycopg2.connect(database="vkinder", user="postgres", password="7") as conn:
        cur = conn.cursor()
        cur.execute("SELECT viewed_profile FROM viewed_profiles WHERE viewed_profile = %s", (viewed_profile,))
        answer_viewed = cur.fetchone()
        if answer_viewed is None:
            write_db(viewing_id, viewed_profile)
        else:
            return True
