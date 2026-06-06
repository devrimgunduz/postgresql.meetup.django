from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db import transaction

from .models import Language, Meetup, MeetupTranslation, Talk, TalkTranslation


# ── Auth ─────────────────────────────────────────────────────

def admin_login(request):
    if request.user.is_authenticated:
        return redirect('admin_index')
    error = ''
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username', ''),
            password=request.POST.get('password', ''),
        )
        if user and user.is_staff:
            login(request, user)
            return redirect('admin_index')
        error = 'Invalid credentials or insufficient permissions.'
    return render(request, 'meetups/admin/login.html', {'error': error})


def admin_logout(request):
    logout(request)
    return redirect('admin_login')


# ── Dashboard ─────────────────────────────────────────────────

@login_required
def admin_index(request):
    Meetup.auto_archive()
    meetups   = Meetup.objects.prefetch_related('translations', 'talks').all()
    def_lang  = Language.get_default()
    return render(request, 'meetups/admin/index.html', {
        'meetups':  meetups,
        'def_lang': def_lang.code if def_lang else 'en',
    })


# ── Meetups ───────────────────────────────────────────────────

@login_required
def meetup_edit(request, pk=None):
    meetup    = get_object_or_404(Meetup, pk=pk) if pk else None
    languages = Language.get_active()
    tr        = meetup.translations_dict() if meetup else {}

    if request.method == 'POST':
        with transaction.atomic():
            if not meetup:
                meetup = Meetup()
            meetup.status           = request.POST.get('status', 'draft')
            meetup.event_date       = request.POST.get('event_date') or None
            meetup.event_end        = request.POST.get('event_end') or None
            meetup.venue_address    = request.POST.get('venue_address', '')
            meetup.venue_map_url    = request.POST.get('venue_map_url', '')
            meetup.registration_url = request.POST.get('registration_url', '')
            meetup.save()

            # Save translations
            for lang in languages:
                for field in ('meetup_title', 'notes'):
                    key   = f'trans_{lang.code}_{field}'
                    value = request.POST.get(key, '').strip()
                    if value:
                        MeetupTranslation.objects.update_or_create(
                            meetup=meetup, lang=lang.code, field=field,
                            defaults={'value': value},
                        )
                    else:
                        MeetupTranslation.objects.filter(
                            meetup=meetup, lang=lang.code, field=field
                        ).delete()

        messages.success(request, 'Meetup saved.')
        return redirect('meetup_edit', pk=meetup.pk)

    import json
    return render(request, 'meetups/admin/meetup_edit.html', {
        'meetup':    meetup,
        'languages': languages,
        'tr':        tr,
        'tr_json':   json.dumps(tr),
        'lang_codes': json.dumps([l.code for l in languages]),
    })


@login_required
def meetup_delete(request, pk):
    get_object_or_404(Meetup, pk=pk).delete()
    messages.success(request, 'Meetup deleted.')
    return redirect('admin_index')


# ── Talks ─────────────────────────────────────────────────────

