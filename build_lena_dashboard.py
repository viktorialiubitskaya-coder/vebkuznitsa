#!/usr/bin/env python3
"""
build_lena_dashboard.py
Читает лиды из Baserow (Russia Pipeline, table 580),
генерирует питчи через Claude API,
рендерит lena/index.html для партнёра Лены.

Запуск: python3 build_lena_dashboard.py
Требует: ANTHROPIC_API_KEY (обязательно), BASEROW_API_TOKEN (опционально)
"""

import os, json, html as html_mod
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
BASEROW_API_TOKEN = os.environ.get("BASEROW_API_TOKEN", "")
BASEROW_URL = "https://leads.vebkuznitsa.ru/api/database/rows/table/580/?user_field_names=true&size=100"
OUT_FILE = Path(__file__).parent / "lena" / "index.html"

DEMO_URLS = {
    1: "https://viktorialiubitskaya-coder.github.io/vebkuznitsa/restaurants/barin-i-barash/",
    3: "https://viktorialiubitskaya-coder.github.io/vebkuznitsa/restaurants/lazhechnikov/",
}

CITY_RU = {
    "Kolomna": "Коломна", "Moscow": "Москва",
    "Saint Petersburg": "Санкт-Петербург", "Kazan": "Казань",
    "Yekaterinburg": "Екатеринбург", "Sochi": "Сочи",
    "Novosibirsk": "Новосибирск", "Krasnodar": "Краснодар",
    "Krasnoyarsk": "Красноярск", "Other": "Другой"
}
CUISINE_RU = {
    "Russian": "Русская", "European": "Европейская", "Italian": "Итальянская",
    "Georgian": "Грузинская", "Japanese": "Японская", "Author": "Авторская",
    "Sushi": "Суши", "Pizza": "Пицца", "American": "Американская",
    "Burgers": "Бургеры", "Vegan": "Веганская", "Other": "Другая",
    "Caucasian": "Кавказская", "Coffee": "Кофейня", "Desserts": "Десерты",
    "Asian": "Азиатская", "French": "Французская", "Seafood": "Морепродукты",
    "Modern": "Современная", "Spanish": "Испанская", "Vietnamese": "Вьетнамская",
}


def fmtnum(n):
    return f"{n:,}".replace(",", " ")  # non-breaking space


def sel_val(field):
    if not field:
        return ""
    if isinstance(field, dict):
        return field.get("value", "")
    return str(field)


def multi_val(field):
    if not field:
        return []
    if isinstance(field, list):
        return [x.get("value", "") if isinstance(x, dict) else str(x) for x in field]
    return []


def card_cover(photos):
    if photos and isinstance(photos, list) and len(photos) > 0:
        p = photos[0]
        thumbs = p.get("thumbnails", {})
        if "card_cover" in thumbs:
            return thumbs["card_cover"]["url"]
        return p.get("url", "")
    return ""


def h(s):
    return html_mod.escape(str(s), quote=True)


def recommend_package(city_en, avg_check):
    is_moscow = city_en in ("Moscow", "Saint Petersburg")
    avg_check = avg_check or 0
    if avg_check >= 2000:
        pkg, price = "Гость", (25000 if is_moscow else 20000)
    elif avg_check >= 1200:
        pkg, price = "Витрина+", (20000 if is_moscow else 15000)
    else:
        pkg, price = "Витрина+", (20000 if is_moscow else 15000)
    return {"name": pkg, "price": price, "commission": int(price * 0.3)}


# ── Baserow ──────────────────────────────────────────────────────────────────

def fetch_leads():
    if not BASEROW_API_TOKEN:
        print("  ⚠️  BASEROW_API_TOKEN не задан — работаем с офлайн-данными.")
        return _mock_leads()
    import urllib.request
    req = urllib.request.Request(
        BASEROW_URL,
        headers={"Authorization": f"Token {BASEROW_API_TOKEN}"}
    )
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
    return data.get("results", [])


def _mock_leads():
    return [
        {
            "id": 1,
            "Название": "Барин и Бараш",
            "Город": {"value": "Kolomna"},
            "Адрес": "ул. Лажечникова, 3",
            "Тип заведения": {"value": "restaurant"},
            "Кухня": [{"value": "Russian"}, {"value": "European"}],
            "Средний чек, ₽": 1500,
            "Ссылка на 2gis или Яндекс": "https://yandex.ru/maps/org/barin_and_barash/88986911340/",
            "Есть ли свой сайт?": {"value": "no"},
            "ВКонтакте": "https://vk.com/barinandbarash",
            "Телефон ресторана": "+7 (901) 577-67-77",
            "Рейтинг 2gis/Яндекс": 49,
            "Сколько оценок": 2280,
            "Что особенного (в 2 предложениях)": (
                "Ресторан и бар в Коломенском кремле — самой туристической локации города. "
                "Концепция «огонь вкуса»: блюда на углях, пельмени ручной лепки, кальцоне. "
                "Активные банкеты, медовуха, авторские чаи. Работают до полуночи в пт-сб."
            ),
            "Уникальная концепция?": {"value": "yes strong"},
            "Банкеты": {"value": "yes"},
            "Афиша событий": {"value": "sometimes"},
            "Дата сбора": "2026-04-28",
            "Фото": [{"url": "", "thumbnails": {"card_cover": {"url": "https://leads.vebkuznitsa.ru/media/thumbnails/card_cover/mtxUOWwrpPzeN27B19l6WrzthnCmeLzo_fbba0ef0d7a6b5e1507deb89b6025d561a7733fdd73c922011a65caf1bb601b1.jpg"}}}],
        },
        {
            "id": 3,
            "Название": "Литературное кафе Лажечников",
            "Город": {"value": "Kolomna"},
            "Адрес": "улица Лажечникова, 13А",
            "Тип заведения": {"value": "cafe"},
            "Кухня": [{"value": "Russian"}],
            "Средний чек, ₽": None,
            "Ссылка на 2gis или Яндекс": "https://yandex.ru/maps/org/lazhechnikov_literary_cafe/100397037904/",
            "Есть ли свой сайт?": {"value": "only platform card like clients.site or restoplace"},
            "ВКонтакте": "https://vk.com/cafelazhechnikov",
            "Телефон ресторана": "+7 (916) 583-13-82",
            "Рейтинг 2gis/Яндекс": 5,
            "Сколько оценок": 1477,
            "Что особенного (в 2 предложениях)": (
                "Литературное кафе в сердце Коломны — названо в честь писателя Лажечникова. "
                "Используют старорусские слова: «увеселения», «кушанья», «убранство». "
                "Регулярные театральные вечера с немым кино 1920-х, тапёром и коломенской пастилой. "
                "Место с историей — туристы идут специально."
            ),
            "Уникальная концепция?": {"value": "yes strong"},
            "Банкеты": {"value": "not specified"},
            "Афиша событий": {"value": "yes regular"},
            "Дата сбора": "2026-04-30",
            "Фото": [{"url": "", "thumbnails": {"card_cover": {"url": "https://leads.vebkuznitsa.ru/media/thumbnails/card_cover/jevOmmCZ37qpRI45Ut8ocnJo95Hjyp3q_2fd02161a921a6d59128a31eae6a03a9eaae9c143b96bdcf3bff9bc8ff2de54e.jpg"}}}],
        }
    ]


