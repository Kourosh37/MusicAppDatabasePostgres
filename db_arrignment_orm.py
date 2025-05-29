from sqlalchemy import create_engine, Column, Integer, String, Text, Date, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

console = Console()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:123@localhost:5432/music_app")

# SQLAlchemy setup
Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# ========== MODELS ==========
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    playlists = relationship("Playlist", back_populates="user")
    play_history = relationship("PlayHistory", back_populates="user")
    ratings = relationship("SongRating", back_populates="user")

class Artist(Base):
    __tablename__ = 'artists'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    bio = Column(Text)
    
    albums = relationship("Album", back_populates="artist")

class Album(Base):
    __tablename__ = 'albums'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    artist_id = Column(Integer, ForeignKey('artists.id'))
    release_date = Column(Date)
    
    artist = relationship("Artist", back_populates="albums")
    songs = relationship("Song", back_populates="album")

class Song(Base):
    __tablename__ = 'songs'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    album_id = Column(Integer, ForeignKey('albums.id'))
    duration = Column(Integer)
    file_path = Column(String, nullable=False)
    
    album = relationship("Album", back_populates="songs")
    playlist_associations = relationship("PlaylistSong", back_populates="song")
    play_history = relationship("PlayHistory", back_populates="song")
    ratings = relationship("SongRating", back_populates="song")

class Playlist(Base):
    __tablename__ = 'playlists'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    
    user = relationship("User", back_populates="playlists")
    song_associations = relationship("PlaylistSong", back_populates="playlist")

class PlaylistSong(Base):
    __tablename__ = 'playlist_songs'
    
    playlist_id = Column(Integer, ForeignKey('playlists.id'), primary_key=True)
    song_id = Column(Integer, ForeignKey('songs.id'), primary_key=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    
    playlist = relationship("Playlist", back_populates="song_associations")
    song = relationship("Song", back_populates="playlist_associations")

class PlayHistory(Base):
    __tablename__ = 'play_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    song_id = Column(Integer, ForeignKey('songs.id'))
    played_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="play_history")
    song = relationship("Song", back_populates="play_history")

class SongRating(Base):
    __tablename__ = 'song_ratings'
    
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    song_id = Column(Integer, ForeignKey('songs.id'), primary_key=True)
    rating = Column(Integer, nullable=False)
    
    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
    )
    
    user = relationship("User", back_populates="ratings")
    song = relationship("Song", back_populates="ratings")

# ========== HELPER FUNCTIONS ==========
def create_tables():
    Base.metadata.create_all(engine)
    console.print("[green]All tables created successfully![/green]")

def get_session():
    return Session()

def validate_input(text, max_length=100, allow_empty=False):
    """Validate user input to prevent SQL injection and other issues"""
    if not allow_empty and not text.strip():
        raise ValueError("Input cannot be empty")
    if len(text) > max_length:
        raise ValueError(f"Input too long (max {max_length} characters)")
    # Prevent common SQL injection patterns
    if any(char in text for char in [";", "--", "/*", "*/", "'", '"', "\\"]):
        raise ValueError("Invalid characters in input")
    return text.strip()

# ========== MENU SYSTEM ==========
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
    try:
        username = validate_input(Prompt.ask("Enter username"))
        email = validate_input(Prompt.ask("Enter email"))
        password = validate_input(Prompt.ask("Enter password", password=True))
        
        session = get_session()
        try:
            # Check if username or email already exists
            if session.query(User).filter((User.username == username) | (User.email == email)).first():
                console.print("[red]Username or email already exists![/red]")
                return
            
            new_user = User(username=username, email=email, password=password)
            session.add(new_user)
            session.commit()
            console.print(f"[green]User '{username}' added successfully with ID {new_user.id}![/green]")
        except Exception as e:
            session.rollback()
            console.print(f"[red]Database error: {e}[/red]")
        finally:
            session.close()
    except ValueError as e:
        console.print(f"[red]Validation error: {e}[/red]")

def show_users():
    session = get_session()
    try:
        users = session.query(User).order_by(User.id).all()
        
        table = Table(title="👥 Users")
        table.add_column("ID", justify="right")
        table.add_column("Username")
        table.add_column("Email")
        table.add_column("Created At")
        
        for user in users:
            table.add_row(str(user.id), user.username, user.email, str(user.created_at))
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        session.close()