@login_required
def talks_list(request, meetup_pk):
    meetup    = get_object_or_404(Meetup, pk=meetup_pk)
    languages = Language.get_active()
    def_lang  = Language.get_default()
    talks     = meetup.talks.prefetch_related('translations').all()

    edit_pk  = request.GET.get('edit')
    edit_talk = get_object_or_404(Talk, pk=edit_pk, meetup=meetup) if edit_pk else None
    ttr      = edit_talk.translations_dict() if edit_talk else {}
    is_new   = 'new' in request.GET

    if request.method == 'POST':
        talk_pk = request.POST.get('talk_id')
        with transaction.atomic():
            if talk_pk:
                talk = get_object_or_404(Talk, pk=talk_pk, meetup=meetup)
            else:
                talk = Talk(meetup=meetup)
            talk.sort_order        = int(request.POST.get('sort_order', 0))
            talk.speaker_name      = request.POST.get('speaker_name', '')
            talk.speaker_photo_url = request.POST.get('speaker_photo_url', '')
            dur = request.POST.get('talk_duration_min', '')
            talk.talk_duration_min = int(dur) if dur.strip() else None
            talk.save()

            for lang in languages:
                for field in ('talk_title', 'talk_abstract', 'speaker_bio'):
                    key   = f'trans_{lang.code}_{field}'
                    value = request.POST.get(key, '').strip()
                    if value:
                        TalkTranslation.objects.update_or_create(
                            talk=talk, lang=lang.code, field=field,
                            defaults={'value': value},
                        )
                    else:
                        TalkTranslation.objects.filter(
                            talk=talk, lang=lang.code, field=field
                        ).delete()

        messages.success(request, 'Talk saved.')
        return redirect('talks_list', meetup_pk=meetup_pk)

    import json
    return render(request, 'meetups/admin/talks.html', {
        'meetup':    meetup,
        'talks':     talks,
        'languages': languages,
        'def_lang':  def_lang.code if def_lang else 'en',
        'edit_talk': edit_talk,
        'ttr':       ttr,
        'ttr_json':  json.dumps(ttr),
        'lang_codes': json.dumps([l.code for l in languages]),
        'is_new':    is_new,
    })


@login_required
def talk_delete(request, pk):
    talk = get_object_or_404(Talk, pk=pk)
    meetup_pk = talk.meetup_id
    talk.delete()
    messages.success(request, 'Talk deleted.')
    return redirect('talks_list', meetup_pk=meetup_pk)


# ── Languages ─────────────────────────────────────────────────

@login_required
def languages_list(request):
    error   = ''
    if request.method == 'POST':
        code  = request.POST.get('code', '').strip().lower()
        label = request.POST.get('label', '').strip()
        order = int(request.POST.get('sort_order', 99))
        if not code or not label:
            error = 'Code and label are required.'
        elif not code.replace('-', '').replace('_', '').isalpha():
            error = 'Code must contain only letters, hyphens, or underscores.'
        else:
            try:
                Language.objects.create(code=code, label=label, sort_order=order)
                messages.success(request, f'Language "{label}" added.')
                return redirect('languages_list')
            except Exception:
                error = f'Language code "{code}" already exists.'

    action = request.GET.get('action')
    lang_id = request.GET.get('id')
    if action and lang_id:
        lang = get_object_or_404(Language, pk=lang_id)
        if action == 'set_default':
            Language.objects.all().update(is_default=False)
            lang.is_default = True
            lang.is_active  = True
            lang.save()
        elif action == 'toggle' and not lang.is_default:
            lang.is_active = not lang.is_active
            lang.save()
        elif action == 'delete' and not lang.is_default:
            lang.delete()
        return redirect('languages_list')

    return render(request, 'meetups/admin/languages.html', {
        'languages': Language.objects.all(),
        'error':     error,
    })


# ── Users ─────────────────────────────────────────────────────

@login_required
def users_list(request):
    from django.contrib.auth.models import User
    error = ''
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            uname = request.POST.get('username', '').strip()
            pwd   = request.POST.get('password', '')
            if len(uname) < 2 or len(pwd) < 8:
                error = 'Username ≥2 chars and password ≥8 chars required.'
            elif User.objects.filter(username=uname).exists():
                error = f'Username "{uname}" already exists.'
            else:
                User.objects.create_user(username=uname, password=pwd, is_staff=True)
                messages.success(request, f'User "{uname}" created.')
                return redirect('users_list')
        elif action == 'change_password':
            uid = request.POST.get('user_id')
            pwd = request.POST.get('new_password', '')
            if len(pwd) < 8:
                error = 'Password must be ≥8 characters.'
            else:
                u = get_object_or_404(User, pk=uid)
                u.set_password(pwd)
                u.save()
                messages.success(request, 'Password updated.')
                return redirect('users_list')

    users = User.objects.filter(is_staff=True).order_by('id')
    return render(request, 'meetups/admin/users.html', {
        'users': users,
        'error': error,
    })
