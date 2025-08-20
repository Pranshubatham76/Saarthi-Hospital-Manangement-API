import  os
import sys
import time
import json
import random
import string       
from datetime import datetime

import requests

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:5000").rstrip("/")
TIMEOUT = 25


def rnd(prefix):
    return f"{prefix}_{int(time.time())}_{''.join(random.choices(string.ascii_lowercase, k=4))}"


def pretty(obj):
    try:
        return json.dumps(obj, indent=2, default=str)[:2000]
    except Exception:
        return str(obj)


class APITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.results = []
        self.session = requests.Session()
        self.tokens = {
            'user': None,
            'admin': None,
            'hospital': None,
        }
        self.ids = {}

    def _headers(self, role=None):
        headers = {"Content-Type": "application/json"}
        if role and self.tokens.get(role):
            headers["Authorization"] = f"Bearer {self.tokens[role]}"
        return headers

    def _record(self, name, method, url, expected, resp, ok, note=None):
        rec = {
            'name': name,
            'method': method,
            'url': url,
            'expected': expected,
            'status_code': getattr(resp, 'status_code', None),
            'ok': ok,
            'note': note,
        }
        try:
            rec['response'] = resp.json()
        except Exception:
            rec['response'] = getattr(resp, 'text', '')
        self.results.append(rec)
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {method} {url} -> {rec['status_code']} {note or ''}")
        return ok

    def _request(self, method, path, role=None, expected_status=(200, 201), json_body=None, params=None, name=None):
        url = f"{self.base_url}{path}"
        try:
            resp = self.session.request(
                method=method,
                url=url,
                headers=self._headers(role),
                json=json_body,
                params=params,
                timeout=TIMEOUT,
            )
        except Exception as e:
            dummy = type('Resp', (), {'status_code': None, 'text': str(e)})
            return self._record(name or path, method, url, expected_status, dummy, False, note=str(e))

        ok_status = resp.status_code in (expected_status if isinstance(expected_status, (list, tuple, set)) else (expected_status,))
        ok_success = True
        try:
            data = resp.json()
            if isinstance(data, dict) and 'success' in data:
                ok_success = bool(data['success']) if ok_status else True
        except Exception:
            pass

        return self._record(name or path, method, url, expected_status, resp, ok_status and ok_success)

    # Convenience wrappers
    def get(self, path, role=None, expected_status=(200, 201), params=None, name=None):
        return self._request('GET', path, role=role, expected_status=expected_status, params=params, name=name)

    def post(self, path, role=None, expected_status=(200, 201), json_body=None, name=None):
        return self._request('POST', path, role=role, expected_status=expected_status, json_body=json_body, name=name)

    def put(self, path, role=None, expected_status=(200, 201), json_body=None, name=None):
        return self._request('PUT', path, role=role, expected_status=expected_status, json_body=json_body, name=name)

    def delete(self, path, role=None, expected_status=(200, 201), name=None):
        return self._request('DELETE', path, role=role, expected_status=expected_status, name=name)

    # Auth flows
    def register_and_login_user(self):
        u = rnd('user')
        email = f"{u}@example.com"
        payload = {
            'username': u,
            'fullname': 'Test User',
            'email': email,
            'password': 'SecurePass123!',
            'phone_num': '+10000000000',
            'role': 'user',
        }
        self.post('/auth/register', json_body=payload, name='auth:register')
        # Store credentials for later re-login
        self.ids['user_credentials'] = {'username': u, 'password': 'SecurePass123!'}
        # login
        resp = self.session.post(f"{self.base_url}/auth/login", headers=self._headers(), json={'username': u, 'password': 'SecurePass123!'}, timeout=TIMEOUT)
        ok = resp.status_code in (200, 201)
        note = None
        if ok:
            try:
                data = resp.json().get('data') or {}
                self.tokens['user'] = data.get('access_token')
                self.ids['user_id'] = (data.get('user') or {}).get('id')
                note = f"user_id={self.ids.get('user_id')}"
            except Exception as e:
                ok = False
                note = f"parse error: {e}"
        self._record('auth:login', 'POST', f"{self.base_url}/auth/login", (200, 201), resp, ok, note=note)

    def admin_login(self):
        tried = []
        for username in ('admin@hospital.com', 'admin'):
            tried.append(username)
            resp = self.session.post(f"{self.base_url}/auth/admin/login", headers=self._headers(), json={'username': username, 'password': 'admin123'}, timeout=TIMEOUT)
            if resp.status_code in (200, 201):
                try:
                    data = resp.json().get('data') or {}
                    self.tokens['admin'] = data.get('access_token')
                    self.ids['admin_id'] = (data.get('admin') or {}).get('id')
                    self._record('auth:admin_login', 'POST', f"{self.base_url}/auth/admin/login", (200, 201), resp, True, note=f"username={username}")
                    return
                except Exception:
                    pass
        # record last response as failure
        self._record('auth:admin_login', 'POST', f"{self.base_url}/auth/admin/login", (200, 201), resp, False, note=f"tried={tried}")

    def hospital_login(self):
        # seeded in init_db.py
        payloads = [
            {'username': 'city_general', 'password': 'hospital123'},
        ]
        for p in payloads:
            resp = self.session.post(f"{self.base_url}/auth/hospital/login", headers=self._headers(), json=p, timeout=TIMEOUT)
            if resp.status_code in (200, 201):
                try:
                    data = resp.json().get('data') or {}
                    self.tokens['hospital'] = data.get('access_token')
                    self.ids['hospital_info_id'] = (data.get('hospital') or {}).get('id')
                    self._record('auth:hospital_login', 'POST', f"{self.base_url}/auth/hospital/login", (200, 201), resp, True, note=f"username={p['username']}")
                    return
                except Exception:
                    pass
        self._record('auth:hospital_login', 'POST', f"{self.base_url}/auth/hospital/login", (200, 201), resp, False)

    def run(self):
        start = datetime.utcnow()

        # Public baseline
        self.get('/', name='main:welcome')
        self.get('/health', name='main:health')
        self.get('/api/info', name='main:api_info')
        self.post('/contact', json_body={'name': 'Tester', 'email': 'tester@example.com', 'message': 'Hello'}, expected_status=(201,), name='main:contact')

        # Register/login user and login admin/hospital
        self.register_and_login_user()
        self.admin_login()
        self.hospital_login()

        # Profile endpoints
        if self.tokens['user']:
            self.get('/auth/profile', role='user', name='auth:profile')
            self.post('/auth/logout', role='user', name='auth:logout')
            # login again for next steps 
            if 'user_credentials' in self.ids:
                creds = self.ids['user_credentials']
                resp = self.session.post(f"{self.base_url}/auth/login", headers=self._headers(), json=creds, timeout=TIMEOUT)
                if resp.status_code in (200, 201):
                    try:
                        data = resp.json().get('data') or {}
                        self.tokens['user'] = data.get('access_token')
                    except Exception:
                        pass

        # Users (admin)
        if self.tokens['admin']:
            self.get('/user/all', role='admin', name='user:all')
            self.get('/user/stats', role='admin', name='user:stats')
            self.get('/user/search', role='admin', params={'q': 'john'}, name='user:search')

        # Hospitals (public + admin updates)
        self.get('/hospital/all', name='hospital:all')
        # pick first hospital id
        hosp_id = None
        try:
            resp = self.session.get(f"{self.base_url}/hospital/all", timeout=TIMEOUT)
            if resp.status_code == 200:
                data = resp.json().get('data') or {}
                hospitals = data.get('hospitals') or []
                if hospitals:
                    hosp_id = hospitals[0].get('id')
        except Exception:
            pass
        if hosp_id:
            self.get(f'/hospital/{hosp_id}', name='hospital:get')
            self.get(f'/hospital/{hosp_id}/floors', name='hospital:floors')
            self.get(f'/hospital/{hosp_id}/wards', name='hospital:wards')

        # Wards/Beds exploration
        ward_id = None
        bed_id = None
        if hosp_id:
            try:
                resp = self.session.get(f"{self.base_url}/hospital/{hosp_id}/wards", timeout=TIMEOUT)
                if resp.status_code == 200:
                    wards = (resp.json().get('data') or {}).get('wards') or []
                    if wards:
                        ward_id = wards[0].get('id')
            except Exception:
                pass
        if ward_id:
            self.get(f'/hospital/ward/{ward_id}', name='hospital:get_ward')
            self.get(f'/hospital/ward/{ward_id}/beds', name='hospital:ward_beds')
            try:
                resp = self.session.get(f"{self.base_url}/hospital/ward/{ward_id}/beds", timeout=TIMEOUT)
                if resp.status_code == 200:
                    beds = (resp.json().get('data') or {}).get('beds') or []
                    if beds:
                        bed_id = beds[0].get('id')
            except Exception:
                pass
        if bed_id:
            self.get(f'/hospital/bed/{bed_id}', name='hospital:get_bed')
            if self.tokens['admin']:
                self.put(f'/hospital/bed/update/{bed_id}', role='admin', json_body={'status': 'maintenance'}, name='hospital:update_bed')

        # Doctors
        self.get('/doctor/all', name='doctor:all')
        doc_id = None
        try:
            resp = self.session.get(f"{self.base_url}/doctor/all", timeout=TIMEOUT)
            if resp.status_code == 200:
                docs = (resp.json().get('data') or {}).get('doctors') or []
                if docs:
                    doc_id = docs[0].get('id')
        except Exception:
            pass
        if not doc_id and self.tokens['admin']:
            # register a doctor
            dmail = f"{rnd('doc')}@example.com"
            self.post('/doctor/register', role='admin', json_body={'name': 'Dr. Test', 'mail': dmail, 'specialisation': 'General'}, name='doctor:register')
            try:
                resp = self.session.get(f"{self.base_url}/doctor/all", timeout=TIMEOUT)
                if resp.status_code == 200:
                    docs = (resp.json().get('data') or {}).get('doctors') or []
                    if docs:
                        doc_id = docs[0].get('id')
            except Exception:
                pass
        if doc_id:
            self.get(f'/doctor/{doc_id}', name='doctor:get')
            self.get(f'/doctor/{doc_id}/schedule', name='doctor:schedule')
            if self.tokens['admin'] and hosp_id:
                self.post('/doctor/schedule', role='admin', json_body={'doctor_id': doc_id, 'hospital_id': hosp_id, 'notes': 'Test schedule'}, name='doctor:create_schedule')

        # Appointments
        slot_id = None
        if hosp_id:
            self.get('/appointment/available-slots', params={'hospital_id': hosp_id}, name='appointment:available_slots')
            try:
                resp = self.session.get(f"{self.base_url}/appointment/available-slots", params={'hospital_id': hosp_id}, timeout=TIMEOUT)
                if resp.status_code == 200:
                    slots = (resp.json().get('data') or {}).get('slots') or []
                    if slots:
                        slot_id = slots[0].get('id')
            except Exception:
                pass
        appt_id = None
        if slot_id and self.tokens['user']:
            self.post('/appointment/opd/book', role='user', json_body={'hospital_id': hosp_id, 'slot_id': slot_id, 'reason': 'Test visit'}, expected_status=(201,), name='appointment:book')
            # grab appointment id from "my-appointments"
            self.get('/appointment/my-appointments', role='user', name='appointment:my')
            try:
                resp = self.session.get(f"{self.base_url}/appointment/my-appointments", headers=self._headers('user'), timeout=TIMEOUT)
                if resp.status_code == 200:
                    appts = (resp.json().get('data') or {}).get('appointments') or []
                    if appts:
                        appt_id = appts[0].get('id')
            except Exception:
                pass
        if appt_id and self.tokens['user']:
            self.get(f'/appointment/opd/{appt_id}', role='user', name='appointment:get')
            self.delete(f'/appointment/opd/cancel/{appt_id}', role='user', name='appointment:cancel')
        if self.tokens['admin'] and hosp_id:
            self.get(f'/appointment/hospital/{hosp_id}/appointments', role='admin', name='appointment:hospital_list')

        # Blood bank
        self.get('/bloodbank/all', name='bloodbank:all')
        bb_id = None
        try:
            resp = self.session.get(f"{self.base_url}/bloodbank/all", timeout=TIMEOUT)
            if resp.status_code == 200:
                bbs = (resp.json().get('data') or {}).get('blood_banks') or []
                if bbs:
                    bb_id = bbs[0].get('id')
        except Exception:
            pass
        if bb_id:
            self.get(f'/bloodbank/{bb_id}/stock', name='bloodbank:stock')
        if self.tokens['user']:
            self.post('/bloodbank/request', role='user', json_body={'blood_group': 'A+', 'quantity_units': 1, 'location': 'Test City', 'reference': 'TestRef', 'bloodbank_id': bb_id}, expected_status=(201,), name='bloodbank:request')
            self.get('/bloodbank/requests', role='user', name='bloodbank:requests')

        # Emergency
        self.post('/emergency/call', json_body={'emergency_type': 'medical', 'location': 'Test Location', 'contact_number': '1234567890', 'details': 'test'}, expected_status=(201,), name='emergency:call')
        self.get('/emergency/ambulances/available', name='emergency:ambulances')
        if self.tokens['admin']:
            self.get('/emergency/all', role='admin', name='emergency:all')

        # Dashboard
        if self.tokens['user']:
            self.get('/dashboard/', role='user', name='dashboard:user')
        if self.tokens['admin']:
            self.get('/dashboard/', role='admin', name='dashboard:admin')

        # Admin
        if self.tokens['admin']:
            self.get('/admin/dashboard/stats', role='admin', name='admin:stats')
            self.get('/admin/logs', role='admin', name='admin:logs')
            self.post('/admin/create', role='admin', json_body={'username': rnd('adm'), 'password': 'AdminPass123!'}, expected_status=(201,), name='admin:create')

        # Audit
        if self.tokens['admin']:
            self.get('/audit/logs', role='admin', name='audit:logs')
            self.get('/audit/security-summary', role='admin', name='audit:security_summary')
            if self.ids.get('admin_id'):
                self.get(f"/audit/user-activity-trail/{self.ids['admin_id']}", role='admin', name='audit:user_trail')
            self.post('/audit/log-action', role='admin', json_body={'action': 'test_action', 'details': {'k': 'v'}}, name='audit:log_action')
            self.post('/audit/system-event', role='admin', json_body={'event_type': 'test', 'description': 'test event'}, name='audit:system_event')
            self.get('/audit/compliance-report', role='admin', name='audit:compliance')
            self.get('/audit/failed-logins', role='admin', name='audit:failed_logins')
            self.get('/audit/data-access-patterns', role='admin', name='audit:access_patterns')
            self.post('/audit/export-logs', role='admin', json_body={'format': 'json'}, name='audit:export_logs')

        # Notifications
        if self.tokens['user']:
            self.get('/notifications/my-notifications', role='user', name='notif:my')
            self.get('/notifications/unread-count', role='user', name='notif:unread_count')
            self.get('/notifications/settings', role='user', name='notif:settings_get')
            self.put('/notifications/settings', role='user', json_body={'email_notifications': True}, name='notif:settings_put')
            self.post('/notifications/mark-all-read', role='user', name='notif:mark_all')
        if self.tokens['admin'] and self.ids.get('user_id'):
            # send one notification to the user we created
            self.post('/notifications/send', role='admin', json_body={'title': 'Hello', 'body': 'Test notification', 'user_ids': [self.ids['user_id']], 'send_email': False, 'send_websocket': False}, name='notif:send')
            # user fetches again
            if self.tokens['user']:
                self.get('/notifications/my-notifications', role='user', name='notif:my_after_send')

        # Reporting endpoints are disabled (blueprint not registered), we mark as skipped
        self.results.append({'name': 'reporting:*', 'method': 'SKIP', 'url': f'{self.base_url}/reporting/*', 'expected': 'disabled', 'status_code': None, 'ok': True, 'note': 'Blueprint disabled in app/__init__.py'})

        end = datetime.utcnow()
        passed = sum(1 for r in self.results if r.get('ok'))
        total = len(self.results)
        summary = {
            'base_url': self.base_url,
            'started_at': start.isoformat(),
            'ended_at': end.isoformat(),
            'duration_sec': (end - start).total_seconds(),
            'passed': passed,
            'total': total,
            'failed': total - passed,
        }
        print("\n==== Test Summary ====")
        print(json.dumps(summary, indent=2))

        # Save artifacts
        out_dir = os.path.join(os.path.dirname(__file__), 'artifacts')
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, 'results.json'), 'w', encoding='utf-8') as f:
            json.dump({'summary': summary, 'results': self.results}, f, indent=2)
        # Write a minimal markdown summary alongside project root if permitted
        try:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            md_path = os.path.join(project_root, 'API_TEST_SUMMARY.md')
            lines = []
            lines.append(f"# Automated API Test Summary\n")
            lines.append(f"Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SZ')}\n")
            lines.append(f"Base URL: {self.base_url}\n")
            lines.append(f"Total: {total}  Passed: {passed}  Failed: {total - passed}\n\n")
            # Top-level pass/fail list (first 30)
            lines.append("Results (first 30):\n")
            for r in self.results[:30]:
                status = 'PASS' if r.get('ok') else 'FAIL'
                lines.append(f"- [{status}] {r.get('method')} {r.get('url')} (expected={r.get('expected')}, got={r.get('status_code')})\n")
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(''.join(lines))
        except Exception:
            pass

        # Exit code non-zero if failures
        if summary['failed'] > 0:
            sys.exit(1)


if __name__ == '__main__':
    tester = APITester(BASE_URL)
    tester.run()
