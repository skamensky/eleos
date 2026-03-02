BEGIN;

DELETE FROM experiment.playbook_steps
WHERE playbook_fk IN (
    SELECT id
    FROM experiment.playbooks
    WHERE playbook_id IN (
        'incident_support_supabase',
        'billing_support_supabase',
        'general_support_supabase'
    )
      AND version = '1.0.0'
);

DELETE FROM experiment.playbooks
WHERE playbook_id IN (
    'incident_support_supabase',
    'billing_support_supabase',
    'general_support_supabase'
)
  AND version = '1.0.0';

WITH incident AS (
    INSERT INTO experiment.playbooks (
        playbook_id,
        version,
        title,
        status,
        enforcement_mode,
        applicable_case_classes,
        objective_template,
        created_by
    ) VALUES (
        'incident_support_supabase',
        '1.0.0',
        'Incident Support (Supabase)',
        'active',
        'suggestive',
        ARRAY['incident'],
        'Investigate incident objective: {{ objective }}',
        'test_env_supabase'
    )
    RETURNING id
)
INSERT INTO experiment.playbook_steps (
    playbook_fk,
    step_order,
    step_id,
    name,
    goal,
    tool_selector,
    required,
    order_constraint,
    preconditions,
    expected_evidence,
    completion_check,
    failure_action
)
SELECT
    incident.id,
    steps.step_order,
    steps.step_id,
    steps.name,
    steps.goal,
    steps.tool_selector,
    steps.required,
    steps.order_constraint,
    steps.preconditions,
    steps.expected_evidence,
    steps.completion_check,
    steps.failure_action
FROM incident
CROSS JOIN (
    VALUES
        (
            1,
            'log_signal',
            'Collect log signal',
            'Find dominant failure signatures in support logs',
            'supabase/log_scan',
            TRUE,
            'sequential',
            ARRAY[]::text[],
            'Top error signatures and timing clusters',
            'At least one dominant failure signature is identified',
            'branch'
        ),
        (
            2,
            'function_health',
            'Inspect function runtime health',
            'Correlate failures with function run status and latency',
            'supabase/function_runs',
            TRUE,
            'sequential',
            ARRAY[]::text[],
            'Function error classes and latency anomalies',
            'At least one likely failing runtime component is identified',
            'branch'
        ),
        (
            3,
            'access_path',
            'Inspect access path denials',
            'Assess policy and access-control contribution',
            'supabase/access_path_explain',
            FALSE,
            'sequential',
            ARRAY[]::text[],
            'Denied paths and likely policy causes',
            'Policy contribution has been assessed',
            'branch'
        ),
        (
            4,
            'meta_inspect',
            'Inspect metadata surface',
            'Check table/column/index metadata for drift signals',
            'supabase/metadata_api_inspect',
            FALSE,
            'sequential',
            ARRAY[]::text[],
            'Metadata signals relevant to incident',
            'Metadata drift contribution has been assessed',
            'branch'
        )
) AS steps (
    step_order,
    step_id,
    name,
    goal,
    tool_selector,
    required,
    order_constraint,
    preconditions,
    expected_evidence,
    completion_check,
    failure_action
);

WITH billing AS (
    INSERT INTO experiment.playbooks (
        playbook_id,
        version,
        title,
        status,
        enforcement_mode,
        applicable_case_classes,
        objective_template,
        created_by
    ) VALUES (
        'billing_support_supabase',
        '1.0.0',
        'Billing Support (Supabase)',
        'active',
        'suggestive',
        ARRAY['billing'],
        'Investigate billing objective: {{ objective }}',
        'test_env_supabase'
    )
    RETURNING id
)
INSERT INTO experiment.playbook_steps (
    playbook_fk,
    step_order,
    step_id,
    name,
    goal,
    tool_selector,
    required,
    order_constraint,
    preconditions,
    expected_evidence,
    completion_check,
    failure_action
)
SELECT
    billing.id,
    steps.step_order,
    steps.step_id,
    steps.name,
    steps.goal,
    steps.tool_selector,
    steps.required,
    steps.order_constraint,
    steps.preconditions,
    steps.expected_evidence,
    steps.completion_check,
    steps.failure_action
