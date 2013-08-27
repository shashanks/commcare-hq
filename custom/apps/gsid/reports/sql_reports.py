from sqlagg.columns import *
from sqlagg.base import AliasColumn
from sqlalchemy import func
from corehq.apps.fixtures.models import FixtureDataItem, FixtureDataType
from corehq.apps.reports.basic import Column
from corehq.apps.reports.datatables import DataTablesColumnGroup
from corehq.apps.reports.sqlreport import SqlTabularReport, DatabaseColumn, SummingSqlTabularReport, AggregateColumn
from corehq.apps.reports.standard import CustomProjectReport, DatespanMixin
from util import get_unique_combinations
from dimagi.utils.decorators.memoized import memoized


class GSIDSQLReport(SummingSqlTabularReport, CustomProjectReport, DatespanMixin):
    fields = ['custom.apps.gsid.reports.AsyncTestField', DatespanMixin.datespan_field, 'custom.apps.gsid.reports.AsyncClinicField']

    name = "Basic sql report"
    exportable = True
    emailable = True
    slug = "my_basic_sql"
    section_name = "event demonstrations"

    @property
    def group_by(self):
        return ["clinic"]

    @property
    def filter_values(self):
        return dict(domain=self.domain,
                    startdate=self.datespan.startdate_param_utc,
                    enddate=self.datespan.enddate_param_utc,
                    male="male",
                    female="female",
                    positive="Positive")

    @property
    def filters(self):
        return ["date between :startdate and :enddate"]

    @property
    def keys(self):
        return [['highpoint'], ['high_point']]

    def selected_fixture(self):
        fixture = self.request.GET.get('fixture_id', "")
        return fixture.split(':') if fixture else None

    @property
    @memoized
    def place_types(self):
        opts = ['state', 'district', 'block', 'village']
        agg_at = self.request.GET.get('aggregate_at', None)
        agg_at = agg_at if agg_at and opts.index(agg_at) <= opts.inAliasColumndex(self.default_aggregation) else self.default_aggregation
        return opts[:opts.index(agg_at) + 1]

class GSIDSQLPatientReport(GSIDSQLReport):

    name = "Patient Summary Report"
    slug = "patient_summary_sql"
    section_name = "patient summary"
    table_name = "gsid_patient_summary"

    @property
    def columns(self):
        agg_fn = lambda x, y: str(x)+"-"+str(y)
        sum_agg_fn = lambda x, y: x + y
        patient_number_group = DataTablesColumnGroup("Tests")
        positive_group = DataTablesColumnGroup("Positive Tests")
        age_range_group = DataTablesColumnGroup("Age Range")
        return [
            DatabaseColumn("Clinic Name", SimpleColumn("clinic")),
            DatabaseColumn("Number of Males ", CountColumn('gender', alias="male-total", filters=["gender = :male"]), header_group=patient_number_group),
            DatabaseColumn("Number of Females ", CountColumn('gender', alias="female-total", filters=["gender = :female"]), header_group=patient_number_group),
            DatabaseColumn("Number of Male Postives", CountColumn("diagnosis", alias="male-positive", filters=["gender = :male", "diagnosis = :positive"]), header_group=positive_group),
            DatabaseColumn("Number of Female Postives", CountColumn("diagnosis", alias="female-positive", filters=["gender = :female", "diagnosis = :positive"]), header_group=positive_group),
            #DatabaseColumn("Number of Male Postives", CountColumn("diagnosis", alias="male-positive", filters=["gender = :male", "diagnosis = :positive"])),
            #DatabaseColumn("Number of Female Postives", CountColumn("diagnosis", alias="female-positive", filters=["gender = :female", "diagnosis = :positive"])),
            #DatabaseColumn("num of", agg_fn, AliasColumn("male-positive"), AliasColumn("female-positive")),
            DatabaseColumn("Total", AggregateColumn(sum_agg_fn, AliasColumn("male-total"), AliasColumn("female-total"))),
            #CountColumn("gender", filters=['gender = :male']),
            #DatabaseColumn("Total Male", CountColumn("gender", filters=['gender = :male'])),
            #SumColumn("Total Female", filters=['sex = :female']),
            #AggregateColumn("age", agg_fn, MaxColumn('age', filters=['gender = :male']), MinColumn('age', filters=['gender = :male'])),
            #DatabaseColumn("Male range", AggregateColumn(agg_fn, MaxColumn('age', filters=['gender = :male']), MinColumn('age', filters=['gender = :male']))),            
        ]

class GSIDSQLByDayReport(GSIDSQLReport):
    name = "Day Summary Report"
    slug = "day_summary_sql"
    section_name = "day summary"
    table_name = "gsid_results_by_day"

class GSIDSQLTestLotsReport(GSIDSQLReport):
    name = "Test Lots Report"
    slug = "test_lots_sql"
    section_name = "test lots"
    table_name = "gsid_test_lots"

class GSIDSQLByAgeReport(GSIDSQLReport):
    name = "Age Summary Report"
    slug = "age_summary_sql"
    section_name = "age summary"
    table_name = "gsid_results_by_age"

    @property
    def filter_values(self):
        default_filter_values = super(GSIDSQLByAgeReport, self).filter_values
        age_filters = dict(zero=0,
                    ten=10,
                    twenty=20,
                    fifty=50)
        return default_filter_values.update(age_filters)

    @property
    def columns(self):
        return [
            DatabaseColumn("Clinic Name", SimpleColumn("clinic")),
        ]
