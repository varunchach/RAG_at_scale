import pytest

from src.observability.evals import EvalPayload, LLMJudgeEvaluator


@pytest.fixture
def sample_payload():
    return EvalPayload(
        request_id="req-123",
        route="search",
        query="Who approved Project Meridian and what failed in Zurich?",
        answer="Aisha Raman approved Project Meridian, and the Zurich mirror lagged by 11 minutes.",
        chunks=[
            {
                "doc_id": "chunk-1",
                "content": "Aisha Raman approved Project Meridian, and the Zurich mirror lagged by 11 minutes.",
            }
        ],
        retrieval_count=3,
        reranked_count=1,
        search_time=0.12,
        rerank_time=0.03,
        answer_time=0.4,
        total_time=0.52,
    )


def test_extract_json_handles_wrapped_text():
    evaluator = LLMJudgeEvaluator()
    parsed = evaluator._extract_json(
        "Here is the result:\n"
        '{"faithfulness":0.9,"context_precision":0.8,"context_coverage":0.7,"answer_relevancy":0.95,'
        '"judge_verdict":"Grounded","reasoning":"Supported by the supplied chunk."}\n'
        "Done."
    )
    assert parsed["faithfulness"] == 0.9
    assert parsed["judge_verdict"] == "Grounded"


def test_evaluate_and_record_swallows_judge_failures(sample_payload, monkeypatch):
    monkeypatch.setenv("ENABLE_LLM_JUDGE_EVALS", "true")
    monkeypatch.setenv("EVAL_SAMPLE_RATE", "1.0")

    evaluator = LLMJudgeEvaluator()
    failure_calls = []
    sample_calls = []

    monkeypatch.setattr(evaluator, "evaluate", lambda payload: (_ for _ in ()).throw(RuntimeError("judge failed")))
    monkeypatch.setattr("src.observability.evals.metrics.publish_eval_sample_count", lambda route: sample_calls.append(route))
    monkeypatch.setattr("src.observability.evals.metrics.publish_judge_failure", lambda route: failure_calls.append(route))

    result = evaluator.evaluate_and_record(sample_payload)

    assert result is None
    assert sample_calls == ["search"]
    assert failure_calls == ["search"]
