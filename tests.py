from django.test import TestCase

import datetime
from models import CalendarYear
from models import CalendarDay


class CalendarYearTest(TestCase):

    def test_create(self):
        day = datetime.date.today()
        year = day.year
        cal_year = CalendarYear(name=str(year), year_number=year)
        cal_year.clean()
        cal_year.save()
        delt = datetime.date(year, 12, 31) - datetime.date(year-1, 12, 31)
        day_count = CalendarDay.objects.filter(calendar_month__calendar_year__year_number=year).count()
        self.assertEquals(day_count, delt.days)

        test_day = datetime.date(year, 5, 1)
        cal_day = CalendarDay.objects.get(date=test_day)
        self.assertEquals(cal_day.week_day_number, test_day.isocalendar()[2])
        self.assertEquals(cal_day.calendar_week.week_number, test_day.isocalendar()[1])
        self.assertEquals(cal_day.calendar_month.month_number, 5)

        test_day = datetime.date(year, 1, 1)
        cal_day = CalendarDay.objects.get(date=test_day)
        self.assertEquals(cal_day.week_day_number, test_day.isocalendar()[2])
        self.assertIn(cal_day.calendar_week.week_number, (0, 1))
        self.assertEquals(cal_day.calendar_month.month_number, 1)

        test_day = datetime.date(year, 12, 31)
        cal_day = CalendarDay.objects.get(date=test_day)
        self.assertEquals(cal_day.week_day_number, test_day.isocalendar()[2])
        self.assertIn(cal_day.calendar_week.week_number, (52, 53, 54))
        self.assertEquals(cal_day.calendar_month.month_number, 12)
