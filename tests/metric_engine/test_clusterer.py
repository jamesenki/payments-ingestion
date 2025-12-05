"""
Unit tests for clusterer.
"""

import pytest
import numpy as np
from decimal import Decimal
from datetime import datetime, timedelta

from src.metric_engine.clusterer import Clusterer
from src.metric_engine.models import NormalizedTransaction, TimeWindow


class TestClusterer:
    """Tests for Clusterer."""
    
    @pytest.fixture
    def sample_time_window(self):
        """Create a sample time window."""
        start = datetime.now().replace(minute=0, second=0, microsecond=0)
        return TimeWindow(
            name="hourly",
            duration_seconds=3600,
            start_time=start,
            end_time=start + timedelta(hours=1),
            enabled=True
        )
    
    @pytest.fixture
    def sample_transactions(self, sample_time_window):
        """Create sample transactions for clustering."""
        transactions = []
        base_time = sample_time_window.start_time
        
        # Create transactions with varying amounts
        amounts = [50, 100, 150, 200, 250, 300, 350, 400, 450, 500]
        
        for i, amount in enumerate(amounts):
            transactions.append(
                NormalizedTransaction(
                    transaction_id=f"tx-{i}",
                    transaction_timestamp=base_time + timedelta(minutes=i * 5),
                    amount=Decimal(f"{amount}.00"),
                    currency="USD",
                    payment_method="credit_card" if i % 2 == 0 else "debit_card",
                    payment_status="completed",
                    customer_id=f"cust-{i % 3}"
                )
            )
        
        return transactions
    
    def test_cluster_kmeans(self, sample_time_window, sample_transactions):
        """Test K-means clustering."""
        clusterer = Clusterer(
            algorithm="kmeans",
            n_clusters=3,
            similarity_metric="euclidean",
            features=["amount"],
            min_cluster_size=2
        )
        
        clusters = clusterer.cluster(sample_transactions, sample_time_window)
        
        # Should have clusters
        assert len(clusters) > 0
        assert all(c.algorithm == "kmeans" for c in clusters)
    
    def test_cluster_dbscan(self, sample_time_window, sample_transactions):
        """Test DBSCAN clustering."""
        clusterer = Clusterer(
            algorithm="dbscan",
            n_clusters=3,
            similarity_metric="euclidean",
            features=["amount"],
            min_cluster_size=2
        )
        
        clusters = clusterer.cluster(sample_transactions, sample_time_window)
        
        # DBSCAN may or may not create clusters depending on density
        # Just verify it doesn't crash
        assert isinstance(clusters, list)
        assert all(c.algorithm == "dbscan" for c in clusters)
    
    def test_cluster_hierarchical(self, sample_time_window, sample_transactions):
        """Test hierarchical clustering."""
        clusterer = Clusterer(
            algorithm="hierarchical",
            n_clusters=3,
            similarity_metric="euclidean",
            features=["amount"],
            min_cluster_size=2
        )
        
        clusters = clusterer.cluster(sample_transactions, sample_time_window)
        
        assert len(clusters) > 0
        assert all(c.algorithm == "hierarchical" for c in clusters)
    
    def test_cluster_insufficient_transactions(self, sample_time_window):
        """Test clustering with insufficient transactions."""
        # Create only 2 transactions (less than min_cluster_size)
        transactions = [
            NormalizedTransaction(
                transaction_id="tx-1",
                transaction_timestamp=sample_time_window.start_time,
                amount=Decimal("100.00"),
                currency="USD",
                payment_method="credit_card",
                payment_status="completed"
            ),
            NormalizedTransaction(
                transaction_id="tx-2",
                transaction_timestamp=sample_time_window.start_time + timedelta(minutes=1),
                amount=Decimal("200.00"),
                currency="USD",
                payment_method="debit_card",
                payment_status="completed"
            )
        ]
        
        clusterer = Clusterer(
            algorithm="kmeans",
            n_clusters=2,
            min_cluster_size=5  # Higher than transaction count
        )
        
        clusters = clusterer.cluster(transactions, sample_time_window)
        
        # Should return empty list
        assert len(clusters) == 0
    
    def test_extract_features_amount(self, sample_transactions):
        """Test feature extraction for amount."""
        clusterer = Clusterer(
            algorithm="kmeans",
            n_clusters=2,
            features=["amount"]
        )
        
        feature_matrix = clusterer._extract_features(sample_transactions)
        
        assert feature_matrix.shape[0] == len(sample_transactions)
        assert feature_matrix.shape[1] == 1  # One feature
        assert all(feature_matrix[i, 0] > 0 for i in range(len(sample_transactions)))
    
    def test_extract_features_payment_method(self, sample_transactions):
        """Test feature extraction for payment method."""
        clusterer = Clusterer(
            algorithm="kmeans",
            n_clusters=2,
            features=["amount", "payment_method_encoded"]
        )
        
        feature_matrix = clusterer._extract_features(sample_transactions)
        
        assert feature_matrix.shape[0] == len(sample_transactions)
        assert feature_matrix.shape[1] == 2  # Two features
    
    def test_extract_features_currency(self, sample_transactions):
        """Test feature extraction for currency."""
        clusterer = Clusterer(
            algorithm="kmeans",
            n_clusters=2,
            features=["amount", "currency_encoded"]
        )
        
        feature_matrix = clusterer._extract_features(sample_transactions)
        
        assert feature_matrix.shape[0] == len(sample_transactions)
        assert feature_matrix.shape[1] == 2
    
    def test_cluster_outside_window(self, sample_time_window):
        """Test that transactions outside window are excluded."""
        # Create transaction outside window
        outside_tx = NormalizedTransaction(
            transaction_id="tx-outside",
            transaction_timestamp=sample_time_window.start_time - timedelta(hours=1),
            amount=Decimal("1000.00"),
            currency="USD",
            payment_method="credit_card",
            payment_status="completed"
        )
        
        clusterer = Clusterer(
            algorithm="kmeans",
            n_clusters=1,
            min_cluster_size=1
        )
        
        clusters = clusterer.cluster([outside_tx], sample_time_window)
        
        # Should have no clusters (transaction outside window)
        assert len(clusters) == 0
    
    def test_cluster_size_constraints(self, sample_time_window, sample_transactions):
        """Test cluster size constraints."""
        clusterer = Clusterer(
            algorithm="kmeans",
            n_clusters=2,
            min_cluster_size=3,
            max_cluster_size=5,
            features=["amount"]
        )
        
        clusters = clusterer.cluster(sample_transactions, sample_time_window)
        
        # All clusters should respect size constraints
        for cluster in clusters:
            assert cluster.size >= clusterer.min_cluster_size
            assert cluster.size <= clusterer.max_cluster_size
    
    def test_cluster_centroid_calculation(self, sample_time_window, sample_transactions):
        """Test that clusters have centroids calculated."""
        clusterer = Clusterer(
            algorithm="kmeans",
            n_clusters=2,
            features=["amount"]
        )
        
        clusters = clusterer.cluster(sample_transactions, sample_time_window)
        
        # All clusters should have centroids
        for cluster in clusters:
            assert cluster.centroid is not None
            assert "amount" in cluster.centroid

