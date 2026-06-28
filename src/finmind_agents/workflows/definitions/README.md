# Workflow Definitions

YAML workflow definitions are the machine-readable execution contracts for
FinMind workflows. They declare supported markets, required inputs, required
datasets, ordered stages, output sections, citation policy, chart requirements,
and referenced Markdown agent skills.

The guarded Python runtime loads these definitions before execution. Agent skills
may guide analysis behavior, but the YAML definition remains the contract used by
the API, UI catalog, validation, and future external adapters.