# ── Pitches ───────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = (
    "Ты Лена — менеджер из Коломны, 30 лет, дружелюбная, разбирается в маркетинге. "
    "Пишешь от первого лица. Тон живой, тёплый, без официоза. "
    "НЕЛЬЗЯ упоминать: Google, Instagram, Telegram, WhatsApp, Facebook, YouTube. "
    "МОЖНО упоминать: Яндекс.Карты, Яндекс.Поиск, ВКонтакте, звонок, email. "
    "Не используй: «инновационный», «уникальный опыт», «представитель агентства»."
)


def claude(prompt):
    import urllib.request
    payload = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 700,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
    )
    with urllib.request.urlopen(req) as r:
        resp = json.loads(r.read())
    return resp["content"][0]["text"].strip()


def generate_pitches(lead):
    if not ANTHROPIC_API_KEY:
        return {
            "vk": "Добавь ANTHROPIC_API_KEY для генерации питчей.",
            "phone": "Добавь ANTHROPIC_API_KEY для генерации скрипта.",
            "email": "Добавь ANTHROPIC_API_KEY для генерации email.",
        }

    name = lead.get("Название", "")
    city = CITY_RU.get(sel_val(lead.get("Город")), sel_val(lead.get("Город")))
    special = (lead.get("Что особенного (в 2 предложениях)") or "")[:400]
    vk = lead.get("ВКонтакте", "")
    avg_check = lead.get("Средний чек, ₽")
    banquets = sel_val(lead.get("Банкеты", {}))
    events = sel_val(lead.get("Афиша событий", {}))
    demo_url = lead.get("demo_url", "")

    ctx_parts = [f"Заведение: «{name}» ({city})."]
    if avg_check:
        ctx_parts.append(f"Средний чек: {avg_check} ₽.")
    if banquets in ("yes", "yes strong", "Yes"):
        ctx_parts.append("Делают банкеты.")
    if events in ("yes regular", "sometimes", "Yes"):
        ctx_parts.append("Регулярные мероприятия и афиша.")
    ctx_parts.append(f"Что особенного: {special}.")
    ctx_parts.append(f"Демо-сайт: {'готов — ' + demo_url if demo_url else 'в работе, будет скоро'}.")
    ctx = " ".join(ctx_parts)

    vk_prompt = (
        f"{ctx}\n\n"
        f"Напиши короткое сообщение во ВКонтакте на страницу заведения {vk or name}. "
        "До 4 предложений. Заметила что нет своего сайта — только ВКонтакте и Яндекс.Карты. "
        "Предлагаю сделать демо-сайт. Без хэштегов. Начни с «Добрый день!»"
    )
    phone_prompt = (
        f"{ctx}\n\n"
        "Напиши скрипт телефонного разговора на 30-40 секунд. "
        "Представься Леной. Скажи что нашла на Яндекс.Картах — впечатлил высокий рейтинг. "
        "Предложи демо-сайт. Формат: блоки 'Лена:' и 'Если говорят...' (2-3 возражения)."
    )
    email_prompt = (
        f"{ctx}\n\n"
        "Напиши email владельцу. Первая строка: 'Тема: ...'. "
        "Тон дружелюбный но чуть более формальный чем ВК. До 150 слов. "
        "Нашла в Яндекс.Поиске — нет своего сайта. Предлагаю демо. "
        "Подпись: Лена, ВебКузница."
    )

    print(f"    ВКонтакте питч...")
    vk_text = claude(vk_prompt)
    print(f"    Скрипт звонка...")
    phone_text = claude(phone_prompt)
    print(f"    Email...")
    email_text = claude(email_prompt)

    return {"vk": vk_text, "phone": phone_text, "email": email_text}


# ── Card builder ──────────────────────────────────────────────────────────────

