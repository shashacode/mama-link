import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch
from mama_link.foundry import (execute_tool, run_agent, run_knowledge_agent,
                               canonical_agent_output, AGENT_ROLES, PIPELINE_ROLES,
                               TOOL_ROLES, AGENT_CONTRACT_VERSION, agent_name, demo,
                               bootstrap_chat, bootstrap_tools, chat_agent_reference)


class FoundryBoundaryTests(unittest.TestCase):
    def test_six_role_architecture_is_registered(self):
        self.assertEqual(set(AGENT_ROLES), {"intake", "triage", "knowledge", "referral", "transport_support", "follow_up"})
        self.assertEqual(PIPELINE_ROLES, ("intake", "triage", "knowledge", "referral", "transport_support", "follow_up"))
        self.assertEqual(agent_name("follow_up"), "mama-link-follow-up")
        self.assertEqual(agent_name("transport_support"), "mama-link-transport-support")

    def test_cross_case_and_mutating_tools_are_rejected(self):
        for name, args in [("send_alert", {"case_id": "MAT-005"}), ("screen_case", {"case_id": "MAT-009"}),
                           ("screen_case", {"case_id": "MAT-005", "consent": True})]:
            with self.assertRaises(ValueError):
                execute_tool(name, args, "MAT-005", "triage")

    def test_canonical_tool_result(self):
        self.assertEqual(execute_tool("screen_case", {"case_id": "MAT-005"}, "MAT-005", "triage")["classification"], "critical")

    def test_every_tool_agent_has_a_canonical_result(self):
        intake = canonical_agent_output("intake", "MAT-005")
        self.assertEqual(intake["case_id"], "MAT-005")
        self.assertIn("reported_prolonged_or_obstructed_labour", intake["reported_symptoms"])
        self.assertNotIn("patient_alias", intake)

        referral = canonical_agent_output("referral", "MAT-005")
        self.assertEqual(referral["classification"], "critical")
        self.assertEqual(referral["facility_ids"], ["FAC-009", "FAC-002", "FAC-004"])

        support = canonical_agent_output("transport_support", "MAT-005")
        self.assertEqual(support["classification"], "critical")
        self.assertTrue(support["resource_ids"])
        self.assertFalse(support["contacted"])

        follow_up = canonical_agent_output("follow_up", "MAT-005")
        self.assertTrue(follow_up["review_required"])
        self.assertFalse(follow_up["scheduled"])
        self.assertFalse(follow_up["notification_sent"])

    def test_agent_must_call_tool_and_cannot_downgrade(self):
        client = Mock()
        client.conversations.create.return_value.id = "conversation-demo"
        client.responses.create.return_value = SimpleNamespace(output=[], output_text='{"classification":"critical"}')
        with self.assertRaisesRegex(ValueError, "without"):
            run_agent(client, {"name": "triage", "version": "1"}, "triage", "MAT-005")
        client.conversations.delete.assert_called_with(conversation_id="conversation-demo")
        call = SimpleNamespace(type="function_call", name="screen_case", arguments=json.dumps({"case_id": "MAT-005"}), call_id="tool-1")
        client.responses.create.side_effect = [SimpleNamespace(output=[call]), SimpleNamespace(output=[], output_text='{"classification":"normal"}')]
        with self.assertRaisesRegex(ValueError, "authoritative"):
            run_agent(client, {"name": "triage", "version": "1"}, "triage", "MAT-005")

    def test_validated_agent_success(self):
        client = Mock()
        client.conversations.create.return_value.id = "conversation-demo"
        call = SimpleNamespace(type="function_call", name="screen_case", arguments='{"case_id":"MAT-005"}', call_id="tool-1")
        client.responses.create.side_effect = [SimpleNamespace(output=[call]), SimpleNamespace(output=[], output_text='{"classification":"critical"}')]
        result = run_agent(client, {"name": "triage", "version": "1"}, "triage", "MAT-005")
        self.assertEqual(result["validated_output"], {"classification": "critical"})

    def test_new_tool_agent_is_executed_and_validated(self):
        client = Mock()
        client.conversations.create.return_value.id = "conversation-demo"
        call = SimpleNamespace(type="function_call", name="support_plan", arguments='{"case_id":"MAT-005"}', call_id="tool-1")
        expected = canonical_agent_output("transport_support", "MAT-005")
        client.responses.create.side_effect = [
            SimpleNamespace(output=[call]),
            SimpleNamespace(output=[], output_text=json.dumps(expected)),
        ]
        result = run_agent(client, {"name": "transport", "version": "1"}, "transport_support", "MAT-005")
        self.assertEqual(result["validated_output"], expected)
        self.assertEqual(result["tool_calls"], [{"tool": "support_plan", "status": "completed"}])

    def test_knowledge_agent_requires_file_search(self):
        client = Mock()
        client.conversations.create.return_value.id = "conversation-demo"
        client.responses.create.return_value = SimpleNamespace(output=[], output_text="Ungrounded answer")
        with self.assertRaisesRegex(ValueError, "without File Search"):
            run_knowledge_agent(client, {"name": "knowledge", "version": "1"}, "Question")
        client.conversations.delete.assert_called_with(conversation_id="conversation-demo")

        file_call = SimpleNamespace(type="file_search_call")
        client.responses.create.return_value = SimpleNamespace(output=[file_call], output_text="Grounded educational answer")
        result = run_knowledge_agent(client, {"name": "knowledge", "version": "1"}, "Question")
        self.assertEqual(result["role"], "knowledge")
        self.assertEqual(result["validated_output"]["review_status"], "pending_clinical_review")
        self.assertEqual(result["tool_calls"], [{"tool": "file_search", "status": "completed"}])

    def test_demo_orchestrates_all_six_roles_in_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            main_manifest = root / "agents.json"
            knowledge_manifest = root / "knowledge.json"
            endpoint = "https://example.services.ai.azure.com/api/projects/mama-link"
            main_manifest.write_text(json.dumps({
                "endpoint": endpoint,
                "contract_version": AGENT_CONTRACT_VERSION,
                "agents": {role: {"name": role, "version": "1"} for role in TOOL_ROLES},
            }), encoding="utf-8")
            knowledge_manifest.write_text(json.dumps({
                "endpoint": endpoint,
                "agent": {"name": "knowledge", "version": "1"},
            }), encoding="utf-8")

            project_context = MagicMock()
            project = project_context.__enter__.return_value
            client_context = MagicMock()
            project.get_openai_client.return_value = client_context
            client = client_context.__enter__.return_value

            def tool_result(_client, _reference, role, _case_id):
                return {"role": role, "validated_output": {}, "tool_calls": []}

            knowledge_result = {"role": "knowledge", "validated_output": {}, "tool_calls": []}
            with patch("mama_link.foundry.MANIFEST", main_manifest), \
                 patch("mama_link.foundry.KNOWLEDGE_MANIFEST", knowledge_manifest), \
                 patch("mama_link.foundry.validated_settings", return_value={
                     "AZURE_AI_PROJECT_ENDPOINT": endpoint,
                     "AZURE_AI_MODEL_DEPLOYMENT_NAME": "test-model",
                 }), \
                 patch("mama_link.foundry.project_client", return_value=project_context), \
                 patch("mama_link.foundry.run_agent", side_effect=tool_result) as tool_agent, \
                 patch("mama_link.foundry.run_knowledge_agent", return_value=knowledge_result) as knowledge_agent:
                result = demo("MAT-005")

            self.assertEqual([item["role"] for item in result["agents"]], list(PIPELINE_ROLES))
            self.assertEqual([call.args[2] for call in tool_agent.call_args_list],
                             [role for role in PIPELINE_ROLES if role != "knowledge"])
            knowledge_agent.assert_called_once()
            self.assertIs(tool_agent.call_args_list[0].args[0], client)
            self.assertEqual(result["knowledge_status"], "connected_pending_clinical_review")

    def test_bootstrap_chat_updates_only_chat_reference_and_model(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest_path = Path(directory) / "agents.json"
            endpoint = "https://example.services.ai.azure.com/api/projects/mama-link"
            manifest_path.write_text(json.dumps({
                "endpoint": endpoint,
                "contract_version": "existing-contract",
                "chat_model": "old-model",
                "agents": {
                    "triage": {"name": "mama-link-triage", "version": "7"},
                    "chat": {"name": "mama-link-chat", "version": "1"},
                },
            }), encoding="utf-8")
            project_context = MagicMock()
            project = project_context.__enter__.return_value
            project.agents.create_version.return_value = SimpleNamespace(
                name="mama-link-chat", version=2)

            with patch("mama_link.foundry.MANIFEST", manifest_path), \
                 patch("mama_link.foundry.validated_settings", return_value={
                     "AZURE_AI_PROJECT_ENDPOINT": endpoint,
                     "AZURE_AI_MODEL_DEPLOYMENT_NAME": "gpt-4.1-mini",
                 }), \
                 patch("mama_link.foundry.project_client", return_value=project_context):
                result = bootstrap_chat()
                reference = chat_agent_reference("gpt-4.1-mini")

            saved = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(result["created"]["chat"]["version"], "2")
            self.assertEqual(saved["chat_model"], "gpt-4.1-mini")
            self.assertEqual(saved["contract_version"], "existing-contract")
            self.assertEqual(saved["agents"]["triage"]["version"], "7")
            self.assertEqual(reference, {"name": "mama-link-chat", "version": "2"})
            self.assertIsNone(chat_agent_reference("gpt-4.1"))

    def test_bootstrap_tools_preserves_chat_and_updates_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest_path = Path(directory) / "agents.json"
            endpoint = "https://example.services.ai.azure.com/api/projects/mama-link"
            chat_reference = {"name": "mama-link-chat", "version": "2"}
            manifest_path.write_text(json.dumps({
                "endpoint": endpoint,
                "chat_model": "gpt-4.1-mini",
                "agents": {"chat": chat_reference},
            }), encoding="utf-8")
            project_context = MagicMock()
            references = {
                role: {"name": agent_name(role), "version": "9"}
                for role in TOOL_ROLES
            }

            with patch("mama_link.foundry.MANIFEST", manifest_path), \
                 patch("mama_link.foundry.validated_settings", return_value={
                     "AZURE_AI_PROJECT_ENDPOINT": endpoint,
                     "AZURE_AI_MODEL_DEPLOYMENT_NAME": "gpt-4.1-mini",
                 }), \
                 patch("mama_link.foundry.project_client", return_value=project_context), \
                 patch("mama_link.foundry.create_tool_agents", return_value=references):
                result = bootstrap_tools()

            saved = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(result["contract_version"], AGENT_CONTRACT_VERSION)
            self.assertEqual(saved["agents"]["chat"], chat_reference)
            self.assertEqual(saved["chat_model"], "gpt-4.1-mini")
            self.assertEqual(set(saved["agents"]), set(TOOL_ROLES) | {"chat"})
