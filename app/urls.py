"""Expose the Django project's URL configuration for deployment entrypoints."""

from backend.app.app import urls as backend_urls

urlpatterns = backend_urls.urlpatterns

for _handler in ("handler400", "handler403", "handler404", "handler500"):
    _value = getattr(backend_urls, _handler, None)
    if _value is not None:
        globals()[_handler] = _value
