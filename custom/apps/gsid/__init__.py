from custom.apps.gsid.reports import (GSIDReport)
from custom.apps.gsid.reports.sql_reports import GSIDSQLReport

CUSTOM_REPORTS = (
    ('Custom Reports', (
        # PSIEventsReport,
        #GSIDReport,
        GSIDSQLReport
    )),

)
