"""Reset ephemeral request counters before isolated development test runs."""
from .config import settings
from .security import redis
if settings.app_env!='development': raise RuntimeError('Test reset запрещён в production')
for pattern in ['login:*','register:*','submit:*','draft:*','events:*']:
    keys=list(redis.scan_iter(match=pattern))
    if keys: redis.delete(*keys)
print('Development test rate counters reset; protections remain enabled')
