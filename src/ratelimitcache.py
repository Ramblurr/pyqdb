from flask import request, current_app, abort
from flaskext.cache import Cache

from datetime import datetime, timedelta

import functools, sha
from functools import wraps


class ratelimit(object):
    "Instances of this class can be used as decorators"
    # This class is designed to be sub-classed
    minutes = 2 # The time period
    requests = 20 # Number of allowed requests in that time period

    prefix = 'rl-' # Prefix for memcache key

    def __init__(self, **options):
        for key, value in options.items():
            setattr(self, key, value)

    def __call__(self, fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            return self.view_wrapper(fn, *args, **kwargs)
        return wrapper

    def view_wrapper(self, fn, *args, **kwargs):
        if not self.should_ratelimit(request):
            return fn(*args, **kwargs)

        counts = self.get_counters(request)

        # Increment rate limiting counter
        self.cache_incr(self.current_key(request))

        # Have they failed?
        if sum(counts) >= self.requests:
            return self.disallowed(request)

        return fn(*args, **kwargs)

    def cache_get_many(self, keys):
        return self.cache.get_many(*keys)

    def cache_incr(self, key):
        # memcache is only backend that can increment atomically
        self.cache.add(key, 0, self.expire_after())
        self.cache.inc(key)

    def should_ratelimit(self, request):
        return True

    def get_counters(self, request):
        keys = self.keys_to_check(request)
        l = self.cache_get_many(keys)
        return [ 0 if i is None else i for i in l ]

    def keys_to_check(self, request):
        extra = self.key_extra(request)
        now = datetime.now()
        return [
            '%s%s-%s' % (
                self.prefix,
                extra,
                (now - timedelta(minutes = minute)).strftime('%Y%m%d%H%M')
            ) for minute in range(self.minutes + 1)
        ]

    def current_key(self, request):
        return '%s%s-%s' % (
            self.prefix,
            self.key_extra(request),
            datetime.now().strftime('%Y%m%d%H%M')
        )

    def key_extra(self, request):
        # By default, their IP address is used
        return request.remote_addr

    def disallowed(self, request):
        "Over-ride this method if you want to log incidents"
        abort(403)
        return 'Rate limit exceeded'

    def expire_after(self):
        "Used for setting the memcached cache expiry"
        return (self.minutes + 1) * 60

class ratelimit_post(ratelimit):
    "Rate limit POSTs - can be used to protect a login form"
    key_field = None # If provided, this POST var will affect the rate limit

    def should_ratelimit(self, request):
        return request.method == 'POST'

    def key_extra(self, request):
        # IP address and key_field (if it is set)
        extra = super(ratelimit_post, self).key_extra(request)
        if self.key_field:
            value = sha.new(request.POST.get(self.key_field, '')).hexdigest()
            extra += '-' + value
        return extra

