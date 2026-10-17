{# 
  Override dbt's default schema-naming behavior.
 
  By default, dbt concatenates the profile's target schema with any
  model-level `+schema:` config (e.g. "marts" + "staging" ->
  "marts_staging"). That's a safety default for multi-environment
  setups, but here it just creates datasets that don't match what
  Terraform provisioned. This override makes a model's custom schema
  the ACTUAL dataset name, with no prefix -- so +schema: staging goes
  to the `staging` dataset, +schema: marts goes to `marts`, exactly as
  created in terraform/main.tf.
#}
 
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
 