def build_card(lead):
    lid = lead["id"]
    name = lead.get("Название", "")
    city_en = sel_val(lead.get("Город"))
    city = CITY_RU.get(city_en, city_en)
    addr = lead.get("Адрес", "")
    phone = lead.get("Телефон ресторана", "")
    vk = lead.get("ВКонтакте", "")
    yandex = lead.get("Ссылка на 2gis или Яндекс", "")
    rating_raw = lead.get("Рейтинг 2gis/Яндекс") or 0
    rating = rating_raw / 10.0 if rating_raw > 10 else float(rating_raw)
    reviews = lead.get("Сколько оценок") or 0
    cuisine = [CUISINE_RU.get(c, c) for c in multi_val(lead.get("Кухня"))]
    avg_check = lead.get("Средний чек, ₽")
    special = lead.get("Что особенного (в 2 предложениях)") or ""
    photo = card_cover(lead.get("Фото") or [])
    demo_url = lead.get("demo_url", "")
    pkg = lead["_package"]
    pitches = lead.get("_pitches", {})
    has_site = sel_val(lead.get("Есть ли свой сайт?") or {})
    banquets = sel_val(lead.get("Банкеты") or {})
    events = sel_val(lead.get("Афиша событий") or {})

    # Badges (combinable)
    badges = []
    if has_site in ("no", "No") or "platform" in has_site.lower():
        badges.append('<span class="badge badge-hot">🔥 Без своего сайта</span>')
    if demo_url:
        badges.append('<span class="badge badge-demo">✅ Демо готово</span>')
    badge = "".join(badges)

    stars = f"★ {rating:.1f}".rstrip("0").rstrip(".")
    photo_style = (
        f'style="background-image:url(\'{h(photo)}\')"' if photo
        else 'style="background:#e8ddd5"'
    )

    phone_href = "".join(c for c in phone if c in "0123456789+")
    vk_short = vk.split("vk.com/")[-1] if vk else ""

    cuisine_str = ", ".join(cuisine)
    check_str = f"{fmtnum(avg_check)} ₽" if avg_check else "не указан"

    # Note badges
    notes = []
    if banquets in ("yes", "yes strong", "Yes"):
        notes.append("🎉 Банкетный зал")
    if events in ("yes regular", "Yes"):
        notes.append("📅 Регулярные мероприятия")
    notes_html = "".join(f'<div class="note-item">{n}</div>' for n in notes)

    # Demo highlight block (prominent CTA above contacts)
    if demo_url:
        demo_hl_html = (
            '<section class="section demo-hl-section">'
            '<div class="demo-hl-block">'
            '<div class="demo-hl-label">'
            '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">'
            '<circle cx="12" cy="12" r="10"/>'
            '<path d="M2 12h20M12 2a15.3 15.3 0 0 1 0 20M12 2a15.3 15.3 0 0 0 0 20"/>'
            '</svg>'
            'Готовое демо для показа клиенту'
            '</div>'
            f'<a href="{h(demo_url)}" target="_blank" rel="noopener" class="demo-open-btn">'
            'Открыть демо ↗'
            '</a>'
            '<div class="demo-hl-footer">'
            f'<button class="copy-url-btn" onclick="copyUrl(\'{h(demo_url)}\', this)">📋 Скопировать ссылку</button>'
            '<span class="demo-hl-hint">Покажи это клиенту в первом разговоре</span>'
            '</div>'
            '</div>'
            '</section>'
        )
    else:
        demo_hl_html = (
            '<section class="section demo-hl-section">'
            '<div class="demo-wip-block">'
            '<span class="demo-wip-icon">⏳</span>'
            '<span>Демо в работе — появится скоро</span>'
            '</div>'
            '</section>'
        )

    # Contact rows
    def info_row(icon, label, inner):
        return (
            '<div class="info-row">'
            f'<span class="info-icon">{icon}</span>'
            '<div>'
            f'<div class="info-label">{label}</div>'
            f'{inner}'
            '</div></div>'
        )

    contact_rows = []
    if addr:
        contact_rows.append(info_row("📍", "Адрес", f'<div class="info-val">{h(addr)}</div>'))
    if phone:
        contact_rows.append(info_row("📞", "Телефон",
            f'<a href="tel:{h(phone_href)}" class="info-link">{h(phone)}</a>'))
    if vk:
        contact_rows.append(info_row("🔵", "ВКонтакте",
            f'<a href="{h(vk)}" target="_blank" class="info-link">vk.com/{h(vk_short)}</a>'))
    if yandex:
        contact_rows.append(info_row("🗺", "Яндекс.Карты",
            f'<a href="{h(yandex)}" target="_blank" class="info-link">Открыть карту ↗</a>'))
    if demo_url:
        contact_rows.append(info_row("🌐", "Демо-сайт",
            f'<a href="{h(demo_url)}" target="_blank" class="demo-link">Открыть демо ↗</a>'))
    else:
        contact_rows.append(info_row("🔧", "Демо-сайт",
            '<div class="demo-wip">В работе — будет скоро</div>'))
    contacts_html = "\n".join(contact_rows)

    # Demo copy block
    demo_copy_html = ""
    if demo_url:
        demo_copy_html = (
            '<div class="pitch-block">'
            '<div class="pitch-title">📤 Ссылка для отправки</div>'
            f'<div class="pitch-text" id="demo-{lid}">{h(demo_url)}</div>'
            f'<button class="copy-btn" onclick="copyText(\'demo-{lid}\')">📋 Скопировать ссылку</button>'
            '</div>'
        )

    # Pitches
    def pitch_block(icon_title, elem_id, text):
        return (
            '<div class="pitch-block">'
            f'<div class="pitch-title">{icon_title}</div>'
            f'<div class="pitch-text" id="{elem_id}">{h(text)}</div>'
            f'<button class="copy-btn" onclick="copyText(\'{elem_id}\')">📋 Скопировать</button>'
            '</div>'
        )

    pitches_html = "\n".join([
        pitch_block("ВКонтакте — сообщение в группу", f"vk-{lid}", pitches.get("vk", "")),
        pitch_block("📞 Скрипт телефонного разговора", f"phone-{lid}", pitches.get("phone", "")),
        pitch_block("✉️ Email-версия", f"email-{lid}", pitches.get("email", "")),
        demo_copy_html,
    ])

    return f"""
  <div class="card" id="card-{lid}">
    <div class="card-hero" {photo_style}>
      <div class="card-hero-overlay">
        <div class="card-badges">{badge}</div>
      </div>
    </div>
    <div class="card-body">
      <div class="card-header-row">
        <div>
          <h2 class="card-title">{h(name)}</h2>
          <div class="card-meta">{h(city)} · {h(cuisine_str)}</div>
        </div>
        <div class="card-rating">
          <span class="stars">{stars}</span>
          <span class="reviews">{fmtnum(reviews)} отз.</span>
        </div>
      </div>
      <div class="pkg-teaser">
        <span class="pkg-name">{h(pkg['name'])}</span>
        <span class="pkg-sep">·</span>
        <span class="pkg-price">{fmtnum(pkg['price'])} ₽</span>
        <span class="pkg-arrow">→</span>
        <span class="pkg-comm">твоих <strong>{fmtnum(pkg['commission'])} ₽</strong></span>
      </div>
      <button class="expand-btn" onclick="toggleLead({lid})">
        <span id="btn-text-{lid}">Открыть детали</span>
        <span id="btn-icon-{lid}">↓</span>
      </button>
    </div>

    <div class="lead-detail" id="detail-{lid}" style="display:none">
      <div class="detail-inner">

        {demo_hl_html}

        <section class="section">
          <h3 class="section-title">Контакты</h3>
          <div class="info-grid">{contacts_html}</div>
        </section>

        <section class="section">
          <h3 class="section-title">Цифры</h3>
          <div class="stats-row">
            <div class="stat-item"><div class="stat-val">{stars}</div><div class="stat-label">Рейтинг</div></div>
            <div class="stat-item"><div class="stat-val">{fmtnum(reviews)}</div><div class="stat-label">Оценок</div></div>
            <div class="stat-item"><div class="stat-val">{h(check_str)}</div><div class="stat-label">Средний чек</div></div>
          </div>
          <div class="notes-list">{notes_html}</div>
        </section>

        <section class="section">
          <h3 class="section-title">🤖 Сильные сигналы</h3>
          <div class="special-text">{h(special)}</div>
        </section>

        <section class="section pkg-section">
          <h3 class="section-title">💰 Рекомендуемый пакет</h3>
          <div class="pkg-detail">
            <div class="pkg-detail-name">{h(pkg['name'])}</div>
            <div class="pkg-detail-row"><span>Цена клиенту</span><strong>{fmtnum(pkg['price'])} ₽</strong></div>
            <div class="pkg-detail-row highlight">
              <span>Твоя комиссия 30%</span>
              <strong class="commission">{fmtnum(pkg['commission'])} ₽</strong>
            </div>
          </div>
        </section>

        <section class="section">
          <h3 class="section-title">💬 Готовые питчи</h3>
          {pitches_html}
        </section>

        <section class="section">
          <h3 class="section-title">📤 Статус</h3>
          <div class="status-row">
            <span id="status-dot-{lid}">🟡</span>
            <span id="status-label-{lid}">Не отправлено</span>
          </div>
          <div class="status-btns">
            <button class="status-btn" onclick="setStatus({lid}, 'sent')">✅ Отметить отправлено</button>
            <button class="status-btn status-btn-reply" onclick="setStatus({lid}, 'replied')">💬 Получен ответ</button>
            <button class="status-btn status-btn-reset" onclick="setStatus({lid}, 'new')">↩ Сбросить</button>
          </div>
        </section>

      </div>
    </div>
  </div>"""


