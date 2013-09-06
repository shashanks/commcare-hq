from sqlagg.columns import *
from sqlagg.base import AliasColumn
from sqlagg.filters import *
from sqlalchemy import func
from corehq.apps.fixtures.models import FixtureDataItem, FixtureDataType
from corehq.apps.reports.basic import Column
from corehq.apps.reports.datatables import DataTablesColumn, DataTablesHeader, DataTablesColumnGroup
from corehq.apps.reports.sqlreport import SqlTabularReport, DatabaseColumn, SummingSqlTabularReport, AggregateColumn
from corehq.apps.reports.standard import CustomProjectReport, DatespanMixin
from util import get_unique_combinations
from dimagi.utils.decorators.memoized import memoized

from datetime import datetime, timedelta

class GSIDSQLReport(SummingSqlTabularReport, CustomProjectReport, DatespanMixin):
    fields = ['custom.apps.gsid.reports.TestField', 
              DatespanMixin.datespan_field, 
              'custom.apps.gsid.reports.AsyncClinicField',
              'custom.apps.gsid.reports.AggregateAtField']

    name = "Basic sql report"
    exportable = True
    emailable = True
    slug = "my_basic_sql"
    section_name = "event demonstrations"
    table_name = "gsid_patient_summary"
    default_aggregation = "clinic"

    @property
    def filter_values(self):
        ret = dict(domain=self.domain,
                   startdate=self.datespan.startdate_param_utc,
                   enddate=self.datespan.enddate_param_utc,
                   male="male",
                   female="female",
                   positive="Positive"
                )

        disease_fixtures = FixtureDataItem.by_data_type(
                                self.domain, 
                                FixtureDataType.by_domain_tag(self.domain, "diseases").one()
                        )
        test_fixtures = FixtureDataItem.by_data_type(
                            self.domain, 
                            FixtureDataType.by_domain_tag(self.domain, "tests").one()
                        )
        DISEASES = [d.fields["disease_id"] for d in disease_fixtures]
        TESTS = [t.fields["test_name"] for t in test_fixtures]

        ret.update(zip(DISEASES, DISEASES))
        ret.update(zip(TESTS, TESTS))

        return ret

    @property
    def filters(self):
        return [EQ("domain", "domain"), BETWEEN("date", "startdate", "enddate")] + self.disease_filters

    @property
    def disease_filters(self):
        disease = self.request.GET.get('test_type_disease', '')
        test = self.request.GET.get('test_type_test', '')
        disease = disease.split(':') if disease else None
        test = test.split(':') if test else None
        filters = []
        if test:
            filters.append(EQ("test_version", test[0]))
        elif disease:
            filters.append(EQ("disease_name", disease[0]))

        return filters

    @property
    def group_by(self):
        return self.place_types
        return ["clinic"]

    @property
    def keys(self):
        combos = get_unique_combinations(self.domain, place_types=self.place_types, place=self.selected_fixture())
        for c in combos:
            yield [c[pt] for pt in self.place_types]
        #return [['highpoint'], ['high_point']]

    def selected_fixture(self):
        fixture = self.request.GET.get('fixture_id', "")
        return fixture.split(':') if fixture else None

    @property
    @memoized
    def place_types(self):
        opts = ['country', 'province', 'district', 'clinic']
        agg_at = self.request.GET.get('aggregate_at', None)
        agg_at = agg_at if agg_at and opts.index(agg_at) <= opts.index(self.default_aggregation) else self.default_aggregation
        return opts[:opts.index(agg_at) + 1]

    @property
    def common_columns(self):
        columns = []
        for place in self.place_types:
            columns.append(DatabaseColumn(place.capitalize(), SimpleColumn(place)))

        return columns

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

        return self.common_columns + [
            
            DatabaseColumn("Number of Males ", 
                            CountColumn('gender', alias="male-total", filters= self.filters + [EQ("gender", "male")]), 
                            header_group=patient_number_group),
            DatabaseColumn("Number of Females ", 
                            CountColumn('gender', alias="female-total", filters= self.filters + [EQ("gender", "female")]), 
                            header_group=patient_number_group),
            AggregateColumn("Total", sum_fn, 
                            [AliasColumn("male-total"), AliasColumn("female-total")],
                            header_group=patient_number_group),

            AggregateColumn("Male +ve Percent", percent_agg_fn,
                            [CountColumn("diagnosis", alias="male-positive", filters= self.filters + [AND([EQ("gender", "male"), EQ("diagnosis", "positive")])]), 
                             AliasColumn("male-total"), AliasColumn("female-total")],
                            header_group=positive_group),
            AggregateColumn("Female +ve Percent", percent_agg_fn,
                            [CountColumn("diagnosis", alias="female-positive", filters= self.filters + [AND([EQ("gender", "female"), EQ("diagnosis", "positive")])]), 
                             AliasColumn("male-total"), AliasColumn("female-total")],
                            header_group=positive_group),
            AggregateColumn("Total +ve Percent", total_percent_agg_fn,
                            [AliasColumn("female-positive"), 
                             AliasColumn("male-positive"),
                             AliasColumn("male-total"), AliasColumn("female-total")],
                            header_group=positive_group),

            AggregateColumn("Male age range", age_fn,
                            [MinColumn("age", alias="male-min", filters= self.filters + [EQ("gender", "male")]),
                             MaxColumn("age", alias="male-max", filters= self.filters + [EQ("gender", "male")])],
                            header_group=age_range_group),
            AggregateColumn("FeMale age range", age_fn,
                            [MinColumn("age", alias="female-min", filters= self.filters + [EQ("gender", "female")]),
                             MaxColumn("age", alias="female-max", filters= self.filters + [EQ("gender", "female")])],
                            header_group=age_range_group),
            AggregateColumn("All age range", age_fn,
                            [MinColumn("age", alias="age-min", filters= self.filters + [OR([EQ("gender", "female"), EQ("gender", "male")])]),
                             MaxColumn("age", alias="age-max", filters= self.filters + [OR([EQ("gender", "female"), EQ("gender", "male")])])],
                            header_group=age_range_group),
        ]

