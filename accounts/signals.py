import django.dispatch

# Custom signals dispatched by accounts.views / accounts.api_views. accounts intentionally has no knowledge of the audit app.
# "audit" app will import these and connect a receiver that writes an AuditLog row, keeping the two apps decoupled.

user_registered = django.dispatch.Signal()          # kwargs: user, request
user_logged_in_custom = django.dispatch.Signal()    # kwargs: user, request
user_logged_out_custom = django.dispatch.Signal()   # kwargs: user, request
login_failed = django.dispatch.Signal()             # kwargs: identifier, request