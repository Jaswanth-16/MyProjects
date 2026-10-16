-- Replace workspace.caselake_demo with your actual catalog and schema.
SELECT category, priority_number, ticket_count
FROM workspace.caselake_demo.gold_ticket_metrics
ORDER BY ticket_count DESC;

SELECT suggested_category, needs_review, COUNT(*) AS tickets,
       ROUND(AVG(confidence), 3) AS average_model_confidence
FROM workspace.caselake_demo.gold_ai_suggestions
GROUP BY suggested_category, needs_review;

-- Gold AI rows retain both source event ID and MLflow run ID for traceability.
SELECT s.ticket_id, s.category AS recorded_category,
       p.suggested_category, p.confidence, p.model_run_id
FROM workspace.caselake_demo.silver_tickets s
JOIN workspace.caselake_demo.gold_ai_suggestions p
  ON s.ticket_id = p.ticket_id AND s.event_id = p.event_id
WHERE p.needs_review = true;

DESCRIBE HISTORY workspace.caselake_demo.bronze_ticket_events;