def update_user():
    show_users()
    try:
        user_id = int(validate_input(Prompt.ask("Enter ID of user to update"), max_length=10))
        
        session = get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                console.print("[red]User not found![/red]")
                return
            
            username = validate_input(
                Prompt.ask(f"Enter new username (current: {user.username})"), 
                default=user.username
            )
            email = validate_input(
                Prompt.ask(f"Enter new email (current: {user.email})"), 
                default=user.email
            )
            
            # Check if new email is already used by another user
            if session.query(User).filter(User.email == email, User.id != user.id).first():
                console.print("[red]Email already in use by another user![/red]")
                return
            
            password = Prompt.ask(
                "Enter new password (leave blank to keep current)", 
                password=True, 
                default=""
            )
            
            user.username = username
            user.email = email
            if password:
                user.password = validate_input(password)
            
            session.commit()
            console.print(f"[green]User {user.id} updated successfully![/green]")
        except Exception as e:
            session.rollback()
            console.print(f"[red]Database error: {e}[/red]")
        finally:
            session.close()
    except ValueError as e:
        console.print(f"[red]Validation error: {e}[/red]")

def delete_user():
    show_users()
    try:
        user_id = int(validate_input(Prompt.ask("Enter ID of user to update"), max_length=10))
        
        if not Confirm.ask(f"[red]Are you sure you want to delete user {user_id}?[/red]"):
            return
            
        session = get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                console.print("[red]User not found![/red]")
                return
            
            # Delete dependent records first
            session.query(Playlist).filter_by(user_id=user.id).delete()
            session.query(PlayHistory).filter_by(user_id=user.id).delete()
            session.query(SongRating).filter_by(user_id=user.id).delete()
            
            # Then delete the user
            session.delete(user)
            session.commit()
            console.print(f"[green]User {user_id} deleted successfully![/green]")
        except Exception as e:
            session.rollback()
            console.print(f"[red]Database error: {e}[/red]")
        finally:
            session.close()
    except ValueError as e:
        console.print(f"[red]Validation error: {e}[/red]")

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
    try:
        name = validate_input(Prompt.ask("Enter artist name"))
        bio = validate_input(Prompt.ask("Enter artist bio (optional)", default=""), allow_empty=True)
        
        session = get_session()
        try:
            new_artist = Artist(name=name, bio=bio if bio else None)
            session.add(new_artist)
            session.commit()
            console.print(f"[green]Artist '{name}' added successfully with ID {new_artist.id}![/green]")
        except Exception as e:
            session.rollback()
            console.print(f"[red]Database error: {e}[/red]")
        finally:
            session.close()
    except ValueError as e:
        console.print(f"[red]Validation error: {e}[/red]")

def show_artists():
    session = get_session()
    try:
        artists = session.query(Artist).order_by(Artist.name).all()
        
        table = Table(title="🎤 Artists")
        table.add_column("ID", justify="right")
        table.add_column("Name")
        table.add_column("Bio")
        
        for artist in artists:
            bio = artist.bio if artist.bio else "N/A"
            table.add_row(str(artist.id), artist.name, bio)
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        session.close()

def update_artist():
    show_artists()
    try:
        artist_id = int(validate_input(Prompt.ask("Enter ID of artist to update"), max_length=10))
        
        session = get_session()
        try:
            artist = session.query(Artist).filter_by(id=artist_id).first()
            if not artist:
                console.print("[red]Artist not found![/red]")
                return
            
            name = validate_input(
                Prompt.ask(f"Enter new name (current: {artist.name})"), 
                default=artist.name
            )
            bio = validate_input(
                Prompt.ask(f"Enter new bio (current: {artist.bio if artist.bio else 'N/A'})"), 
                default=artist.bio if artist.bio else "",
                allow_empty=True
            )
            
            artist.name = name
            artist.bio = bio if bio else None
            
            session.commit()
            console.print(f"[green]Artist {artist.id} updated successfully![/green]")
        except Exception as e:
            session.rollback()
            console.print(f"[red]Database error: {e}[/red]")
        finally:
            session.close()
    except ValueError as e:
        console.print(f"[red]Validation error: {e}[/red]")

