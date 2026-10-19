import random
import statistics
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, timedelta

@dataclass
class BridgeTransaction:
    tx_hash: str
    source_chain: str
    dest_chain: str
    token: str
    amount_usd: float
    timestamp: datetime
    is_anomaly: bool = False

class BridgeMonitor:
    def __init__(self, z_score_threshold: float = 3.0):
        self.transactions: List[BridgeTransaction] = []
        self.z_threshold = z_score_threshold
        self.alerts: List[str] = []

    def add_transaction(self, tx: BridgeTransaction):
        self.transactions.append(tx)
        self._check_anomaly(tx)

    def _check_anomaly(self, tx: BridgeTransaction):
        similar = [t.amount_usd for t in self.transactions
                   if t.source_chain == tx.source_chain and t.token == tx.token]
        if len(similar) < 10:
            return
        mean = statistics.mean(similar)
        stdev = statistics.stdev(similar)
        if stdev == 0:
            return
        z = (tx.amount_usd - mean) / stdev
        if abs(z) > self.z_threshold:
            tx.is_anomaly = True
            alert = (f"⚠️  ANOMALY DETECTED | {tx.source_chain}→{tx.dest_chain} | "
                     f"{tx.token} ${tx.amount_usd:,.0f} | Z={z:.2f}")
            self.alerts.append(alert)
            print(alert)

    def summary(self) -> dict:
        total_vol = sum(t.amount_usd for t in self.transactions)
        anomalies = [t for t in self.transactions if t.is_anomaly]
        return {
            "total_transactions": len(self.transactions),
            "total_volume_usd": total_vol,
            "anomalies_detected": len(anomalies),
            "anomaly_rate": f"{len(anomalies)/max(len(self.transactions),1):.2%}",
        }

if __name__ == "__main__":
    monitor = BridgeMonitor(z_score_threshold=2.5)
    chains = [("Ethereum","Polygon"), ("Ethereum","Arbitrum"), ("BSC","Ethereum")]
    tokens = ["USDC","ETH","WBTC"]
    base = datetime.utcnow() - timedelta(hours=24)

    for i in range(200):
        src, dst = random.choice(chains)
        token = random.choice(tokens)
        # Inject anomaly at i=150
        amount = random.uniform(1_000, 500_000) if i != 150 else 50_000_000
        tx = BridgeTransaction(
            tx_hash=f"0x{i:064x}",
            source_chain=src, dest_chain=dst, token=token,
            amount_usd=amount,
            timestamp=base + timedelta(minutes=i*7),
        )
        monitor.add_transaction(tx)

    import json
    print(json.dumps(monitor.summary(), indent=2))