# ── HTML template ─────────────────────────────────────────────────────────────

CSS = """
    :root {
      --cream:   #FFF8F1;
      --card-bg: #FFFFFF;
      --terra:   #C8502A;
      --terra-lt:#F2E5DF;
      --sage:    #5C8C6A;
      --sage-lt: #E3EFE7;
      --text:    #2A2017;
      --muted:   #7A6E65;
      --border:  #EAE0D8;
      --gold:    #C8961E;
    }
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:'Onest',sans-serif;background:var(--cream);color:var(--text);-webkit-font-smoothing:antialiased}

    .hero{background:linear-gradient(135deg,#3D1F0E 0%,#5C2D16 50%,#3D1F0E 100%);color:#FFF8F1;padding:2.5rem 1.5rem 2rem;text-align:center}
    .hero-emoji{font-size:2.5rem;margin-bottom:.5rem}
    .hero-title{font-size:clamp(1.6rem,5vw,2.4rem);font-weight:700;letter-spacing:-.02em;line-height:1.1;margin-bottom:.4rem}
    .hero-sub{font-size:1rem;color:#D4A34A;font-weight:500;margin-bottom:.8rem}
    .hero-date{font-size:.8rem;color:rgba(255,248,241,.5)}

    .stats-bar{display:grid;grid-template-columns:repeat(2,1fr);background:#fff;border-bottom:1px solid var(--border);max-width:860px;margin:0 auto}
    @media(min-width:640px){.stats-bar{grid-template-columns:repeat(4,1fr)}}
    .stat-cell{padding:1rem .75rem;text-align:center;border-right:1px solid var(--border);border-bottom:1px solid var(--border)}
    .stat-cell:last-child{border-right:none}
    .stat-cell .sv{font-size:1.4rem;font-weight:700;color:var(--terra)}
    .stat-cell .sl{font-size:.72rem;color:var(--muted);margin-top:.15rem}

    .main{max-width:860px;margin:0 auto;padding:1.5rem 1rem 4rem}
    .section-header{font-size:1.1rem;font-weight:600;margin:2rem 0 1rem;color:var(--text)}

    .cards-grid{display:grid;grid-template-columns:1fr;gap:1.25rem}
    @media(min-width:640px){.cards-grid{grid-template-columns:1fr 1fr}}

    .card{background:var(--card-bg);border:1px solid var(--border);border-radius:16px;overflow:hidden;box-shadow:0 2px 12px rgba(42,32,23,.06);transition:box-shadow .2s}
    .card:hover{box-shadow:0 4px 20px rgba(42,32,23,.10)}
    .card-hero{height:170px;background-size:cover;background-position:center;position:relative;background-color:var(--terra-lt)}
    .card-hero-overlay{position:absolute;inset:0;background:linear-gradient(to top,rgba(42,32,23,.45) 0%,transparent 50%);display:flex;align-items:flex-start;padding:.75rem}
    .card-badges{display:flex;gap:.4rem;flex-wrap:wrap}
    .badge{font-size:.68rem;font-weight:600;padding:.25rem .6rem;border-radius:100px;letter-spacing:.02em}
    .badge-hot{background:var(--terra);color:white}
    .badge-warm{background:var(--gold);color:white}
    .badge-demo{background:var(--sage);color:white}

    .card-body{padding:1rem 1rem 1.25rem}
    .card-header-row{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:.6rem}
    .card-title{font-size:1.05rem;font-weight:700;line-height:1.25;color:var(--text)}
    .card-meta{font-size:.78rem;color:var(--muted);margin-top:.2rem}
    .card-rating{text-align:right;flex-shrink:0;margin-left:.5rem}
    .stars{font-size:.9rem;font-weight:600;color:var(--gold)}
    .reviews{display:block;font-size:.7rem;color:var(--muted);margin-top:.1rem;white-space:nowrap}

    .pkg-teaser{display:flex;align-items:center;gap:.4rem;flex-wrap:wrap;background:var(--sage-lt);border-radius:8px;padding:.5rem .75rem;margin-bottom:.75rem;font-size:.82rem}
    .pkg-name{font-weight:600;color:var(--sage)}
    .pkg-sep{color:var(--muted)}
    .pkg-price{color:var(--muted)}
    .pkg-arrow{color:var(--muted)}
    .pkg-comm{color:var(--text)}
    .pkg-comm strong{color:var(--terra)}

    .expand-btn{width:100%;background:var(--terra);color:white;border:none;border-radius:10px;padding:.65rem 1rem;font-size:.875rem;font-weight:600;cursor:pointer;font-family:'Onest',sans-serif;display:flex;align-items:center;justify-content:center;gap:.5rem;transition:background .15s,transform .1s}
    .expand-btn:hover{background:#a8401e}
    .expand-btn:active{transform:scale(.98)}

    .lead-detail{border-top:1px solid var(--border)}
    .detail-inner{padding:1.25rem 1rem}
    .section{margin-bottom:1.5rem}
    .section-title{font-size:.8rem;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin-bottom:.75rem;padding-bottom:.4rem;border-bottom:1px solid var(--border)}

    .info-grid{display:flex;flex-direction:column;gap:.65rem}
    .info-row{display:flex;gap:.65rem;align-items:flex-start}
    .info-icon{font-size:1.1rem;flex-shrink:0;width:1.5rem;text-align:center}
    .info-label{font-size:.72rem;color:var(--muted);margin-bottom:.1rem}
    .info-val{font-size:.9rem;color:var(--text)}
    .info-link{font-size:.9rem;color:var(--terra);text-decoration:none}
    .info-link:hover{text-decoration:underline}
    .demo-link{font-size:.9rem;color:var(--sage);font-weight:500;text-decoration:none}
    .demo-link:hover{text-decoration:underline}
    .demo-wip{font-size:.85rem;color:var(--muted);font-style:italic}

    .demo-hl-section{padding-bottom:0}
    .demo-hl-block{background:linear-gradient(135deg,rgba(92,140,106,.08),rgba(92,140,106,.04));border:1.5px solid rgba(92,140,106,.35);border-radius:12px;padding:1.1rem 1rem 1rem;margin-bottom:1.5rem}
    .demo-hl-label{display:flex;align-items:center;gap:.45rem;font-size:.78rem;font-weight:600;color:var(--sage);text-transform:uppercase;letter-spacing:.05em;margin-bottom:.75rem}
    .demo-open-btn{display:block;width:100%;text-align:center;background:transparent;color:var(--terra);border:2px solid var(--terra);border-radius:10px;padding:.8rem 1rem;font-size:.95rem;font-weight:700;text-decoration:none;transition:background .15s,color .15s;letter-spacing:.02em;cursor:pointer}
    .demo-open-btn:hover{background:var(--terra);color:white}
    .demo-hl-footer{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:.5rem;margin-top:.75rem}
    .demo-hl-hint{font-size:.75rem;color:var(--muted);font-style:italic}
    .copy-url-btn{background:var(--terra-lt);color:var(--terra);border:1px solid rgba(200,80,42,.3);border-radius:7px;padding:.35rem .8rem;font-size:.78rem;font-weight:500;cursor:pointer;font-family:'Onest',sans-serif;transition:background .15s;white-space:nowrap}
    .copy-url-btn:hover{background:#e8c4b8}
    .copy-url-btn.copied{background:var(--sage-lt);color:var(--sage);border-color:rgba(92,140,106,.4)}
    .demo-wip-block{display:flex;align-items:center;gap:.5rem;font-size:.88rem;color:var(--muted);font-style:italic;background:var(--cream);border:1px dashed var(--border);border-radius:10px;padding:.85rem 1rem;margin-bottom:1.5rem}
    .demo-wip-icon{font-size:1.1rem}

    .stats-row{display:flex;border:1px solid var(--border);border-radius:10px;overflow:hidden;margin-bottom:.75rem}
    .stat-item{flex:1;text-align:center;padding:.65rem .5rem;border-right:1px solid var(--border)}
    .stat-item:last-child{border-right:none}
    .stat-item .stat-val{font-size:1rem;font-weight:700;color:var(--terra)}
    .stat-item .stat-label{font-size:.68rem;color:var(--muted);margin-top:.1rem}

    .notes-list{display:flex;flex-direction:column;gap:.25rem;margin-top:.5rem}
    .note-item{font-size:.82rem;color:var(--sage)}

    .special-text{font-size:.88rem;color:var(--text);line-height:1.6;background:var(--cream);border-left:3px solid var(--terra);padding:.75rem 1rem;border-radius:0 8px 8px 0;white-space:pre-line}

    .pkg-section .pkg-detail{background:var(--sage-lt);border-radius:10px;padding:.875rem 1rem}
    .pkg-detail-name{font-size:1rem;font-weight:700;color:var(--sage);margin-bottom:.5rem}
    .pkg-detail-row{display:flex;justify-content:space-between;font-size:.88rem;color:var(--muted);margin-top:.3rem}
    .pkg-detail-row.highlight{margin-top:.5rem;padding-top:.5rem;border-top:1px solid rgba(92,140,106,.3);color:var(--text)}
    .commission{color:var(--terra)!important;font-size:1.1rem}

    .pitch-block{background:var(--cream);border:1px solid var(--border);border-radius:10px;padding:.875rem 1rem;margin-bottom:.875rem}
    .pitch-title{font-size:.82rem;font-weight:600;color:var(--muted);margin-bottom:.6rem}
    .pitch-text{font-size:.875rem;color:var(--text);line-height:1.6;white-space:pre-line;margin-bottom:.6rem}
    .copy-btn{background:var(--terra-lt);color:var(--terra);border:1px solid rgba(200,80,42,.3);border-radius:7px;padding:.4rem .9rem;font-size:.8rem;font-weight:500;cursor:pointer;font-family:'Onest',sans-serif;transition:background .15s}
    .copy-btn:hover{background:#e8c4b8}
    .copy-btn.copied{background:var(--sage-lt);color:var(--sage);border-color:rgba(92,140,106,.4)}

    .status-row{display:flex;align-items:center;gap:.5rem;font-size:.9rem;margin-bottom:.75rem}
    .status-btns{display:flex;flex-wrap:wrap;gap:.5rem}
    .status-btn{background:white;border:1px solid var(--border);border-radius:8px;padding:.45rem .85rem;font-size:.8rem;font-weight:500;cursor:pointer;font-family:'Onest',sans-serif;color:var(--text);transition:all .15s}
    .status-btn:hover{border-color:var(--terra);color:var(--terra)}
    .status-btn-reply:hover{border-color:var(--sage);color:var(--sage)}
    .status-btn-reset:hover{border-color:var(--muted);color:var(--muted)}

    .pricing-section{margin-top:3rem;padding-top:2rem;border-top:2px solid var(--border)}
    .pricing-section h2{font-size:1.25rem;font-weight:700;margin-bottom:1.25rem}
    .pkg-cards{display:grid;grid-template-columns:1fr;gap:1rem}
    @media(min-width:640px){.pkg-cards{grid-template-columns:repeat(3,1fr)}}
    .pkg-card{background:white;border:1px solid var(--border);border-radius:14px;padding:1.25rem 1rem}
    .pkg-card.featured{border-color:var(--terra);border-width:2px}
    .pkg-card-name{font-size:1rem;font-weight:700;margin-bottom:.3rem}
    .pkg-card-price{font-size:1.1rem;font-weight:700;color:var(--terra);margin-bottom:.25rem}
    .pkg-card-comm{font-size:.82rem;color:var(--sage);font-weight:600;margin-bottom:.75rem}
    .pkg-card-features{list-style:none;padding:0}
    .pkg-card-features li{font-size:.8rem;color:var(--muted);padding:.2rem 0 .2rem 1.2rem;position:relative}
    .pkg-card-features li::before{content:"•";position:absolute;left:0;color:var(--terra)}
    .pkg-card-note{font-size:.75rem;margin-top:.5rem}
    .pkg-card-note.warn{color:var(--muted);font-style:italic}
    .pkg-card-note.good{color:var(--sage)}

    .tips-section{margin-top:2.5rem}
    .tips-section h2{font-size:1.1rem;font-weight:700;margin-bottom:1rem}
    .tips-grid{display:grid;grid-template-columns:1fr;gap:.75rem}
    @media(min-width:640px){.tips-grid{grid-template-columns:1fr 1fr}}
    .tip-block{background:white;border:1px solid var(--border);border-radius:12px;padding:1rem}
    .tip-block h4{font-size:.85rem;font-weight:700;margin-bottom:.5rem}
    .tip-block ul{list-style:none;padding:0}
    .tip-block li{font-size:.82rem;color:var(--muted);padding:.15rem 0 .15rem 1.3rem;position:relative}
    .tip-block li::before{content:attr(data-b);position:absolute;left:0}

    .footer{text-align:center;padding:2rem 1rem;border-top:1px solid var(--border);margin-top:2rem;font-size:.82rem;color:var(--muted)}
    .footer a{color:var(--terra);text-decoration:none}

    .toast{position:fixed;bottom:1.5rem;left:50%;transform:translateX(-50%);background:#2A2017;color:white;padding:.6rem 1.2rem;border-radius:100px;font-size:.85rem;opacity:0;transition:opacity .2s;pointer-events:none;z-index:999}
    .toast.show{opacity:1}
"""

