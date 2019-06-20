{% block header %}
from bloop import BaseModel, Column, Engine{% if type_imports %}
from bloop.types import ({% for t in type_imports|sort %}
    {{ t }},{% endfor %}
){% endif %}


engine = Engine()
# to create tables, use engine.bind(BaseModel)
{% endblock %}


{% block model %}
class {{ model.name }}(BaseModel):{% for field_name, field in model.fields.items() %}
    {{ field_name }} = Column({{ typedefs[field_name] }}{% if field.kwargs %}, {% for k, v in field.kwargs.items() %}{{ k }}={{ v|python }}{{ ", " if not loop.last }}{% endfor %}{% endif %}){% endfor %}
{% endblock %}
