# PROP-{{ number }}: {{ title }}

**URI:** spec://{{ module }}/PROP-{{ number }}
**Версия:** 0.1.0 · **Статус:** Черновик

---

## 1. Решение

{{ decision }}

---

## 2. Альтернативы

{% for alt in alternatives %}
### {{ alt.name }}

{{ alt.description }}

**Почему не выбрали:** {{ alt.why_rejected }}
{% endfor %}

---

## 3. Последствия

{{ consequences }}