class GSIDSQLByDayReport(GSIDSQLReport):
    name = "Day Summary Report"
    slug = "day_summary_sql"
    section_name = "day summary"

    @property
    def group_by(self):
        return super(GSIDSQLByDayReport, self).group_by + ["date"]

    @property
    def columns(self):
        return self.common_columns + [
                DatabaseColumn("Count", CountColumn("age", alias="day_count"))
            ]

    @property
    def startdate_obj(self):
        default_filter_values = super(GSIDSQLByDayReport, self).filter_values
        startdate = datetime.strptime(default_filter_values["startdate"], "%Y-%m-%dT%H:%M:%S")
        return startdate

    @property
    def enddate_obj(self):
        default_filter_values = super(GSIDSQLByDayReport, self).filter_values
        enddate = datetime.strptime(default_filter_values["enddate"], "%Y-%m-%dT%H:%M:%S")
        return enddate

    def daterange(self, start_date, end_date):
        for n in range(int ((end_date - start_date).days)):
            yield (start_date + timedelta(n)).strftime("%Y-%m-%d")

    @property
    def headers(self):
        startdate = self.startdate_obj
        enddate = self.enddate_obj

        column_headers = []
        group_by = self.group_by[:-1]
        for place in group_by:
            column_headers.append(DataTablesColumn(place))

        prev_month = startdate.month
        month_columns = [startdate.strftime("%B %Y")]
        for n, day in enumerate(self.daterange(startdate, enddate)):
            day_obj = datetime.strptime(day, "%Y-%m-%d")
            month = day_obj.month
            day_column = DataTablesColumn("Day%(n)s (%(day)s)" % {'n':n+1, 'day': day})

            if month == prev_month:
                month_columns.append(day_column)
            else:
                month_group = DataTablesColumnGroup(*month_columns)
                column_headers.append(month_group)
                month_columns = [day_obj.strftime("%B %Y")]
                month_columns.append(day_column)
                prev_month = month
        
        month_group = DataTablesColumnGroup(*month_columns)
        column_headers.append(month_group)

        return DataTablesHeader(*column_headers)

    @property
    def rows(self):
        startdate = self.startdate_obj
        enddate = self.enddate_obj

        old_data = self.data
        rows = []
        for loc_key in self.keys:
            row = [x for x in loc_key]
            for n, day in enumerate(self.daterange(startdate, enddate)):
                temp_key = [loc for loc in loc_key]
                temp_key.append(datetime.strptime(day, "%Y-%m-%d").date())
                keymap = old_data.get(tuple(temp_key), None)
                day_count = (keymap["day_count"] if keymap else None) or self.no_value
                row.append(day_count)
            rows.append(row)

        return rows

    """
    @property
    def columns(self):
        def daterange(start_date, end_date):
            for n in range(int ((end_date - start_date).days)):
                yield (start_date + timedelta(n)).strftime("%Y-%m-%d")
    
        default_filter_values = super(GSIDSQLByDayReport, self).filter_values
        print default_filter_values["startdate"]   
        startdate = datetime.strptime(default_filter_values["startdate"], "%Y-%m-%dT%H:%M:%S")
        enddate = datetime.strptime(default_filter_values["enddate"], "%Y-%m-%dT%H:%M:%S")
    
        columns = self.common_columns
        for n, day in enumerate(daterange(startdate, enddate)):
            default_filter_values["startdate"] = day
            default_filter_values["enddate"] = day
            self.filter_values = default_filter_values
            db_column = DatabaseColumn(
                            "Day%(n)s (%(day)s)" % {'n':n, 'day': day},
                            CountColumn("date", alias="day"+str(n), filters=self.filters)
                        )
            columns.append(db_column)

        return columns"""

    
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
                                [CountColumn("age", alias="zero_ten_" + gender, filters= self.filters + age_range_filter(gender, "zero", "ten")),
                                 CountColumn("age", alias=gender+"_total", filters= self.filters + [EQ("gender", gender)])],
                                header_group=age_range_group),
                AggregateColumn("10-20", percent_fn, 
                                [CountColumn("age", alias="ten_twenty_" + gender, filters= self.filters + age_range_filter(gender, "ten_plus", "twenty")),
                                 AliasColumn(gender+"_total")],
                                header_group=age_range_group),
                AggregateColumn("20-50", percent_fn,
                                [CountColumn("age", alias="twenty_fifty_" + gender, filters= self.filters + age_range_filter(gender, "twenty_plus", "fifty")),
                                AliasColumn(gender+"_total")],
                                header_group=age_range_group),
                AggregateColumn("50+", percent_fn,
                                [CountColumn("age", alias="fifty_" + gender, filters= self.filters + [AND([EQ("gender", gender), EQ("diagnosis", "positive"), GT("age", "fifty")])]),
                                AliasColumn(gender+"_total")],
                                header_group=age_range_group),
            ]

        return self.common_columns + generate_columns("male") + generate_columns("female")