JS_TEMPLATE = """
function toggleLead(id) {
  const d = document.getElementById('detail-' + id);
  const t = document.getElementById('btn-text-' + id);
  const ic = document.getElementById('btn-icon-' + id);
  const open = d.style.display !== 'none';
  d.style.display = open ? 'none' : 'block';
  t.textContent = open ? 'Открыть детали' : 'Закрыть';
  ic.textContent = open ? '↓' : '↑';
}
function copyUrl(url, btn) {
  const doMark = () => {
    btn.textContent = '✓ Скопировано';
    btn.classList.add('copied');
    setTimeout(() => { btn.textContent = '📋 Скопировать ссылку'; btn.classList.remove('copied'); }, 2000);
    showToast('Скопировано ✓');
  };
  navigator.clipboard.writeText(url).then(doMark).catch(() => {
    const tmp = document.createElement('textarea');
    tmp.value = url; document.body.appendChild(tmp); tmp.select();
    document.execCommand('copy'); document.body.removeChild(tmp); doMark();
  });
}
function copyText(id) {
  const el = document.getElementById(id);
  const text = el.textContent;
  const btn = el.nextElementSibling;
  const doMark = () => {
    if (btn && btn.classList.contains('copy-btn')) {
      btn.textContent = '✓ Скопировано';
      btn.classList.add('copied');
      setTimeout(() => { btn.textContent = '📋 Скопировать'; btn.classList.remove('copied'); }, 2000);
    }
    showToast('Скопировано!');
  };
  navigator.clipboard.writeText(text).then(doMark).catch(() => {
    const r = document.createRange(); r.selectNodeContents(el);
    window.getSelection().removeAllRanges(); window.getSelection().addRange(r);
    document.execCommand('copy'); doMark();
  });
}
const STATUS_META = {
  new:     { dot: '🟡', label: 'Не отправлено' },
  sent:    { dot: '🟢', label: 'Питч отправлен' },
  replied: { dot: '✅', label: 'Ответ получен'  }
};
function setStatus(id, s) {
  localStorage.setItem('lena_status_' + id, s);
  applyStatus(id, s);
  updateSentCount();
}
function applyStatus(id, s) {
  const m = STATUS_META[s] || STATUS_META.new;
  document.getElementById('status-dot-' + id).textContent = m.dot;
  document.getElementById('status-label-' + id).textContent = m.label;
}
function updateSentCount() {
  const ids = LEAD_IDS;
  let c = 0;
  ids.forEach(id => { const s = localStorage.getItem('lena_status_' + id); if (s && s !== 'new') c++; });
  document.getElementById('stat-sent-val').textContent = c;
}
function initStatuses() {
  const ids = LEAD_IDS;
  ids.forEach(id => { applyStatus(id, localStorage.getItem('lena_status_' + id) || 'new'); });
  updateSentCount();
}
function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg; t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 1800);
}
document.addEventListener('DOMContentLoaded', initStatuses);
"""


