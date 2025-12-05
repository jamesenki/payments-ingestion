"""
Main entry point for the Payment Data Simulator application.
"""

import asyncio
import signal
import sys
import time
from datetime import datetime
from typing import Optional

from .config_loader import load_simulator_config
from .logger_config import setup_logging, get_logger
from .transaction_generator import TransactionGenerator
from .compliance_generator import ComplianceViolationGenerator
from .event_publisher import create_publisher
from .config.schema import TransactionConfig


class SimulatorApp:
    """
    Main application orchestrator for the payment data simulator.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the simulator application.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = None
        self.logger = None
        self.transaction_generator = None
        self.compliance_generator = None
        self.publisher = None
        self.running = False
        self.stats = {
            "total_generated": 0,
            "total_published": 0,
            "total_violations": 0,
            "start_time": None,
        }
    
    def initialize(self):
        """Initialize all components."""
        # Load configuration
        self.config = load_simulator_config(self.config_path)
        
        # Setup logging
        log_config = self.config.logging
        if log_config:
            self.logger = setup_logging(
                level=log_config.level,
                format_type=log_config.format,
                log_file=log_config.file,
                include_metrics=log_config.include_metrics
            )
        else:
            self.logger = setup_logging()
        
        self.logger.info("Initializing Payment Data Simulator")
        
        # Initialize transaction generator
        transaction_config = TransactionConfig(**self.config.simulator.get("transaction", {}))
        self.transaction_generator = TransactionGenerator(transaction_config)
        
        # Initialize compliance generator
        compliance_config = self.config.compliance
        if compliance_config:
            self.compliance_generator = ComplianceViolationGenerator(compliance_config)
        else:
            self.compliance_generator = None
        
        # Initialize publisher
        output_config = self.config.simulator.get("output", {})
        self.publisher = create_publisher(output_config)
        
        self.logger.info("Simulator initialized successfully")
    
    async def run(self):
        """Run the simulator."""
        if not self.config:
            raise RuntimeError("Simulator not initialized. Call initialize() first.")
        
        self.running = True
        self.stats["start_time"] = datetime.now()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        
        self.logger.info("Starting transaction generation")
        
        try:
            # Get volume configuration
            volume = self.config.simulator.get("transaction", {}).get("volume", {})
            total = volume.get("total", 10000)
            rate = volume.get("rate", 100)  # transactions per second
            duration = volume.get("duration")
            
            # Calculate batch size and delay
            batch_size = min(rate, 100)  # Generate in batches
            delay = 1.0 / rate if rate > 0 else 0.01
            
            # Determine if we're time-based or count-based
            if duration:
                # Time-based: run for specified duration
                end_time = time.time() + duration
                while self.running and time.time() < end_time:
                    await self._generate_and_publish_batch(batch_size)
                    await asyncio.sleep(delay)
            else:
                # Count-based: generate specified number
                generated = 0
                while self.running and generated < total:
                    batch_count = min(batch_size, total - generated)
                    await self._generate_and_publish_batch(batch_count)
                    generated += batch_count
                    await asyncio.sleep(delay)
            
        except Exception as e:
            self.logger.error(f"Error during simulation: {e}", exc_info=True)
            raise
        finally:
            await self.shutdown()
    
    async def _generate_and_publish_batch(self, batch_size: int):
        """Generate and publish a batch of transactions."""
        # Get metadata config
        if self.config.metadata:
            metadata_config = {
                "include_ip_address": self.config.metadata.include_ip_address,
                "include_user_agent": self.config.metadata.include_user_agent,
                "include_card_data": self.config.metadata.include_card_data,
                "include_risk_score": self.config.metadata.include_risk_score,
                "include_fraud_indicators": self.config.metadata.include_fraud_indicators,
            }
        else:
            metadata_config = {}
        
        # Generate transactions
        transactions = self.transaction_generator.generate_batch(batch_size, metadata_config)
        
        # Apply compliance violations
        if self.compliance_generator:
            for i, transaction in enumerate(transactions):
                transaction, violations = self.compliance_generator.apply_violation(
                    transaction,
                    self.config.compliance.scenarios if self.config.compliance else None
                )
                if violations:
                    self.stats["total_violations"] += len(violations)
                transactions[i] = transaction
        
        # Convert to dictionaries for publishing
        transaction_dicts = [t.to_event_hub_format() for t in transactions]
        
        # Publish batch
        published_count = await self.publisher.publish_batch(transaction_dicts)
        
        # Update stats
        self.stats["total_generated"] += len(transactions)
        self.stats["total_published"] += published_count
        
        # Log progress
        if self.stats["total_generated"] % 1000 == 0:
            self.logger.info(
                f"Progress: {self.stats['total_generated']} generated, "
                f"{self.stats['total_published']} published, "
                f"{self.stats['total_violations']} violations"
            )
    
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    async def shutdown(self):
        """Shutdown the simulator gracefully."""
        self.logger.info("Shutting down simulator...")
        
        # Flush any remaining batch
        if self.publisher:
            await self.publisher.flush_batch()
            await self.publisher.close()
        
        # Print final stats
        elapsed = (datetime.now() - self.stats["start_time"]).total_seconds() if self.stats["start_time"] else 0
        self.logger.info(
            f"Simulation complete. "
            f"Generated: {self.stats['total_generated']}, "
            f"Published: {self.stats['total_published']}, "
            f"Violations: {self.stats['total_violations']}, "
            f"Elapsed: {elapsed:.2f}s"
        )
        
        # Print publisher metrics
        if self.publisher and hasattr(self.publisher, 'get_metrics'):
            metrics = self.publisher.get_metrics()
            self.logger.info(f"Publisher metrics: {metrics}")


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Payment Data Simulator")
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file",
        default=None
    )
    args = parser.parse_args()
    
    app = SimulatorApp(config_path=args.config)
    app.initialize()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())