def delete_artist():
    show_artists()
    try:
        artist_id = int(validate_input(Prompt.ask("Enter ID of artist to delete"), max_length=10))
        
        if not Confirm.ask(f"[red]Are you sure you want to delete artist {artist_id}?[/red]"):
            return
            
        session = get_session()
        try:
            artist = session.query(Artist).filter_by(id=artist_id).first()
            if not artist:
                console.print("[red]Artist not found![/red]")
                return
            
            # Check if artist has albums
            if session.query(Album).filter_by(artist_id=artist.id).count() > 0:
                console.print("[red]Cannot delete artist with existing albums![/red]")
                return
            
            session.delete(artist)
            session.commit()
            console.print(f"[green]Artist {artist_id} deleted successfully![/green]")
        except Exception as e:
            session.rollback()
            console.print(f"[red]Database error: {e}[/red]")
        finally:
            session.close()
    except ValueError as e:
        console.print(f"[red]Validation error: {e}[/red]")

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
    try:
        artist_id = int(validate_input(Prompt.ask("Enter artist ID for the album"), max_length=10))
        title = validate_input(Prompt.ask("Enter album title"))
        release_date_str = validate_input(
            Prompt.ask("Enter release date (YYYY-MM-DD)", default=""), 
            allow_empty=True
        )
        
        release_date = None
        if release_date_str:
            try:
                release_date = datetime.strptime(release_date_str, "%Y-%m-%d").date()
            except ValueError:
                console.print("[red]Invalid date format! Please use YYYY-MM-DD[/red]")
                return
        
        session = get_session()
        try:
            # Check if artist exists
            artist = session.query(Artist).filter_by(id=artist_id).first()
            if not artist:
                console.print("[red]Artist not found![/red]")
                return
            
            new_album = Album(
                title=title,
                artist_id=artist_id,
                release_date=release_date
            )
            session.add(new_album)
            session.commit()
            console.print(f"[green]Album '{title}' added successfully with ID {new_album.id}![/green]")
        except Exception as e:
            session.rollback()
            console.print(f"[red]Database error: {e}[/red]")
        finally:
            session.close()
    except ValueError as e:
        console.print(f"[red]Validation error: {e}[/red]")

def show_albums():
    session = get_session()
    try:
        albums = session.query(Album).join(Artist).order_by(Album.title).all()
        
        table = Table(title="💿 Albums")
        table.add_column("ID", justify="right")
        table.add_column("Title")
        table.add_column("Artist")
        table.add_column("Release Date")
        
        for album in albums:
            release_date = str(album.release_date) if album.release_date else "N/A"
            table.add_row(str(album.id), album.title, album.artist.name, release_date)
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        session.close()

def update_album():
    show_albums()
    try:
        album_id = int(validate_input(Prompt.ask("Enter ID of album to update"), max_length=10))
        
        session = get_session()
        try:
            album = session.query(Album).filter_by(id=album_id).first()
            if not album:
                console.print("[red]Album not found![/red]")
                return
            
            title = validate_input(
                Prompt.ask(f"Enter new title (current: {album.title})"), 
                default=album.title
            )
            
            # Show artists and allow change
            show_artists()
            artist_id = int(
                validate_input(
                    Prompt.ask(
                        f"Enter new artist ID (current: {album.artist_id} - {album.artist.name})", 
                        default=str(album.artist_id)
                    ), 
                    max_length=10
                )
            )
            
            # Check if new artist exists
            artist = session.query(Artist).filter_by(id=artist_id).first()
            if not artist:
                console.print("[red]Artist not found![/red]")
                return
            
            release_date_str = validate_input(
                Prompt.ask(
                    f"Enter new release date (current: {album.release_date if album.release_date else 'N/A'})", 
                    default=str(album.release_date) if album.release_date else ""
                ),
                allow_empty=True
            )
            
            release_date = None
            if release_date_str:
                try:
                    release_date = datetime.strptime(release_date_str, "%Y-%m-%d").date()
                except ValueError:
                    console.print("[red]Invalid date format! Please use YYYY-MM-DD[/red]")
                    return
            
            album.title = title
            album.artist_id = artist_id
            album.release_date = release_date
            
            session.commit()
            console.print(f"[green]Album {album.id} updated successfully![/green]")
        except Exception as e:
            session.rollback()
            console.print(f"[red]Database error: {e}[/red]")
        finally:
            session.close()
    except ValueError as e:
        console.print(f"[red]Validation error: {e}[/red]")

