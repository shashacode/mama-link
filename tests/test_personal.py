import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from mama_link.api import create_app

H = {'X-Mama-Link': 'local-demo'}


class PersonalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.app = create_app(Path(self.temp.name) / 'test.db')
        self.a = TestClient(self.app, headers=H)
        self.b = TestClient(self.app, headers=H)
        for client, name in [(self.a, 'amaka'), (self.b, 'bisi')]:
            self.assertEqual(client.post('/api/register', json={'username': name, 'password': 'fictional-password', 'profile': {'name': name.title(), 'synthetic': True}}).status_code, 200)

    def tearDown(self):
        self.a.close(); self.b.close(); self.temp.cleanup()

    def body(self):
        return {'case': {'synthetic': True, 'pregnancy_stage': 'unknown', 'symptoms': {}}}

    def payload(self):
        return {'source': 'sample_device', 'provider': 'apple_health', 'device_name': 'Fictional sample', 'synthetic': True, 'reviewed': True,
                'measurements': [{'metric': 'heart_rate', 'value': 83, 'unit': 'bpm', 'measured_at': datetime.now(timezone.utc).isoformat()}]}

    def test_private_accounts_and_admin_routes(self):
        other_id = self.b.get('/api/me').json()['user']['id']
        self.assertEqual(self.a.get('/api/history', headers={'X-Mama-Account':other_id}).status_code,401)
        for path in ['/api/cases', '/api/evaluation', '/api/hotspots']:
            self.assertEqual(self.a.get(path).status_code, 403)
        self.assertEqual(self.a.post('/api/assessments', json={'case_id': 'MAT-005'}).status_code, 403)
        record = self.a.post('/api/assessments', json=self.body()).json()
        self.assertEqual(record['result']['risk']['classification'], 'unassessed')
        self.assertEqual(self.b.get('/api/history').json(), [])
        self.assertEqual(self.b.post('/api/assessments/'+record['id']+'/consent', json={'consent': True, 'facility_id': 'FAC-002'}).status_code, 404)
        self.a.post('/api/logout')
        self.assertEqual(self.a.get('/api/history').status_code, 401)
        self.assertEqual(self.a.post('/api/login', json={'username': 'amaka', 'password': 'wrong-password'}).status_code, 401)
        self.assertEqual(self.a.post('/api/login', json={'username': 'amaka', 'password': 'fictional-password'}).status_code, 200)
        self.assertEqual(len(self.a.get('/api/history').json()), 1)

    def test_import_consent_ownership_provenance_override_and_revocation(self):
        payload = self.payload()
        self.assertEqual(self.a.post('/api/device/import', json=payload).status_code, 403)
        for client in [self.a, self.b]: client.put('/api/device', json={'enabled': True})
        imported = self.a.post('/api/device/import', json=payload).json()
        body = self.body() | {'import_id': imported['id']}
        self.assertEqual(self.b.post('/api/assessments', json=body).status_code, 404)
        record = self.a.post('/api/assessments', json=body).json()
        self.assertEqual(record['case']['readings']['heart_rate']['value'], 83)
        self.assertEqual(record['case']['provenance']['heart_rate']['source'], 'sample_device')
        body['case']['readings'] = {'heart_rate': 90}
        record = self.a.post('/api/assessments', json=body).json()
        self.assertEqual(record['case']['readings']['heart_rate']['value'], 90)
        self.assertEqual(record['case']['provenance']['heart_rate']['source'], 'manual_entry')
        self.a.put('/api/device', json={'enabled': False})
        self.assertEqual(self.a.get('/api/device').json()['imports'], [])
        self.assertEqual(self.a.post('/api/assessments', json=body).status_code, 403)

    def test_import_rejects_stale_future_bad_units_and_duplicate_metrics(self):
        self.a.put('/api/device', json={'enabled': True})
        for change in [{'unit':'C'}, {'value': float('inf')}, {'measured_at':(datetime.now(timezone.utc)-timedelta(days=2)).isoformat()}, {'measured_at':(datetime.now(timezone.utc)+timedelta(days=1)).isoformat()}]:
            payload=self.payload();payload['measurements'][0].update(change)
            if change.get('value') == float('inf'):
                payload['measurements'][0]['value']='Infinity'
            self.assertEqual(self.a.post('/api/device/import',json=payload).status_code,422)
        payload=self.payload();payload['measurements']*=2
        self.assertEqual(self.a.post('/api/device/import',json=payload).status_code,422)

    def test_chat_safety_and_no_cloud_without_consent(self):
        with patch('mama_link.chat.project_client') as cloud:
            for question, mode in [('Can I take ibuprofen?', 'local_medication_guidance'), ('I am bleeding heavily', 'local_safety_message'), ('I feel worried', 'consent_required')]:
                r=self.a.post('/api/chat',json={'message':question}).json()
                self.assertEqual(r['mode'],mode)
            cloud.assert_not_called()
        self.assertEqual(self.a.get('/api/history').json(),[])

    def test_general_pregnancy_questions_are_educational_not_diagnostic(self):
        from mama_link.chat import answer
        with patch('mama_link.chat.configuration',return_value={'configured':False,'specialist_configured':False,'model':'','mode':'foundry_education'}):
            reply=answer('Is nausea in early pregnancy normal?', {'pregnancy_stage':'first_trimester','gestational_age':8}, [], True)
            self.assertEqual(reply['mode'],'local_education')
            self.assertIn('general pregnancy education', reply['answer'].lower())
            self.assertIn('not a diagnosis or treatment plan', reply['answer'].lower())
            self.assertNotIn('i am diagnosing', reply['answer'].lower())
            self.assertIn('midwife', reply['answer'].lower())
            self.assertIn('urgent care', reply['answer'].lower())

    def test_cloud_failure_is_not_misrepresented_as_an_agent_answer(self):
        from mama_link.chat import answer
        config = {'configured': True, 'specialist_configured': False, 'model': 'demo-model', 'mode': 'foundry_education'}
        with patch('mama_link.chat.configuration', return_value=config), patch('mama_link.chat.project_client', side_effect=RuntimeError('auth unavailable')):
            reply = answer('Is nausea in early pregnancy normal?', {'name': 'Test User'}, [], True)
            self.assertEqual(reply['mode'], 'unavailable')
            self.assertIn('online education agent is temporarily unavailable', reply['answer'].lower())
            self.assertEqual(reply['sources'], [])

    def test_chat_passes_only_current_account_context(self):
        self.a.post('/api/assessments',json=self.body())
        with patch('mama_link.api.chat.answer',return_value={'answer':'ok'}) as answer:
            self.b.post('/api/chat',json={'message':'How can I prepare?', 'share_context':True})
            self.assertEqual(answer.call_args.args[1]['name'],'Bisi')
            self.assertEqual(answer.call_args.args[2],[])

    def test_public_learning_and_no_account_required(self):
        with TestClient(self.app) as guest:
            self.assertEqual(guest.get('/api/education').status_code,200)
            self.assertEqual(guest.get('/static/mama-link-guide.html').status_code,200)
            self.assertEqual(guest.get('/api/cases').status_code,401)
            self.assertEqual(guest.get('/api/history').status_code,401)

    def test_cloud_payload_excludes_identity_and_supports_conversation(self):
        from mama_link.chat import answer
        config = {'configured':True, 'specialist_configured':True, 'model':'test-health-model', 'mode':'specialist_foundry'}
        with patch('mama_link.chat.configuration',return_value=config), patch('mama_link.chat.specialist_reply',return_value='Bring your questions to your visit.') as model:
            reply=answer('Help me prepare', {'name':'Must not be sent','username':'private','pregnancy_stage':'second_trimester','gestational_age':22}, [], True, [{'role':'user','content':'I am nervous'}])
            payload=model.call_args.args[0]
            self.assertNotIn('name',payload['pregnancy_context'])
            self.assertNotIn('username',payload['pregnancy_context'])
            self.assertEqual(payload['pregnancy_context']['gestational_age'],22)
            self.assertEqual(len(payload['conversation']),1)
            self.assertEqual(reply['mode'],'specialist_foundry')

    def test_specialist_failure_never_falls_back_silently(self):
        from mama_link.chat import answer
        config={'configured':True,'specialist_configured':True,'model':'test-health-model','mode':'specialist_foundry'}
        with patch('mama_link.chat.configuration',return_value=config), patch('mama_link.chat.specialist_reply',side_effect=RuntimeError('private provider error')), patch('mama_link.chat.project_client') as general:
            reply=answer('Help me prepare',{},[],True)
            self.assertEqual(reply['mode'],'unavailable')
            self.assertNotIn('private provider error',reply['answer'])
            general.assert_not_called()
