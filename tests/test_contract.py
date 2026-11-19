"""Fast behavioral tests using a deliberately minimal GenLayer boundary double.
These do not emulate GenVM, web providers, consensus, gas or finality.
"""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
class UserError(Exception): pass
class Return:
    def __init__(self, calldata): self.calldata = calldata
public = types.SimpleNamespace(write=lambda f:f, view=lambda f:f)
gl = types.SimpleNamespace(Contract=object, public=public, message=types.SimpleNamespace(sender_address="curator"),
    vm=types.SimpleNamespace(UserError=UserError, Return=Return), eq_principle=types.SimpleNamespace(),
    nondet=types.SimpleNamespace(web=types.SimpleNamespace(), exec_prompt=None))
sys.modules['genlayer'] = types.SimpleNamespace(gl=gl, TreeMap=dict, Address=str, __all__=['gl','TreeMap','Address'])
spec = importlib.util.spec_from_file_location('contract', ROOT/'contracts/curriculum_bridge.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class ContractTests(unittest.TestCase):
    def setUp(self):
        gl.message.sender_address = 'curator'
        self.c = m.CurriculumBridge()
        for name in ('courses','rubrics','requests','assessments','invalidations'): setattr(self.c,name,{})
        self.r = json.loads((ROOT/'examples/programming_rubric.json').read_text())
        self.snapshot = 'Official Python curriculum. ' + 'Variables functions lists debugging assessed programming project. '*3
        gl.nondet.web.render = lambda *args,**kw:self.snapshot
        gl.eq_principle.strict_eq = lambda fn:fn()
        self.a = self.c.register_course('MIT','6.0001','2016','https://ocw.mit.edu/syllabus/')
        self.b = self.c.register_course('Harvard','CS50P','2026','https://cs50.harvard.edu/python/')
        self.rid = self.c.create_rubric(json.dumps(self.r))
        self.id = self.c.request_equivalence(self.a,self.b,self.rid)
        self.raw = {'authenticity':['OFFICIAL','OFFICIAL'],'hours':-1,'competencies':[
            {'id':c['id'],'coverage':'MET','a_quote':'Variables','b_quote':'Variables'} for c in self.r['competencies']]}
        gl.nondet.exec_prompt = lambda p,**kw:json.dumps(self.raw)
        def run(leader,validator):
            self.validator=validator
            result=leader()
            if not validator(Return(copy.deepcopy(result))): raise UserError('Consensus rejected')
            return result
        gl.vm.run_nondet_unsafe=run
    def norm(self):
        return m.normalize(self.raw,self.r,{'snapshot':self.snapshot},{'snapshot':self.snapshot})
    def test_equivalent(self):
        self.assertEqual(json.loads(self.c.evaluate_equivalence(self.id))['verdict'],'EQUIVALENT')
        self.assertFalse(json.loads(self.c.get_equivalence(self.id))['result']['academic_credit_awarded'])
    def test_structured_provider_response(self):
        def provider(prompt, **kwargs):
            self.assertEqual(kwargs.get("response_format"), "json")
            return copy.deepcopy(self.raw)
        gl.nondet.exec_prompt = provider
        self.assertEqual(json.loads(self.c.evaluate_equivalence(self.id))["verdict"], "EQUIVALENT")
    def test_core_gap_overrides_high_score(self):
        self.raw['competencies'][4]['coverage']='PARTIAL'
        self.assertEqual(self.norm()['verdict'],'PARTIAL')
        self.assertGreaterEqual(self.norm()['score'],80)
    def test_not_equivalent(self):
        for row in self.raw['competencies']:row['coverage']='ABSENT'
        self.assertEqual(self.norm()['verdict'],'NOT_EQUIVALENT')
    def test_missing_evidence(self):
        self.raw['competencies'][0].update(coverage='UNKNOWN',a_quote='')
        self.assertEqual(self.norm()['verdict'],'INCONCLUSIVE')
    def test_unknown_hours_only_when_required(self):
        self.assertEqual(self.norm()['verdict'],'EQUIVALENT')
        self.r['min_hours']=30
        self.assertEqual(self.norm()['verdict'],'INCONCLUSIVE')
    def test_insufficient_hours(self):
        self.r['min_hours']=30; self.raw['hours']=20
        self.assertEqual(self.norm()['verdict'],'PARTIAL')
    def test_unverified_source(self):
        self.raw['authenticity'][0]='UNVERIFIED'
        self.assertEqual(self.norm()['verdict'],'INCONCLUSIVE')
    def test_fabricated_quote(self):
        self.raw['competencies'][0]['a_quote']='invented'
        with self.assertRaises(UserError):self.norm()
    def test_target_quote_required(self):
        self.raw['competencies'][0]['b_quote']=''
        with self.assertRaises(UserError):self.norm()
    def test_bad_rubrics(self):
        for change in ('weight','id','core'):
            r=copy.deepcopy(self.r)
            if change=='weight':r['competencies'][0]['weight']=26
            if change=='id':r['competencies'][0]['id']=r['competencies'][1]['id']
            if change=='core':r['competencies'][0]['core']='true'
            with self.assertRaises(UserError):m.validate_rubric(json.dumps(r))
    def test_permissions(self):
        gl.message.sender_address='other'
        with self.assertRaises(UserError):self.c.create_rubric(json.dumps(self.r))
        with self.assertRaises(UserError):self.c.invalidate_assessment(self.id,'stale','')
    def test_idempotence_and_direction(self):
        self.assertEqual(self.id,self.c.request_equivalence(self.a,self.b,self.rid))
        self.assertNotEqual(self.id,self.c.request_equivalence(self.b,self.a,self.rid))
        with self.assertRaises(UserError):self.c.request_equivalence(self.a,self.a,self.rid)
    def test_version_changes_fingerprint(self):
        new=self.c.register_course('MIT','6.0001','2017','https://ocw.mit.edu/syllabus/')
        self.assertNotEqual(new,self.a)
    def test_evidence_changes_fingerprint(self):
        self.snapshot+=' New topic.'
        new=self.c.register_course('MIT','6.0001','2016','https://ocw.mit.edu/syllabus/')
        self.assertNotEqual(new,self.a)
    def test_invalidation_preserves_history(self):
        self.c.evaluate_equivalence(self.id)
        original=self.c.assessments[self.id]
        self.c.invalidate_assessment(self.id,'Syllabus superseded','')
        self.assertEqual(self.c.assessments[self.id],original)
        self.assertEqual(json.loads(self.c.get_equivalence(self.id))['status'],'INVALIDATED')
        with self.assertRaises(UserError):self.c.request_equivalence(self.a,self.b,self.rid)
    def test_double_evaluation_rejected(self):
        self.c.evaluate_equivalence(self.id)
        with self.assertRaises(UserError):self.c.evaluate_equivalence(self.id)
    def test_validator_rejects_tampered_score_and_failure(self):
        result=json.loads(self.c.evaluate_equivalence(self.id))
        for k in ('course_a_hash','course_b_hash','rubric_hash','direction','academic_credit_awarded'):result.pop(k)
        result['score']=0
        self.assertFalse(self.validator(Return(result)))
        self.assertFalse(self.validator(UserError('error')))
    def test_validator_independently_rejects_different_coverage(self):
        result=self.norm()
        self.c.evaluate_equivalence(self.id)
        self.raw['competencies'][0]['coverage']='PARTIAL'
        self.assertFalse(self.validator(Return(result)))
    def test_url_restrictions(self):
        for url in ('http://mit.edu/x','https://127.0.0.1/x','https://evil.com/a.edu','https://evil@mit.edu/x'):
            with self.assertRaises(UserError):self.c.register_course('X','Y','Z',url)
    def test_missing_records(self):
        for fn in (self.c.get_course,self.c.get_rubric,self.c.get_equivalence,self.c.evaluate_equivalence):
            with self.assertRaises(UserError):fn('missing')

if __name__=='__main__':unittest.main()
