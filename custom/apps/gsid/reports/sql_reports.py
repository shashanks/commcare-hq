from sqlagg.columns import *
from sqlagg.base import AliasColumn
from sqlagg.filters import *
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
    table_name = "gsid_patient_summary"

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
    
    @property
    def columns(self):
        age_fn = lambda x, y: str(x or "-")+"-"+str(y or "-")
        sum_fn = lambda x, y: int(x or 0) + int(y or 0)
        percent_agg_fn = lambda x, m, f: "%(x)s (%(p)s%%)" % {"x": x or 0, "p": (100*int(x or 0) / (sum_fn(m, f) or 1))}
        total_percent_agg_fn = lambda x, y, m, f: "%(x)s (%(p)s%%)" % {"x": sum_fn(x, y), "p": (100*sum_fn(x, y) / (sum_fn(m, f) or 1))}

        patient_number_group = DataTablesColumnGroup("Tests")
        positive_group = DataTablesColumnGroup("Positive Tests")
        age_range_group = DataTablesColumnGroup("Age Range")

        return [
            DatabaseColumn("Clinic Name", SimpleColumn("clinic")),
            
            DatabaseColumn("Number of Males ", 
                            CountColumn('gender', alias="male-total", filters=[EQ("gender", "male")]), 
                            header_group=patient_number_group),
            DatabaseColumn("Number of Females ", 
                            CountColumn('gender', alias="female-total", filters=[EQ("gender", "female")]), 
                            header_group=patient_number_group),
            AggregateColumn("Total", sum_fn, 
                            [AliasColumn("male-total"), AliasColumn("female-total")],
                            header_group=patient_number_group),

            AggregateColumn("Male +ve Percent", percent_agg_fn,
                            [CountColumn("diagnosis", alias="male-positive", filters=[AND([EQ("gender", "male"), EQ("diagnosis", "positive")])]), 
                             AliasColumn("male-total"), AliasColumn("female-total")],
                            header_group=positive_group),
            AggregateColumn("Female +ve Percent", percent_agg_fn,
                            [CountColumn("diagnosis", alias="female-positive", filters=[AND([EQ("gender", "female"), EQ("diagnosis", "positive")])]), 
                             AliasColumn("male-total"), AliasColumn("female-total")],
                            header_group=positive_group),
            AggregateColumn("Total +ve Percent", total_percent_agg_fn,
                            [AliasColumn("female-positive"), 
                             AliasColumn("male-positive"),
                             AliasColumn("male-total"), AliasColumn("female-total")],
                            header_group=positive_group),

            AggregateColumn("Male age range", age_fn,
                            [MinColumn("age", alias="male-min", filters=[EQ("gender", "male")]),
                             MaxColumn("age", alias="male-max", filters=[EQ("gender", "male")])],
                            header_group=age_range_group),
            AggregateColumn("FeMale age range", age_fn,
                            [MinColumn("age", alias="female-min", filters=[EQ("gender", "female")]),
                             MaxColumn("age", alias="female-max", filters=[EQ("gender", "female")])],
                            header_group=age_range_group),
            AggregateColumn("All age range", age_fn,
                            [MinColumn("age", alias="age-min"),
                             MaxColumn("age", alias="age-max")],
                            header_group=age_range_group),
        ]

class GSIDSQLByDayReport(GSIDSQLReport):
    name = "Day Summary Report"
    slug = "day_summary_sql"
    section_name = "day summary"
    
class GSIDSQLTestLotsReport(GSIDSQLReport):
    name = "Test Lots Report"
    slug = "test_lots_sql"
    section_name = "test lots"
    
class GSIDSQLByAgeReport(GSIDSQLReport):
    name = "Age Summary Report"
    slug = "age_summary_sql"
    section_name = "age summary"
    
    @property
    def filter_values(self):
        age_filters = dict(zero=0,
                    ten=10,
                    ten_plus=11,
                    twenty=20,
                    twenty_plus=21,
                    fifty=50)
        default_filter_values = super(GSIDSQLByAgeReport, self).filter_values
        default_filter_values.update(age_filters)
        return default_filter_values

    @property
    def columns(self):
        percent_fn = lambda x, y: "%(x)s (%(p)s%%)" % {"x": int(x or 0), "p": 100*(x or 0) / (y or 1)}
        
        female_range_group = DataTablesColumnGroup("Female Positive Tests (% positive)")
        male_range_group = DataTablesColumnGroup("Male Positive Tests (% positive)")

        def age_range_filter(gender, age_from, age_to):
            return [AND([EQ("gender", gender), EQ("diagnosis", "positive"), BETWEEN("age", age_from, age_to)])]

        def generate_columns(gender):
            age_range_group = male_range_group if gender is "male" else female_range_group
            return [
                AggregateColumn("0-10", percent_fn,
                                [CountColumn("age", alias="zero_ten_" + gender, filters=age_range_filter(gender, "zero", "ten")),
                                 CountColumn("age", alias=gender+"_total", filters=[EQ("gender", gender)])],
                                header_group=age_range_group),
                AggregateColumn("10-20", percent_fn, 
                                [CountColumn("age", alias="ten_twenty_" + gender, filters=age_range_filter(gender, "ten_plus", "twenty")),
                                 AliasColumn(gender+"_total")],
                                header_group=age_range_group),
                AggregateColumn("20-50", percent_fn,
                                [CountColumn("age", alias="twenty_fifty_" + gender, filters=age_range_filter(gender, "twenty_plus", "fifty")),
                                AliasColumn(gender+"_total")],
                                header_group=age_range_group),
                AggregateColumn("50+", percent_fn,
                                [CountColumn("age", alias="fifty_" + gender, filters=[AND([EQ("gender", gender), EQ("diagnosis", "positive"), GT("age", "fifty")])]),
                                AliasColumn(gender+"_total")],
                                header_group=age_range_group),
            ]

        return [DatabaseColumn("Clinic Name", SimpleColumn("clinic"))
               ] + generate_columns("male") + generate_columns("female")

