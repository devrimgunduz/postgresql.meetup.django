from django.db import OperationalError, ProgrammingError


class LanguageMiddleware:
    """
    Reads ?lang= from query string, validates it against active languages,
    and stores the result on request.current_lang for use in views/templates.
    Gracefully handles the case where the DB tables don't exist yet (e.g. during migrate).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            from .models import Language
            active_codes = list(
                Language.objects.filter(is_active=True).values_list('code', flat=True)
            )
            requested = request.GET.get('lang', request.session.get('lang', ''))
            if requested in active_codes:
                request.current_lang = requested
                request.session['lang'] = requested
            else:
                default = Language.get_default()
                request.current_lang = default.code if default else 'en'
        except (OperationalError, ProgrammingError):
            # Tables don't exist yet (e.g. running migrate for the first time)
            request.current_lang = 'en'

        return self.get_response(request)
