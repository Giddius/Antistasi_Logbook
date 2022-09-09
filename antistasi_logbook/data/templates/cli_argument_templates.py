

ARG_DOC_MARKDOWN_TEMPLATE = """

# {name}

---

# Description


> {help_text}

---

# Arguments

{argument_strings}

---

# Default

{default_value}

---

# Required

{is_required}

---

# Flag

{is_flag}


""".strip()


ARG_DOC_HTML_TEMPLATE: str = """



<a id="{{name}}"><b><u>{{name}}</b></u></a>

<dl>
<dt>Description</dt>
<dd>
<blockquote>
<div class="description">
{{help_text}}
</div>
</blockquote>

</dd>

<dt>Arguments</dt>
<dd>
<ul>
{%for arg in argument_strings%}
<li> <pre><code>{{arg}}</code></pre>
{% endfor %}
</ul>
</dd>
{% if default_value is not none %}
<dt>Default</dt>
<dd>{{default_value}}</dd>
{% endif %}
<dt>Required</dt>
<dd>{{is_required}}</dd>

<dt>Flag</dt>
<dd>{{is_flag}}</dd>
</dl>

"""