def render_html(leads_data):
    now_dt = datetime.now()
    months = ["января","февраля","марта","апреля","мая","июня",
              "июля","августа","сентября","октября","ноября","декабря"]
    now_str = f"{now_dt.day} {months[now_dt.month - 1]} {now_dt.year}"

    total = len(leads_data)
    demos_ready = sum(1 for l in leads_data if l.get("demo_url"))
    commissions = [l["_package"]["commission"] for l in leads_data]
    total_comm = sum(commissions)
    comm_range = f"{fmtnum(total_comm)} ₽"

    cards_html = "\n".join(build_card(l) for l in leads_data)
    lead_ids_json = json.dumps([l["id"] for l in leads_data])
    js = JS_TEMPLATE.replace("LEAD_IDS", lead_ids_json)

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>Лена · Лиды ВебКузница</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Onest:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com"></script>
  <style>{CSS}</style>
</head>
<body>

<div class="hero">
  <div class="hero-emoji">🤝</div>
  <h1 class="hero-title">Лен, держи лиды!</h1>
  <div class="hero-sub">Твоя комиссия 30% с каждой продажи</div>
  <div class="hero-date">Обновлено: {now_str}</div>
</div>

<div class="stats-bar">
  <div class="stat-cell"><div class="sv">{total}</div><div class="sl">Всего лидов</div></div>
  <div class="stat-cell"><div class="sv">{demos_ready}</div><div class="sl">Готовых демо</div></div>
  <div class="stat-cell"><div class="sv" id="stat-sent-val">0</div><div class="sl">Отправлено</div></div>
  <div class="stat-cell"><div class="sv" style="font-size:1rem">{comm_range}</div><div class="sl">Потенц. комиссия</div></div>
