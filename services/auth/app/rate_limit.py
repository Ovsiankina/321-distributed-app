import math
import threading
import time
from collections import deque
from collections.abc import Callable

MAX_ATTEMPTS = 10
WINDOW_SECONDS = 60


class LoginRateLimiter:
    """Au plus max_attempts tentatives de login par email sur toute fenêtre glissante.

    Par email et non par IP : Auth ne voit que l'IP de la Gateway.

    Une tentative est comptée avant la vérification du mot de passe, et un succès
    efface le compteur : seuls les échecs restent comptés. Le contrôle et le comptage
    se font sous le même verrou, sinon des requêtes simultanées passeraient toutes le
    contrôle avant que le premier échec soit enregistré.
    """

    def __init__(
        self,
        max_attempts: int = MAX_ATTEMPTS,
        window_seconds: float = WINDOW_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._max_attempts = max_attempts
        self._window_seconds = window_seconds
        self._clock = clock
        self._lock = threading.Lock()
        # Instants des tentatives encore dans la fenêtre, du plus ancien au plus récent.
        self._attempts: dict[str, deque[float]] = {}
        self._last_prune = clock()

    def acquire(self, email: str) -> int:
        """Compte une tentative.

        Renvoie 0 si elle est permise, sinon les secondes à attendre (Retry-After).
        """
        now = self._clock()
        with self._lock:
            self._prune(now)
            attempts = self._attempts.setdefault(email, deque())
            while attempts and now - attempts[0] >= self._window_seconds:
                attempts.popleft()
            if len(attempts) >= self._max_attempts:
                # Une place se libère quand la plus ancienne tentative sort de la
                # fenêtre. Jamais 0 : l'appelant y lirait une tentative permise.
                return max(1, math.ceil(attempts[0] + self._window_seconds - now))
            attempts.append(now)
            return 0

    def reset(self, email: str) -> None:
        with self._lock:
            self._attempts.pop(email, None)

    def _prune(self, now: float) -> None:
        # Au plus une fois par fenêtre : la mémoire reste bornée face à des emails
        # aléatoires, sans parcourir tout le dictionnaire à chaque tentative.
        if now - self._last_prune < self._window_seconds:
            return
        self._last_prune = now
        self._attempts = {
            email: attempts
            for email, attempts in self._attempts.items()
            if attempts and now - attempts[-1] < self._window_seconds
        }


login_limiter = LoginRateLimiter()