def delete_album():
    show_albums()
    try:
        album_id = int(validate_input(Prompt.ask("Enter ID of album to delete"), max_length=10))
        
        if not Confirm.ask(f"[red]Are you sure you want to delete album {album_id}?[/red]"):
            return
            
        session = get_session()
        try:
            album = session.query(Album).filter_by(id=album_id).first()
            if not album:
                console.print("[red]Album not found![/red]")
                return
            
            # Check if album has songs
            if session.query(Song).filter_by(album_id=album.id).count() > 0:
                console.print("[red]Cannot delete album with existing songs![/red]")
                return
            
            session.delete(album)
            session.commit()
            console.print(f"[green]Album {album_id} deleted successfully![/green]")
        except Exception as e:
            session.rollback()
            console.print(f"[red]Database error: {e}[/red]")
        finally:
            session.close()
    except ValueError as e:
        console.print(f"[red]Validation error: {e}[/red]")

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
    try:
        album_id = int(validate_input(Prompt.ask("Enter album ID for the song"), max_length=10))
        title = validate_input(Prompt.ask("Enter song title"))
        duration = int(validate_input(
            Prompt.ask("Enter song duration in seconds", default="0"), 
            max_length=10
        ))
        file_path = validate_input(Prompt.ask("Enter file path for the song"))
        
        session = get_session()
        try:
            # Check if album exists
            album = session.query(Album).filter_by(id=album_id).first()
            if not album:
                console.print("[red]Album not found![/red]")
                return
            
            new_song = Song(
                title=title,
                album_id=album_id,
                duration=duration,
                file_path=file_path
            )
            session.add(new_song)
            session.commit()
            console.print(f"[green]Song '{title}' added successfully with ID {new_song.id}![/green]")
        except Exception as e:
            session.rollback()
            console.print(f"[red]Database error: {e}[/red]")
        finally:
            session.close()
    except ValueError as e:
        console.print(f"[red]Validation error: {e}[/red]")

def show_songs():
    session = get_session()
    try:
        songs = session.query(Song).join(Album).join(Artist).order_by(Song.title).all()
        
        table = Table(title="🎵 Songs")
        table.add_column("ID", justify="right")
        table.add_column("Title")
        table.add_column("Album")
        table.add_column("Artist")
        table.add_column("Duration (sec)")
        table.add_column("File Path")
        
        for song in songs:
            duration = str(song.duration) if song.duration else "N/A"
            table.add_row(
                str(song.id), 
                song.title, 
                song.album.title, 
                song.album.artist.name, 
                duration, 
                song.file_path
            )
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        session.close()

def update_song():
    show_songs()
    try:
        song_id = int(validate_input(Prompt.ask("Enter ID of song to update"), max_length=10))
        
        session = get_session()
        try:
            song = session.query(Song).filter_by(id=song_id).first()
            if not song:
                console.print("[red]Song not found![/red]")
                return
            
            title = validate_input(
                Prompt.ask(f"Enter new title (current: {song.title})"), 
                default=song.title
            )
            
            # Show albums and allow change
            show_albums()
            album_id = int(validate_input(
                Prompt.ask(
                    f"Enter new album ID (current: {song.album_id} - {song.album.title})", 
                    default=str(song.album_id)
                ),
                max_length=10
            ))
            
            # Check if new album exists
            album = session.query(Album).filter_by(id=album_id).first()
            if not album:
                console.print("[red]Album not found![/red]")
                return
            
            duration = int(validate_input(
                Prompt.ask(
                    f"Enter new duration in seconds (current: {song.duration if song.duration else 'N/A'})", 
                    default=str(song.duration) if song.duration else "0"
                ),
                max_length=10
            ))
            
            file_path = validate_input(
                Prompt.ask(f"Enter new file path (current: {song.file_path})"), 
                default=song.file_path
            )
            
            song.title = title
            song.album_id = album_id
            song.duration = duration
            song.file_path = file_path
            
            session.commit()
            console.print(f"[green]Song {song.id} updated successfully![/green]")
        except Exception as e:
            session.rollback()
            console.print(f"[red]Database error: {e}[/red]")
        finally:
            session.close()
    except ValueError as e:
        console.print(f"[red]Validation error: {e}[/red]")

