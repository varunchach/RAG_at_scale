import json
import logging
import os
import random
from dataclasses import dataclass
from typing import Any

import boto3

from .logging_config import log_eval_failure, log_eval_result
from .metrics import metrics

logger = logging.getLogger(__name__)

_DEFAULT_JUDGE_MODEL = "us.anthropic.claude-haiku-4-5-20251001-v1:0"


@dataclass(slots=True)
class EvalPayload:
    request_id: str
    route: str
    query: str
    answer: str | None
    chunks: list[dict[str, Any]]
    retrieval_count: int
    reranked_count: int
    search_time: float
    rerank_time: float | None
    answer_time: float | None
    total_time: float


class LLMJudgeEvaluator:
    def __init__(self):
        self._bedrock = None

    def enabled(self) -> bool:
        return os.environ.get("ENABLE_LLM_JUDGE_EVALS", "false").lower() == "true"

    def sample_rate(self) -> float:
        try:
            value = float(os.environ.get("EVAL_SAMPLE_RATE", "0.1"))
        except ValueError:
            value = 0.0
        return min(max(value, 0.0), 1.0)

    def should_sample(self, payload: EvalPayload) -> bool:
        if not self.enabled() or not payload.answer or not payload.chunks:
            return False
        return random.random() < self.sample_rate()

    def _judge_model_id(self) -> str:
        return os.environ.get("EVAL_JUDGE_MODEL_ID") or os.environ.get("BEDROCK_MODEL_ID") or _DEFAULT_JUDGE_MODEL

    def _get_bedrock_client(self):
        if self._bedrock is None:
            self._bedrock = boto3.client(
                "bedrock-runtime",
                region_name=os.environ.get("AWS_REGION", "us-east-1"),
            )
        return self._bedrock

    def _trim_chunks(self, chunks: list[dict[str, Any]]) -> str:
        max_chunks = max(int(os.environ.get("EVAL_MAX_CHUNKS", "4")), 1)
        max_chars = max(int(os.environ.get("EVAL_MAX_CHARS_PER_CHUNK", "1200")), 200)
        sections = []
        for idx, chunk in enumerate(chunks[:max_chunks], start=1):
            content = (chunk.get("content") or "").strip()[:max_chars]
            doc_id = chunk.get("doc_id", f"chunk-{idx}")
            sections.append(f"[Chunk {idx} - {doc_id}]\n{content}")
        return "\n\n".join(sections)

    def _extract_json(self, text: str) -> dict[str, Any]:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise ValueError("Judge response did not contain JSON")
        return json.loads(text[start : end + 1])

    def _coerce_score(self, data: dict[str, Any], key: str) -> float:
        value = float(data[key])
        return min(max(value, 0.0), 1.0)

    def evaluate(self, payload: EvalPayload) -> dict[str, Any]:
        context = self._trim_chunks(payload.chunks)
        if not context or not payload.answer:
            raise ValueError("Missing answer or context for evaluation")

        body = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 600,
                "system": (
                    "You are a strict RAG evaluator. Score only from the supplied query, retrieved context, "
                    "and answer. Return JSON only."
                ),
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "Evaluate the answer using only the retrieved context.\n\n"
                            "Return a JSON object with exactly these keys:\n"
                            "faithfulness, context_precision, context_coverage, answer_relevancy, "
                            "judge_verdict, reasoning.\n\n"
                            "All four score fields must be floats between 0 and 1.\n"
                            "context_coverage is a practical proxy for contextual recall based only on retrieved evidence.\n"
                            "judge_verdict should be a one-sentence summary.\n"
                            "reasoning should be concise.\n\n"
                            f"QUERY:\n{payload.query}\n\n"
                            f"RETRIEVED_CONTEXT:\n{context}\n\n"
                            f"ANSWER:\n{payload.answer}"
                        ),
                    }
                ],
            }
        )

        response = self._get_bedrock_client().invoke_model(
            modelId=self._judge_model_id(),
            body=body,
        )
        result = json.loads(response["body"].read())
        text = result["content"][0]["text"].strip()
        parsed = self._extract_json(text)
        scores = {
            "faithfulness": self._coerce_score(parsed, "faithfulness"),
            "context_precision": self._coerce_score(parsed, "context_precision"),
            "context_coverage": self._coerce_score(parsed, "context_coverage"),
            "answer_relevancy": self._coerce_score(parsed, "answer_relevancy"),
        }
        return {
            "scores": scores,
            "judge_verdict": str(parsed.get("judge_verdict", ""))[:280],
            "reasoning": str(parsed.get("reasoning", ""))[:600],
            "model_id": self._judge_model_id(),
        }

    def evaluate_and_record(self, payload: EvalPayload):
        sampled = self.should_sample(payload)
        if not sampled:
            return None

        try:
            metrics.publish_eval_sample_count(payload.route)
            result = self.evaluate(payload)
            metrics.publish_eval_scores(payload.route, result["scores"])
            log_eval_result(
                request_id=payload.request_id,
                query=payload.query,
                scores=result["scores"],
                sampled=sampled,
                verdict=result["judge_verdict"],
                reasoning=result["reasoning"],
                model_id=result["model_id"],
            )
            return result
        except Exception as exc:
            logger.exception("LLM judge evaluation failed")
            metrics.publish_judge_failure(payload.route)
            log_eval_failure(payload.request_id, str(exc), sampled=sampled)
            return None
