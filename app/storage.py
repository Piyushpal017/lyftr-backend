from datetime import datetime
import sqlite3
from app.models import get_db_connection

def insert_message(data: dict) -> bool:
    """
    Returns True if inserted
    Returns False if duplicate
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO messages (message_id, from_msisdn, to_msisdn, ts, text, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data["message_id"],
            data["from"],
            data["to"],
            data["ts"],
            data.get("text"),
            datetime.utcnow().isoformat() + "Z"
        ))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        # Duplicate message_id
        return False

def list_messages(
    limit: int,
    offset: int,
    from_msisdn: str | None,
    since: str | None,
    q: str | None,
):
    conn = get_db_connection()
    cursor = conn.cursor()

    conditions = []
    params = []

    if from_msisdn:
        conditions.append("from_msisdn = ?")
        params.append(from_msisdn)

    if since:
        conditions.append("ts >= ?")
        params.append(since)

    if q:
        conditions.append("LOWER(text) LIKE ?")
        params.append(f"%{q.lower()}%")

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    # total count (IMPORTANT)
    count_query = f"""
        SELECT COUNT(*) FROM messages {where_clause}
    """
    cursor.execute(count_query, params)
    total = cursor.fetchone()[0]

    # actual data
    data_query = f"""
        SELECT message_id, from_msisdn AS "from", to_msisdn AS "to", ts, text
        FROM messages
        {where_clause}
        ORDER BY ts ASC, message_id ASC
        LIMIT ? OFFSET ?
    """
    cursor.execute(data_query, params + [limit, offset])
    rows = cursor.fetchall()

    conn.close()

    return rows, total

def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()

    # total messages
    cursor.execute("SELECT COUNT(*) FROM messages")
    total_messages = cursor.fetchone()[0]

    # unique senders
    cursor.execute("SELECT COUNT(DISTINCT from_msisdn) FROM messages")
    senders_count = cursor.fetchone()[0]

    # messages per sender (top 10)
    cursor.execute("""
        SELECT from_msisdn AS "from", COUNT(*) AS count
        FROM messages
        GROUP BY from_msisdn
        ORDER BY count DESC
        LIMIT 10
    """)
    messages_per_sender = [
        {"from": row["from"], "count": row["count"]}
        for row in cursor.fetchall()
    ]

    # first & last message timestamps
    cursor.execute("SELECT MIN(ts), MAX(ts) FROM messages")
    first_ts, last_ts = cursor.fetchone()

    conn.close()

    return {
        "total_messages": total_messages,
        "senders_count": senders_count,
        "messages_per_sender": messages_per_sender,
        "first_message_ts": first_ts,
        "last_message_ts": last_ts,
    }