def delete_song():
    show_songs()
    try:
        song_id = int(validate_input(Prompt.ask("Enter ID of song to delete"), max_length=10))
        
        if not Confirm.ask(f"[red]Are you sure you want to delete song {song_id}?[/red]"):
            return
            
        session = get_session()
        try:
            song = session.query(Song).filter_by(id=song_id).first()
            if not song:
                console.print("[red]Song not found![/red]")
                return
            
            # Delete dependent records first
            session.query(PlaylistSong).filter_by(song_id=song.id).delete()
            session.query(PlayHistory).filter_by(song_id=song.id).delete()
            session.query(SongRating).filter_by(song_id=song.id).delete()
            
            # Then delete the song
            session.delete(song)
            session.commit()
            console.print(f"[green]Song {song_id} deleted successfully![/green]")
        except Exception as e:
            session.rollback()
            console.print(f"[red]Database error: {e}[/red]")
        finally:
            session.close()
    except ValueError as e:
        console.print(f"[red]Validation error: {e}[/red]")

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
    try:
        user_id = int(validate_input(Prompt.ask("Enter user ID for the playlist"), max_length=10))
        name = validate_input(Prompt.ask("Enter playlist name"))
        
        session = get_session()
        try:
            # Check if user exists
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                console.print("[red]User not found![/red]")
                return
            
            new_playlist = Playlist(name=name, user_id=user_id)
            session.add(new_playlist)
            session.commit()
            console.print(f"[green]Playlist '{name}' added successfully with ID {new_playlist.id}![/green]")
        except Exception as e:
            session.rollback()
            console.print(f"[red]Database error: {e}[/red]")
        finally:
            session.close()
    except ValueError as e:
        console.print(f"[red]Validation error: {e}[/red]")

def show_playlists():
    session = get_session()
    try:
        playlists = session.query(Playlist).join(User).order_by(Playlist.name).all()
        
        table = Table(title="📋 Playlists")
        table.add_column("ID", justify="right")
        table.add_column("Name")
        table.add_column("Owner")
        
        for playlist in playlists:
            table.add_row(str(playlist.id), playlist.name, playlist.user.username)
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        session.close()

def update_playlist():
    show_playlists()
    try:
        playlist_id = int(validate_input(Prompt.ask("Enter ID of playlist to update"), max_length=10))
        
        session = get_session()
        try:
            playlist = session.query(Playlist).filter_by(id=playlist_id).first()
            if not playlist:
                console.print("[red]Playlist not found![/red]")
                return
            
            name = validate_input(
                Prompt.ask(f"Enter new name (current: {playlist.name})"), 
                default=playlist.name
            )
            
            # Show users and allow change
            show_users()
            user_id = int(validate_input(
                Prompt.ask(
                    f"Enter new user ID (current: {playlist.user_id} - {playlist.user.username})", 
                    default=str(playlist.user_id)
                ),
                max_length=10
            ))
            
            # Check if new user exists
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                console.print("[red]User not found![/red]")
                return
            
            playlist.name = name
            playlist.user_id = user_id
            
            session.commit()
            console.print(f"[green]Playlist {playlist.id} updated successfully![/green]")
        except Exception as e:
            session.rollback()
            console.print(f"[red]Database error: {e}[/red]")
        finally:
            session.close()
    except ValueError as e:
        console.print(f"[red]Validation error: {e}[/red]")

def delete_playlist():
    show_playlists()
    try:
        playlist_id = int(validate_input(Prompt.ask("Enter ID of playlist to delete"), max_length=10))
        
        if not Confirm.ask(f"[red]Are you sure you want to delete playlist {playlist_id}?[/red]"):
            return
            
        session = get_session()
        try:
            playlist = session.query(Playlist).filter_by(id=playlist_id).first()
            if not playlist:
                console.print("[red]Playlist not found![/red]")
                return
            
            # Delete dependent records first
            session.query(PlaylistSong).filter_by(playlist_id=playlist.id).delete()
            
            # Then delete the playlist
            session.delete(playlist)
            session.commit()
            console.print(f"[green]Playlist {playlist_id} deleted successfully![/green]")
        except Exception as e:
            session.rollback()
            console.print(f"[red]Database error: {e}[/red]")
        finally:
            session.close()
    except ValueError as e:
        console.print(f"[red]Validation error: {e}[/red]")

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
    try:
        playlist_id = int(validate_input(Prompt.ask("Enter playlist ID"), max_length=10))
        show_songs()
        song_id = int(validate_input(Prompt.ask("Enter song ID to add"), max_length=10))
        
        session = get_session()
        try:
            # Check if playlist and song exist
            playlist = session.query(Playlist).filter_by(id=playlist_id).first()
            if not playlist:
                console.print("[red]Playlist not found![/red]")
                return
            
            song = session.query(Song).filter_by(id=song_id).first()
            if not song:
                console.print("[red]Song not found![/red]")
                return
            
            # Check if song is already in playlist
            existing = session.query(PlaylistSong).filter_by(
                playlist_id=playlist_id, 
                song_id=song_id
            ).first()
            
            if existing:
                console.print("[yellow]Song already exists in this playlist![/yellow]")
                return
            
            playlist_song = PlaylistSong(playlist_id=playlist_id, song_id=song_id)
            session.add(playlist_song)
            session.commit()
            console.print(f"[green]Song {song_id} added to playlist {playlist_id} successfully![/green]")
        except Exception as e:
            session.rollback()
            console.print(f"[red]Database error: {e}[/red]")
        finally:
            session.close()
    except ValueError as e:
        console.print(f"[red]Validation error: {e}[/red]")

