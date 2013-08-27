from custom.apps.gsid.reports import (GSIDReport)
from custom.apps.gsid.reports.sql_reports import GSIDSQLPatientReport, GSIDSQLByDayReport, GSIDSQLTestLotsReport, \
	GSIDSQLByAgeReport

CUSTOM_REPORTS = (
    ('Custom Reports', (
        # PSIEventsReport,
        #GSIDReport,
        GSIDSQLPatientReport,
        GSIDSQLByDayReport,
        GSIDSQLTestLotsReport,
        GSIDSQLByAgeReport
    )),

)
