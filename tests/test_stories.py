import json
import tempfile
import threading
import unittest
from studio import Store, Worker
from stories import StoryService
from test_studio import fake_provider


class StoryContractTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.store=Store(self.temp.name); self.service=StoryService(self.store)
    def tearDown(self):
        self.temp.cleanup()
    def story(self):
        return self.service.execute('story.create', {'project_id':'realify','title':'La boussole','premise':'Trois héroïnes cherchent une île.','subjects':['Nami','Robin','Boa'],'continuity':'Boussole turquoise, vêtements de voyage.'},'create-story')
    def test_episode_continuity_and_replay(self):
        story=self.story(); data={'story_id':story['id']}
        pack=self.service.execute('story.next',data,'episode-1')
        self.assertEqual(pack,self.service.execute('story.next',data,'episode-1'))
        self.assertEqual(len(self.store.jobs()),1)
        with self.assertRaises(ValueError): self.service.execute('story.next',data,'too-early')
        Worker(self.store,fake_provider).run_one()
        self.store.feedback(pack['id'],{'text':'Conserver les mêmes visages.'})
        p2=self.service.execute('story.next',data,'episode-2');self.assertEqual(p2['episode_number'],2)
        Worker(self.store,fake_provider).run_one()
        job=next(j for j in self.store.jobs() if j['pack_id']==p2['id'])
        brief=json.loads((self.store.runtime/'jobs'/job['id']/'brief.json').read_text())
        self.assertEqual(brief['story_context']['previous'][0]['pack_id'],pack['id'])
        self.assertIn('Conserver les mêmes visages.',json.dumps(brief,ensure_ascii=False))
        self.assertEqual(len(brief['continuity_images']),2)
        self.assertEqual(len(self.service.story(story['id'])['episodes']),2)
        with self.assertRaises(ValueError): self.service.execute('pack.create',{'project_id':'realify'},'episode-1')
    def test_concurrent_replay_creates_one_job(self):
        story=self.story();results=[]
        threads=[threading.Thread(target=lambda:results.append(self.service.execute('story.next',{'story_id':story['id']},'same-request')['id'])) for _ in range(2)]
        for t in threads:t.start()
        for t in threads:t.join()
        self.assertEqual(len(results),2);self.assertEqual(results[0],results[1]);self.assertEqual(len(self.store.jobs()),1)
    def test_failed_creation_rolls_back_episode_and_request(self):
        story=self.story()
        with self.assertRaises(ValueError):self.service.execute('story.next',{'story_id':story['id'],'notes':'x'*2001},'bad')
        self.assertEqual(self.service.story(story['id'])['episodes'],[])
        self.assertEqual(self.store.jobs(),[])
        self.service.execute('story.next',{'story_id':story['id']},'bad')
    def test_correction_request_is_replayed_after_completion(self):
        p=self.service.execute('pack.create',{'project_id':'realify','count':1},'pack')
        Worker(self.store,fake_provider).run_one()
        data={'pack_id':p['id'],'slot':'cover','instruction':'Lumière naturelle.'}
        j=self.service.execute('pack.correct',data,'edit');Worker(self.store,fake_provider).run_one()
        self.assertEqual(j,self.service.execute('pack.correct',data,'edit'))
        self.assertEqual(len(self.store.pack(p['id'])['slots'][0]['versions']),2)
    def test_attach_existing_post_preserves_images_and_next_continues(self):
        p=self.store.create_pack({'project_id':'realify'});Worker(self.store,fake_provider).run_one();p=self.store.pack(p['id'])
        original=[s['active'] for s in p['slots']];story=self.story()
        attached=self.service.execute('story.attach',{'story_id':story['id'],'pack_id':p['id']},'attach')
        self.assertEqual([s['active'] for s in attached['slots']],original)
        published=self.store.publish(p['id'],{})
        self.assertEqual(published['next']['episode_number'],2)
        self.assertEqual(published['next']['story_id'],story['id'])
    def test_agent_resolves_feedback_without_removing_preferences(self):
        p=self.service.execute('pack.create',{'project_id':'realify','count':1},'p')
        feedback=self.service.execute('pack.feedback',{'pack_id':p['id'],'text':'Plus de lumière.'},'f')['feedback'][-1]
        result=self.service.execute('feedback.resolve',{'pack_id':p['id'],'feedback_id':feedback['id'],'resolution':'Pris en compte dans la prochaine scène.'},'r')
        self.assertEqual(result['feedback'][-1]['text'],'Plus de lumière.')
        self.assertTrue(result['feedback'][-1]['resolved_at'])
    def test_update_future_story_preserves_generated_episode_plan(self):
        story=self.story();self.service.execute('story.next',{'story_id':story['id']},'first')
        outline=story['outline'];outline[1]['beat']='La nouvelle conséquence du retour du créateur.'
        updated=self.service.execute('story.update',{'story_id':story['id'],'outline':outline},'update')
        self.assertEqual(updated['outline'][1]['beat'],outline[1]['beat'])
        outline[0]['beat']='Réécrire le passé.'
        with self.assertRaises(ValueError):self.service.execute('story.update',{'story_id':story['id'],'outline':outline},'bad-update')
    def test_generic_series_brief_stays_in_its_own_universe(self):
        project=self.store.create_project({'name':'Botanique','universe':'Jardin','direction':'Illustration botanique','subjects':['Orchidée'],'ratio':'1:1'})
        story=self.service.execute('story.create',{'project_id':project['id'],'title':'Une graine','premise':'Suivre une germination.'},'botanical-story')
        p=self.service.execute('story.next',{'story_id':story['id']},'botanical-episode')
        Worker(self.store,fake_provider).run_one()
        job=self.store.jobs()[0];folder=self.store.runtime/'jobs'/job['id']
        brief=json.loads((folder/'brief.json').read_text())
        self.assertEqual(brief['project']['universe'],'Jardin')
        self.assertEqual(brief['style_reference_images'],[])
        self.assertEqual(brief['ratio'],'1:1')
        self.assertEqual(p['story_context']['premise'],'Suivre une germination.')
        self.assertEqual(self.service.stories('realify'),[])
    def test_received_files_are_not_marked_ready_before_validation(self):
        p=self.store.create_pack({'project_id':'realify','count':1});job=self.store.jobs()[0]
        with self.store.db() as db:db.execute("UPDATE jobs SET state='running' WHERE id=?",(job['id'],))
        folder=self.store.runtime/'jobs'/job['id']/'images';folder.mkdir(parents=True);(folder/'cover.png').write_bytes(b'not a validated image')
        reported=self.store.jobs()[0]
        self.assertEqual(reported['received_slots'],['cover'])
        self.assertEqual(reported['completed_slots'],[])
        self.assertIsNone(self.store.pack(p['id'])['slots'][0]['active'])
    def test_episode_references_do_not_include_unrelated_archive_cast(self):
        story=self.story();p=self.service.execute('story.next',{'story_id':story['id']},'one')
        Worker(self.store,fake_provider).run_one()
        p2=self.service.execute('story.next',{'story_id':story['id']},'two');Worker(self.store,fake_provider).run_one()
        job=next(j for j in self.store.jobs() if j['pack_id']==p2['id']);brief=json.loads((self.store.runtime/'jobs'/job['id']/'brief.json').read_text())
        self.assertEqual(brief['style_reference_images'],[])
        self.assertEqual(len(brief['continuity_images']),2)
    def test_agent_recovers_finished_artifacts_without_another_generation(self):
        p=self.store.create_pack({'project_id':'realify','count':2});job=self.store.jobs()[0]
        folder=self.store.runtime/'jobs'/job['id'];folder.mkdir(parents=True)
        worker=Worker(self.store,fake_provider);worker.prepare(job,p,folder);fake_provider(job,folder)
        with self.store.db() as db:db.execute("UPDATE jobs SET state='failed' WHERE id=?",(job['id'],))
        with self.assertRaises(ValueError):self.service.execute('job.recover',{'job_id':job['id']},'recover')
        (folder/'result.txt').write_text('Test fixture: completed output files.')
        result=self.service.execute('job.recover',{'job_id':job['id']},'recover')
        self.assertEqual(result['state'],'completed');self.assertEqual(len(self.store.jobs()),1)
        self.assertEqual(self.store.pack(p['id'])['status'],'ready')
        self.assertEqual(result,self.service.execute('job.recover',{'job_id':job['id']},'recover'))
        self.assertEqual(len(self.store.pack(p['id'])['slots'][0]['versions']),1)
    def test_completed_series_does_not_generate_an_unrelated_fourth_post(self):
        project=self.store.project('realify');project['auto_next']=False;self.store.put_project(project)
        story=self.story()
        for number in range(1,4):
            pack=self.service.execute('story.next',{'story_id':story['id']},f'episode-{number}')
            Worker(self.store,fake_provider).run_one()
            if number<3:self.store.publish(pack['id'],{})
        with self.assertRaises(ValueError):self.service.execute('story.next',{'story_id':story['id']},'fourth')
        project['auto_next']=True;self.store.put_project(project)
        self.assertIsNone(self.store.publish(pack['id'],{})['next'])
        self.assertEqual(len(self.store.packs()),3)
    def test_explicit_local_budget_is_enforced_atomically(self):
        import os
        from unittest.mock import patch
        with patch.dict(os.environ,{'STUDIO_DAILY_IMAGES':'1'}):
            self.service.execute('pack.create',{'project_id':'realify','count':1},'first-image')
            with self.assertRaises(ValueError):self.service.execute('pack.create',{'project_id':'realify','count':1},'over-budget')
        self.assertEqual(len(self.store.packs()),1)
        self.assertEqual(len(self.store.jobs()),1)
