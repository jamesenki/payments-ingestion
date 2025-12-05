"""
Clustering module for grouping similar transactions.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler

from .models import NormalizedTransaction, Cluster, TimeWindow
from .utils.logger import get_logger


class Clusterer:
    """Clusters similar transactions using various algorithms."""
    
    def __init__(
        self,
        algorithm: str = "kmeans",
        n_clusters: int = 5,
        similarity_metric: str = "euclidean",
        features: List[str] = None,
        min_cluster_size: int = 10,
        max_cluster_size: int = 1000
    ):
        """
        Initialize clusterer.
        
        Args:
            algorithm: Clustering algorithm ("kmeans", "dbscan", "hierarchical")
            n_clusters: Number of clusters (for K-means and hierarchical)
            similarity_metric: Similarity metric ("euclidean", "manhattan", "cosine")
            features: List of feature fields to use for clustering
            min_cluster_size: Minimum cluster size
            max_cluster_size: Maximum cluster size
        """
        self.algorithm = algorithm
        self.n_clusters = n_clusters
        self.similarity_metric = similarity_metric
        self.features = features or ["amount"]
        self.min_cluster_size = min_cluster_size
        self.max_cluster_size = max_cluster_size
        self.logger = get_logger("metric_engine.clusterer")
        self.scaler = StandardScaler()
    
    def cluster(
        self,
        transactions: List[NormalizedTransaction],
        time_window: TimeWindow
    ) -> List[Cluster]:
        """
        Cluster transactions.
        
        Args:
            transactions: List of transactions to cluster
            time_window: Time window for clustering
            
        Returns:
            List of clusters
        """
        # Filter transactions within time window
        window_transactions = [
            tx for tx in transactions
            if time_window.contains(tx.transaction_timestamp)
        ]
        
        if len(window_transactions) < self.min_cluster_size:
            self.logger.info(
                f"Not enough transactions for clustering: {len(window_transactions)} < {self.min_cluster_size}"
            )
            return []
        
        # Extract features
        feature_matrix = self._extract_features(window_transactions)
        
        if feature_matrix.shape[0] < self.min_cluster_size:
            return []
        
        # Normalize features
        feature_matrix_scaled = self.scaler.fit_transform(feature_matrix)
        
        # Perform clustering
        labels = self._perform_clustering(feature_matrix_scaled)
        
        # Build clusters
        clusters = self._build_clusters(
            window_transactions,
            labels,
            time_window,
            feature_matrix
        )
        
        self.logger.info(
            f"Clustered {len(window_transactions)} transactions into {len(clusters)} clusters",
            extra={"extra_fields": {
                "algorithm": self.algorithm,
                "n_clusters": self.n_clusters,
                "window_start": time_window.start_time.isoformat(),
                "window_end": time_window.end_time.isoformat()
            }}
        )
        
        return clusters
    
    def _extract_features(
        self,
        transactions: List[NormalizedTransaction]
    ) -> np.ndarray:
        """Extract feature matrix from transactions."""
        features_list = []
        
        for tx in transactions:
            feature_vector = []
            
            for feature in self.features:
                if feature == "amount":
                    feature_vector.append(float(tx.amount))
                elif feature == "payment_method_encoded":
                    # Simple encoding: map payment method to numeric
                    method_map = {
                        "credit_card": 1,
                        "debit_card": 2,
                        "bank_transfer": 3,
                        "digital_wallet": 4,
                        "cryptocurrency": 5,
                        "cash_equivalent": 6
                    }
                    feature_vector.append(
                        method_map.get(tx.payment_method, 0)
                    )
                elif feature == "currency_encoded":
                    # Simple encoding: map currency to numeric
                    currency_map = {"USD": 1, "EUR": 2, "GBP": 3, "JPY": 4, "CAD": 5, "AUD": 6}
                    feature_vector.append(
                        currency_map.get(tx.currency, 0)
                    )
                else:
                    # Try to get attribute value
                    value = getattr(tx, feature, None)
                    if value is None:
                        feature_vector.append(0)
                    elif isinstance(value, (int, float)):
                        feature_vector.append(float(value))
                    else:
                        feature_vector.append(0)
            
            features_list.append(feature_vector)
        
        return np.array(features_list)
    
    def _perform_clustering(self, feature_matrix: np.ndarray) -> np.ndarray:
        """Perform clustering using selected algorithm."""
        if self.algorithm == "kmeans":
            clusterer = KMeans(
                n_clusters=self.n_clusters,
                random_state=42,
                n_init=10
            )
            labels = clusterer.fit_predict(feature_matrix)
        
        elif self.algorithm == "dbscan":
            clusterer = DBSCAN(
                eps=0.5,
                min_samples=self.min_cluster_size
            )
            labels = clusterer.fit_predict(feature_matrix)
        
        elif self.algorithm == "hierarchical":
            clusterer = AgglomerativeClustering(
                n_clusters=self.n_clusters,
                linkage="ward"
            )
            labels = clusterer.fit_predict(feature_matrix)
        
        else:
            raise ValueError(f"Unknown clustering algorithm: {self.algorithm}")
        
        return labels
    
    def _build_clusters(
        self,
        transactions: List[NormalizedTransaction],
        labels: np.ndarray,
        time_window: TimeWindow,
        feature_matrix: np.ndarray
    ) -> List[Cluster]:
        """Build Cluster objects from clustering results."""
        clusters_dict = {}
        
        for i, (tx, label) in enumerate(zip(transactions, labels)):
            # Skip noise points (label == -1 for DBSCAN)
            if label == -1:
                continue
            
            if label not in clusters_dict:
                clusters_dict[label] = {
                    "transaction_ids": [],
                    "indices": []
                }
            
            clusters_dict[label]["transaction_ids"].append(tx.transaction_id)
            clusters_dict[label]["indices"].append(i)
        
        clusters = []
        for cluster_id, cluster_data in clusters_dict.items():
            # Filter by size constraints
            size = len(cluster_data["transaction_ids"])
            if size < self.min_cluster_size or size > self.max_cluster_size:
                continue
            
            # Calculate centroid
            indices = cluster_data["indices"]
            centroid_features = feature_matrix[indices].mean(axis=0)
            centroid = {
                feature: float(centroid_features[i])
                for i, feature in enumerate(self.features)
            }
            
            cluster = Cluster(
                cluster_id=int(cluster_id),
                transaction_ids=cluster_data["transaction_ids"],
                centroid=centroid,
                size=size,
                time_window_start=time_window.start_time,
                time_window_end=time_window.end_time,
                algorithm=self.algorithm,
                similarity_metric=self.similarity_metric
            )
            clusters.append(cluster)
        
        return clusters