def show_playlist_songs():
    show_playlists()
    try:
        playlist_id = int(validate_input(Prompt.ask("Enter playlist ID to view songs"), max_length=10))
        
        session = get_session()
        try:
            playlist = session.query(Playlist).filter_by(id=playlist_id).first()
            if not playlist:
                console.print("[red]Playlist not found![/red]")
                return
            
            songs = (
                session.query(Song, PlaylistSong.added_at)
                .join(PlaylistSong, Song.id == PlaylistSong.song_id)
                .join(Album, Song.album_id == Album.id)
                .join(Artist, Album.artist_id == Artist.id)
                .filter(PlaylistSong.playlist_id == playlist_id)
                .order_by(PlaylistSong.added_at)
                .all()
            )
            
            table = Table(title=f"🎶 Songs in Playlist: {playlist.name} (Owner: {playlist.user.username})")
            table.add_column("ID", justify="right")
            table.add_column("Title")
            table.add_column("Album")
            table.add_column("Artist")
            table.add_column("Added At")
            
            for song, added_at in songs:
                table.add_row(str(song.id), song.title, song.album.title, song.album.artist.name, str(added_at))
            console.print(table)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
        finally:
            session.close()
    except ValueError as e:
        console.print(f"[red]Validation error: {e}[/red]")

def remove_song_from_playlist():
    show_playlists()
    try:
        playlist_id = int(validate_input(Prompt.ask("Enter playlist ID"), max_length=10))
        show_playlist_songs()
        song_id = int(validate_input(Prompt.ask("Enter song ID to remove"), max_length=10))
        
        if not Confirm.ask(f"[red]Are you sure you want to remove song {song_id} from playlist {playlist_id}?[/red]"):
            return
            
        session = get_session()
        try:
            result = session.query(PlaylistSong).filter_by(
                playlist_id=playlist_id, 
                song_id=song_id
            ).delete()
            
            if result == 0:
                console.print("[red]Song not found in this playlist![/red]")
            else:
                session.commit()
                console.print(f"[green]Song {song_id} removed from playlist {playlist_id} successfully![/green]")
        except Exception as e:
            session.rollback()
            console.print(f"[red]Database error: {e}[/red]")
        finally:
            session.close()
    except ValueError as e:
        console.print(f"[red]Validation error: {e}[/red]")

