from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Meetup, Language


def _build_talks(meetup):
    talks = []
    for talk in meetup.talks.prefetch_related('translations'):
        talks.append({'obj': talk, 'tr': talk.translations_dict()})
    return talks


def index(request):
    lang   = request.current_lang
    meetup = Meetup.get_next()
    ctx = {
        'meetup': meetup,
        'lang':   lang,
        'tr':     meetup.translations_dict() if meetup else {},
        'talks':  _build_talks(meetup) if meetup else [],
    }
    return render(request, 'meetups/index.html', ctx)


def previous(request):
    lang      = request.current_lang
    qs        = Meetup.get_past().prefetch_related('translations', 'talks__translations')
    paginator = Paginator(qs, 10)
    page_obj  = paginator.get_page(request.GET.get('page'))

    meetups = []
    for m in page_obj:
        talks = [{'obj': t, 'tr': t.translations_dict()} for t in m.talks.all()]
        meetups.append({'obj': m, 'tr': m.translations_dict(), 'talks': talks})

    return render(request, 'meetups/previous.html', {
        'meetups': meetups,
        'lang':    lang,
        'page_obj': page_obj,
    })


def meetup_detail(request, pk):
    lang   = request.current_lang
    meetup = Meetup.get_public(pk)  # None if draft or nonexistent — never leaks drafts

    ctx = {'meetup': meetup, 'lang': lang}
    if meetup:
        ctx['tr']    = meetup.translations_dict()
        ctx['talks'] = _build_talks(meetup)
        if meetup.status == 'past':
            ctx['hero_label'] = 'Geçmiş Etkinlik' if lang == 'tr' else 'Past Meetup'
        else:
            ctx['hero_label'] = 'Sonraki Etkinlik' if lang == 'tr' else 'Next Meetup'

    return render(request, 'meetups/meetup_detail.html', ctx)