</div>

<div class="main">
  <div class="section-header">🔥 Лиды в работе</div>
  <div class="cards-grid">
{cards_html}
  </div>

  <div class="pricing-section">
    <h2>🪟 Что мы продаём</h2>
    <div class="pkg-cards">
      <div class="pkg-card">
        <div class="pkg-card-name">Витрина</div>
        <div class="pkg-card-price">10 000 ₽ <span style="font-size:.75rem;color:var(--muted)">Коломна</span></div>
        <div class="pkg-card-comm">Твоих: 3 000 (Кол.) · 4 500 (Мск.)</div>
        <ul class="pkg-card-features">
          <li>Лендинг, мобайл</li>
          <li>Карта Яндекс</li>
          <li>Кнопка «Позвонить»</li>
          <li>Иконка ВКонтакте</li>
          <li>Базовое SEO</li>
          <li>1 раунд правок</li>
        </ul>
        <div class="pkg-card-note warn">⚠️ Хостинг и домен — клиент сам</div>
      </div>
      <div class="pkg-card featured">
        <div class="pkg-card-name">Витрина+ ⭐</div>
        <div class="pkg-card-price">15 000 ₽ <span style="font-size:.75rem;color:var(--muted)">Коломна</span></div>
        <div class="pkg-card-comm">Твоих: 4 500 (Кол.) · 6 000 (Мск.)</div>
        <ul class="pkg-card-features">
          <li>Всё из Витрины</li>
          <li>Галерея фото</li>
          <li>Меню (PDF / блок)</li>
          <li>Форма бронирования → email</li>
          <li>3 цитаты отзывов + Яндекс</li>
          <li>RU + EN версии</li>
          <li>Schema.org микроразметка</li>
          <li>Яндекс.Метрика</li>
          <li>2 раунда правок</li>
        </ul>
        <div class="pkg-card-note good">✅ Хостинг 1 год — продлеваем мы</div>
      </div>
      <div class="pkg-card">
        <div class="pkg-card-name">Гость</div>
        <div class="pkg-card-price">20 000 ₽ <span style="font-size:.75rem;color:var(--muted)">Коломна</span></div>
        <div class="pkg-card-comm">Твоих: 6 000 (Кол.) · 7 500 (Мск.)</div>
        <ul class="pkg-card-features">
          <li>Всё из Витрины+</li>
          <li>Система бронирования + админ</li>
          <li>Виджет Яндекс.Карт live</li>
          <li>Лента ВКонтакте</li>
          <li>Спецстраница (банкеты/меню)</li>
          <li>Email-уведомления о бронях</li>
          <li>Локальное SEO для туристов</li>
          <li>3 раунда правок</li>
        </ul>
      </div>
    </div>
  </div>

  <div class="tips-section">
    <h2>💡 Важные напоминания</h2>
    <div class="tips-grid">
      <div class="tip-block">
        <h4>⚠️ При разговоре с клиентами</h4>
        <ul>
          <li data-b="·">Не упоминай Telegram и Instagram как каналы для бизнеса</li>
          <li data-b="·">Цены не озвучивай в первом разговоре</li>
          <li data-b="·">Сначала покажи демо — заинтересуй, цена потом</li>
        </ul>
      </div>
      <div class="tip-block">
        <h4>🎯 Хорошие лиды</h4>
        <ul>
          <li data-b="✓">Нет своего сайта (только Яндекс.Карты, ВК)</li>
          <li data-b="✓">Активный постинг в ВКонтакте</li>
          <li data-b="✓">Рейтинг 4.5+</li>
          <li data-b="✓">Туристическая локация</li>
          <li data-b="✓">Уникальная концепция</li>
        </ul>
      </div>
      <div class="tip-block">
        <h4>❌ Плохие лиды</h4>
        <ul>
          <li data-b="×">Сетевые места (Шоколадница, Якитория)</li>
          <li data-b="×">Низкий рейтинг (ниже 4.0)</li>
          <li data-b="×">Закрылись или редко работают</li>
        </ul>
      </div>
      <div class="tip-block">
        <h4>📱 Где искать лиды</h4>
        <ul>
          <li data-b="→">Яндекс.Карты — рестораны рядом</li>
          <li data-b="→">2ГИС — вкладка «Где поесть»</li>
          <li data-b="→">ВКонтакте — группы «Коломна еда»</li>
          <li data-b="→">Прогулки — замечай вывески без сайта</li>
        </ul>
      </div>
    </div>
  </div>
