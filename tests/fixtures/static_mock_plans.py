"""tests/fixtures/static_mock_plans.py

Static mock plan dictionaries migrated from scene_planner.py for testing fixtures.
All production planning code in engine/director/scene_planner.py is 100% data-driven.
"""

INNGEST_FIXTURE_SCENES = {
    "b1_items": [
        {"label": "Step 1", "detail": "fetch-billing (Completed)", "status": "done"},
        {"label": "Step 2", "detail": "charge-customer (503 Crash)", "status": "crashed"},
        {"label": "Naive Retry", "detail": "Re-runs Step 1 & Double-Charges", "status": "duplicate_risk"},
    ],
    "b3_entities": [
        {"id": "step_1", "label": "step.run('fetch-billing-data')"},
        {"id": "step_2", "label": "step.run('charge-customer')"},
    ],
    "b3_events": [
        {"target": "step_1", "action": "start", "label": "Executing Step 1"},
        {"target": "step_1", "action": "succeed", "label": "Result Saved & Memoized"},
        {"target": "step_2", "action": "start", "label": "Executing Step 2"},
        {"target": "step_2", "action": "fail", "label": "Network Error: 503"},
        {"target": "step_2", "action": "retry", "label": "Retry #1 (Reusing Step 1 State)"},
        {"target": "step_2", "action": "recover", "label": "Step 2 Succeeded"},
    ],
}

STRIPE_FIXTURE_SCENES = {
    "b1_items": [
        {"label": "Request #1", "detail": "POST /v1/charges (Timeout)", "status": "crashed"},
        {"label": "Network Drop", "detail": "Client receives no response", "status": "warning"},
        {"label": "Blind Retry", "detail": "Blind retry charges customer twice", "status": "duplicate_risk"},
    ],
    "b3_entities": [
        {
            "id": "req_1",
            "label": "POST /v1/payment_intents (Key: order_123)",
            "sub_label": "Initial Request: Process & Save State",
            "memoized_detail": "Payment API: Response cached • 0 duplicate charges",
        },
        {
            "id": "req_2",
            "label": "POST /v1/payment_intents (Key: order_123)",
            "sub_label": "Retried Request: Network Timeout Recovery",
        },
    ],
    "b3_events": [
        {"target": "req_1", "action": "start", "label": "Sending Initial Request"},
        {"target": "req_1", "action": "succeed", "label": "200 OK — Response Cached"},
        {"target": "req_2", "action": "start", "label": "Connection Dropped / Timeout"},
        {"target": "req_2", "action": "fail", "label": "Client Network Timeout"},
        {"target": "req_2", "action": "retry", "label": "Retry #1 — Reusing Same Key"},
        {"target": "req_2", "action": "recover", "label": "200 OK — Cached Response Reused"},
    ],
}

