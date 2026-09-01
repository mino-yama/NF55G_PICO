"""Cache validity manager for decoded NF55G data."""

try:
    from . import config
    from .models import CacheEntry
except ImportError:  # pragma: no cover
    import config
    from models import CacheEntry


class CacheError(ValueError):
    pass


class CacheManager:
    def __init__(self, clock_ms=None):
        self._clock_ms = clock_ms
        self._entries = {}
        for name in config.CACHE_NAMES:
            self._entries[name] = CacheEntry()

    def _now_ms(self):
        if self._clock_ms is None:
            return None
        return self._clock_ms()

    def _require_name(self, name):
        if name not in self._entries:
            raise CacheError("unknown cache: {}".format(name))

    def invalidate(self, name):
        self._require_name(name)
        self._entries[name] = CacheEntry(valid=False)

    def invalidate_many(self, names):
        for name in names:
            self.invalidate(name)

    def invalidate_all(self):
        self.invalidate_many(tuple(self._entries.keys()))

    def validate(self, name, data, source_cmd):
        self._require_name(name)
        self._entries[name] = CacheEntry(
            valid=True,
            data=data,
            source_cmd=source_cmd,
            updated_ms=self._now_ms(),
        )

    def is_valid(self, name):
        self._require_name(name)
        return self._entries[name].valid

    def get(self, name):
        self._require_name(name)
        entry = self._entries[name]
        if not entry.valid:
            return None
        return entry.data

    def metadata(self, name):
        self._require_name(name)
        return self._entries[name].metadata()

    def refresh_started(self, name):
        self.invalidate(name)

    def refresh_succeeded(self, name, data, source_cmd):
        self.validate(name, data, source_cmd)

    def refresh_failed(self, name):
        self.invalidate(name)

    def apply_success_invalidation(self, action):
        self.invalidate_many(config.SUCCESS_INVALIDATION.get(action, ()))

    def apply_ambiguous_invalidation(self, action):
        self.apply_success_invalidation(action)
