import psycopg2
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from datetime import datetime

console = Console()

DB_PARAMS = {
    "dbname": "music_app",
    "user": "postgres",
    "password": "123",
    "host": "localhost",
    "port": "5432"
}

def connect():
    return psycopg2.connect(**DB_PARAMS)

def create_tables():
    queries = [
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS artists (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            bio TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS albums (
            id SERIAL PRIMARY KEY,
            title VARCHAR(100) NOT NULL,
            artist_id INTEGER REFERENCES artists(id),
            release_date DATE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS songs (
            id SERIAL PRIMARY KEY,
            title VARCHAR(100) NOT NULL,
            album_id INTEGER REFERENCES albums(id),
            duration INTEGER,
            file_path TEXT NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS playlists (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            user_id INTEGER REFERENCES users(id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS playlist_songs (
            playlist_id INTEGER REFERENCES playlists(id),
            song_id INTEGER REFERENCES songs(id),
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (playlist_id, song_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS play_history (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            song_id INTEGER REFERENCES songs(id),
            played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS song_ratings (
            user_id INTEGER REFERENCES users(id),
            song_id INTEGER REFERENCES songs(id),
            rating INTEGER CHECK (rating >= 1 AND rating <= 5),
            PRIMARY KEY (user_id, song_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS song_likes (
            user_id INTEGER REFERENCES users(id),
            song_id INTEGER REFERENCES songs(id),
            liked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, song_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS artist_follows (
            user_id INTEGER REFERENCES users(id),
            artist_id INTEGER REFERENCES artists(id),
            followed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, artist_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS song_comments (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            song_id INTEGER REFERENCES songs(id),
            comment TEXT NOT NULL,
            commented_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    ]
    conn = connect()
    cur = conn.cursor()
    for q in queries:
        cur.execute(q)
    conn.commit()
    cur.close()
    conn.close()
    console.print("[green]All tables created successfully![/green]")

def menu():
    table = Table(title="🎵 Music App CLI Menu 🎵")
    table.add_column("Option", style="cyan", no_wrap=True)
    table.add_column("Action", style="magenta")
    actions = [
        ("1", "Manage Users"),
        ("2", "Manage Artists"),
        ("3", "Manage Albums"),
        ("4", "Manage Songs"),
        ("5", "Manage Playlists"),
        ("6", "Manage Playlist Songs"),
        ("7", "View Play History"),
        ("8", "Manage Song Ratings"),
        ("9", "Create Tables"),
        ("10", "Manage Song Likes"),
        ("11", "Manage Artist Follows"),
        ("12", "Manage Song Comments"),
        ("0", "Exit")
    ]
    for opt, desc in actions:
        table.add_row(opt, desc)
    console.print(table)


# ========== USER CRUD ==========
def manage_users():
    while True:
        table = Table(title="👥 User Management")
        table.add_column("Option", style="cyan")
        table.add_column("Action", style="magenta")
        table.add_row("1", "Add User")
        table.add_row("2", "View All Users")
        table.add_row("3", "Update User")
        table.add_row("4", "Delete User")
        table.add_row("5", "Back to Main Menu")
        console.print(table)
        
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4", "5"])
        
        if choice == "1":
            add_user()
        elif choice == "2":
            show_users()
        elif choice == "3":
            update_user()
        elif choice == "4":
            delete_user()
        elif choice == "5":
            break

def add_user():
    username = Prompt.ask("Enter username")
    email = Prompt.ask("Enter email")
    password = Prompt.ask("Enter password", password=True)
    
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (username, email, password)
            VALUES (%s, %s, %s);
        """, (username, email, password))
        conn.commit()
        console.print(f"[green]User '{username}' added successfully![/green]")
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        if conn:
            cur.close()
            conn.close()

def show_users():
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT id, username, email, created_at FROM users ORDER BY id;")
        users = cur.fetchall()
        
        table = Table(title="👥 Users")
        table.add_column("ID", justify="right")
        table.add_column("Username")
        table.add_column("Email")
        table.add_column("Created At")
        
        for user in users:
            table.add_row(str(user[0]), user[1], user[2], str(user[3]))
        console.print(table)
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        if conn:
            cur.close()
            conn.close()

def update_user():
    show_users()
    user_id = Prompt.ask("Enter ID of user to update")
    
    try:
        conn = connect()
        cur = conn.cursor()
        
        # Get current user data
        cur.execute("SELECT username, email FROM users WHERE id = %s;", (user_id,))
        user = cur.fetchone()
        
        if not user:
            console.print("[red]User not found![/red]")
            return
            
        current_username, current_email = user
        
        username = Prompt.ask(f"Enter new username (current: {current_username})", default=current_username)
        email = Prompt.ask(f"Enter new email (current: {current_email})", default=current_email)
        password = Prompt.ask("Enter new password (leave blank to keep current)", password=True, default="")
        
        if password:
            cur.execute("""
                UPDATE users 
                SET username = %s, email = %s, password = %s 
                WHERE id = %s;
            """, (username, email, password, user_id))
        else:
            cur.execute("""
                UPDATE users 
                SET username = %s, email = %s 
                WHERE id = %s;
            """, (username, email, user_id))
            
        conn.commit()
        console.print(f"[green]User {user_id} updated successfully![/green]")
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        if conn:
            cur.close()
            conn.close()

def delete_user():
    show_users()
    user_id = Prompt.ask("Enter ID of user to delete")
    
    if not Confirm.ask(f"[red]Are you sure you want to delete user {user_id}?[/red]"):
        return
        
    try:
        conn = connect()
        cur = conn.cursor()
        
        # First delete dependent records
        cur.execute("DELETE FROM playlists WHERE user_id = %s;", (user_id,))
        cur.execute("DELETE FROM play_history WHERE user_id = %s;", (user_id,))
        cur.execute("DELETE FROM song_ratings WHERE user_id = %s;", (user_id,))
        
        # Then delete the user
        cur.execute("DELETE FROM users WHERE id = %s;", (user_id,))
        conn.commit()
        
        if cur.rowcount > 0:
            console.print(f"[green]User {user_id} deleted successfully![/green]")
        else:
            console.print("[red]User not found![/red]")
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
        conn.rollback()
    finally:
        if conn:
            cur.close()
            conn.close()

# ========== ARTIST CRUD ==========
def manage_artists():
    while True:
        table = Table(title="🎤 Artist Management")
        table.add_column("Option", style="cyan")
        table.add_column("Action", style="magenta")
        table.add_row("1", "Add Artist")
        table.add_row("2", "View All Artists")
        table.add_row("3", "Update Artist")
        table.add_row("4", "Delete Artist")
        table.add_row("5", "Back to Main Menu")
        console.print(table)
        
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4", "5"])
        
        if choice == "1":
            add_artist()
        elif choice == "2":
            show_artists()
        elif choice == "3":
            update_artist()
        elif choice == "4":
            delete_artist()
        elif choice == "5":
            break

def add_artist():
    name = Prompt.ask("Enter artist name")
    bio = Prompt.ask("Enter artist bio (optional)", default="")
    
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO artists (name, bio)
            VALUES (%s, %s);
        """, (name, bio))
        conn.commit()
        console.print(f"[green]Artist '{name}' added successfully![/green]")
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        if conn:
            cur.close()
            conn.close()

def show_artists():
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT id, name, bio FROM artists ORDER BY name;")
        artists = cur.fetchall()
        
        table = Table(title="🎤 Artists")
        table.add_column("ID", justify="right")
        table.add_column("Name")
        table.add_column("Bio")
        
        for artist in artists:
            bio = artist[2] if artist[2] else "N/A"
            table.add_row(str(artist[0]), artist[1], bio)
        console.print(table)
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        if conn:
            cur.close()
            conn.close()

def update_artist():
    show_artists()
    artist_id = Prompt.ask("Enter ID of artist to update")
    
    try:
        conn = connect()
        cur = conn.cursor()
        
        # Get current artist data
        cur.execute("SELECT name, bio FROM artists WHERE id = %s;", (artist_id,))
        artist = cur.fetchone()
        
        if not artist:
            console.print("[red]Artist not found![/red]")
            return
            
        current_name, current_bio = artist
        
        name = Prompt.ask(f"Enter new name (current: {current_name})", default=current_name)
        bio = Prompt.ask(f"Enter new bio (current: {current_bio if current_bio else 'N/A'})", 
                         default=current_bio if current_bio else "")
        
        cur.execute("""
            UPDATE artists 
            SET name = %s, bio = %s 
            WHERE id = %s;
        """, (name, bio, artist_id))
            
        conn.commit()
        console.print(f"[green]Artist {artist_id} updated successfully![/green]")
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        if conn:
            cur.close()
            conn.close()

def delete_artist():
    show_artists()
    artist_id = Prompt.ask("Enter ID of artist to delete")
    
    if not Confirm.ask(f"[red]Are you sure you want to delete artist {artist_id}?[/red]"):
        return
        
    try:
        conn = connect()
        cur = conn.cursor()
        
        # First check if artist has albums
        cur.execute("SELECT COUNT(*) FROM albums WHERE artist_id = %s;", (artist_id,))
        album_count = cur.fetchone()[0]
        
        if album_count > 0:
            console.print("[red]Cannot delete artist with existing albums![/red]")
            return
            
        # Delete the artist
        cur.execute("DELETE FROM artists WHERE id = %s;", (artist_id,))
        conn.commit()
        
        if cur.rowcount > 0:
            console.print(f"[green]Artist {artist_id} deleted successfully![/green]")
        else:
            console.print("[red]Artist not found![/red]")
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
        conn.rollback()
    finally:
        if conn:
            cur.close()
            conn.close()

# ========== ALBUM CRUD ==========
def manage_albums():
    while True:
        table = Table(title="💿 Album Management")
        table.add_column("Option", style="cyan")
        table.add_column("Action", style="magenta")
        table.add_row("1", "Add Album")
        table.add_row("2", "View All Albums")
        table.add_row("3", "Update Album")
        table.add_row("4", "Delete Album")
        table.add_row("5", "Back to Main Menu")
        console.print(table)
        
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4", "5"])
        
        if choice == "1":
            add_album()
        elif choice == "2":
            show_albums()
        elif choice == "3":
            update_album()
        elif choice == "4":
            delete_album()
        elif choice == "5":
            break

def add_album():
    show_artists()
    artist_id = Prompt.ask("Enter artist ID for the album")
    title = Prompt.ask("Enter album title")
    release_date = Prompt.ask("Enter release date (YYYY-MM-DD)", default="")
    
    try:
        conn = connect()
        cur = conn.cursor()
        
        if release_date:
            cur.execute("""
                INSERT INTO albums (title, artist_id, release_date)
                VALUES (%s, %s, %s);
            """, (title, artist_id, release_date))
        else:
            cur.execute("""
                INSERT INTO albums (title, artist_id)
                VALUES (%s, %s);
            """, (title, artist_id))
            
        conn.commit()
        console.print(f"[green]Album '{title}' added successfully![/green]")
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        if conn:
            cur.close()
            conn.close()

def show_albums():
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            SELECT a.id, a.title, ar.name, a.release_date 
            FROM albums a
            JOIN artists ar ON a.artist_id = ar.id
            ORDER BY a.title;
        """)
        albums = cur.fetchall()
        
        table = Table(title="💿 Albums")
        table.add_column("ID", justify="right")
        table.add_column("Title")
        table.add_column("Artist")
        table.add_column("Release Date")
        
        for album in albums:
            release_date = str(album[3]) if album[3] else "N/A"
            table.add_row(str(album[0]), album[1], album[2], release_date)
        console.print(table)
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        if conn:
            cur.close()
            conn.close()

def update_album():
    show_albums()
    album_id = Prompt.ask("Enter ID of album to update")
    
    try:
        conn = connect()
        cur = conn.cursor()
        
        # Get current album data
        cur.execute("""
            SELECT a.title, a.artist_id, ar.name, a.release_date 
            FROM albums a
            JOIN artists ar ON a.artist_id = ar.id
            WHERE a.id = %s;
        """, (album_id,))
        album = cur.fetchone()
        
        if not album:
            console.print("[red]Album not found![/red]")
            return
            
        current_title, current_artist_id, current_artist_name, current_release_date = album
        
        title = Prompt.ask(f"Enter new title (current: {current_title})", default=current_title)
        
        # Show artists and allow change
        show_artists()
        artist_id = Prompt.ask(
            f"Enter new artist ID (current: {current_artist_id} - {current_artist_name})", 
            default=str(current_artist_id))
        
        release_date = Prompt.ask(
            f"Enter new release date (current: {current_release_date if current_release_date else 'N/A'})", 
            default=str(current_release_date) if current_release_date else "")
        
        cur.execute("""
            UPDATE albums 
            SET title = %s, artist_id = %s, release_date = %s
            WHERE id = %s;
        """, (title, artist_id, release_date if release_date else None, album_id))
            
        conn.commit()
        console.print(f"[green]Album {album_id} updated successfully![/green]")
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        if conn:
            cur.close()
            conn.close()

def delete_album():
    show_albums()
    album_id = Prompt.ask("Enter ID of album to delete")
    
    if not Confirm.ask(f"[red]Are you sure you want to delete album {album_id}?[/red]"):
        return
        
    try:
        conn = connect()
        cur = conn.cursor()
        
        # First check if album has songs
        cur.execute("SELECT COUNT(*) FROM songs WHERE album_id = %s;", (album_id,))
        song_count = cur.fetchone()[0]
        
        if song_count > 0:
            console.print("[red]Cannot delete album with existing songs![/red]")
            return
            
        # Delete the album
        cur.execute("DELETE FROM albums WHERE id = %s;", (album_id,))
        conn.commit()
        
        if cur.rowcount > 0:
            console.print(f"[green]Album {album_id} deleted successfully![/green]")
        else:
            console.print("[red]Album not found![/red]")
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
        conn.rollback()
    finally:
        if conn:
            cur.close()
            conn.close()

# ========== SONG CRUD ==========
def manage_songs():
    while True:
        table = Table(title="🎵 Song Management")
        table.add_column("Option", style="cyan")
        table.add_column("Action", style="magenta")
        table.add_row("1", "Add Song")
        table.add_row("2", "View All Songs")
        table.add_row("3", "Update Song")
        table.add_row("4", "Delete Song")
        table.add_row("5", "Back to Main Menu")
        console.print(table)
        
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4", "5"])
        
        if choice == "1":
            add_song()
        elif choice == "2":
            show_songs()
        elif choice == "3":
            update_song()
        elif choice == "4":
            delete_song()
        elif choice == "5":
            break

def add_song():
    show_albums()
    album_id = Prompt.ask("Enter album ID for the song")
    title = Prompt.ask("Enter song title")
    duration = Prompt.ask("Enter song duration in seconds", default="0")
    file_path = Prompt.ask("Enter file path for the song")
    
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO songs (title, album_id, duration, file_path)
            VALUES (%s, %s, %s, %s);
        """, (title, album_id, int(duration), file_path))
        conn.commit()
        console.print(f"[green]Song '{title}' added successfully![/green]")
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        if conn:
            cur.close()
            conn.close()

def show_songs():
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            SELECT s.id, s.title, al.title, ar.name, s.duration, s.file_path 
            FROM songs s
            JOIN albums al ON s.album_id = al.id
            JOIN artists ar ON al.artist_id = ar.id
            ORDER BY s.title;
        """)
        songs = cur.fetchall()
        
        table = Table(title="🎵 Songs")
        table.add_column("ID", justify="right")
        table.add_column("Title")
        table.add_column("Album")
        table.add_column("Artist")
        table.add_column("Duration (sec)")
        table.add_column("File Path")
        
        for song in songs:
            duration = str(song[4]) if song[4] else "N/A"
            table.add_row(str(song[0]), song[1], song[2], song[3], duration, song[5])
        console.print(table)
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        if conn:
            cur.close()
            conn.close()

def update_song():
    show_songs()
    song_id = Prompt.ask("Enter ID of song to update")
    
    try:
        conn = connect()
        cur = conn.cursor()
        
        # Get current song data
        cur.execute("""
            SELECT s.title, s.album_id, al.title, s.duration, s.file_path 
            FROM songs s
            JOIN albums al ON s.album_id = al.id
            WHERE s.id = %s;
        """, (song_id,))
        song = cur.fetchone()
        
        if not song:
            console.print("[red]Song not found![/red]")
            return
            
        current_title, current_album_id, current_album_title, current_duration, current_file_path = song
        
        title = Prompt.ask(f"Enter new title (current: {current_title})", default=current_title)
        
        # Show albums and allow change
        show_albums()
        album_id = Prompt.ask(
            f"Enter new album ID (current: {current_album_id} - {current_album_title})", 
            default=str(current_album_id))
        
        duration = Prompt.ask(
            f"Enter new duration in seconds (current: {current_duration if current_duration else 'N/A'})", 
            default=str(current_duration) if current_duration else "0")
        
        file_path = Prompt.ask(
            f"Enter new file path (current: {current_file_path})", 
            default=current_file_path)
        
        cur.execute("""
            UPDATE songs 
            SET title = %s, album_id = %s, duration = %s, file_path = %s
            WHERE id = %s;
        """, (title, album_id, int(duration), file_path, song_id))
            
        conn.commit()
        console.print(f"[green]Song {song_id} updated successfully![/green]")
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        if conn:
            cur.close()
            conn.close()

def delete_song():
    show_songs()
    song_id = Prompt.ask("Enter ID of song to delete")
    
    if not Confirm.ask(f"[red]Are you sure you want to delete song {song_id}?[/red]"):
        return
        
    try:
        conn = connect()
        cur = conn.cursor()
        
        # First delete dependent records
        cur.execute("DELETE FROM playlist_songs WHERE song_id = %s;", (song_id,))
        cur.execute("DELETE FROM play_history WHERE song_id = %s;", (song_id,))
        cur.execute("DELETE FROM song_ratings WHERE song_id = %s;", (song_id,))
        
        # Then delete the song
        cur.execute("DELETE FROM songs WHERE id = %s;", (song_id,))
        conn.commit()
        
        if cur.rowcount > 0:
            console.print(f"[green]Song {song_id} deleted successfully![/green]")
        else:
            console.print("[red]Song not found![/red]")
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
        conn.rollback()
    finally:
        if conn:
            cur.close()
            conn.close()

# ========== PLAYLIST CRUD ==========
def manage_playlists():
    while True:
        table = Table(title="📋 Playlist Management")
        table.add_column("Option", style="cyan")
        table.add_column("Action", style="magenta")
        table.add_row("1", "Add Playlist")
        table.add_row("2", "View All Playlists")
        table.add_row("3", "Update Playlist")
        table.add_row("4", "Delete Playlist")
        table.add_row("5", "Back to Main Menu")
        console.print(table)
        
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4", "5"])
        
        if choice == "1":
            add_playlist()
        elif choice == "2":
            show_playlists()
        elif choice == "3":
            update_playlist()
        elif choice == "4":
            delete_playlist()
        elif choice == "5":
            break

def add_playlist():
    show_users()
    user_id = Prompt.ask("Enter user ID for the playlist")
    name = Prompt.ask("Enter playlist name")
    
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO playlists (name, user_id)
            VALUES (%s, %s);
        """, (name, user_id))
        conn.commit()
        console.print(f"[green]Playlist '{name}' added successfully![/green]")
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        if conn:
            cur.close()
            conn.close()

def show_playlists():
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            SELECT p.id, p.name, u.username 
            FROM playlists p
            JOIN users u ON p.user_id = u.id
            ORDER BY p.name;
        """)
        playlists = cur.fetchall()
        
        table = Table(title="📋 Playlists")
        table.add_column("ID", justify="right")
        table.add_column("Name")
        table.add_column("Owner")
        
        for playlist in playlists:
            table.add_row(str(playlist[0]), playlist[1], playlist[2])
        console.print(table)
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        if conn:
            cur.close()
            conn.close()

def update_playlist():
    show_playlists()
    playlist_id = Prompt.ask("Enter ID of playlist to update")
    
    try:
        conn = connect()
        cur = conn.cursor()
        
        # Get current playlist data
        cur.execute("""
            SELECT p.name, p.user_id, u.username 
            FROM playlists p
            JOIN users u ON p.user_id = u.id
            WHERE p.id = %s;
        """, (playlist_id,))
        playlist = cur.fetchone()
        
        if not playlist:
            console.print("[red]Playlist not found![/red]")
            return
            
        current_name, current_user_id, current_username = playlist
        
        name = Prompt.ask(f"Enter new name (current: {current_name})", default=current_name)
        
        # Show users and allow change
        show_users()
        user_id = Prompt.ask(
            f"Enter new user ID (current: {current_user_id} - {current_username})", 
            default=str(current_user_id))
        
        cur.execute("""
            UPDATE playlists 
            SET name = %s, user_id = %s
            WHERE id = %s;
        """, (name, user_id, playlist_id))
            
        conn.commit()
        console.print(f"[green]Playlist {playlist_id} updated successfully![/green]")
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        if conn:
            cur.close()
            conn.close()

def delete_playlist():
    show_playlists()
    playlist_id = Prompt.ask("Enter ID of playlist to delete")
    
    if not Confirm.ask(f"[red]Are you sure you want to delete playlist {playlist_id}?[/red]"):
        return
        
    try:
        conn = connect()
        cur = conn.cursor()
        
        # First delete dependent records
        cur.execute("DELETE FROM playlist_songs WHERE playlist_id = %s;", (playlist_id,))
        
        # Then delete the playlist
        cur.execute("DELETE FROM playlists WHERE id = %s;", (playlist_id,))
        conn.commit()
        
        if cur.rowcount > 0:
            console.print(f"[green]Playlist {playlist_id} deleted successfully![/green]")
        else:
            console.print("[red]Playlist not found![/red]")
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
        conn.rollback()
    finally:
        if conn:
            cur.close()
            conn.close()

# ========== PLAYLIST SONGS CRUD ==========
def manage_playlist_songs():
    while True:
        table = Table(title="🎶 Playlist Songs Management")
        table.add_column("Option", style="cyan")
        table.add_column("Action", style="magenta")
        table.add_row("1", "Add Song to Playlist")
        table.add_row("2", "View Songs in Playlist")
        table.add_row("3", "Remove Song from Playlist")
        table.add_row("4", "Back to Main Menu")
        console.print(table)
        
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4"])
        
        if choice == "1":
            add_song_to_playlist()
        elif choice == "2":
            show_playlist_songs()
        elif choice == "3":
            remove_song_from_playlist()
        elif choice == "4":
            break

def add_song_to_playlist():
    show_playlists()
    playlist_id = Prompt.ask("Enter playlist ID")
    show_songs()
    song_id = Prompt.ask("Enter song ID to add")
    
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO playlist_songs (playlist_id, song_id)
            VALUES (%s, %s)
            ON CONFLICT (playlist_id, song_id) DO NOTHING;
        """, (playlist_id, song_id))
        conn.commit()
        
        if cur.rowcount > 0:
            console.print(f"[green]Song {song_id} added to playlist {playlist_id} successfully![/green]")
        else:
            console.print("[yellow]Song already exists in this playlist![/yellow]")
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        if conn:
            cur.close()
            conn.close()

def show_playlist_songs():
    show_playlists()
    playlist_id = Prompt.ask("Enter playlist ID to view songs")
    
    try:
        conn = connect()
        cur = conn.cursor()
        
        # Get playlist info
        cur.execute("""
            SELECT p.name, u.username 
            FROM playlists p
            JOIN users u ON p.user_id = u.id
            WHERE p.id = %s;
        """, (playlist_id,))
        playlist_info = cur.fetchone()
        
        if not playlist_info:
            console.print("[red]Playlist not found![/red]")
            return
            
        playlist_name, username = playlist_info
        
        # Get songs in playlist
        cur.execute("""
            SELECT s.id, s.title, al.title, ar.name, ps.added_at 
            FROM playlist_songs ps
            JOIN songs s ON ps.song_id = s.id
            JOIN albums al ON s.album_id = al.id
            JOIN artists ar ON al.artist_id = ar.id
            WHERE ps.playlist_id = %s
            ORDER BY ps.added_at;
        """, (playlist_id,))
        songs = cur.fetchall()
        
        table = Table(title=f"🎶 Songs in Playlist: {playlist_name} (Owner: {username})")
        table.add_column("ID", justify="right")
        table.add_column("Title")
        table.add_column("Album")
        table.add_column("Artist")
        table.add_column("Added At")
        
        for song in songs:
            table.add_row(str(song[0]), song[1], song[2], song[3], str(song[4]))
        console.print(table)
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        if conn:
            cur.close()
            conn.close()

def remove_song_from_playlist():
    show_playlists()
    playlist_id = Prompt.ask("Enter playlist ID")
    show_playlist_songs()
    song_id = Prompt.ask("Enter song ID to remove")
    
    if not Confirm.ask(f"[red]Are you sure you want to remove song {song_id} from playlist {playlist_id}?[/red]"):
        return
        
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM playlist_songs 
            WHERE playlist_id = %s AND song_id = %s;
        """, (playlist_id, song_id))
        conn.commit()
        
        if cur.rowcount > 0:
            console.print(f"[green]Song {song_id} removed from playlist {playlist_id} successfully![/green]")
        else:
            console.print("[red]Song not found in this playlist![/red]")
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        if conn:
            cur.close()
            conn.close()

# ========== PLAY HISTORY ==========
def view_play_history():
    show_users()
    user_id = Prompt.ask("Enter user ID to view play history", default="")
    
    try:
        conn = connect()
        cur = conn.cursor()
        
        if user_id:
            # Get play history for specific user
            cur.execute("""
                SELECT ph.id, s.title, u.username, ph.played_at 
                FROM play_history ph
                JOIN songs s ON ph.song_id = s.id
                JOIN users u ON ph.user_id = u.id
                WHERE ph.user_id = %s
                ORDER BY ph.played_at DESC;
            """, (user_id,))
            title = f"Play History for User {user_id}"
        else:
            # Get all play history
            cur.execute("""
                SELECT ph.id, s.title, u.username, ph.played_at 
                FROM play_history ph
                JOIN songs s ON ph.song_id = s.id
                JOIN users u ON ph.user_id = u.id
                ORDER BY ph.played_at DESC;
            """)
            title = "All Play History"
        
        history = cur.fetchall()
        
        table = Table(title=f"⏳ {title}")
        table.add_column("ID", justify="right")
        table.add_column("Song")
        table.add_column("User")
        table.add_column("Played At")
        
        for item in history:
            table.add_row(str(item[0]), item[1], item[2], str(item[3]))
        console.print(table)
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        if conn:
            cur.close()
            conn.close()

# ========== SONG RATINGS ==========
def manage_song_ratings():
    while True:
        table = Table(title="⭐ Song Ratings Management")
        table.add_column("Option", style="cyan")
        table.add_column("Action", style="magenta")
        table.add_row("1", "Add/Update Rating")
        table.add_row("2", "View Ratings")
        table.add_row("3", "Delete Rating")
        table.add_row("4", "Back to Main Menu")
        console.print(table)
        
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4"])
        
        if choice == "1":
            add_update_rating()
        elif choice == "2":
            show_ratings()
        elif choice == "3":
            delete_rating()
        elif choice == "4":
            break

def add_update_rating():
    show_users()
    user_id = Prompt.ask("Enter user ID")
    show_songs()
    song_id = Prompt.ask("Enter song ID")
    rating = Prompt.ask("Enter rating (1-5)", choices=["1", "2", "3", "4", "5"])
    
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO song_ratings (user_id, song_id, rating)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, song_id) 
            DO UPDATE SET rating = EXCLUDED.rating;
        """, (user_id, song_id, rating))
        conn.commit()
        console.print(f"[green]Rating {rating} added/updated for song {song_id} by user {user_id}![/green]")
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        if conn:
            cur.close()
            conn.close()

def show_ratings():
    show_users()
    user_id = Prompt.ask("Enter user ID to filter (leave blank for all)", default="")
    show_songs()
    song_id = Prompt.ask("Enter song ID to filter (leave blank for all)", default="")
    
    try:
        conn = connect()
        cur = conn.cursor()
        
        if user_id and song_id:
            # Get specific rating
            cur.execute("""
                SELECT u.username, s.title, sr.rating 
                FROM song_ratings sr
                JOIN users u ON sr.user_id = u.id
                JOIN songs s ON sr.song_id = s.id
                WHERE sr.user_id = %s AND sr.song_id = %s;
            """, (user_id, song_id))
            title = f"Rating for Song {song_id} by User {user_id}"
        elif user_id:
            # Get all ratings by user
            cur.execute("""
                SELECT u.username, s.title, sr.rating 
                FROM song_ratings sr
                JOIN users u ON sr.user_id = u.id
                JOIN songs s ON sr.song_id = s.id
                WHERE sr.user_id = %s
                ORDER BY s.title;
            """, (user_id,))
            title = f"All Ratings by User {user_id}"
        elif song_id:
            # Get all ratings for song
            cur.execute("""
                SELECT u.username, s.title, sr.rating 
                FROM song_ratings sr
                JOIN users u ON sr.user_id = u.id
                JOIN songs s ON sr.song_id = s.id
                WHERE sr.song_id = %s
                ORDER BY sr.rating DESC;
            """, (song_id,))
            title = f"All Ratings for Song {song_id}"
        else:
            # Get all ratings
            cur.execute("""
                SELECT u.username, s.title, sr.rating 
                FROM song_ratings sr
                JOIN users u ON sr.user_id = u.id
                JOIN songs s ON sr.song_id = s.id
                ORDER BY s.title, sr.rating DESC;
            """)
            title = "All Song Ratings"
        
        ratings = cur.fetchall()
        
        table = Table(title=f"⭐ {title}")
        table.add_column("User")
        table.add_column("Song")
        table.add_column("Rating")
        
        for item in ratings:
            # Add star emojis based on rating
            stars = "★" * int(item[2]) + "☆" * (5 - int(item[2]))
            table.add_row(item[0], item[1], stars)
        console.print(table)
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        if conn:
            cur.close()
            conn.close()

def delete_rating():
    show_users()
    user_id = Prompt.ask("Enter user ID")
    show_songs()
    song_id = Prompt.ask("Enter song ID")
    
    if not Confirm.ask(f"[red]Are you sure you want to delete rating for song {song_id} by user {user_id}?[/red]"):
        return
        
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM song_ratings 
            WHERE user_id = %s AND song_id = %s;
        """, (user_id, song_id))
        conn.commit()
        
        if cur.rowcount > 0:
            console.print(f"[green]Rating for song {song_id} by user {user_id} deleted successfully![/green]")
        else:
            console.print("[red]Rating not found![/red]")
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        if conn:
            cur.close()
            conn.close()

# ========== SONG LIKES ==========
def manage_song_likes():
    while True:
        table = Table(title="👍 Song Likes Management")
        table.add_column("Option", style="cyan")
        table.add_column("Action", style="magenta")
        table.add_row("1", "Add Like")
        table.add_row("2", "Show Likes")
        table.add_row("3", "Delete Like")
        table.add_row("4", "Back to Main Menu")
        console.print(table)

        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4"])
        if choice == "1":
            add_song_like()
        elif choice == "2":
            show_song_likes()
        elif choice == "3":
            delete_song_like()
        elif choice == "4":
            break

def add_song_like():
    show_users()
    user_id = Prompt.ask("Enter user ID")
    show_songs()
    song_id = Prompt.ask("Enter song ID")
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO song_likes (user_id, song_id)
            VALUES (%s, %s)
            ON CONFLICT (user_id, song_id) DO NOTHING;
        """, (user_id, song_id))
        conn.commit()
        if cur.rowcount > 0:
            console.print(f"[green]Like added successfully![/green]")
        else:
            console.print("[yellow]User already liked this song![/yellow]")
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        if conn:
            cur.close()
            conn.close()

def show_song_likes():
    show_songs()
    song_id = Prompt.ask("Enter song ID to show likes (leave blank for all)", default="")
    try:
        conn = connect()
        cur = conn.cursor()
        if song_id:
            cur.execute("""
                SELECT u.username, s.title, sl.liked_at
                FROM song_likes sl
                JOIN users u ON sl.user_id = u.id
                JOIN songs s ON sl.song_id = s.id
                WHERE sl.song_id = %s
                ORDER BY sl.liked_at DESC
            """, (song_id,))
            title = f"Likes for Song {song_id}"
        else:
            cur.execute("""
                SELECT u.username, s.title, sl.liked_at
                FROM song_likes sl
                JOIN users u ON sl.user_id = u.id
                JOIN songs s ON sl.song_id = s.id
                ORDER BY sl.liked_at DESC
            """)
            title = "All Song Likes"
        likes = cur.fetchall()
        table = Table(title=title)
        table.add_column("User")
        table.add_column("Song")
        table.add_column("Liked At")
        for l in likes:
            table.add_row(l[0], l[1], str(l[2]))
        console.print(table)
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        if conn:
            cur.close()
            conn.close()

def delete_song_like():
    show_users()
    user_id = Prompt.ask("Enter user ID")
    show_songs()
    song_id = Prompt.ask("Enter song ID")
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM song_likes WHERE user_id=%s AND song_id=%s
        """, (user_id, song_id))
        conn.commit()
        if cur.rowcount > 0:
            console.print(f"[green]Like deleted successfully![/green]")
        else:
            console.print("[red]Like not found![/red]")
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        if conn:
            cur.close()
            conn.close()

# ========== ARTIST FOLLOWS ==========
def manage_artist_follows():
    while True:
        table = Table(title="👤 Artist Follows Management")
        table.add_column("Option", style="cyan")
        table.add_column("Action", style="magenta")
        table.add_row("1", "Follow Artist")
        table.add_row("2", "Show Follows")
        table.add_row("3", "Unfollow Artist")
        table.add_row("4", "Back to Main Menu")
        console.print(table)

        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4"])
        if choice == "1":
            add_artist_follow()
        elif choice == "2":
            show_artist_follows()
        elif choice == "3":
            delete_artist_follow()
        elif choice == "4":
            break

def add_artist_follow():
    show_users()
    user_id = Prompt.ask("Enter user ID")
    show_artists()
    artist_id = Prompt.ask("Enter artist ID")
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO artist_follows (user_id, artist_id)
            VALUES (%s, %s)
            ON CONFLICT (user_id, artist_id) DO NOTHING;
        """, (user_id, artist_id))
        conn.commit()
        if cur.rowcount > 0:
            console.print("[green]Artist followed successfully![/green]")
        else:
            console.print("[yellow]User already follows this artist![/yellow]")
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        if conn:
            cur.close()
            conn.close()

def show_artist_follows():
    show_users()
    user_id = Prompt.ask("Enter user ID to show follows (leave blank for all)", default="")
    try:
        conn = connect()
        cur = conn.cursor()
        if user_id:
            cur.execute("""
                SELECT u.username, a.name, af.followed_at
                FROM artist_follows af
                JOIN users u ON af.user_id = u.id
                JOIN artists a ON af.artist_id = a.id
                WHERE af.user_id = %s
                ORDER BY af.followed_at DESC
            """, (user_id,))
            title = f"Follows for User {user_id}"
        else:
            cur.execute("""
                SELECT u.username, a.name, af.followed_at
                FROM artist_follows af
                JOIN users u ON af.user_id = u.id
                JOIN artists a ON af.artist_id = a.id
                ORDER BY af.followed_at DESC
            """)
            title = "All Artist Follows"
        follows = cur.fetchall()
        table = Table(title=title)
        table.add_column("User")
        table.add_column("Artist")
        table.add_column("Followed At")
        for f in follows:
            table.add_row(f[0], f[1], str(f[2]))
        console.print(table)
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        if conn:
            cur.close()
            conn.close()

def delete_artist_follow():
    show_users()
    user_id = Prompt.ask("Enter user ID")
    show_artists()
    artist_id = Prompt.ask("Enter artist ID")
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM artist_follows WHERE user_id=%s AND artist_id=%s
        """, (user_id, artist_id))
        conn.commit()
        if cur.rowcount > 0:
            console.print("[green]Unfollowed successfully![/green]")
        else:
            console.print("[red]Follow not found![/red]")
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        if conn:
            cur.close()
            conn.close()

# ========== SONG COMMENTS ==========
def manage_song_comments():
    while True:
        table = Table(title="💬 Song Comments Management")
        table.add_column("Option", style="cyan")
        table.add_column("Action", style="magenta")
        table.add_row("1", "Add Comment")
        table.add_row("2", "Show Comments")
        table.add_row("3", "Delete Comment")
        table.add_row("4", "Back to Main Menu")
        console.print(table)

        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4"])
        if choice == "1":
            add_song_comment()
        elif choice == "2":
            show_song_comments()
        elif choice == "3":
            delete_song_comment()
        elif choice == "4":
            break

def add_song_comment():
    show_users()
    user_id = Prompt.ask("Enter user ID")
    show_songs()
    song_id = Prompt.ask("Enter song ID")
    comment = Prompt.ask("Enter comment text")
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO song_comments (user_id, song_id, comment)
            VALUES (%s, %s, %s);
        """, (user_id, song_id, comment))
        conn.commit()
        console.print("[green]Comment added successfully![/green]")
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        if conn:
            cur.close()
            conn.close()

def show_song_comments():
    show_songs()
    song_id = Prompt.ask("Enter song ID to show comments (leave blank for all)", default="")
    try:
        conn = connect()
        cur = conn.cursor()
        if song_id:
            cur.execute("""
                SELECT sc.id, u.username, s.title, sc.comment, sc.commented_at
                FROM song_comments sc
                JOIN users u ON sc.user_id = u.id
                JOIN songs s ON sc.song_id = s.id
                WHERE sc.song_id = %s
                ORDER BY sc.commented_at DESC
            """, (song_id,))
            title = f"Comments for Song {song_id}"
        else:
            cur.execute("""
                SELECT sc.id, u.username, s.title, sc.comment, sc.commented_at
                FROM song_comments sc
                JOIN users u ON sc.user_id = u.id
                JOIN songs s ON sc.song_id = s.id
                ORDER BY sc.commented_at DESC
            """)
            title = "All Song Comments"
        comments = cur.fetchall()
        table = Table(title=title)
        table.add_column("ID")
        table.add_column("User")
        table.add_column("Song")
        table.add_column("Comment")
        table.add_column("Commented At")
        for c in comments:
            table.add_row(str(c[0]), c[1], c[2], c[3], str(c[4]))
        console.print(table)
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        if conn:
            cur.close()
            conn.close()

def delete_song_comment():
    show_song_comments()
    comment_id = Prompt.ask("Enter comment ID to delete")
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM song_comments WHERE id=%s
        """, (comment_id,))
        conn.commit()
        if cur.rowcount > 0:
            console.print("[green]Comment deleted successfully![/green]")
        else:
            console.print("[red]Comment not found![/red]")
    except psycopg2.Error as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        if conn:
            cur.close()
            conn.close()


# ========== MAIN FUNCTION ==========
def main():
    while True:
        menu()
        choice = Prompt.ask("Choose an option", choices=[str(i) for i in range(13)])
        if choice == "1":
            manage_users()
        elif choice == "2":
            manage_artists()
        elif choice == "3":
            manage_albums()
        elif choice == "4":
            manage_songs()
        elif choice == "5":
            manage_playlists()
        elif choice == "6":
            manage_playlist_songs()
        elif choice == "7":
            view_play_history()
        elif choice == "8":
            manage_song_ratings()
        elif choice == "9":
            create_tables()
        elif choice == "10":
            manage_song_likes()
        elif choice == "11":
            manage_artist_follows()
        elif choice == "12":
            manage_song_comments()
        elif choice == "0":
            console.print("[yellow]Goodbye![/yellow]")
            break


if __name__ == '__main__':
    main()