FROM billing
CROSS JOIN (
    VALUES
        (
            1,
            'readonly_sql_driver',
            'Query cost/usage driver via read-only SQL',
            'Extract top usage and spend drivers from support datasets',
            'supabase/sql_readonly',
            TRUE,
            'sequential',
            ARRAY[]::text[],
            'Top spend/usage contributors and deltas',
            'Top cost/usage driver is identified',
            'branch'
        ),
        (
            2,
            'function_context',
            'Check function context',
            'Correlate billing anomalies with function failures/retries',
            'supabase/function_runs',
            FALSE,
            'sequential',
            ARRAY[]::text[],
            'Function-level contributors to billing anomaly',
            'Function contribution to billing anomaly is assessed',
            'branch'
        ),
        (
            3,
            'log_context',
            'Check log context',
            'Correlate error bursts with usage spikes',
            'supabase/log_scan',
            FALSE,
            'sequential',
            ARRAY[]::text[],
            'Log evidence aligned to usage anomaly windows',
            'Log contribution to billing anomaly is assessed',
            'branch'
        )
) AS steps (
    step_order,
    step_id,
    name,
    goal,
    tool_selector,
    required,
    order_constraint,
    preconditions,
    expected_evidence,
    completion_check,
    failure_action
);

WITH general AS (
    INSERT INTO experiment.playbooks (
        playbook_id,
        version,
        title,
        status,
        enforcement_mode,
        applicable_case_classes,
        objective_template,
        created_by
    ) VALUES (
        'general_support_supabase',
        '1.0.0',
        'General Support (Supabase)',
        'active',
        'suggestive',
        ARRAY['general'],
        'Investigate support objective: {{ objective }}',
        'test_env_supabase'
    )
    RETURNING id
)
INSERT INTO experiment.playbook_steps (
    playbook_fk,
    step_order,
    step_id,
    name,
    goal,
    tool_selector,
    required,
    order_constraint,
    preconditions,
    expected_evidence,
    completion_check,
    failure_action
)
SELECT
    general.id,
    steps.step_order,
    steps.step_id,
    steps.name,
    steps.goal,
    steps.tool_selector,
    steps.required,
    steps.order_constraint,
    steps.preconditions,
    steps.expected_evidence,
    steps.completion_check,
    steps.failure_action
FROM general
CROSS JOIN (
    VALUES
        (
            1,
            'baseline_logs',
            'Collect baseline logs',
            'Establish first high-signal error indicators',
            'supabase/log_scan',
            TRUE,
            'sequential',
            ARRAY[]::text[],
            'Top anomalies and failure hints',
            'At least one actionable hypothesis is available',
            'branch'
        ),
        (
            2,
            'auth_timeline',
            'Inspect auth timeline',
            'Assess session/provider issues contribution',
            'supabase/auth_timeline',
            FALSE,
            'sequential',
            ARRAY[]::text[],
            'Auth/session event correlation',
            'Auth contribution has been assessed',
            'branch'
        ),
        (
            3,
            'access_path',
            'Inspect access path',
            'Assess deny/policy contributions for general issue',
            'supabase/access_path_explain',
            FALSE,
            'sequential',
            ARRAY[]::text[],
            'Access-path denial correlation',
            'Access contribution has been assessed',
            'branch'
        ),
        (
            4,
            'meta_inspect',
            'Inspect metadata API surface',
            'Assess metadata drift or schema signal',
            'supabase/metadata_api_inspect',
            FALSE,
            'sequential',
            ARRAY[]::text[],
            'Metadata drift indicators',
            'Metadata contribution has been assessed',
            'branch'
        )
) AS steps (
    step_order,
    step_id,
    name,
    goal,
    tool_selector,
    required,
    order_constraint,
    preconditions,
    expected_evidence,
    completion_check,
    failure_action
);

COMMIT;
