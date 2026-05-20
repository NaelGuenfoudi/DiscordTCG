"""
Base de données SQLite pour la marketplace.

Tables :
- users     : profils membres (réputation, compteurs)
- listings  : annonces postées
- transactions / feedbacks : prévus pour plus tard (réputation)
"""
import sqlite3
from typing import Optional

import config


class Database:
    """Wrapper SQLite simple et synchrone.

    SQLite est suffisant pour le volume d'une communauté Discord.
    Si besoin de scaler : migrer vers PostgreSQL (changer cette classe,
    le reste du bot ne bouge pas car il passe par ces méthodes).
    """

    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        conn = self._connect()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id         TEXT UNIQUE NOT NULL,
                discord_username   TEXT,
                reputation_avg     REAL DEFAULT 0.0,
                total_transactions INTEGER DEFAULT 0,
                total_feedback     INTEGER DEFAULT 0,
                verified           INTEGER DEFAULT 0,
                member_since       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS listings (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL,
                listing_type  TEXT NOT NULL,
                tcg           TEXT NOT NULL,
                card_name     TEXT NOT NULL,
                card_set      TEXT,
                price         REAL,
                condition     TEXT,
                description   TEXT,
                location      TEXT,
                photo_url     TEXT,
                status        TEXT DEFAULT 'disponible',
                forum_post_id TEXT,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id    INTEGER NOT NULL,
                buyer_id     INTEGER NOT NULL,
                listing_id   INTEGER,
                status       TEXT DEFAULT 'pending',
                created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (seller_id) REFERENCES users(id),
                FOREIGN KEY (buyer_id) REFERENCES users(id),
                FOREIGN KEY (listing_id) REFERENCES listings(id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS feedbacks (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id INTEGER NOT NULL,
                from_user_id   INTEGER NOT NULL,
                to_user_id     INTEGER NOT NULL,
                rating         INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                comment        TEXT,
                created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    # ── Users ──────────────────────────────────────────────

    def get_or_create_user(self, discord_id: str, username: str | None = None) -> int:
        """Retourne l'id interne du user, le crée s'il n'existe pas."""
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE discord_id = ?", (discord_id,))
        row = cur.fetchone()
        if row:
            user_id = row[0]
        else:
            cur.execute(
                "INSERT INTO users (discord_id, discord_username) VALUES (?, ?)",
                (discord_id, username),
            )
            user_id = cur.lastrowid
            conn.commit()
        conn.close()
        return user_id

    def get_user_profile(self, discord_id: str) -> Optional[dict]:
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE discord_id = ?", (discord_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    # ── Listings ───────────────────────────────────────────

    def create_listing(self, data: dict) -> int:
        """Insère une annonce, retourne son id."""
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO listings
            (user_id, listing_type, tcg, card_name, card_set, price,
             condition, description, location, photo_url, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'disponible')
        """, (
            data["user_id"],
            data["listing_type"],
            data["tcg"],
            data["card_name"],
            data.get("card_set"),
            data.get("price"),
            data.get("condition"),
            data.get("description"),
            data.get("location"),
            data.get("photo_url"),
        ))
        listing_id = cur.lastrowid
        conn.commit()
        conn.close()
        return listing_id

    def set_listing_post_id(self, listing_id: int, post_id: str) -> None:
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            "UPDATE listings SET forum_post_id = ? WHERE id = ?",
            (post_id, listing_id),
        )
        conn.commit()
        conn.close()

    def get_listing_by_post(self, post_id: str) -> Optional[dict]:
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM listings WHERE forum_post_id = ?", (post_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def set_listing_status(self, listing_id: int, status: str) -> None:
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            "UPDATE listings SET status = ? WHERE id = ?",
            (status, listing_id),
        )
        conn.commit()
        conn.close()

    # ── Transactions & Feedbacks ──────────────────────────

    def create_transaction(self, listing_id: int, seller_id: int, buyer_id: int) -> int:
        """Crée une transaction et retourne son ID."""
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO transactions (listing_id, seller_id, buyer_id, status)
            VALUES (?, ?, ?, 'completed')
        """, (listing_id, seller_id, buyer_id))
        tx_id = cur.lastrowid
        conn.commit()
        conn.close()
        return tx_id

    def add_feedback(self, transaction_id: int, from_id: int, to_id: int, rating: int, comment: str = None) -> None:
        """Ajoute un feedback et met à jour les stats du destinataire."""
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO feedbacks (transaction_id, from_user_id, to_user_id, rating, comment)
            VALUES (?, ?, ?, ?, ?)
        """, (transaction_id, from_id, to_id, rating, comment))
        conn.commit()
        conn.close()
        # Mettre à jour les stats de celui qui a reçu la note
        self.update_user_stats(to_id)

    def update_user_stats(self, user_id: int) -> None:
        """Recalcule la moyenne de réputation et le total de feedbacks."""
        conn = self._connect()
        cur = conn.cursor()
        # Calcul de la moyenne et du compte depuis la table feedbacks
        cur.execute("""
            SELECT AVG(rating), COUNT(id)
            FROM feedbacks
            WHERE to_user_id = ?
        """, (user_id,))
        avg, count = cur.fetchone()

        # Nombre de transactions uniques (en tant qu'acheteur ou vendeur)
        cur.execute("""
            SELECT COUNT(id) FROM transactions
            WHERE (seller_id = ? OR buyer_id = ?) AND status = 'completed'
        """, (user_id, user_id))
        total_tx = cur.fetchone()[0]

        cur.execute("""
            UPDATE users
            SET reputation_avg = ?, total_feedback = ?, total_transactions = ?
            WHERE id = ?
        """, (avg or 0.0, count, total_tx, user_id))
        conn.commit()
        conn.close()

# Instance partagée
db = Database()
