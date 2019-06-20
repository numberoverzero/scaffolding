{% block header %}
from sqlalchemy import Column, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker{% if type_imports %}
from sqlalchemy.types import ({% for t in type_imports|sort %}
    {{ t }},{% endfor %}
){% endif %}


engine = create_engine("sqlite:///:memory:", echo=True)
Base = declarative_base()
Session = sessionmaker(bind=engine)
# to create tables, use Base.metadata.create_all(engine)
{% endblock %}


{% block model %}
class {{ model.name }}(Base):{% for field_name, field in model.fields.items() %}
    {{ field_name }} = Column({{ typedefs[field_name] }}{% if field.kwargs %}, {% for k, v in field.kwargs.items() %}{{ k }}={{ v|python }}{{ ", " if not loop.last }}{% endfor %}{% endif %}){% endfor %}
{% endblock %}
