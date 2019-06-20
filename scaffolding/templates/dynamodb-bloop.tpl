{% block header %}from bloop import BaseModel, Column, Engine{% if bloop_types %}
from bloop.types import ({% for t in bloop_types|sort %}
    {{ t }},{% endfor %}
){% endif %}


engine = Engine()
{% endblock %}

{% block model %}class {{ model.name }}(BaseModel):{% for field_name, field in model.fields.items() %}
    {{ field_name }} = Column({{ typedefs[field_name] }}{% if field.kwargs %}, {% for k, v in field.kwargs.items() %}{{ k }}={{ v|python }}{{ ", " if not loop.last }}{% endfor %}{% endif %}){% endfor %}
{% endblock %}
