from datetime import datetime

try:
    import firebase_admin
    import pytz
    from firebase_admin import credentials, firestore
    _FIREBASE_AVAILABLE = True
except Exception:
    # If firebase SDK isn't installed, gracefully degrade to no-ops.
    firebase_admin = None
    pytz = None
    credentials = None
    firestore = None
    _FIREBASE_AVAILABLE = False


def initialize_firebase():
    """Initialize firebase if available. Raises an exception only if SDK present but init fails."""
    if not _FIREBASE_AVAILABLE:
        # No-op when firebase SDK isn't installed
        return

    from fb_env import keys

    cred = credentials.Certificate(keys)
    firebase_admin.initialize_app(cred)


def get_db():
    """Return firestore client or None if firebase isn't available."""
    if not _FIREBASE_AVAILABLE:
        return None

    return firestore.client()


def log_game(db, game_dict):
    """Log game to firestore; no-op when firebase isn't available or db is None."""
    if not _FIREBASE_AVAILABLE or db is None:
        return

    est = pytz.timezone('US/Eastern')
    time = datetime.now(est)

    doc_ref = db.collection('games').document()
    doc_ref.set({**game_dict, 'date': time})
