from django import template

register = template.Library()


@register.filter
def trans(translations_dict, lang_field):
    """
    Usage: {{ meetup.translations_dict|trans:"en:venue_name" }}
    Falls back gracefully if lang or field missing.
    """
    try:
        lang, field = lang_field.split(':', 1)
    except ValueError:
        return ''
    by_lang = translations_dict.get(lang, {})
    return by_lang.get(field, '')


@register.simple_tag(takes_context=True)
def lang_url(context, lang_code):
    """Render current URL with ?lang=<code> substituted."""
    request = context.get('request')
    if not request:
        return f'?lang={lang_code}'
    params = request.GET.copy()
    params['lang'] = lang_code
    return f'?{params.urlencode()}'
