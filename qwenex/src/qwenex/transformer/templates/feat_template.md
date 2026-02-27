# FEAT-{{ number }}: {{ title }}

**URI:** spec://{{ module }}/FEAT-{{ number }}
**Версия:** 0.1.0 · **Статус:** Черновик

---

## 1. Цель

{{ goal }}

---

## 2. Пользовательские сценарии

{% for scenario in scenarios %}
- **Сценарий {{ loop.index }}:** {{ scenario }}
{% endfor %}

---

## 3. Функциональные требования

{% for req in requirements %}
### 3.{{ loop.index }} {{ req.name }}

{{ req.description }}

**Почему:** {{ req.why }}
{% endfor %}

---

## 4. Out of scope

{% for item in out_of_scope %}
- {{ item }}
{% endfor %}

---

## 5. Тестовые сценарии

{% for test in tests %}
- `{{ test.name }}`: {{ test.description }}
{% endfor %}