# ========== PLAY HISTORY ==========
def view_play_history():
    show_users()
    try:
        user_id_str = validate_input(Prompt.ask("Enter user ID to view play history", default=""), allow_empty=True)
        user_id = int(user_id_str) if user_id_str else None
        
        session = get_session()
        try:
            query = (
                session.query(PlayHistory, Song.title, User.username)
                .join(Song, PlayHistory.song_id == Song.id)
                .join(User, PlayHistory.user_id == User.id)
            )
            
            if user_id:
                query = query.filter(PlayHistory.user_id == user_id)
                title = f"Play History for User {user_id}"
            else:
                title = "All Play History"
            
            history = query.order_by(PlayHistory.played_at.desc()).all()
            
            table = Table(title=f"⏳ {title}")
            table.add_column("ID", justify="right")
            table.add_column("Song")
            table.add_column("User")
            table.add_column("Played At")
            
            for play, song_title, username in history:
                table.add_row(str(play.id), song_title, username, str(play.played_at))
            console.print(table)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
        finally:
            session.close()
    except ValueError as e:
        console.print(f"[red]Validation error: {e}[/red]")

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
    try:
        user_id = int(validate_input(Prompt.ask("Enter user ID"), max_length=10))
        show_songs()
        song_id = int(validate_input(Prompt.ask("Enter song ID"), max_length=10))
        rating = int(validate_input(
            Prompt.ask("Enter rating (1-5)", choices=["1", "2", "3", "4", "5"]),
            max_length=1
        ))
        
        session = get_session()
        try:
            # Check if user and song exist
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                console.print("[red]User not found![/red]")
                return
            
            song = session.query(Song).filter_by(id=song_id).first()
            if not song:
                console.print("[red]Song not found![/red]")
                return
            
            # Add or update rating
            existing_rating = session.query(SongRating).filter_by(
                user_id=user_id,
                song_id=song_id
            ).first()
            
            if existing_rating:
                existing_rating.rating = rating
                action = "updated"
            else:
                new_rating = SongRating(user_id=user_id, song_id=song_id, rating=rating)
                session.add(new_rating)
                action = "added"
            
            session.commit()
            console.print(f"[green]Rating {rating} {action} for song {song_id} by user {user_id}![/green]")
        except Exception as e:
            session.rollback()
            console.print(f"[red]Database error: {e}[/red]")
        finally:
            session.close()
    except ValueError as e:
        console.print(f"[red]Validation error: {e}[/red]")

def show_ratings():
    show_users()
    try:
        user_id_str = validate_input(Prompt.ask("Enter user ID to filter (leave blank for all)", default=""), allow_empty=True)
        user_id = int(user_id_str) if user_id_str else None
        
        show_songs()
        song_id_str = validate_input(Prompt.ask("Enter song ID to filter (leave blank for all)", default=""), allow_empty=True)
        song_id = int(song_id_str) if song_id_str else None
        
        session = get_session()
        try:
            query = (
                session.query(SongRating, User.username, Song.title)
                .join(User, SongRating.user_id == User.id)
                .join(Song, SongRating.song_id == Song.id)
            )
            
            if user_id and song_id:
                query = query.filter(SongRating.user_id == user_id, SongRating.song_id == song_id)
                title = f"Rating for Song {song_id} by User {user_id}"
            elif user_id:
                query = query.filter(SongRating.user_id == user_id)
                title = f"All Ratings by User {user_id}"
            elif song_id:
                query = query.filter(SongRating.song_id == song_id)
                title = f"All Ratings for Song {song_id}"
            else:
                title = "All Song Ratings"
            
            ratings = query.order_by(Song.title, SongRating.rating.desc()).all()
            
            table = Table(title=f"⭐ {title}")
            table.add_column("User")
            table.add_column("Song")
            table.add_column("Rating")
            
            for rating, username, song_title in ratings:
                stars = "★" * rating.rating + "☆" * (5 - rating.rating)
                table.add_row(username, song_title, stars)
            console.print(table)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
        finally:
            session.close()
    except ValueError as e:
        console.print(f"[red]Validation error: {e}[/red]")

def delete_rating():
    show_users()
    try:
        user_id = int(validate_input(Prompt.ask("Enter user ID"), max_length=10))
        show_songs()
        song_id = int(validate_input(Prompt.ask("Enter song ID"), max_length=10))
        
        if not Confirm.ask(f"[red]Are you sure you want to delete rating for song {song_id} by user {user_id}?[/red]"):
            return
            
        session = get_session()
        try:
            result = session.query(SongRating).filter_by(
                user_id=user_id,
                song_id=song_id
            ).delete()
            
            if result == 0:
                console.print("[red]Rating not found![/red]")
            else:
                session.commit()
                console.print(f"[green]Rating for song {song_id} by user {user_id} deleted successfully![/green]")
        except Exception as e:
            session.rollback()
            console.print(f"[red]Database error: {e}[/red]")
        finally:
            session.close()
    except ValueError as e:
        console.print(f"[red]Validation error: {e}[/red]")

# ========== MAIN FUNCTION ==========
def main():
    while True:
        menu()
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"])
        
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
        elif choice == "0":
            console.print("[yellow]Goodbye![/yellow]")
            break

if __name__ == '__main__':
    main()