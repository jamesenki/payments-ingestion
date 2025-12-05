"""
Main orchestrator for the metric engine.
"""

import os
import yaml
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from .data_extractor import DataExtractor
from .data_normalizer import DataNormalizer
from .rule_processor import RuleProcessor
from .aggregator import Aggregator
from .clusterer import Clusterer
from .utils.time_window_manager import TimeWindowManager
from .utils.logger import setup_logging, get_logger, log_operation
from .models import (
    RawTransaction,
    NormalizedTransaction,
    DerivedMetric,
    AggregatedMetric,
    Cluster,
    TimeWindow
)


class MetricEngine:
    """Main orchestrator for the metric engine."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize metric engine.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()
        self.logger = setup_logging(
            level=self.config.get("logging", {}).get("level", "INFO"),
            format_type=self.config.get("logging", {}).get("format", "json"),
            log_file=self.config.get("logging", {}).get("file"),
            include_metrics=self.config.get("logging", {}).get("include_metrics", True)
        )
        
        # Initialize components
        self.extractor = None
        self.normalizer = DataNormalizer()
        self.rule_processor = None
        self.aggregator = None
        self.clusterer = None
        self.time_window_manager = None
        
        self._initialize_components()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        return str(Path(__file__).parent.parent.parent / "config" / "metric_engine_settings.yaml")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}", exc_info=True)
            raise
    
    def _initialize_components(self):
        """Initialize all components."""
        metric_config = self.config.get("metric_engine", {})
        
        # Data extractor
        data_source_config = metric_config.get("data_source", {})
        connection_string = data_source_config.get("connection_string", "")
        # Expand environment variables
        connection_string = os.path.expandvars(connection_string)
        
        self.extractor = DataExtractor(
            connection_string=connection_string,
            batch_size=data_source_config.get("batch_size", 1000),
            max_retries=data_source_config.get("max_retries", 3),
            retry_delay_seconds=data_source_config.get("retry_delay_seconds", 5)
        )
        
        # Rule processor
        rules_config = metric_config.get("rules", {})
        self.rule_processor = RuleProcessor(
            rules_file=rules_config.get("rules_file", "config/metric_rules.yaml"),
            rule_version=rules_config.get("rule_version", "1.0.0")
        )
        
        # Time window manager
        time_windows = metric_config.get("time_windows", [])
        self.time_window_manager = TimeWindowManager(time_windows)
        
        self.logger.info("Metric engine components initialized")
    
    def process_time_window(
        self,
        window_name: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """
        Process transactions for a specific time window.
        
        Args:
            window_name: Name of the time window type
            start_time: Start of the time range
            end_time: End of the time range
            
        Returns:
            Dictionary with processing results
        """
        log_operation(
            self.logger,
            "process_time_window",
            window_name=window_name,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat()
        )
        
        # Extract transactions
        raw_transactions = self.extractor.extract_transactions(
            start_time=start_time,
            end_time=end_time
        )
        
        if not raw_transactions:
            self.logger.info("No transactions found for time window")
            return {
                "transactions_processed": 0,
                "metrics_derived": 0,
                "aggregated_metrics": 0,
                "clusters": 0
            }
        
        # Normalize transactions
        normalized_transactions = self.normalizer.normalize_batch(raw_transactions)
        
        if not normalized_transactions:
            self.logger.warning("No valid transactions after normalization")
            return {
                "transactions_processed": 0,
                "metrics_derived": 0,
                "aggregated_metrics": 0,
                "clusters": 0
            }
        
        # Process rules
        all_derived_metrics = []
        for tx in normalized_transactions:
            metrics = self.rule_processor.process_transaction(tx)
            all_derived_metrics.extend(metrics)
        
        # Aggregate metrics
        aggregated_metrics = []
        if self.config.get("metric_engine", {}).get("aggregation", {}).get("enabled", True):
            aggregation_config = self.config.get("metric_engine", {}).get("aggregation", {})
            dimensions = aggregation_config.get("dimensions", ["payment_method", "currency"])
            
            # Get time window
            time_window = self.time_window_manager.get_window_for_timestamp(
                start_time,
                window_name
            )
            
            if time_window:
                aggregator = Aggregator(
                    dimensions=dimensions,
                    operations=aggregation_config.get("operations", ["sum", "average", "count"]),
                    time_window=time_window
                )
                aggregated_metrics = aggregator.aggregate(normalized_transactions)
        
        # Cluster transactions
        clusters = []
        if self.config.get("metric_engine", {}).get("clustering", {}).get("enabled", True):
            clustering_config = self.config.get("metric_engine", {}).get("clustering", {})
            
            # Get time window for clustering
            cluster_window_name = clustering_config.get("time_window", "hourly")
            time_window = self.time_window_manager.get_window_for_timestamp(
                start_time,
                cluster_window_name
            )
            
            if time_window:
                clusterer = Clusterer(
                    algorithm=clustering_config.get("algorithm", "kmeans"),
                    n_clusters=clustering_config.get("n_clusters", 5),
                    similarity_metric=clustering_config.get("similarity_metric", "euclidean"),
                    features=clustering_config.get("features", ["amount"]),
                    min_cluster_size=clustering_config.get("min_cluster_size", 10),
                    max_cluster_size=clustering_config.get("max_cluster_size", 1000)
                )
                clusters = clusterer.cluster(normalized_transactions, time_window)
        
        results = {
            "transactions_processed": len(normalized_transactions),
            "metrics_derived": len(all_derived_metrics),
            "aggregated_metrics": len(aggregated_metrics),
            "clusters": len(clusters),
            "derived_metrics": all_derived_metrics,
            "aggregated_metrics_list": aggregated_metrics,
            "clusters_list": clusters
        }
        
        self.logger.info(
            f"Processed time window: {results['transactions_processed']} transactions, "
            f"{results['metrics_derived']} metrics, {results['aggregated_metrics']} aggregated, "
            f"{results['clusters']} clusters"
        )
        
        return results
    
    def process_recent_transactions(
        self,
        hours: int = 1,
        window_name: str = "5min"
    ) -> Dict[str, Any]:
        """
        Process recent transactions.
        
        Args:
            hours: Number of hours to look back
            window_name: Time window name for processing
            
        Returns:
            Dictionary with processing results
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        return self.process_time_window(window_name, start_time, end_time)
    
    def close(self):
        """Close all resources."""
        if self.extractor:
            self.extractor.close()
        self.logger.info("Metric engine closed")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Metric Engine")
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file",
        default=None
    )
    parser.add_argument(
        "--hours",
        type=int,
        help="Number of hours to process",
        default=1
    )
    parser.add_argument(
        "--window",
        type=str,
        help="Time window name",
        default="5min"
    )
    
    args = parser.parse_args()
    
    engine = MetricEngine(config_path=args.config)
    
    try:
        results = engine.process_recent_transactions(
            hours=args.hours,
            window_name=args.window
        )
        
        print(f"Processed {results['transactions_processed']} transactions")
        print(f"Derived {results['metrics_derived']} metrics")
        print(f"Created {results['aggregated_metrics']} aggregated metrics")
        print(f"Created {results['clusters']} clusters")
    
    finally:
        engine.close()


if __name__ == "__main__":
    main()

