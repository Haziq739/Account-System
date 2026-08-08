import bcrypt
from database.session import SessionLocal
from models.user import User
from utils.logger import logger


class AuthService:
    """Service for handling all authentication and user management."""

    @staticmethod
    def _hash(password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def _verify(plain: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
        except Exception:
            return False

    # ── Read-only queries ─────────────────────────────────────────────────────

    @staticmethod
    def is_first_run() -> bool:
        """True when no users exist (first-time setup)."""
        with SessionLocal() as s:
            return s.query(User).count() == 0

    @staticmethod
    def username_exists(username: str) -> bool:
        with SessionLocal() as s:
            return s.query(User).filter(User.username == username).count() > 0

    @staticmethod
    def email_exists(email: str) -> bool:
        with SessionLocal() as s:
            return s.query(User).filter(User.email == email).count() > 0

    # ── Write operations ──────────────────────────────────────────────────────

    @staticmethod
    def create_user(username: str, email: str, password: str, role: str = "admin") -> bool:
        """
        Create any user (owner on first run, or additional user later).
        Returns True on success, raises ValueError on validation failure.
        """
        with SessionLocal() as s:
            if s.query(User).filter(User.username == username).count() > 0:
                raise ValueError(f"Username '{username}' is already taken.")
            if s.query(User).filter(User.email == email).count() > 0:
                raise ValueError(f"Email '{email}' is already registered.")

            user = User(
                username=username,
                email=email,
                password_hash=AuthService._hash(password),
                role=role,
            )
            s.add(user)
            s.commit()
            logger.info(f"User '{username}' created with role '{role}'.")
            return True

    # Keep backward-compat alias used by older code
    @staticmethod
    def create_owner(username: str, email: str, password: str) -> bool:
        return AuthService.create_user(username, email, password, role="admin")

    @staticmethod
    def login(username: str, password: str):
        """
        Returns a plain dict of user data on success, or None on failure.
        Using a dict avoids detached-instance errors after session closes.
        """
        with SessionLocal() as s:
            user = s.query(User).filter(User.username == username).first()
            if not user:
                return None
            if not AuthService._verify(password, user.password_hash):
                return None
            # Return a simple dict so the object is never detached
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
            }

    @staticmethod
    def verify_email(email: str) -> bool:
        """True if the email belongs to a registered user."""
        with SessionLocal() as s:
            return s.query(User).filter(User.email == email).count() > 0

    @staticmethod
    def reset_password(email: str, new_password: str) -> bool:
        """Reset password by email. Returns True on success."""
        with SessionLocal() as s:
            user = s.query(User).filter(User.email == email).first()
            if not user:
                return False
            user.password_hash = AuthService._hash(new_password)
            s.commit()
            logger.info(f"Password reset for email '{email}'.")
            return True

    @staticmethod
    def change_password(user_id: int, old_password: str, new_password: str) -> bool:
        """
        Change password for a logged-in user.
        Verifies old password, hashes new one, commits in the same session.
        Returns True on success, False if old password is wrong.
        """
        with SessionLocal() as s:
            user = s.query(User).filter(User.id == user_id).first()
            if not user:
                logger.warning(f"change_password: user id {user_id} not found.")
                return False
            if not AuthService._verify(old_password, user.password_hash):
                logger.warning(f"change_password: wrong old password for user id {user_id}.")
                return False
            user.password_hash = AuthService._hash(new_password)
            s.commit()
            logger.info(f"Password changed for user id {user_id}.")
            return True

    @staticmethod
    def seed_companies():
        """Seed initial companies safely."""
        from models.company import Company
        with SessionLocal() as s:
            if s.query(Company).count() == 0:
                c1 = Company(
                    name="K Dynamics (PRIVATE) LIMITED",
                    address="Office #03, Ittehad Center,\nFazal-e-Haq Road,\nBlue Area, Islamabad",
                    phone="0320-0222204",
                    email="KDynamicspvt@gmail.com",
                    ntn_number="G650435",
                    gst_registration="G650435",
                    tax_enabled=True,
                    default_tax_rate=18.0,
                    logo_path="k_dynamics_logo.png"
                )
                c2 = Company(
                    name="RN Scanner and Digital Print House",
                    address="Office #03, Ittehad Center,\nFazal-e-Haq Road,\nBlue Area, Islamabad",
                    phone="0321-8476168",
                    email="rnscanner@gmail.com",
                    tax_enabled=False,
                    logo_path="rn_scanner_logo.png"
                )
                s.add_all([c1, c2])
                s.commit()
                logger.info("Companies seeded successfully.")
