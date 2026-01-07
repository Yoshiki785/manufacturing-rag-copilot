"""Tests for Prometheus metrics."""

import pytest
from prometheus_client import REGISTRY

from src.app.core.metrics import (
    chunks_created_total,
    chunks_retrieved_total,
    document_ingestion_duration_seconds,
    documents_ingested_total,
    embedding_batch_size,
    embedding_generation_duration_seconds,
    embedding_generations_total,
    openai_tokens_total,
    response_generation_duration_seconds,
    response_generations_total,
    retrieval_duration_seconds,
    retrieval_queries_total,
    retrieval_similarity_scores,
)


class TestCustomMetrics:
    """Test custom RAG metrics."""

    def test_embedding_metrics_exist(self):
        """Test that embedding metrics are defined."""
        metric_name = "embedding_generations_total"
        assert any(
            metric.startswith(metric_name)
            for metric in REGISTRY._collector_to_names.values()
            for metric in metric
        )

    def test_document_metrics_exist(self):
        """Test that document ingestion metrics are defined."""
        metric_name = "documents_ingested_total"
        assert any(
            metric.startswith(metric_name)
            for metric in REGISTRY._collector_to_names.values()
            for metric in metric
        )

    def test_retrieval_metrics_exist(self):
        """Test that retrieval metrics are defined."""
        metric_name = "retrieval_queries_total"
        assert any(
            metric.startswith(metric_name)
            for metric in REGISTRY._collector_to_names.values()
            for metric in metric
        )

    def test_generation_metrics_exist(self):
        """Test that generation metrics are defined."""
        metric_name = "response_generations_total"
        assert any(
            metric.startswith(metric_name)
            for metric in REGISTRY._collector_to_names.values()
            for metric in metric
        )


class TestMetricLabels:
    """Test metric labels."""

    def test_embedding_metrics_have_labels(self):
        """Test that embedding metrics accept proper labels."""
        # Test that labels can be set without error
        metric = embedding_generations_total.labels(
            model="test-model", status="success"
        )
        assert metric is not None

    def test_document_metrics_have_labels(self):
        """Test that document metrics accept proper labels."""
        metric = documents_ingested_total.labels(status="success")
        assert metric is not None

    def test_retrieval_metrics_have_labels(self):
        """Test that retrieval metrics accept proper labels."""
        metric = retrieval_queries_total.labels(status="success")
        assert metric is not None

    def test_generation_metrics_have_labels(self):
        """Test that generation metrics accept proper labels."""
        metric = response_generations_total.labels(model="test-model", status="success")
        assert metric is not None


class TestMetricIncrement:
    """Test metric incrementation."""

    def test_counter_increment(self):
        """Test that counters can increment."""
        # Test that increment works without error
        chunks_created_total.inc(5)
        assert True  # If we get here, increment worked

    def test_chunks_retrieved_counter(self):
        """Test chunks retrieved counter can increment."""
        chunks_retrieved_total.inc(10)
        assert True


class TestHistogramMetrics:
    """Test histogram metrics."""

    def test_histogram_observe(self):
        """Test that histogram metrics can record observations."""
        # Test that observe works without error
        retrieval_duration_seconds.observe(0.5)
        retrieval_duration_seconds.observe(1.0)
        retrieval_duration_seconds.observe(2.0)
        assert True

    def test_embedding_duration_histogram(self):
        """Test embedding duration histogram."""
        embedding_generation_duration_seconds.labels(model="test-model").observe(1.5)
        assert True

    def test_document_ingestion_histogram(self):
        """Test document ingestion duration histogram."""
        document_ingestion_duration_seconds.observe(10.0)
        assert True

    def test_embedding_batch_size_histogram(self):
        """Test embedding batch size histogram."""
        embedding_batch_size.observe(100)
        assert True


class TestTokenMetrics:
    """Test token usage metrics."""

    def test_openai_tokens_counter(self):
        """Test OpenAI token counter."""
        openai_tokens_total.labels(model="gpt-4", token_type="prompt").inc(100)
        openai_tokens_total.labels(model="gpt-4", token_type="completion").inc(50)
        assert True
