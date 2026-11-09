from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from fraud_dt.config import AppConfig
from fraud_dt.control import PolicyOrchestrator
from fraud_dt.decision import DecisionEngine
from fraud_dt.devices import MockBillingMeter, MockForensicDevice, MockTransport
from fraud_dt.twin import ForensicTwin


@dataclass
class SimulationRunner:
    config: AppConfig
    decision_engine: DecisionEngine
    orchestrator: PolicyOrchestrator
    transport: MockTransport

    def run(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        if df.empty:
            empty = pd.DataFrame()
            return empty, empty, empty, empty, empty

        ordered_df = df.sort_values("timestamp").reset_index(drop=True)
        fusion_strategy_name = getattr(self.decision_engine.fusion_strategy, "strategy_name", "unknown")
        twin = ForensicTwin(
            dev_eui=str(ordered_df.iloc[0]["dev_eui"]),
            initial_mode="basal",
            initial_capture_period_minutes=self.config.policy.basal_minutes,
        )
        device = MockForensicDevice(
            dev_eui=twin.dev_eui,
            initial_capture_period_minutes=self.config.policy.basal_minutes,
        )
        billing_meter = MockBillingMeter(ordered_df[["timestamp", "dev_eui", "billing_active_power", "billing_active_energy"]].copy())

        timeline_rows: list[dict[str, Any]] = []
        decision_rows = []
        state_rows = []
        command_rows = []
        transport_rows = []
        last_decision = None

        for event_index, row in ordered_df.iterrows():
            timestamp = pd.Timestamp(row["timestamp"])
            dev_eui = str(row["dev_eui"])
            billing_snapshot = billing_meter.get_at(timestamp, dev_eui)
            observed = int(device.should_emit(timestamp))
            current_mode_before = twin.current_mode
            current_capture_before = twin.current_capture_period_minutes
            timeline_row = row.to_dict()
            timeline_row["billing_active_power"] = billing_snapshot["billing_active_power"]
            timeline_row["billing_active_energy"] = billing_snapshot["billing_active_energy"]
            timeline_row["observed"] = observed
            timeline_row["policy_name"] = "adaptive"
            timeline_row["fusion_strategy"] = fusion_strategy_name

            if observed == 1:
                observation = twin.observe(event_index, row.to_dict())
                decision = self.decision_engine.evaluate(observation)
                command = self.orchestrator.build_command(twin, decision)
                delivered_command, delivery = self.transport.deliver(
                    command,
                    timestamp=timestamp,
                    link_ok=int(row["link_ok"]),
                    heartbeat_ok=int(row["heartbeat_ok"]),
                )
                twin.apply_command(delivered_command)
                device.mark_emitted(timestamp)
                device.apply_command(delivered_command)
                snapshot = twin.snapshot(observation, decision)
                last_decision = decision

                timeline_row["observation_mode"] = twin.current_mode
                timeline_row["capture_period_minutes"] = twin.current_capture_period_minutes
                timeline_row["decision_probability"] = decision.decision_probability
                timeline_row["decision_probability_source"] = decision.probability_source
                timeline_row["decision_risk_class"] = decision.risk_class
                timeline_row["decision_rationale"] = decision.rationale
                timeline_row["command_id"] = delivered_command.command_id
                timeline_row["command_action"] = delivered_command.action
                timeline_row["command_transport"] = delivered_command.transport_preference
                timeline_row["command_ack_status"] = delivered_command.ack_status

                decision_record = decision.to_record()
                decision_record["fusion_strategy"] = fusion_strategy_name
                snapshot_record = snapshot.to_record()
                snapshot_record["fusion_strategy"] = fusion_strategy_name
                command_record = delivered_command.to_record()
                command_record["fusion_strategy"] = fusion_strategy_name
                delivery_record = delivery.to_record()
                delivery_record["fusion_strategy"] = fusion_strategy_name
                decision_rows.append(decision_record)
                state_rows.append(snapshot_record)
                command_rows.append(command_record)
                transport_rows.append(delivery_record)
            else:
                timeline_row["observation_mode"] = current_mode_before
                timeline_row["capture_period_minutes"] = current_capture_before
                timeline_row["command_id"] = ""
                timeline_row["command_action"] = ""
                timeline_row["command_transport"] = ""
                timeline_row["command_ack_status"] = ""
                if last_decision is not None:
                    timeline_row["decision_probability"] = last_decision.decision_probability
                    timeline_row["decision_probability_source"] = last_decision.probability_source
                    timeline_row["decision_risk_class"] = last_decision.risk_class
                    timeline_row["decision_rationale"] = last_decision.rationale
                else:
                    timeline_row["decision_probability"] = row["risk_probability"]
                    timeline_row["decision_probability_source"] = "bootstrap_rule_only"
                    timeline_row["decision_risk_class"] = "low"
                    timeline_row["decision_rationale"] = "awaiting_first_observation"

            timeline_rows.append(timeline_row)

        return (
            pd.DataFrame(timeline_rows),
            pd.DataFrame(decision_rows),
            pd.DataFrame(state_rows),
            pd.DataFrame(command_rows),
            pd.DataFrame(transport_rows),
        )