</div>

<div class="footer">
  Виктория · ВебКузница ·
  <a href="tel:+393513904408">+39 351 390 4408</a> ·
  <a href="https://vk.com/vebkuznitsa" target="_blank">vk.com/vebkuznitsa</a>
</div>

<div class="toast" id="toast"></div>

<script>
{js}
</script>
</body>
</html>"""


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("🚀 ВебКузница · Генератор дашборда Лены")
    print("=" * 45)

    print("\n📦 Загружаем лиды из Baserow...")
    raw_leads = fetch_leads()
    print(f"   Найдено: {len(raw_leads)} лидов")

    leads_data = []
    for lead in raw_leads:
        city_en = sel_val(lead.get("Город"))
        avg_check = lead.get("Средний чек, ₽") or 0
        lead["_package"] = recommend_package(city_en, avg_check)
        lead["demo_url"] = DEMO_URLS.get(lead.get("id", 0), lead.get("demo_url", ""))
        leads_data.append(lead)

    print("\n🤖 Генерируем питчи через Claude...")
    for lead in leads_data:
        name = lead.get("Название", "")
        print(f"\n  «{name}»:")
        lead["_pitches"] = generate_pitches(lead)

    print("\n🎨 Рендерим HTML...")
    content = render_html(leads_data)

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(content, encoding="utf-8")
    print(f"   ✅ Сохранено: {OUT_FILE}")
    print(f"\n🌐 URL: https://viktorialiubitskaya-coder.github.io/vebkuznitsa/lena/")
    print(f"\n📋 Повторная генерация: python3 build_lena_dashboard.py\n")


if __name__ == "__main__":
    main()
