from django.utils.unittest.case import TestCase
from django.conf import settings
import simplejson
from corehq.pillows.base import restore_property_dict

from corehq.pillows.reportxform import ReportXFormPillow


CONCEPT_XFORM =  {
   "_id": "concept_xform",
   "domain": "test-domain",
   "form": {
       "@xmlns": "http://openrosa.org/formdesigner/test_concepts",
       "@uiVersion": "1",
       "@name": "Visit",
       "last_visit": "2013-09-01",
       "any_other_sick": {
           "#text": "no",
           "@concept_id": "1907"
       },
       "cur_num_fp": "2",
       "#type": "data",
       "cur_counsel_topics": "bednet handwashing",
       "case": {
           "@xmlns": "http://commcarehq.org/case/transaction/v2",
           "@date_modified": "2013-09-01T11:02:34Z",
           "@user_id": "abcde",
           "@case_id": "test_case_123345",
           "update": {
               "location_code": "",
               "last_visit_counsel_topics": "bednet handwashing",
               "last_visit": "2013-10-09",
               "num_ec": "2"
           }
       },
       "member_available": {
           "#text": "yes",
           "@concept_id": "1890"
       },
       "modern_fp": [
           {
               "fp_type": {
                   "#text": "iud",
                   "@concept_id": "374"
               }
           },
           {
               "fp_type": {
                   "#text": "ij",
                   "@concept_id": "374"
               }
           }
       ],
       "meta": {
           "@xmlns": "http://openrosa.org/jr/xforms",
           "username": "airene",
           "instanceID": "some_form",
           "userID": "some_user",
           "timeEnd": "2013-09-09T11:02:34Z",
           "appVersion": {
               "@xmlns": "http://commcarehq.org/xforms",
               "#text": "some version"
           },
           "timeStart": "2013-09-01T11:22:40Z",
           "deviceID": "unittests"
       },
       "num_using_fp": {
           "#text": "2",
           "@concept_id": "1902"
       },
       "location_code_1": "",
       "counseling": {
           "sanitation_counseling": {
               "handwashing_importance": "",
               "handwashing_instructions": "",
               "when_to_wash_hands": ""
           },
           "counsel_type_ec": "bednet handwashing",
           "previous_counseling": "OK",
           "bednet_counseling": {
               "bednets_reduce_risk": "",
               "wash_bednet": "",
               "all_people_bednet": ""
           }
       },
       "prev_location_code": "",
       "@version": "234",
       "num_ec": {
           "#text": "2",
           "@concept_id": "1901"
       },
       "prev_counsel_topics": "handwashing"
   },
   "initial_processing_complete": True,
   "computed_modified_on_": "2013-10-01T23:13:38Z",
   "app_id": "some_app",
   "auth_context": {
       "user_id": None,
       "domain": "some-domain",
       "authenticated": False,
       "doc_type": "AuthContext"
   },
   "doc_type": "XFormInstance",
   "xmlns": "http://openrosa.org/formdesigner/something",
   "partial_submission": False,
   "#export_tag": [
       "domain",
       "xmlns"
   ],
   "received_on": "2013-10-09T14:21:56Z",
   "submit_ip": "105.230.106.73",
   "computed_": {},
   "openrosa_headers": {
       "HTTP_X_OPENROSA_VERSION": "1.0"
   },
   "history": [
   ]
}



class testReportXFormProcessing(TestCase):
    def testConvertAndRestoreReportXFormDicts(self):
        pillow = ReportXFormPillow(online=False)
        orig = CONCEPT_XFORM
        orig['domain'] = settings.ES_XFORM_FULL_INDEX_DOMAINS[0]
        for_indexing = pillow.change_transform(orig)

        restored = restore_property_dict(for_indexing)

        #appVersion might be munged in meta, so swapping it out
        orig_appversion = orig['form']['meta']['appVersion']
        restored_appversion = restored['form']['meta']['appVersion']
        if isinstance(orig_appversion, dict):
            self.assertEqual(restored_appversion, orig_appversion['#text'])
        else:
            self.assertEqual(restored_appversion, orig_appversion)

        del(orig['form']['meta']['appVersion'])
        del(restored['form']['meta']['appVersion'])

        self.assertNotEqual(for_indexing, orig)
        self.assertNotEqual(for_indexing, restored)

        self.assertEqual(orig, restored)


    def testConceptReportConversion(self):
        pillow = ReportXFormPillow(online=False)
        orig = CONCEPT_XFORM
        orig['domain'] = settings.ES_XFORM_FULL_INDEX_DOMAINS[0]
        for_indexing = pillow.change_transform(orig)

        self.assertTrue(isinstance(for_indexing['form']['last_visit'], dict))
        self.assertTrue('#value' in for_indexing['form']['last_visit'])

        self.assertTrue(isinstance(for_indexing['form']['member_available'], dict))
        self.assertTrue(isinstance(for_indexing['form']['member_available']['#text'], dict))
        self.assertTrue(isinstance(for_indexing['form']['member_available']['@concept_id'], dict))

        self.assertEqual(for_indexing['form']['member_available'],
                         {
                             "#text": {
                                 "#value": "yes"
                             },
                             "@concept_id": {
                                 "#value": "1890"
                             }
                         }
        )
        self.assertEqual(for_indexing['form']['modern_fp'],
                         [
                             {
                                 "fp_type": {
                                     "#text": {
                                         "#value": "iud"
                                     },
                                     "@concept_id": {
                                         "#value": "374"
                                     }
                                 }
                             },
                             {
                                 "fp_type": {
                                     "#text": {
                                         "#value": "ij"
                                     },
                                     "@concept_id": {
                                         "#value": "374"
                                     }
                                 }
                             }
                         ]
        )










