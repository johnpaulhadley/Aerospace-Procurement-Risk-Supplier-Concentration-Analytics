{# Category group for a Product or Service Code.
   Products (codes starting with a digit) group on the first two characters.
   Research and development (codes starting with A) also group on two characters,
   which separates defense R&D from space R&D.
   All other services group on their first letter, the service category. #}
{% macro psc_group(code) -%}
    case
        when {{ code }} ~ '^[B-Z]' then left({{ code }}, 1)
        else left({{ code }}, 2)
    end
{%- endmacro %}
