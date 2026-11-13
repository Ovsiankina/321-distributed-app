import math
import threading
import time
from collections.abc import Callable

MAX_FAILURES = 10
WINDOW_SECONDS = 60


class LoginRateLimiter:
    """Compte les échecs de login par email, sur une fenêtre ouverte au premier échec.

    Par email et non par IP : Auth ne voit que l'IP de la Gateway.
    """

    def __init__(
        self,
        max_failures: int = MAX_FAILURES,
        window_seconds: float = WINDOW_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._max_failures = max_failures
        self._window_seconds = window_seconds
        self._clock = clock
        self._lock = threading.Lock()
        self._failures: dict[str, tuple[float, int]] = {}
        self._last_prune = clock()

    def retry_after(self, email: str) -> int:
        """Secondes à attendre avant la prochaine tentative, 0 si elle est permise."""
        now = self._clock()
        with self._lock:
            window_start, count = self._failures.get(email, (now, 0))
            remaining = window_start + self._window_seconds - now
            if count < self._max_failures or remaining <= 0:
                return 0
            return math.ceil(remaining)

    def record_failure(self, email: str) -> None:
        now = self._clock()
        with self._lock:
            self._prune(now)
            window_start, count = self._failures.get(email, (now, 0))
            if now - window_start >= self._window_seconds:
                window_start, count = now, 0
            self._failures[email] = (window_start, count + 1)

    def reset(self, email: str) -> None:
        with self._lock:
            self._failures.pop(email, None)

    def _prune(self, now: float) -> None:
        # Au plus une fois par fenêtre : la mémoire reste bornée face à des emails
        # aléatoires, sans parcourir tout le dictionnaire à chaque échec.
        if now - self._last_prune < self._window_seconds:
            return
        self._last_prune = now
        self._failures = {
            email: entry
            for email, entry in self._failures.items()
            if now - entry[0] < self._window_seconds
        }


login_limiter = LoginRateLimiter()
