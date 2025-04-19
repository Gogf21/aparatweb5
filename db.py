import psycopg2
import os
import hashlib

def create_connection():
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        database=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD')
    )

def save_user(user_data):
    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO Users 
            (first_name, last_name, middle_name, phone, email, birthdate, 
             gender, biography, username, password_hash)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            user_data['first_name'],
            user_data['last_name'],
            user_data['middle_name'],
            user_data['phone'],
            user_data['email'],
            user_data['birthdate'],
            user_data['gender'],
            user_data['biography'],
            user_data['username'],
            user_data['password_hash']
        ))

        user_id = cursor.fetchone()[0]

        for lang in user_data['languages']:
            cursor.execute("""
                INSERT INTO UserProgrammingLanguages (user_id, language_id)
                VALUES (%s, (SELECT id FROM ProgrammingLanguages WHERE name = %s))
            """, (user_id, lang))
        
        conn.commit()
        return user_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def get_user_by_id(user_id):
    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT u.id, u.first_name, u.last_name, u.middle_name, u.phone, 
                   u.email, u.birthdate, u.gender, u.biography, u.username,
                   array_agg(pl.name) as languages
            FROM Users u
            LEFT JOIN UserProgrammingLanguages upl ON u.id = upl.user_id
            LEFT JOIN ProgrammingLanguages pl ON upl.language_id = pl.id
            WHERE u.id = %s
            GROUP BY u.id
        """, (user_id,))

        row = cursor.fetchone()
        if not row:
            return None

        return {
            'id': row[0],
            'first_name': row[1],
            'last_name': row[2],
            'middle_name': row[3],
            'phone': row[4],
            'email': row[5],
            'birthdate': row[6],
            'gender': row[7],
            'biography': row[8],
            'username': row[9],
            'languages': row[10] if row[10] and row[10][0] else []
        }
    except Exception as e:
        raise e
    finally:
        cursor.close()
        conn.close()

def get_user_by_credentials(username, password):
    conn = create_connection()
    cursor = conn.cursor()

    try:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute("""
            SELECT id FROM Users 
            WHERE username = %s AND password_hash = %s
        """, (username, password_hash))

        row = cursor.fetchone()
        if not row:
            return None
            
        return get_user_by_id(row[0])
    except Exception as e:
        raise e
    finally:
        cursor.close()
        conn.close()

def update_user(user_id, user_data):
    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE Users
            SET first_name = %s,
                last_name = %s,
                middle_name = %s,
                phone = %s,
                email = %s,
                birthdate = %s,
                gender = %s,
                biography = %s
            WHERE id = %s
        """, (
            user_data['first_name'],
            user_data['last_name'],
            user_data['middle_name'],
            user_data['phone'],
            user_data['email'],
            user_data['birthdate'],
            user_data['gender'],
            user_data['biography'],
            user_id
        ))

        cursor.execute("""
            DELETE FROM UserProgrammingLanguages WHERE user_id = %s
        """, (user_id,))

        for lang in user_data['languages']:
            cursor.execute("""
                INSERT INTO UserProgrammingLanguages (user_id, language_id)
                VALUES (%s, (SELECT id FROM ProgrammingLanguages WHERE name = %s))
            """, (user_id, lang))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()
